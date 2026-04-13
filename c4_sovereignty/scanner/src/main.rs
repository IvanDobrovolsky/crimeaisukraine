use clap::Parser;
use flate2::read::GzDecoder;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::fs::{self, File};
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;

/// Fast scanner for Crimea-mentioning documents in C4/Dolma training corpora.
///
/// Two modes:
///   --input "glob"           Scan local gzipped JSONL files
///   --download ru --shards 4096  Download-scan-delete from HuggingFace
#[derive(Parser)]
#[command(name = "crimea-scanner", version)]
struct Args {
    /// Glob pattern for local input files
    #[arg(short, long)]
    input: Option<String>,

    /// Download mode: language code (en, ru, uk)
    #[arg(short, long)]
    download: Option<String>,

    /// Total number of shards (default 1024; ru=4096)
    #[arg(long, default_value = "1024")]
    shards: usize,

    /// Start shard index (default 0)
    #[arg(long, default_value = "0")]
    shard_start: usize,

    /// End shard index (inclusive; default = shards-1)
    #[arg(long)]
    shard_end: Option<usize>,

    /// HuggingFace token for authenticated downloads
    #[arg(long)]
    token: Option<String>,

    /// Output JSONL file
    #[arg(short, long)]
    output: String,

    /// Number of parallel threads
    #[arg(short, long, default_value = "16")]
    threads: usize,

    /// Temp directory for downloaded shards
    #[arg(long, default_value = "/tmp/crimea_scan_tmp")]
    tmpdir: String,
}

#[derive(Deserialize)]
struct InputDoc {
    text: String,
    #[serde(default)]
    url: String,
    #[serde(default)]
    timestamp: serde_json::Value,
}

#[derive(Serialize)]
struct OutputDoc {
    text: String,
    url: String,
    file: String,
}

const TERMS: &[&str] = &[
    "crimea", "crimean", "simferopol", "sevastopol", "yalta", "kerch",
    "feodosia", "evpatoria", "bakhchisarai", "dzhankoi", "alushta",
    "chersonesus", "chersonesos",
    "крым", "крымск", "симферопол", "севастопол", "ялт", "керч",
    "феодоси", "евпатори", "бахчисара", "джанкой", "алушт", "херсонес",
    "крим", "кримськ", "сімферопол", "євпаторі", "феодосі",
];

fn has_crimea_mention(text: &str) -> bool {
    let lower = text.to_lowercase();
    TERMS.iter().any(|t| lower.contains(t))
}

fn truncate_utf8(s: &str, max_bytes: usize) -> &str {
    if s.len() <= max_bytes {
        return s;
    }
    let mut end = max_bytes;
    while end > 0 && !s.is_char_boundary(end) {
        end -= 1;
    }
    &s[..end]
}

fn scan_gz_reader<R: std::io::Read>(reader: R, fname: &str) -> (Vec<OutputDoc>, u64, u64) {
    let decoder = GzDecoder::new(reader);
    let buf = BufReader::with_capacity(256 * 1024, decoder);
    let mut matches = Vec::new();
    let mut total: u64 = 0;
    let mut crimea: u64 = 0;

    for line in buf.lines() {
        let line = match line {
            Ok(l) => l,
            Err(_) => continue,
        };
        total += 1;
        let doc: InputDoc = match serde_json::from_str(&line) {
            Ok(d) => d,
            Err(_) => continue,
        };
        if has_crimea_mention(&doc.text) {
            crimea += 1;
            matches.push(OutputDoc {
                text: truncate_utf8(&doc.text, 3000).to_string(),
                url: doc.url,
                file: fname.to_string(),
            });
        }
    }
    (matches, total, crimea)
}

fn scan_local_file(path: &PathBuf) -> (Vec<OutputDoc>, u64, u64) {
    let file = match File::open(path) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("  ERROR {:?}: {}", path, e);
            return (vec![], 0, 0);
        }
    };
    let fname = path.file_name().unwrap_or_default().to_string_lossy().to_string();
    scan_gz_reader(file, &fname)
}

