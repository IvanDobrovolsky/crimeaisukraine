use clap::Parser;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader, Write};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;

/// Categorize Russia-framing documents by origin (TLD) and type (Curlie + sanctions).
///
/// Uses:
///   - EU/US/UK sanctions lists for media classification (legally authoritative)
///   - TLD for country of origin (.ru/.ua/.com)
///   - Curlie/DMOZ full paths for domain type (news/commerce/education/etc.)
///
/// Usage:
///   crimea-categorize --input "data/classified_c4_*_rust.jsonl" --curlie /tmp/curlie_enriched.tsv
#[derive(Parser)]
#[command(name = "crimea-categorize", version)]
struct Args {
    /// Glob for classified JSONL files
    #[arg(short, long)]
    input: String,

    /// Curlie enriched TSV (domain\torigin\ttype\tpath)
    #[arg(long, default_value = "/tmp/curlie_enriched.tsv")]
    curlie: String,

    /// Output JSONL with per-doc categorization
    #[arg(short, long, default_value = "")]
    output: String,

    /// Number of threads
    #[arg(short, long, default_value = "8")]
    threads: usize,
}

#[derive(Deserialize)]
struct ClassifiedDoc {
    url: String,
    label: String,
    #[serde(default)]
    is_quoted: bool,
}

#[derive(Serialize)]
struct CategorizedDoc {
    url: String,
    origin: String,
    site_type: String,
    sanction: String,
}

// =========================================================================
// EU/US/UK SANCTIONED MEDIA — legally authoritative sources
// =========================================================================
// Each entry: (domain, entity_name, sanction_authority, regulation)

const SANCTIONED_MEDIA: &[(&str, &str, &str)] = &[
    // EU Wave 1 — Reg. 2022/350 (2 March 2022)
    ("rt.com", "RT (TV-Novosti)", "EU 2022/350, US EO14024, UK RUS1102"),
    ("russian.rt.com", "RT Russian", "EU 2022/350"),
    ("de.rt.com", "RT Germany", "EU 2022/350"),
    ("francais.rt.com", "RT France", "EU 2022/350"),
    ("actualidad.rt.com", "RT Spanish", "EU 2022/350"),
    ("arabic.rt.com", "RT Arabic", "EU 2023/427"),
    ("rtarabic.com", "RT Arabic", "EU 2023/427"),
    ("sputniknews.com", "Sputnik (Rossiya Segodnya)", "EU 2022/350, US EO14024, UK RUS1103"),
    ("sputnikglobe.com", "Sputnik", "EU 2022/350"),
    ("ruptly.tv", "Ruptly (RT subsidiary)", "US Foreign Mission"),
    // RT clone/mirror domains (post-ban)
    ("freedert.online", "RT mirror", "EU 2022/350"),
    ("dert.online", "RT mirror", "EU 2022/350"),
    ("rtde.live", "RT mirror", "EU 2022/350"),
    ("swentr.site", "RT mirror", "EU 2022/350"),
    ("rurtnews.com", "RT mirror", "EU 2022/350"),
    // EU Wave 2 — Reg. 2022/879 (25 June 2022)
    ("vesti.ru", "VGTRK (Rossiya 24)", "EU 2022/879, UK RUS1418"),
    ("rtr-planeta.com", "RTR Planeta (VGTRK)", "EU 2022/879"),
    // EU Wave 5 — Reg. 2023/1214 (23 June 2023)
    ("orientalreview.org", "Oriental Review", "EU 2023/1214"),
    ("tsargrad.tv", "Tsargrad", "EU 2023/1214, US EO14024, UK RUS1406"),
    ("journal-neo.org", "New Eastern Outlook", "EU 2023/1214"),
    ("katehon.com", "Katehon", "EU 2023/1214"),
    // EU Wave 6 — Reg. 2024/1428 (25 June 2024)
    ("voiceofeurope.com", "Voice of Europe", "EU 2024/1428"),
    ("ria.ru", "RIA Novosti (Rossiya Segodnya)", "EU 2024/1428, US Foreign Mission"),
    ("iz.ru", "Izvestia", "EU 2024/1428"),
    ("rg.ru", "Rossiyskaya Gazeta", "EU 2024/1428"),
    // EU Wave 7 — Reg. 2025/395 (25 February 2025)
    ("eadaily.com", "EADaily", "EU 2025/395"),
    ("fondsk.ru", "Fondsk", "EU 2025/395"),
    ("lenta.ru", "Lenta", "EU 2025/395"),
    ("news-front.info", "NewsFront", "EU 2025/395"),
    ("news-front.su", "NewsFront", "EU 2025/395"),
    ("rubaltic.ru", "RuBaltic", "EU 2025/395"),
    ("southfront.org", "SouthFront", "EU 2025/395, US CYBER2, UK RUS1383"),
    ("strategic-culture.org", "Strategic Culture Foundation", "EU 2025/395, US ELECTION-EO13848, UK RUS1381"),
    ("strategic-culture.su", "Strategic Culture Foundation", "EU 2025/395"),
    ("tvzvezda.ru", "Krasnaya Zvezda / TV Zvezda", "EU 2025/395"),
    ("redstar.ru", "Krasnaya Zvezda", "EU 2025/395"),
    // US-only sanctions (OFAC SDN)
    ("tass.com", "TASS", "US EO14024"),
    ("tass.ru", "TASS", "US EO14024"),
    ("usareally.com", "USA Really (IRA-linked)", "US CYBER2"),
    ("inforos.ru", "InfoRos (GRU-linked)", "US NPWMD/CYBER2, UK RUS1382"),
    ("inosmi.ru", "InoSMI (Rossiya Segodnya)", "US EO14024"),
    ("riafan.ru", "Federal News Agency (Prigozhin-linked)", "US CYBER2"),
    // Rossiya Segodnya subsidiaries
    ("ukraina.ru", "Ukraina.ru (Rossiya Segodnya)", "US EO14024"),
    ("baltnews.ee", "Baltnews (Rossiya Segodnya)", "US EO14024"),
    ("baltnews.lt", "Baltnews (Rossiya Segodnya)", "US EO14024"),
    ("baltnews.lv", "Baltnews (Rossiya Segodnya)", "US EO14024"),
];

