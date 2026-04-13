use clap::Parser;
use flate2::read::GzDecoder;
use rayon::prelude::*;
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::fs::File;
use std::io::{BufRead, BufReader, Write};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;

/// Scan JSONL files for academic contamination evidence in Crimea training data.
///
/// Detects DOIs, academic domain URLs, and citation patterns to identify
/// scholarly content that may have leaked into web corpora.
///
/// Usage:
///   crimea-doi-grep --input "data/c4_*.jsonl" --output data/academic_contamination.jsonl
#[derive(Parser)]
#[command(name = "crimea-doi-grep", version)]
struct Args {
    /// Glob pattern for input JSONL files (supports .jsonl and .jsonl.gz)
    #[arg(short, long)]
    input: String,

    /// Output JSONL file
    #[arg(short, long)]
    output: String,

    /// Number of parallel threads
    #[arg(short, long, default_value = "8")]
    threads: usize,
}

#[derive(Deserialize)]
struct InputDoc {
    text: String,
    #[serde(default)]
    url: String,
    #[serde(default)]
    file: String,
}

#[derive(Serialize)]
struct OutputDoc {
    url: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    doi: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    academic_domain: Option<String>,
    citation_count: u32,
    text_preview: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    file: Option<String>,
}

// =========================================================================
// Academic domain list
// =========================================================================

const ACADEMIC_DOMAINS: &[&str] = &[
    "jstor.org",
    "springer.com",
    "wiley.com",
    "sciencedirect.com",
    "researchgate.net",
    "academia.edu",
    "arxiv.org",
    "doi.org",
    "semantic-scholar",
    "s2-research",
    "ncbi.nlm.nih.gov",
    "pubmed",
    "scopus.com",
    "tandfonline.com",
    "sagepub.com",
    "cambridge.org",
    "oxford.ac.uk",
    "oup.com",
    "nature.com",
    "science.org",
    "elsevier.com",
    "mdpi.com",
    "frontiersin.org",
    "plos.org",
    "biorxiv.org",
    "ssrn.com",
];

// =========================================================================
// Pattern builders
// =========================================================================

struct AcademicDetector {
    doi_re: Regex,
    citation_patterns: Vec<Regex>,
}

impl AcademicDetector {
    fn new() -> Self {
        // DOI pattern: 10.XXXX/YYYY where XXXX is 4+ digits and YYYY is the suffix
        // Using \b word boundary instead of lookahead/lookbehind (not supported by regex crate)
        let doi_re = Regex::new(r"\b10\.\d{4,}/[^\s\]>)}\x22]+").unwrap();

        // Citation patterns - common academic citation formats
        let citation_pats: &[&str] = &[
            // Parenthetical author-year: (Author, 2020) or (Author et al., 2020)
            r"\([A-Z][a-z]+(?:\s+(?:et\s+al\.)?)?,\s*\d{4}\)",
            // Bracketed numeric: [1], [2,3], [1-5]
            r"\[\d+(?:\s*[,\-]\s*\d+)*\]",
            // "et al." in running text
            r"\bet\s+al\.\b",
            // "Journal of ..." — title-case journal names
            r"\bJournal\s+of\s+[A-Z]",
            // Volume/issue notation: Vol. 12, No. 3
            r"\bVol\.\s*\d+",
            // Page ranges: pp. 123-456
            r"\bpp\.\s*\d+",
            // ISSN
            r"\bISSN\s*:?\s*\d{4}-?\d{3}[\dXx]",
            // ISBN
            r"\bISBN\s*:?\s*(?:978|979)[\d\- ]{10,}",
        ];

        let citation_patterns: Vec<Regex> = citation_pats
            .iter()
            .map(|p| Regex::new(p).unwrap())
            .collect();

        AcademicDetector {
            doi_re,
            citation_patterns,
        }
    }

