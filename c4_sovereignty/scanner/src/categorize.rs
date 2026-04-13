use clap::Parser;
use rayon::prelude::*;
use serde::Deserialize;
use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader, Write};
use std::sync::Mutex;

/// Categorize Russia-framing documents by domain using external databases.
///
/// Loads: Curlie (1.96M domains), GDELT news (33K), UT1 blacklist (44K), TLD heuristics.
/// Reads classified JSONL and outputs source category breakdown.
#[derive(Parser)]
#[command(name = "crimea-categorize", version)]
struct Args {
    /// Glob for classified JSONL files
    #[arg(short, long)]
    input: String,

    /// Curlie domain TSV (domain\tcategory)
    #[arg(long, default_value = "/tmp/curlie_domains.tsv")]
    curlie: String,

    /// GDELT domains file
    #[arg(long, default_value = "/tmp/gdelt_domains.txt")]
    gdelt: String,

    /// UT1 blacklist directory
    #[arg(long, default_value = "/tmp/ut1/blacklists")]
    ut1: String,

    /// Number of threads
    #[arg(short, long, default_value = "8")]
    threads: usize,
}

#[derive(Deserialize)]
struct ClassifiedDoc {
    url: String,
    label: String,
    #[serde(default)]
    source_type: String,
}

fn load_curlie(path: &str) -> HashMap<String, String> {
    let mut map = HashMap::new();
    if let Ok(file) = File::open(path) {
        for line in BufReader::new(file).lines().flatten() {
            let parts: Vec<&str> = line.splitn(2, '\t').collect();
            if parts.len() == 2 {
                map.insert(parts[0].to_string(), parts[1].to_string());
            }
        }
    }
    eprintln!("  Curlie: {} domains", map.len());
    map
}

fn load_gdelt(path: &str) -> HashMap<String, String> {
    let mut map = HashMap::new();
    if let Ok(file) = File::open(path) {
        for line in BufReader::new(file).lines().flatten() {
            let parts: Vec<&str> = line.split('\t').collect();
            if parts.len() >= 3 {
                map.insert(parts[0].trim().to_lowercase(), parts[2].trim().to_string());
            }
        }
    }
    eprintln!("  GDELT: {} domains", map.len());
    map
}

fn load_ut1(dir: &str) -> HashMap<String, String> {
    let mut map = HashMap::new();
    for cat in &["press", "blog", "forums", "shopping", "fakenews"] {
        let path = format!("{}/{}/domains", dir, cat);
        if let Ok(file) = File::open(&path) {
            for line in BufReader::new(file).lines().flatten() {
                let d = line.trim().to_lowercase();
                if !d.is_empty() {
                    map.insert(d, cat.to_string());
                }
            }
        }
    }
    eprintln!("  UT1: {} domains", map.len());
    map
}

fn extract_domain(url: &str) -> String {
    let u = url.to_lowercase();
    let after_proto = if let Some(pos) = u.find("://") {
        &u[pos + 3..]
    } else {
        &u
    };
    let host = after_proto.split('/').next().unwrap_or("");
    let host = host.split('?').next().unwrap_or(host);
    if host.starts_with("www.") {
        host[4..].to_string()
    } else {
        host.to_string()
    }
}

fn parent_domain(domain: &str) -> Option<String> {
    let parts: Vec<&str> = domain.split('.').collect();
    if parts.len() >= 2 {
        Some(parts[parts.len() - 2..].join("."))
    } else {
        None
    }
}