fn classify_sanction(url: &str) -> (&'static str, &'static str) {
    let u = url.to_lowercase();
    for &(domain, entity, reg) in SANCTIONED_MEDIA {
        if u.contains(domain) {
            return (entity, reg);
        }
    }
    ("", "")
}

// =========================================================================
// TLD-based origin (100% reliable for ccTLDs)
// =========================================================================

fn classify_origin(domain: &str, url: &str) -> &'static str {
    let u = url.to_lowercase();
    if domain.ends_with(".ua") { return "ukrainian"; }
    if domain.ends_with(".ru") || domain.ends_with(".su") { return "russian"; }
    if u.contains(".gov.ru") || u.contains(".edu.ru") || u.contains(".ac.ru") { return "russian"; }
    if u.contains(".gov.ua") || u.contains(".edu.ua") { return "ukrainian"; }
    if domain.ends_with(".uk") || domain.ends_with(".co.uk") { return "british"; }
    if domain.ends_with(".de") { return "german"; }
    if domain.ends_with(".fr") { return "french"; }
    if domain.ends_with(".eu") { return "european"; }
    "international"
}

// =========================================================================
// TLD-based institutional type
// =========================================================================

fn classify_institution(url: &str) -> &'static str {
    let u = url.to_lowercase();
    if u.contains(".gov.") || u.ends_with(".gov") { return "government"; }
    if u.contains(".edu.") || u.ends_with(".edu") || u.contains(".ac.") { return "education"; }
    if u.contains(".mil.") || u.ends_with(".mil") { return "military"; }
    ""
}