    /// Extract the first DOI found in text, if any.
    fn extract_doi(&self, text: &str) -> Option<String> {
        self.doi_re.find(text).map(|m| {
            let raw = m.as_str();
            // Trim trailing punctuation that may have been captured
            raw.trim_end_matches(|c: char| c == '.' || c == ',' || c == ';' || c == ':')
                .to_string()
        })
    }

    /// Check URL against academic domain list, return matched domain.
    fn match_academic_domain(&self, url: &str) -> Option<String> {
        let lower = url.to_lowercase();
        for &domain in ACADEMIC_DOMAINS {
            if lower.contains(domain) {
                return Some(domain.to_string());
            }
        }
        None
    }

    /// Count how many distinct citation patterns fire in the text.
    fn count_citations(&self, text: &str) -> u32 {
        let mut count: u32 = 0;
        for pat in &self.citation_patterns {
            count += pat.find_iter(text).count() as u32;
        }
        count
    }

    /// Returns true if this document has any academic signal.
    fn has_signal(&self, text: &str, url: &str) -> bool {
        self.doi_re.is_match(text)
            || self.match_academic_domain(url).is_some()
            || self.citation_patterns.iter().any(|p| p.is_match(text))
    }
}

// =========================================================================
// Safe text preview (UTF-8 boundary aware)
// =========================================================================

fn safe_preview(text: &str, max_chars: usize) -> String {
    if text.len() <= max_chars {
        return text.to_string();
    }
    // Walk forward to find a char boundary at or before max_chars bytes
    let mut end = max_chars;
    while end > 0 && !text.is_char_boundary(end) {
        end -= 1;
    }
    // Try to also respect char count (not just byte count)
    let preview: String = text.chars().take(max_chars).collect();
    if preview.len() > end {
        text[..end].to_string()
    } else {
        preview
    }
}

// =========================================================================
// File reader (plain or gzipped)
// =========================================================================

fn open_reader(path: &std::path::Path) -> Box<dyn BufRead + Send> {
    let file = File::open(path).expect("Cannot open file");
    if path.extension().map_or(false, |e| e == "gz") {
        Box::new(BufReader::with_capacity(512 * 1024, GzDecoder::new(file)))
    } else {
        Box::new(BufReader::with_capacity(512 * 1024, file))
    }
}

// =========================================================================
// Main
// =========================================================================