fn download_and_scan_shard(
    lang: &str,
    shard: usize,
    total_shards: usize,
    token: &Option<String>,
    tmpdir: &str,
) -> (Vec<OutputDoc>, u64, u64) {
    let filename = if lang == "en" {
        format!("en/c4-train.{:05}-of-{:05}.json.gz", shard, total_shards)
    } else {
        format!("multilingual/c4-{}.tfrecord-{:05}-of-{:05}.json.gz", lang, shard, total_shards)
    };

    let url = format!(
        "https://huggingface.co/datasets/allenai/c4/resolve/main/{}",
        filename
    );

    let client = reqwest::blocking::Client::builder()
        .timeout(std::time::Duration::from_secs(300))
        .build()
        .unwrap();

    let mut req = client.get(&url);
    if let Some(t) = token {
        req = req.header("Authorization", format!("Bearer {}", t));
    }

    let resp = match req.send() {
        Ok(r) => r,
        Err(e) => {
            eprintln!("  DOWNLOAD ERROR shard {}: {}", shard, e);
            return (vec![], 0, 0);
        }
    };

    if !resp.status().is_success() {
        eprintln!("  HTTP {} for shard {}", resp.status(), shard);
        return (vec![], 0, 0);
    }

    // Save to tmp file
    let tmp_path = format!("{}/shard_{:05}.json.gz", tmpdir, shard);
    let mut tmp_file = match File::create(&tmp_path) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("  FILE ERROR shard {}: {}", shard, e);
            return (vec![], 0, 0);
        }
    };

    let bytes = match resp.bytes() {
        Ok(b) => b,
        Err(e) => {
            eprintln!("  READ ERROR shard {}: {}", shard, e);
            let _ = fs::remove_file(&tmp_path);
            return (vec![], 0, 0);
        }
    };

    if std::io::copy(&mut bytes.as_ref(), &mut tmp_file).is_err() {
        let _ = fs::remove_file(&tmp_path);
        return (vec![], 0, 0);
    }
    drop(tmp_file);

    // Scan from disk
    let file = match File::open(&tmp_path) {
        Ok(f) => f,
        Err(_) => {
            let _ = fs::remove_file(&tmp_path);
            return (vec![], 0, 0);
        }
    };
    let shard_name = format!("c4-{}-{:05}", lang, shard);
    let result = scan_gz_reader(file, &shard_name);

    // Delete
    let _ = fs::remove_file(&tmp_path);

    result
}

fn main() {
    let args = Args::parse();

    rayon::ThreadPoolBuilder::new()
        .num_threads(args.threads)
        .build_global()
        .unwrap();

    let total_docs = AtomicU64::new(0);
    let crimea_docs = AtomicU64::new(0);
    let processed = AtomicU64::new(0);
    let output = Mutex::new(
        std::io::BufWriter::new(File::create(&args.output).expect("Cannot create output")),
    );

    if let Some(ref glob_pattern) = args.input {
        // LOCAL SCAN MODE
        let files: Vec<PathBuf> = glob::glob(glob_pattern)
            .expect("Invalid glob")
            .filter_map(|e| e.ok())
            .collect();

        eprintln!("LOCAL SCAN: {} files, {} threads", files.len(), args.threads);

        files.par_iter().for_each(|path| {
            let (matches, total, crimea) = scan_local_file(path);
            total_docs.fetch_add(total, Ordering::Relaxed);
            crimea_docs.fetch_add(crimea, Ordering::Relaxed);
            let done = processed.fetch_add(1, Ordering::Relaxed) + 1;

            if !matches.is_empty() {
                let mut out = output.lock().unwrap();
                for doc in &matches {
                    serde_json::to_writer(&mut *out, doc).unwrap();
                    out.write_all(b"\n").unwrap();
                }
            }

            if done % 50 == 0 || done == files.len() as u64 {
                eprintln!(
                    "  [{}/{}] docs={} crimea={}",
                    done, files.len(),
                    total_docs.load(Ordering::Relaxed),
                    crimea_docs.load(Ordering::Relaxed),
                );
            }
        });
    } else if let Some(ref lang) = args.download {
        // DOWNLOAD-SCAN-DELETE MODE
        let n = args.shards;
        let token = args.token.clone();

        fs::create_dir_all(&args.tmpdir).ok();
        eprintln!(
            "DOWNLOAD-SCAN-DELETE: c4-{}, {} shards, {} threads",
            lang, n, args.threads
        );

        let shard_end = args.shard_end.unwrap_or(n - 1);
        let shard_indices: Vec<usize> = (args.shard_start..=shard_end).collect();

        shard_indices.par_iter().for_each(|&shard| {
            let (matches, total, crimea) =
                download_and_scan_shard(lang, shard, n, &token, &args.tmpdir);
            total_docs.fetch_add(total, Ordering::Relaxed);
            crimea_docs.fetch_add(crimea, Ordering::Relaxed);
            let done = processed.fetch_add(1, Ordering::Relaxed) + 1;

            if !matches.is_empty() {
                let mut out = output.lock().unwrap();
                for doc in &matches {
                    serde_json::to_writer(&mut *out, doc).unwrap();
                    out.write_all(b"\n").unwrap();
                }
            }

            let total_to_scan = shard_indices.len();
            if done % 20 == 0 || done == total_to_scan as u64 {
                eprintln!(
                    "  [{}/{}] docs={} crimea={} shard={}",
                    done, total_to_scan,
                    total_docs.load(Ordering::Relaxed),
                    crimea_docs.load(Ordering::Relaxed),
                    shard,
                );
            }
        });
    } else {
        eprintln!("Error: specify --input or --download");
        std::process::exit(1);
    }

    eprintln!(
        "\nDONE: docs={} crimea={} → {}",
        total_docs.load(Ordering::Relaxed),
        crimea_docs.load(Ordering::Relaxed),
        args.output,
    );
}