/// URL pattern matching for known platforms (reproducible, no external DB needed)
fn classify_url_pattern(url: &str, domain: &str) -> &'static str {
    let u = url.to_lowercase();
    // Blog platforms
    if domain.contains("livejournal") || domain.contains("blogspot")
        || domain.contains("wordpress.com") || domain.contains("tumblr.com") { return "blog"; }
    // Social media
    if domain == "vk.com" || domain == "m.vk.com" || domain == "ok.ru"
        || domain.contains("t.me") || domain.contains("facebook.com")
        || domain.contains("twitter.com") || domain.contains("instagram.com")
        || domain.contains("youtube.com") { return "social_media"; }
    // Wikipedia / encyclopedia
    if domain.contains("wikipedia.org") { return "encyclopedia"; }
    // Maps / navigation
    if domain.contains("openstreetmap") || domain.contains("wikimapia")
        || u.contains("yandex.ru/maps") || domain.contains("mapsroad")
        || domain.contains("maps.google") { return "maps"; }
    // Weather
    if domain.contains("gismeteo") || domain.contains("weather.com")
        || domain.contains("accuweather") || domain.contains("foreca") { return "weather"; }
    // Travel / hotels
    if domain.contains("booking.com") || domain.contains("tripadvisor")
        || domain.contains("turbina.ru") || u.contains("travel.yandex")
        || domain.contains("level.travel") || domain.contains("hotels.com")
        || domain.contains("airbnb") { return "travel"; }
    // Real estate
    if domain.contains("restate.ru") || domain.contains("mirkvartir")
        || domain.contains("cian.ru") || domain.contains("domofond") { return "real_estate"; }
    // Classifieds
    if domain.contains("avito.ru") || domain.contains("bizorg")
        || domain.contains("board.") || domain.contains("catalog.") { return "classifieds"; }
    // Auto
    if domain.contains("drom.ru") || domain.contains("auto.ru")
        || domain.contains("lada.ru") { return "auto"; }
    // Jobs
    if domain.contains("jooble") || domain.contains("hh.ru")
        || domain.contains("employmentcenter") { return "jobs"; }
    // Finance
    if domain.contains("banki.ru") { return "finance"; }
    // Dating
    if domain.contains("mylove.ru") || domain.contains("znakomstva")
        || domain.contains("passiya") { return "dating"; }
    // News portals / aggregators
    if domain.contains("news.rambler") || domain.contains("news.mail.ru")
        || domain.contains("dzen.ru") || domain.contains("zen.yandex")
        || domain.contains("newsru.com") || domain.contains("dailysmi") { return "news_aggregator"; }
    // Russian portals
    if domain == "yandex.ru" || domain == "mail.ru" || domain == "rambler.ru" { return "portal"; }
    // Known Russian news (not sanctioned but identifiable)
    if domain.contains("interfax.ru") || domain.contains("rbc.ru")
        || domain.contains("vedomosti.ru") || domain.contains("gazeta.ru")
        || domain.contains("mk.ru") || domain.contains("pravda.ru")
        || domain.contains("fedpress.ru") || domain.contains("rueconomics")
        || domain.contains("politnavigator") || domain.contains("ren.tv")
        || domain.contains("nsn.fm") || domain.contains("ura.news")
        || domain.contains("politexpert") || domain.contains("cont.ws") { return "news_ru_other"; }
    // Independent Russian news
    if domain.contains("tvrain.ru") || domain.contains("novayagazeta")
        || domain.contains("meduza") { return "news_ru_independent"; }
    // Ukrainian news/portals (on .com/.org domains)
    if domain.contains("korrespondent.net") || domain.contains("censor.net.ua")
        || domain.contains("unian") || domain.contains("gordonua")
        || domain.contains("pravda.com.ua") || domain.contains("hromadske")
        || domain.contains("for-ua.info") { return "news_ua"; }
    // Education
    if domain.contains("infourok") { return "education"; }
    // Government (Crimea occupation admin)
    if domain.contains("sevproc.ru") || domain.contains("rk.gov.ru") { return "government_crimea"; }
    ""
}

fn extract_domain(url: &str) -> String {
    let u = url.to_lowercase();
    let after = if let Some(pos) = u.find("://") { &u[pos + 3..] } else { &u };
    let host = after.split('/').next().unwrap_or("").split('?').next().unwrap_or("");
    if host.starts_with("www.") { host[4..].to_string() } else { host.to_string() }
}

fn parent_domain(d: &str) -> String {
    let parts: Vec<&str> = d.split('.').collect();
    if parts.len() >= 2 { parts[parts.len()-2..].join(".") } else { d.to_string() }
}

