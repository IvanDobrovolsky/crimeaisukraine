use clap::Parser;
use flate2::read::GzDecoder;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::fs::File;
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};

/// Fast scanner for Crimea-mentioning documents in C4/Dolma training corpora.
/// Reads gzipped JSONL files, filters for Crimea terms, outputs matches.
#[derive(Parser)]
#[command(name = "crimea-scanner")]
#[command(about = "Scan training corpora for Crimea sovereignty framing")]
struct Args {
    /// Glob pattern for input files (e.g., "/tmp/c4_download/**/c4-ru.*.json.gz")
    #[arg(short, long)]
    input: String,

    /// Output JSONL file
    #[arg(short, long)]
    output: String,

    /// Number of parallel threads (default: number of CPUs)
    #[arg(short, long, default_value = "8")]
    threads: usize,
}

#[derive(Deserialize)]
struct InputDoc {
    text: String,
    #[serde(default)]
    url: String,
    #[serde(default)]
    timestamp: String,
}

#[derive(Serialize)]
struct OutputDoc {
    text: String,
    url: String,
    timestamp: String,
    file: String,
}

/// All Crimea-related terms — English, Russian, Ukrainian
const TERMS: &[&str] = &[
    // English
    "crimea", "crimean", "simferopol", "sevastopol", "yalta", "kerch",
    "feodosia", "evpatoria", "bakhchisarai", "dzhankoi", "alushta",
    "chersonesus", "chersonesos",
    // Russian
    "крым", "крымск", "симферопол", "севастопол", "ялт", "керч",
    "феодоси", "евпатори", "бахчисара", "джанкой", "алушт", "херсонес",
    // Ukrainian
    "крим", "кримськ", "сімферопол", "євпаторі", "феодосі",
];

fn has_crimea_mention(text: &str) -> bool {
    let lower = text.to_lowercase();
    TERMS.iter().any(|t| lower.contains(t))
}

fn scan_file(path: &PathBuf, total_docs: &AtomicU64, crimea_docs: &AtomicU64) -> Vec<OutputDoc> {
    let file = match File::open(path) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("  ERROR {:?}: {}", path, e);
            return vec![];
        }
    };

    let decoder = GzDecoder::new(file);
    let reader = BufReader::with_capacity(256 * 1024, decoder);
    let fname = path.file_name().unwrap_or_default().to_string_lossy().to_string();
    let mut matches = Vec::new();
    let mut local_total: u64 = 0;

    for line in reader.lines() {
        let line = match line {
            Ok(l) => l,
            Err(_) => continue,
        };
        local_total += 1;

        let doc: InputDoc = match serde_json::from_str(&line) {
            Ok(d) => d,
            Err(_) => continue,
        };

        if has_crimea_mention(&doc.text) {
            crimea_docs.fetch_add(1, Ordering::Relaxed);
            matches.push(OutputDoc {
                text: if doc.text.len() > 3000 {
                    let end = doc.text.char_indices().take_while(|(i, _)| *i < 3000).last().map(|(i, c)| i + c.len_utf8()).unwrap_or(doc.text.len());
                    doc.text[..end].to_string()
                } else { doc.text },
                url: doc.url,
                timestamp: doc.timestamp,
                file: fname.clone(),
            });
        }
    }

    total_docs.fetch_add(local_total, Ordering::Relaxed);
    matches
}

fn main() {
    let args = Args::parse();

    rayon::ThreadPoolBuilder::new()
        .num_threads(args.threads)
        .build_global()
        .unwrap();

    let files: Vec<PathBuf> = glob::glob(&args.input)
        .expect("Invalid glob pattern")
        .filter_map(|e| e.ok())
        .collect();

    eprintln!("Files: {}, Threads: {}", files.len(), args.threads);

    let total_docs = AtomicU64::new(0);
    let crimea_docs = AtomicU64::new(0);
    let processed = AtomicU64::new(0);

    let all_matches: Vec<Vec<OutputDoc>> = files
        .par_iter()
        .map(|path| {
            let matches = scan_file(path, &total_docs, &crimea_docs);
            let done = processed.fetch_add(1, Ordering::Relaxed) + 1;
            if done % 50 == 0 || done == files.len() as u64 {
                eprintln!(
                    "  [{}/{}] docs={} crimea={}", done, files.len(),
                    total_docs.load(Ordering::Relaxed), crimea_docs.load(Ordering::Relaxed),
                );
            }
            matches
        })
        .collect();

    let out = File::create(&args.output).expect("Cannot create output");
    let mut w = std::io::BufWriter::new(out);
    let mut written = 0u64;

    for batch in &all_matches {
        for doc in batch {
            serde_json::to_writer(&mut w, doc).unwrap();
            w.write_all(b"\n").unwrap();
            written += 1;
        }
    }

    eprintln!("\nDONE: {} files, {} docs, {} crimea matches → {}", files.len(), total_docs.load(Ordering::Relaxed), written, args.output);
}