fn main() {
    let args = Args::parse();

    rayon::ThreadPoolBuilder::new()
        .num_threads(args.threads)
        .build_global()
        .unwrap();

    eprintln!("Loading databases...");
    let curlie = load_curlie(&args.curlie);
    let gdelt = load_gdelt(&args.gdelt);
    let ut1 = load_ut1(&args.ut1);

    let files: Vec<std::path::PathBuf> = glob::glob(&args.input)
        .expect("Invalid glob")
        .filter_map(|e| e.ok())
        .collect();

    eprintln!("Processing {} files...", files.len());

    let counts: Mutex<HashMap<String, u64>> = Mutex::new(HashMap::new());
    let total_ru = std::sync::atomic::AtomicU64::new(0);
    let total_all = std::sync::atomic::AtomicU64::new(0);

    files.par_iter().for_each(|path| {
        let file = match File::open(path) {
            Ok(f) => f,
            Err(_) => return,
        };
        let reader = BufReader::with_capacity(512 * 1024, file);
        let mut local_counts: HashMap<String, u64> = HashMap::new();
        let mut local_ru: u64 = 0;
        let mut local_all: u64 = 0;

        for line in reader.lines() {
            let line = match line {
                Ok(l) => l,
                Err(_) => continue,
            };
            local_all += 1;

            let doc: ClassifiedDoc = match serde_json::from_str(&line) {
                Ok(d) => d,
                Err(_) => continue,
            };

            if doc.label != "russia" {
                continue;
            }
            local_ru += 1;

            let domain = extract_domain(&doc.url);
            let parent = parent_domain(&domain);
            let url_lower = doc.url.to_lowercase();

            // Already classified by source_type
            let cat = if doc.source_type == "state_t1" {
                "State media (RT/Sputnik/TASS)".to_string()
            } else if doc.source_type == "proxy_t2" {
                "GEC proxy outlets".to_string()
            } else if doc.source_type == "state_adj_t4" {
                "Russian state-adjacent".to_string()
            }
            // TLD heuristics
            else if url_lower.contains(".gov.") || url_lower.ends_with(".gov") {
                "Government".to_string()
            } else if url_lower.contains(".edu.") || url_lower.ends_with(".edu")
                || url_lower.contains(".ac.") {
                "Education/Academic".to_string()
            }
            // GDELT news
            else if let Some(country) = gdelt.get(&domain).or_else(|| parent.as_ref().and_then(|p| gdelt.get(p))) {
                if country.contains("Russia") {
                    "News: Russian".to_string()
                } else if country.contains("Ukraine") {
                    "News: Ukrainian".to_string()
                } else {
                    "News: International".to_string()
                }
            }
            // UT1
            else if let Some(cat) = ut1.get(&domain).or_else(|| parent.as_ref().and_then(|p| ut1.get(p))) {
                format!("UT1: {}", cat)
            }
            // Curlie
            else if let Some(cat) = curlie.get(&domain).or_else(|| parent.as_ref().and_then(|p| curlie.get(p))) {
                match cat.as_str() {
                    "Business" => "Business/Commerce".to_string(),
                    "Society" => "Society/Organizations".to_string(),
                    "Arts" => "Arts/Culture".to_string(),
                    "Top" | "NorthAmerica" | "Europe" | "Regional" => "Regional portal".to_string(),
                    _ => format!("Curlie: {}", cat),
                }
            }
            // Fallback
            else if domain.ends_with(".ru") || domain.ends_with(".su") {
                "Russian web (uncategorized)".to_string()
            } else {
                "International web (uncategorized)".to_string()
            };

            *local_counts.entry(cat).or_insert(0) += 1;
        }

        // Merge into global
        total_ru.fetch_add(local_ru, std::sync::atomic::Ordering::Relaxed);
        total_all.fetch_add(local_all, std::sync::atomic::Ordering::Relaxed);
        let mut global = counts.lock().unwrap();
        for (k, v) in local_counts {
            *global.entry(k).or_insert(0) += v;
        }

        eprintln!(
            "  DONE [{}] {}/{} russia-framing",
            path.file_name().unwrap_or_default().to_string_lossy(),
            local_ru, local_all
        );
    });

    let total = total_ru.load(std::sync::atomic::Ordering::Relaxed);
    let global = counts.lock().unwrap();

    // Sort by count descending
    let mut sorted: Vec<_> = global.iter().collect();
    sorted.sort_by(|a, b| b.1.cmp(a.1));

    eprintln!("\n{}", "=".repeat(70));
    eprintln!("RUSSIA-FRAMING SOURCE CATEGORIZATION (database-enriched)");
    eprintln!("{}", "=".repeat(70));
    eprintln!("  Total Russia-framing docs: {:>10}", total);
    eprintln!("{}", "-".repeat(70));
    eprintln!("  {:45} {:>8} {:>7}", "Category", "Count", "%");
    eprintln!("{}", "-".repeat(70));

    let mut categorized: u64 = 0;
    for (cat, count) in &sorted {
        let pct = **count as f64 / total as f64 * 100.0;
        if **count >= 10 {
            eprintln!("  {:45} {:>8} {:>6.1}%", cat, count, pct);
        }
        if !cat.contains("uncategorized") {
            categorized += **count;
        }
    }
    let uncategorized = total - categorized;
    eprintln!("{}", "-".repeat(70));
    eprintln!(
        "  {:45} {:>8} {:>6.1}%",
        "CATEGORIZED",
        categorized,
        categorized as f64 / total as f64 * 100.0
    );
    eprintln!(
        "  {:45} {:>8} {:>6.1}%",
        "UNCATEGORIZED",
        uncategorized,
        uncategorized as f64 / total as f64 * 100.0
    );
}