fn main() {
    let args = Args::parse();

    rayon::ThreadPoolBuilder::new()
        .num_threads(args.threads)
        .build_global()
        .unwrap();

    // Load Curlie enriched (domain → origin, type)
    eprintln!("Loading Curlie...");
    let mut curlie: HashMap<String, (String, String)> = HashMap::new();
    if let Ok(file) = File::open(&args.curlie) {
        for line in BufReader::new(file).lines().flatten() {
            let parts: Vec<&str> = line.splitn(4, '\t').collect();
            if parts.len() >= 3 {
                curlie.insert(parts[0].to_string(), (parts[1].to_string(), parts[2].to_string()));
            }
        }
    }
    eprintln!("  Curlie: {} domains", curlie.len());

    let files: Vec<std::path::PathBuf> = glob::glob(&args.input)
        .expect("Invalid glob")
        .filter_map(|e| e.ok())
        .collect();

    eprintln!("Processing {} files...", files.len());

    // Counters: (origin, type) and (sanction_entity)
    let origin_type: Mutex<HashMap<(String, String), u64>> = Mutex::new(HashMap::new());
    let sanctions: Mutex<HashMap<String, u64>> = Mutex::new(HashMap::new());
    let origins: Mutex<HashMap<String, u64>> = Mutex::new(HashMap::new());
    let types: Mutex<HashMap<String, u64>> = Mutex::new(HashMap::new());
    let total_ru = AtomicU64::new(0);
    let total_all = AtomicU64::new(0);
    let sanctioned_total = AtomicU64::new(0);

    let output_file: Option<Mutex<std::io::BufWriter<File>>> = if !args.output.is_empty() {
        Some(Mutex::new(std::io::BufWriter::new(
            File::create(&args.output).expect("Cannot create output"),
        )))
    } else {
        None
    };

    let curlie_ref = &curlie;

    files.par_iter().for_each(|path| {
        let file = match File::open(path) { Ok(f) => f, Err(_) => return };
        let reader = BufReader::with_capacity(512 * 1024, file);

        let mut local_ot: HashMap<(String, String), u64> = HashMap::new();
        let mut local_sanctions: HashMap<String, u64> = HashMap::new();
        let mut local_origins: HashMap<String, u64> = HashMap::new();
        let mut local_types: HashMap<String, u64> = HashMap::new();
        let mut local_ru: u64 = 0;
        let mut local_all: u64 = 0;
        let mut local_sanctioned: u64 = 0;
        let mut local_output: Vec<CategorizedDoc> = Vec::new();

        for line in reader.lines() {
            let line = match line { Ok(l) => l, Err(_) => continue };
            local_all += 1;
            let doc: ClassifiedDoc = match serde_json::from_str(&line) { Ok(d) => d, Err(_) => continue };
            if doc.label != "russia" { continue; }
            local_ru += 1;

            let domain = extract_domain(&doc.url);
            let parent = parent_domain(&domain);

            // 1. Check sanctions
            let (entity, regulation) = classify_sanction(&doc.url);
            let sanction_str = if !entity.is_empty() {
                local_sanctioned += 1;
                *local_sanctions.entry(entity.to_string()).or_insert(0) += 1;
                format!("{} [{}]", entity, regulation)
            } else {
                String::new()
            };

            // 2. Origin from TLD
            let origin = classify_origin(&domain, &doc.url);

            // 3. Type: institution first, then Curlie
            let inst = classify_institution(&doc.url);
            let site_type = if !inst.is_empty() {
                inst
            } else if !entity.is_empty() {
                "sanctioned_media"
            } else {
                // URL pattern matching (known platforms)
                let url_pat = classify_url_pattern(&doc.url, &domain);
                if !url_pat.is_empty() {
                    url_pat
                } else {
                // Curlie lookup
                let co = curlie_ref.get(&domain)
                    .or_else(|| curlie_ref.get(&parent));
                match co {
                    Some((_, t)) => match t.as_str() {
                        "news" => "news",
                        "commerce" => "commerce",
                        "education" => "education",
                        "society" => "society_org",
                        "culture" => "culture",
                        "travel" => "travel",
                        "health" => "health",
                        "tech" => "tech",
                        "sports" => "sports",
                        "blog" => "blog",
                        "government" => "government",
                        _ => "other_categorized",
                    },
                    None => "uncategorized",
                }
            }};

            *local_ot.entry((origin.to_string(), site_type.to_string())).or_insert(0) += 1;
            *local_origins.entry(origin.to_string()).or_insert(0) += 1;
            *local_types.entry(site_type.to_string()).or_insert(0) += 1;

            if output_file.is_some() {
                local_output.push(CategorizedDoc {
                    url: doc.url,
                    origin: origin.to_string(),
                    site_type: site_type.to_string(),
                    sanction: sanction_str,
                });
            }
        }

        // Write output
        if let Some(ref out) = output_file {
            let mut w = out.lock().unwrap();
            for doc in &local_output {
                serde_json::to_writer(&mut *w, doc).unwrap();
                w.write_all(b"\n").unwrap();
            }
        }

        // Merge counters
        total_ru.fetch_add(local_ru, Ordering::Relaxed);
        total_all.fetch_add(local_all, Ordering::Relaxed);
        sanctioned_total.fetch_add(local_sanctioned, Ordering::Relaxed);

        let mut g = origin_type.lock().unwrap();
        for (k, v) in local_ot { *g.entry(k).or_insert(0) += v; }
        drop(g);
        let mut g = sanctions.lock().unwrap();
        for (k, v) in local_sanctions { *g.entry(k).or_insert(0) += v; }
        drop(g);
        let mut g = origins.lock().unwrap();
        for (k, v) in local_origins { *g.entry(k).or_insert(0) += v; }
        drop(g);
        let mut g = types.lock().unwrap();
        for (k, v) in local_types { *g.entry(k).or_insert(0) += v; }

        eprintln!("  DONE [{}] {}/{} russia, {} sanctioned",
            path.file_name().unwrap_or_default().to_string_lossy(),
            local_ru, local_all, local_sanctioned);
    });

    let total = total_ru.load(Ordering::Relaxed);
    let sanct = sanctioned_total.load(Ordering::Relaxed);

    // Print results
    eprintln!("\n{}", "=".repeat(75));
    eprintln!("RUSSIA-FRAMING SOURCE CATEGORIZATION");
    eprintln!("  Sources: EU Council Regulations, US OFAC/EO14024, UK OFSI");
    eprintln!("           Curlie/DMOZ (1.96M domains), TLD country codes");
    eprintln!("{}", "=".repeat(75));
    eprintln!("  Total Russia-framing: {:>10}", total);
    eprintln!("  EU/US/UK sanctioned:  {:>10} ({:.1}%)", sanct, sanct as f64 / total as f64 * 100.0);

    // Sanctioned entities breakdown
    eprintln!("\n{}", "-".repeat(75));
    eprintln!("  SANCTIONED MEDIA IN C4 TRAINING DATA");
    eprintln!("{}", "-".repeat(75));
    let g = sanctions.lock().unwrap();
    let mut sv: Vec<_> = g.iter().collect();
    sv.sort_by(|a, b| b.1.cmp(a.1));
    for (entity, count) in &sv {
        eprintln!("    {:>6} {}", count, entity);
    }

    // Origin breakdown
    eprintln!("\n{}", "-".repeat(75));
    eprintln!("  BY ORIGIN (TLD-based)");
    eprintln!("{}", "-".repeat(75));
    let g = origins.lock().unwrap();
    let mut ov: Vec<_> = g.iter().collect();
    ov.sort_by(|a, b| b.1.cmp(a.1));
    for (origin, count) in &ov {
        let pct = **count as f64 / total as f64 * 100.0;
        eprintln!("    {:20} {:>8} ({:.1}%)", origin, count, pct);
    }

    // Type breakdown
    eprintln!("\n{}", "-".repeat(75));
    eprintln!("  BY TYPE (Curlie + TLD heuristics)");
    eprintln!("{}", "-".repeat(75));
    let g = types.lock().unwrap();
    let mut tv: Vec<_> = g.iter().collect();
    tv.sort_by(|a, b| b.1.cmp(a.1));
    let categorized: u64 = tv.iter()
        .filter(|(t, _)| t.as_str() != "uncategorized")
        .map(|(_, c)| **c)
        .sum();
    for (stype, count) in &tv {
        let pct = **count as f64 / total as f64 * 100.0;
        eprintln!("    {:20} {:>8} ({:.1}%)", stype, count, pct);
    }
    eprintln!("{}", "-".repeat(75));
    eprintln!("    {:20} {:>8} ({:.1}%)", "CATEGORIZED", categorized, categorized as f64 / total as f64 * 100.0);
    eprintln!("    {:20} {:>8} ({:.1}%)", "UNCATEGORIZED", total - categorized, (total - categorized) as f64 / total as f64 * 100.0);

    // Cross-tab
    eprintln!("\n{}", "=".repeat(75));
    eprintln!("  CROSS-TAB: ORIGIN x TYPE (top cells)");
    eprintln!("{}", "=".repeat(75));
    let g = origin_type.lock().unwrap();
    let mut cv: Vec<_> = g.iter().collect();
    cv.sort_by(|a, b| b.1.cmp(a.1));
    eprintln!("    {:20} {:20} {:>8} {:>6}", "Origin", "Type", "Count", "%");
    eprintln!("    {}", "-".repeat(55));
    for ((origin, stype), count) in cv.iter().take(25) {
        let pct = **count as f64 / total as f64 * 100.0;
        eprintln!("    {:20} {:20} {:>8} {:>5.1}%", origin, stype, count, pct);
    }
}