fn main() {
    let args = Args::parse();

    rayon::ThreadPoolBuilder::new()
        .num_threads(args.threads)
        .build_global()
        .unwrap();

    let files: Vec<std::path::PathBuf> = glob::glob(&args.input)
        .expect("Invalid glob pattern")
        .filter_map(|e| e.ok())
        .collect();

    if files.is_empty() {
        eprintln!("ERROR: no files matched pattern '{}'", args.input);
        std::process::exit(1);
    }

    eprintln!(
        "DOI-GREP: {} files, {} threads",
        files.len(),
        args.threads
    );

    // Global counters
    let total_docs = AtomicU64::new(0);
    let docs_with_doi = AtomicU64::new(0);
    let docs_from_academic = AtomicU64::new(0);
    let docs_with_citations = AtomicU64::new(0);
    let docs_with_any_signal = AtomicU64::new(0);
    let parse_errors = AtomicU64::new(0);

    let output = Mutex::new(std::io::BufWriter::with_capacity(
        1024 * 1024,
        File::create(&args.output).expect("Cannot create output file"),
    ));

    files.par_iter().for_each(|path| {
        let detector = AcademicDetector::new();
        let reader = open_reader(path);
        let fname = path
            .file_name()
            .unwrap_or_default()
            .to_string_lossy()
            .to_string();

        let mut local_results: Vec<OutputDoc> = Vec::new();
        let mut local_total: u64 = 0;
        let mut local_doi: u64 = 0;
        let mut local_academic: u64 = 0;
        let mut local_citation: u64 = 0;
        let mut local_any: u64 = 0;
        let mut local_errors: u64 = 0;

        for line in reader.lines() {
            let line = match line {
                Ok(l) => l,
                Err(_) => continue,
            };
            if line.trim().is_empty() {
                continue;
            }
            local_total += 1;

            let doc: InputDoc = match serde_json::from_str(&line) {
                Ok(d) => d,
                Err(_) => {
                    local_errors += 1;
                    continue;
                }
            };

            // Quick check: skip docs with no academic signal at all
            if !detector.has_signal(&doc.text, &doc.url) {
                continue;
            }

            let doi = detector.extract_doi(&doc.text);
            let academic_domain = detector.match_academic_domain(&doc.url);
            let citation_count = detector.count_citations(&doc.text);

            let has_doi = doi.is_some();
            let has_academic = academic_domain.is_some();
            let has_citations = citation_count > 0;

            if has_doi {
                local_doi += 1;
            }
            if has_academic {
                local_academic += 1;
            }
            if has_citations {
                local_citation += 1;
            }
            local_any += 1;

            let text_preview = safe_preview(&doc.text, 500);

            local_results.push(OutputDoc {
                url: doc.url,
                doi,
                academic_domain,
                citation_count,
                text_preview,
                file: if doc.file.is_empty() {
                    None
                } else {
                    Some(doc.file)
                },
            });

            if local_total % 500_000 == 0 {
                eprintln!(
                    "  [{}] {} docs, doi={} academic={} citations={}",
                    fname, local_total, local_doi, local_academic, local_citation
                );
            }
        }

        // Flush results
        {
            let mut out = output.lock().unwrap();
            for doc in &local_results {
                serde_json::to_writer(&mut *out, doc).unwrap();
                out.write_all(b"\n").unwrap();
            }
        }

        // Update global counters
        total_docs.fetch_add(local_total, Ordering::Relaxed);
        docs_with_doi.fetch_add(local_doi, Ordering::Relaxed);
        docs_from_academic.fetch_add(local_academic, Ordering::Relaxed);
        docs_with_citations.fetch_add(local_citation, Ordering::Relaxed);
        docs_with_any_signal.fetch_add(local_any, Ordering::Relaxed);
        parse_errors.fetch_add(local_errors, Ordering::Relaxed);

        eprintln!(
            "  DONE [{}] {} docs -> doi={} academic={} citations={} (any={})",
            fname, local_total, local_doi, local_academic, local_citation, local_any
        );
    });

    // Summary
    let tot = total_docs.load(Ordering::Relaxed);
    let n_doi = docs_with_doi.load(Ordering::Relaxed);
    let n_academic = docs_from_academic.load(Ordering::Relaxed);
    let n_citation = docs_with_citations.load(Ordering::Relaxed);
    let n_any = docs_with_any_signal.load(Ordering::Relaxed);
    let n_err = parse_errors.load(Ordering::Relaxed);

    eprintln!("\n{}", "=".repeat(72));
    eprintln!("ACADEMIC CONTAMINATION SCAN COMPLETE");
    eprintln!("{}", "=".repeat(72));
    eprintln!("  Total docs scanned:            {:>12}", tot);
    eprintln!(
        "  Docs with DOIs:                {:>12} ({:.2}%)",
        n_doi,
        if tot > 0 {
            n_doi as f64 / tot as f64 * 100.0
        } else {
            0.0
        }
    );
    eprintln!(
        "  Docs from academic domains:    {:>12} ({:.2}%)",
        n_academic,
        if tot > 0 {
            n_academic as f64 / tot as f64 * 100.0
        } else {
            0.0
        }
    );
    eprintln!(
        "  Docs with citation patterns:   {:>12} ({:.2}%)",
        n_citation,
        if tot > 0 {
            n_citation as f64 / tot as f64 * 100.0
        } else {
            0.0
        }
    );
    eprintln!(
        "  Docs with ANY academic signal: {:>12} ({:.2}%)",
        n_any,
        if tot > 0 {
            n_any as f64 / tot as f64 * 100.0
        } else {
            0.0
        }
    );
    if n_err > 0 {
        eprintln!("  Parse errors (skipped):        {:>12}", n_err);
    }
    eprintln!("\n  Output: {}", args.output);
}
