use clap::Parser;
use rayon::prelude::*;
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::fs::File;
use std::io::{BufRead, BufReader, Write};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;

/// Fast sovereignty classifier for pre-filtered C4 Crimea census data.
///
/// Reads JSONL files with {text, url, file} and classifies each document
/// for sovereignty framing, quotation detection, and propaganda source.
///
/// Usage:
///   crimea-classify --input "data/c4_ru_*.jsonl" --output data/classified_ru.jsonl
#[derive(Parser)]
#[command(name = "crimea-classify", version)]
struct Args {
    /// Glob pattern for input JSONL files
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
    label: String,
    is_quoted: bool,
    framing_type: String,    // "assertive_structured", "assertive_pure", "reportage_news", "reportage_attribution", "" (non-russia)
    source_type: String,
    ua_score: f32,
    ru_score: f32,
    #[serde(skip_serializing_if = "Option::is_none")]
    text_preview: Option<String>,
}

// =========================================================================
// Signal definitions — ported from sovereignty_signals.py (91 signals)
// =========================================================================

struct Signal {
    regex: Regex,
    direction: &'static str, // "ukraine" or "russia"
    weight: f32,
}

fn build_signals() -> Vec<Signal> {
    let mut signals = Vec::new();

    // --- ENGLISH UKRAINE (21) ---
    let en_ua: &[(&str, f32)] = &[
        (r"(?i)simferopol\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?ukraine", 2.0),
        (r"(?i)sevastopol\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?ukraine", 2.0),
        (r"(?i)yalta\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?ukraine", 2.0),
        (r"(?i)kerch\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?ukraine", 2.0),
        (r"(?i)feodosia\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?ukraine", 2.0),
        (r"(?i)evpatoria\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?ukraine", 2.0),
        (r"(?i)crimea\s*[,\-]\s*ukraine", 2.0),
        (r"(?i)autonomous\s+republic\s+of\s+crimea", 1.5),
        (r"(?i)UA-43", 1.5),
        (r"(?i)annex(?:ed|ation)\s+(?:of\s+)?crimea", 2.0),
        (r"(?i)illegal(?:ly)?\s+annex", 2.0),
        (r"(?i)occupied?\s+crimea", 1.0),
        (r"(?i)illegal(?:ly)?\s+occupi", 1.0),
        (r"(?i)crimea\s+(?:is|belongs?\s+to)\s+ukraine", 2.0),
        (r"(?i)ukraine\s*['\']\s*s\s+crimea", 1.0),
        (r"(?i)ukrainian\s+(?:peninsula|territory)\s+(?:of\s+)?crimea", 1.5),
        (r"(?i)temporarily\s+occupied\s+(?:territory|crimea)", 1.5),
        (r"(?i)de\s*-?\s*occupation\s+of\s+crimea", 1.5),
        (r"(?i)liberation\s+of\s+crimea", 1.0),
        (r"(?i)crimea\s+platform", 1.0),
        (r"(?i)restore\s+(?:ukraine\s*['\']\s*s\s+)?(?:sovereignty|territorial\s+integrity).*crimea", 1.5),
    ];

    // --- ENGLISH RUSSIA (17) ---
    let en_ru: &[(&str, f32)] = &[
        (r"(?i)simferopol\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?russia", 2.0),
        (r"(?i)sevastopol\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?russia", 2.0),
        (r"(?i)yalta\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?russia", 2.0),
        (r"(?i)kerch\s*[,\-]\s*(?:crimea\s*[,\-]\s*)?russia", 2.0),
        (r"(?i)crimea\s*[,\-]\s*russia\b", 2.0),
        (r"(?i)\brepublic\s+of\s+crimea", 1.5),
        (r"(?i)crimean\s+federal\s+district", 1.5),
        (r"(?i)crimea\s+(?:re)?join(?:ed|ing)\s+russia", 1.5),
        (r"(?i)(?:re)?unif(?:ied|ication)\s+(?:of|with)\s+(?:crimea|russia)", 1.5),
        (r"(?i)crimea\s+(?:is|belongs?\s+to)\s+russia", 2.0),
        (r"(?i)crimea\s+as\s+(?:a\s+)?part\s+of\s+russia", 2.0),
        (r"(?i)crimea\s+return(?:ed)?\s+to\s+russia", 1.5),
        (r"(?i)russia\s*['\']\s*s\s+crimea", 1.0),
        (r"(?i)russian\s+crimea\b", 1.0),
        (r"(?i)accession\s+of\s+crimea\s+to\s+russia", 2.0),
        (r"(?i)crimea\s+(?:became|is)\s+(?:a\s+)?russian\s+(?:territory|region|subject)", 2.0),
        (r"(?i)crimea\s+voted\s+to\s+join\s+russia", 1.5),
    ];

    // --- RUSSIAN UKRAINE (8) ---
    let ru_ua: &[(&str, f32)] = &[
        (r"(?i)(?:симферополь|севастополь|ялта|керчь|феодосия|евпатория)\s*[,\-]\s*(?:крым\s*[,\-]\s*)?украин", 2.0),
        (r"(?i)крым\s*[,\-]\s*украин", 2.0),
        (r"(?i)автономна\s+республ[іи]ка?\s+крим", 1.5),
        (r"(?i)аннекс[ия]\w*\s+крым", 2.0),
        (r"(?i)оккупац[ия]\w*\s+крым", 1.5),
        (r"(?i)оккупированн\w+\s+крым", 1.0),
        (r"(?i)незаконн\w+\s+(?:аннекс|оккупац|присоединени)", 1.0),
        (r"(?i)крым\s+—?\s+(?:это|е)\s+украин", 2.0),
    ];

    // --- RUSSIAN RUSSIA (16) ---
    // NOTE: "республика крым" must NOT match "автономная республика крым" (Ukrainian designation)
    // Since Rust regex has no lookbehinds, we handle this in the scoring logic below
    let ru_ru: &[(&str, f32)] = &[
        (r"(?i)(?:симферополь|севастополь|ялта|керчь|феодосия|евпатория)\s*[,\-]\s*(?:крым\s*[,\-]\s*)?росси", 2.0),
        (r"(?i)крым\s*[,\-]\s*росси", 2.0),
        (r"(?i)республика\s+крым", 1.5),
        (r"(?i)крымский\s+федеральный\s+округ", 1.5),
        (r"(?i)субъект\w*\s+(?:российской\s+)?федерации.*крым", 1.5),
        (r"(?i)воссоединени\w+\s+крым", 1.5),
        (r"(?i)присоединени\w+\s+крым", 1.5),
        (r"(?i)вхождени\w+\s+крым\w*\s+в\s+состав", 1.5),
        (r"(?i)крым\s+в\s+составе?\s+росси", 2.0),
        (r"(?i)крым\s+наш", 2.0),
        (r"(?i)крым\s+—?\s+(?:это|е)\s+росси", 2.0),
        (r"(?i)крым\s+вернулся\s+в\s+росси", 1.5),
        (r"(?i)крым\s+стал\s+(?:частью|регионом)\s+росси", 2.0),
        (r"(?i)крым\s+(?:это\s+)?часть\s+росси", 2.0),
        (r"(?i)крым\s+(?:является|стал)\s+субъект", 1.5),
        (r"(?i)референдум\w*\s+(?:в\s+)?крым\w*.*(?:присоединени|воссоединени)", 1.5),
    ];

    // --- UKRAINIAN UKRAINE (12) ---
    let uk_ua: &[(&str, f32)] = &[
        (r"(?i)(?:сімферополь|севастополь|ялта|керч|феодосія|євпаторія)\s*[,\-]\s*(?:крим\s*[,\-]\s*)?україн", 2.0),
        (r"(?i)крим\s*[,\-]\s*україн", 2.0),
        (r"(?i)автономна\s+республіка\s+крим", 1.5),
        (r"(?i)анекс[ія]\w*\s+крим", 2.0),
        (r"(?i)окупац[ія]\w*\s+крим", 1.5),
        (r"(?i)окупован\w+\s+крим", 1.0),
        (r"(?i)тимчасово\s+окупован\w+", 1.5),
        (r"(?i)незаконн\w+\s+(?:анекс|окупац|приєднання)", 1.0),
        (r"(?i)крим\s+—?\s+це\s+україна", 2.0),
        (r"(?i)деокупац[ія]\w*\s+крим", 1.5),
        (r"(?i)звільненн\w+\s+крим", 1.0),
        (r"(?i)кримськ\w+\s+платформ", 1.0),
    ];

    // --- UKRAINIAN RUSSIA (11) ---
    let uk_ru: &[(&str, f32)] = &[
        (r"(?i)(?:сімферополь|севастополь|ялта|керч|феодосія|євпаторія)\s*[,\-]\s*(?:крим\s*[,\-]\s*)?росі", 2.0),
        (r"(?i)крим\s*[,\-]\s*росі", 2.0),
        (r"(?i)\bреспубліка\s+крим", 1.5),
        (r"(?i)кримський\s+федеральний\s+округ", 1.5),
        (r"(?i)возз'?єднанн\w+\s+крим", 1.5),
        (r"(?i)приєднанн\w+\s+крим\w*\s+до\s+росі", 1.5),
        (r"(?i)крим\s+у\s+складі\s+росі", 2.0),
        (r"(?i)крим\s+став\s+(?:частиною|регіоном)\s+росі", 2.0),
        (r"(?i)крим\s+—?\s+це\s+росі", 2.0),
        (r"(?i)крим\s+повернувся\s+(?:до|в)\s+росі", 1.5),
        (r"(?i)крим\s+наш", 2.0),
    ];

    // --- STRUCTURAL (3+3) ---
    let struct_ua: &[(&str, f32)] = &[
        (r#"(?i)country_code["\s:=]+ua\b"#, 1.5),
        (r#"(?i)country["=:]\s*ukraine"#, 1.5),
        (r"(?i)/ukraine/crimea|/ukraine/simferopol", 1.0),
    ];
    let struct_ru: &[(&str, f32)] = &[
        (r#"(?i)country_code["\s:=]+ru\b"#, 1.5),
        (r#"(?i)country["=:]\s*russia"#, 1.5),
        (r"(?i)/russia/crimea|/russia/simferopol", 1.0),
    ];

    // Build all signals
    for &(pat, w) in en_ua.iter().chain(ru_ua).chain(uk_ua).chain(struct_ua) {
        signals.push(Signal {
            regex: Regex::new(pat).unwrap(),
            direction: "ukraine",
            weight: w,
        });
    }
    for &(pat, w) in en_ru.iter().chain(ru_ru).chain(uk_ru).chain(struct_ru) {
        signals.push(Signal {
            regex: Regex::new(pat).unwrap(),
            direction: "russia",
            weight: w,
        });
    }
    signals
}

// =========================================================================
// Quotation markers (15 patterns)
// =========================================================================

fn build_quotation_markers() -> Vec<Regex> {
    let patterns = [
        // English — explicit attribution to Russia/someone
        r"(?i)(?:russia|moscow|kremlin)\s+(?:says?|claims?|calls?\s+it|argues?|insists?|maintains?|considers?)",
        r"(?i)(?:putin|lavrov)\s+(?:says?|said|claims?|claimed|declared?|stated?|called)",
        r"(?i)according\s+to\b",
        r"(?i)what\s+(?:russia|moscow|the\s+kremlin)\s+calls?",
        r"(?i)\b(?:he|she|they|officials?|authorities|spokesperson)\s+(?:said|says?|claimed|stated|declared|announced|argued)",
        // English — scare quotes around Russia-framing terms
        r#"(?i)["\u{201c}\u{ab}](?:reunif\w+|accession\s+of\s+crimea|rejoined?\s+russia|republic\s+of\s+crimea)["\u{201d}\u{bb}]"#,
        // English — explicit skepticism markers ONLY
        r"(?i)\b(?:so-called|self-proclaimed)\b",
        // Russian — explicit attribution (someone said/claims)
        r"(?i)(?:россия|кремль|москва|путин)\s+(?:считает|называет|утверждает|заявляет)",
        r"(?i)по\s+(?:мнению|версии|заявлению|словам)\s+(?:россии|кремля|москвы|путина)",
        r"(?i)(?:заявил[аио]?|утверждает|по\s+словам|сообщи[лт])\s+(?:что|о\s)",
        // Russian — scare quotes around Russia-framing terms
        r"(?i)[\u{ab}\u{201c}](?:воссоединени|присоединени|республика\s+крым)\w*[\u{bb}\u{201d}]",
        // Russian — explicit skepticism ONLY
        r"(?i)\bтак\s+называем\w+\b",
        r"(?i)\bсамопровозглашённ\w+\b",
        // Ukrainian — explicit attribution
        r"(?i)(?:росія|кремль|москва|путін)\s+(?:вважає|називає|стверджує|заявляє)",
        r"(?i)за\s+(?:версією|заявою|словами)\s+(?:росії|кремля|москви|путіна)",
        r"(?i)(?:заявив|стверджує|за\s+словами|повідомив)\s+(?:що|про\s)",
        // Ukrainian — scare quotes
        r"(?i)[\u{ab}\u{201c}](?:возз'?єднанн|приєднанн|республіка\s+крим)\w*[\u{bb}\u{201d}]",
        // Ukrainian — explicit skepticism ONLY
        r"(?i)\bтак\s+зван\w+\b",
    ];
    // REMOVED: оккупац, аннекси, присоедин, непризнанн, де-факто, annexed, occupation, occupied,
    // disputed, contested, temporarily occupied — these are sovereignty-loaded words that appear
    // on BOTH sides (Russian celebrating "accession", Ukrainian condemning "occupation").
    // They are NOT attribution markers.
    patterns.iter().map(|p| Regex::new(p).unwrap()).collect()
}

// =========================================================================
// Structured data markers (addresses, listings, catalogs)
// =========================================================================

fn build_structured_markers() -> Vec<Regex> {
    let patterns = [
        r"(?i)ул\.\s*\S",
        r"(?i)пр\.\s*\S|просп\.\s*\S",
        r"(?i)д\.\s*\d",
        r"(?i)кв\.\s*\d",
        r"(?i)индекс\s*:?\s*\d{5,6}",
        r"(?i)почтовый\s+индекс",
        r"(?i)тел\.\s*[\+\d\(]",
        r"(?i)ИНН\s*:?\s*\d{10}",
        r"(?i)ОГРН\s*:?\s*\d{13}",
        r"(?i)КПП\s*:?\s*\d{9}",
        r"(?i)купить|продам|аренда|объявлени|доставк",
        r"(?i)postal\s+code|zip\s+code|phone:|fax:|address:",
    ];
    patterns.iter().map(|p| Regex::new(p).unwrap()).collect()
}

// =========================================================================
// News domain detection
// =========================================================================

const NEWS_DOMAINS: &[&str] = &[
    "bbc.com", "bbc.co.uk", "reuters.com", "apnews.com", "cnn.com", "nytimes.com",
    "washingtonpost.com", "theguardian.com", "ft.com", "bloomberg.com", "aljazeera.com",
    "dw.com", "france24.com", "euronews.com", "politico.eu", "politico.com",
    "foreignpolicy.com", "foreignaffairs.com", "theatlantic.com", "economist.com",
    "independent.co.uk", "telegraph.co.uk", "spiegel.de", "lemonde.fr", "elpais.com",
    "time.com", "newsweek.com", "npr.org", "pbs.org", "abc.net.au", "cbc.ca",
    "ukrinform.net", "ukrinform.ua", "pravda.com.ua", "unian.info", "unian.ua",
    "liga.net", "zn.ua", "slovoidilo.ua", "hromadske.ua", "nv.ua",
    "krymr.com", "rferl.org", "interfax.com.ua", "rbc.ua", "focus.ua",
    "gordonua.com", "brookings.edu", "rand.org", "chathamhouse.org", "csis.org",
    "cfr.org", "carnegieendowment.org", "wilsoncenter.org",
];

fn is_news_domain(url: &str) -> bool {
    let u = url.to_lowercase();
    NEWS_DOMAINS.iter().any(|d| u.contains(d))
}

// =========================================================================
// Propaganda source domains (55)
// =========================================================================

// Source: data/russian_state_domains.json — each domain has verifiable legal provenance
// See SIGNAL_SOURCES.md for full citations (OFAC SDN, EU regulations, GEC report, EGRUL)

const GOVERNMENT: &[&str] = &[
    "kremlin.ru", "government.ru", "mid.ru", "mil.ru",
    "duma.gov.ru", "council.gov.ru", "fsb.ru", "mos.ru",
    ".gov.ru",          // All Russian federal/regional government domains
    "sevproc.ru",       // Sevastopol occupation prosecutor
];

const STATE_T1: &[&str] = &[
    // Rossiya Segodnya group (100% federal, Presidential Decree No. 894/2013)
    "ria.ru", "sputniknews.com", "sputnikglobe.com", "inosmi.ru", "ukraina.ru",
    "baltnews.ee", "baltnews.lt", "baltnews.lv", "ruptly.tv",
    // RT / TV-Novosti (federal budget, OFAC SDN #50692)
    "rt.com", "russian.rt.com", "arabic.rt.com", "actualidad.rt.com",
    "rtarabic.com", "freedert.online", "dert.online", "rtde.live", "swentr.site", "rurtnews.com",
    // TASS (100% FGUP, EU Package 16)
    "tass.com", "tass.ru",
    // VGTRK (100% federal, EU Package 6)
    "vesti.ru", "rtr-planeta.com",
    // Channel One (51% federal, EU Package 9)
    "1tv.ru",
    // TV Zvezda (100% MoD, EU Package 16)
    "tvzvezda.ru", "redstar.ru",
    // Rossiyskaya Gazeta (government budgetary institution, EU Package 14)
    "rg.ru",
];

const STATE_T2: &[&str] = &[
    // National Media Group (Kovalchuk, Kremlin-aligned)
    "iz.ru", "izvestia.ru",  // EU Package 14
    "ren.tv",                // EU Package 9
    "5-tv.ru",
    // Gazprom Media (Gazprom = 50%+ federal)
    "ntv.ru",                // EU Package 9
    "rutube.ru",
    // Moscow city government
    "tvc.ru",                // EU Package 6
    "m24.ru",
    // CIS Interstate
    "mir24.tv",
    // Russian Orthodox Church
    "spastv.ru",             // EU Package 12
];

const SANCTIONED_PROXY: &[&str] = &[
    // GEC 'Pillars' 2020 — 7 proxy sites
    "strategic-culture.org", "strategic-culture.su",  // SVR-directed, OFAC + EU Pkg 16
    "globalresearch.ca",                               // GEC-documented proxy
    "journal-neo.org",                                 // RAS, OFAC + EU Pkg 11
    "southfront.org",                                  // GRU-linked, OFAC CYBER2 + EU Pkg 16
    "news-front.info", "news-front.su",                // FSB-linked, OFAC + EU Pkg 16
    "katehon.com",                                     // Malofeev, EU Pkg 11
    "geopolitica.ru",                                  // Dugin, OFAC EO14024
    // OFAC-designated (March 2022, EO14024)
    "inforos.ru",                                      // GRU Unit 54777
    "orientalreview.org", "orientalreview.su",         // OFAC + EU Pkg 11
    "webkamerton.ru",                                  // OFAC EO14024
    "odnarodyna.org",                                  // OFAC EO14024
    "unitedworldint.com", "uwidata.com",               // Prigozhin-linked
    "ritmeurasia.org",                                 // OFAC EO14024
    "usareally.com",                                   // IRA-linked, OFAC EO13694
    "riafan.ru",                                       // Prigozhin/IRA, OFAC CYBER2
    // EU-sanctioned (various packages)
    "tsargrad.tv",                                     // Malofeev, EU Pkg 11
    "voiceofeurope.com",                               // EU Pkg 14
    "eadaily.com",                                     // EU Pkg 16
    "fondsk.ru",                                       // SVR-linked, EU Pkg 16
    "rubaltic.ru",                                     // EU Pkg 16
    // Doppelganger (DOJ seizure Sept 2024)
    "rrn.media",                                       // OFAC EO14024
    "waronfakes.com",                                  // OFAC EO14024
];

const PRAVDA: &[&str] = &[
    // Portal Kombat network (VIGINUM/SGDSN report Feb 2024, 224 domains)
    "news-pravda.com", "dnr-pravda.ru",
];

const STATE_ADJ: &[&str] = &[
    // Sberbank-owned (state-controlled since 2020)
    "lenta.ru",           // EU Pkg 16
    "gazeta.ru",
    "rambler.ru",         // Sberbank-owned (same as lenta/gazeta)
    // Moscow city government-owned
    "aif.ru",
    // Oligarch-owned, editorially aligned
    "kp.ru", "mk.ru", "ng.ru", "kommersant.ru",
    // Pro-Russian / occupation media
    "anna-news.info", "rusvesna.su", "sevastopol.su", "e-crimea.info",
    // Old Pravda brand (NOT Portal Kombat)
    "pravda.ru", "pravda-tv.com",
];

fn domain_matches(url: &str, domain: &str) -> bool {
    // Match domain with proper boundary: must be preceded by '/', '.', or '//' (start of host)
    if let Some(idx) = url.find(domain) {
        if idx == 0 { return true; }
        let prev = url.as_bytes()[idx - 1];
        // Valid domain boundary: after '/' or '.' or '@'
        prev == b'/' || prev == b'.' || prev == b'@'
    } else {
        false
    }
}

fn classify_source(url: &str) -> &'static str {
    let u = url.to_lowercase();
    for d in GOVERNMENT { if domain_matches(&u, d) { return "government"; } }
    for d in STATE_T1 { if domain_matches(&u, d) { return "state_t1"; } }
    for d in STATE_T2 { if domain_matches(&u, d) { return "state_t2"; } }
    for d in SANCTIONED_PROXY { if domain_matches(&u, d) { return "sanctioned_proxy"; } }
    for d in PRAVDA { if domain_matches(&u, d) { return "pravda"; } }
    for d in STATE_ADJ { if domain_matches(&u, d) { return "state_adj"; } }
    "independent"
}

// =========================================================================
// Crimea window extraction
// =========================================================================

fn extract_window(text: &str, half: usize) -> &str {
    let lower = text.to_lowercase();
    let terms = [
        "crimea", "crimean", "крым", "крим", "симферопол", "сімферопол",
        "севастопол", "ялт", "керч",
    ];
    let mut best = None;
    for t in &terms {
        if let Some(idx) = lower.find(t) {
            if best.is_none() || idx < best.unwrap() {
                best = Some(idx);
            }
        }
    }
    match best {
        Some(idx) => {
            let mut s = idx.saturating_sub(half);
            let mut end = (idx + half).min(text.len());
            while s > 0 && !text.is_char_boundary(s) { s -= 1; }
            while end < text.len() && !text.is_char_boundary(end) { end += 1; }
            if end > text.len() { end = text.len(); }
            &text[s..end]
        }
        None => {
            let mut end = text.len().min(2000);
            while end > 0 && !text.is_char_boundary(end) { end -= 1; }
            &text[..end]
        }
    }
}

// =========================================================================
// Classification
// =========================================================================

struct Classifier {
    signals: Vec<Signal>,
    quotation: Vec<Regex>,
    structured: Vec<Regex>,
}

impl Classifier {
    fn new() -> Self {
        Classifier {
            signals: build_signals(),
            quotation: build_quotation_markers(),
            structured: build_structured_markers(),
        }
    }

    fn classify(&self, text: &str, url: &str) -> OutputDoc {
        let window = text;  // Use full text, not windowed
        let lower_window = window.to_lowercase();
        let mut ua_score: f32 = 0.0;
        let mut ru_score: f32 = 0.0;
        let full_text = text; // keep reference for framing analysis

        for sig in &self.signals {
            if sig.regex.is_match(window) {
                match sig.direction {
                    "ukraine" => ua_score += sig.weight,
                    "russia" => ru_score += sig.weight,
                    _ => {}
                }
            }
        }

        // FALSE POSITIVE CORRECTION: "автономная республика крым" is UKRAINIAN,
        // not Russian. If the Russia score includes "республика крым" but the text
        // actually says "автономная республика крым", subtract the false match and
        // add to Ukraine score instead.
        // Same for English "autonomous republic of crimea" and Ukrainian "автономна республіка крим"
        let has_auto_ru = lower_window.contains("автономная республика крым")
            || lower_window.contains("автономна республика крым");
        let has_auto_en = lower_window.contains("autonomous republic of crimea");
        let has_auto_uk = lower_window.contains("автономна республіка крим");
        let has_bare_republic_ru = lower_window.contains("республика крым")
            && !has_auto_ru;
        let has_bare_republic_en = lower_window.contains("republic of crimea")
            && !has_auto_en;
        let has_bare_republic_uk = lower_window.contains("республіка крим")
            && !has_auto_uk;

        if has_auto_ru && !has_bare_republic_ru {
            ru_score -= 1.5;  // remove false Russia signal
            ua_score += 1.5;  // add correct Ukraine signal
        }
        if has_auto_en && !has_bare_republic_en {
            ru_score -= 1.5;
            ua_score += 1.5;
        }
        if has_auto_uk && !has_bare_republic_uk {
            ru_score -= 1.5;
            ua_score += 1.5;
        }
        if ru_score < 0.0 { ru_score = 0.0; }

        let source_type = classify_source(url);

        let (label, is_quoted, framing_type, text_preview) = if ua_score == 0.0 && ru_score == 0.0 {
            ("no_signal", false, String::new(), None)
        } else if ua_score > ru_score {
            ("ukraine", false, String::new(), None)
        } else if ru_score > ua_score {
            let quoted = self.quotation.iter().any(|q| q.is_match(full_text));
            let is_news = is_news_domain(url);
            let is_structured = self.structured.iter().any(|s| s.is_match(full_text));

            let ft = if is_news {
                "reportage_news".to_string()
            } else if quoted {
                "reportage_attribution".to_string()
            } else if is_structured {
                "assertive_structured".to_string()
            } else {
                "assertive_pure".to_string()
            };

            // Text preview: first 300 chars, cleaned
            let preview = {
                let mut end = full_text.len().min(300);
                while end > 0 && !full_text.is_char_boundary(end) { end -= 1; }
                full_text[..end].replace('\n', " ").replace('\r', "")
            };

            ("russia", quoted || is_news, ft, Some(preview))
        } else {
            ("disputed", false, String::new(), None)
        };

        OutputDoc {
            url: url.to_string(),
            label: label.to_string(),
            is_quoted,
            framing_type,
            source_type: source_type.to_string(),
            ua_score,
            ru_score,
            text_preview,
        }
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
        .expect("Invalid glob")
        .filter_map(|e| e.ok())
        .collect();

    eprintln!(
        "SOVEREIGNTY CLASSIFIER: {} files, {} threads",
        files.len(), args.threads
    );

    let total_lines = AtomicU64::new(0);
    let classified = AtomicU64::new(0);
    let ru_count = AtomicU64::new(0);
    let ua_count = AtomicU64::new(0);
    let disputed_count = AtomicU64::new(0);
    let no_signal_count = AtomicU64::new(0);
    let quoted_count = AtomicU64::new(0);
    let assertive_structured_count = AtomicU64::new(0);
    let assertive_pure_count = AtomicU64::new(0);
    let reportage_news_count = AtomicU64::new(0);
    let reportage_attrib_count = AtomicU64::new(0);
    let state_t1_count = AtomicU64::new(0);
    let proxy_t2_count = AtomicU64::new(0);
    let pravda_count = AtomicU64::new(0);
    let state_adj_count = AtomicU64::new(0);

    let output = Mutex::new(
        std::io::BufWriter::with_capacity(
            1024 * 1024,
            File::create(&args.output).expect("Cannot create output"),
        ),
    );

    // Process all files: read lines, then classify in parallel chunks
    for path in &files {
        let file = match File::open(path) {
            Ok(f) => f,
            Err(e) => {
                eprintln!("  ERROR {:?}: {}", path, e);
                continue;
            }
        };
        let reader = BufReader::with_capacity(4 * 1024 * 1024, file);
        let fname = path.file_name().unwrap_or_default().to_string_lossy().to_string();

        // Process in chunks of 500K lines for memory efficiency + parallelism
        let chunk_size = 500_000;
        let mut chunk: Vec<String> = Vec::with_capacity(chunk_size);
        let mut file_total: u64 = 0;
        let mut file_ru: u64 = 0;
        let mut file_ua: u64 = 0;
        let mut file_nosig: u64 = 0;

        for line in reader.lines() {
            let line = match line {
                Ok(l) => l,
                Err(_) => continue,
            };
            chunk.push(line);

            if chunk.len() >= chunk_size {
                // Classify chunk in parallel
                let results: Vec<OutputDoc> = chunk.par_chunks(1000).flat_map(|sub| {
                    let clf = Classifier::new();
                    sub.iter().filter_map(|line| {
                        let doc: InputDoc = serde_json::from_str(line).ok()?;
                        Some(clf.classify(&doc.text, &doc.url))
                    }).collect::<Vec<_>>()
                }).collect();

                // Update counters and write output
                let mut out = output.lock().unwrap();
                for r in &results {
                    match r.label.as_str() {
                        "russia" => {
                            file_ru += 1;
                            ru_count.fetch_add(1, Ordering::Relaxed);
                            if r.is_quoted { quoted_count.fetch_add(1, Ordering::Relaxed); }
                            match r.framing_type.as_str() {
                                "assertive_structured" => assertive_structured_count.fetch_add(1, Ordering::Relaxed),
                                "assertive_pure" => assertive_pure_count.fetch_add(1, Ordering::Relaxed),
                                "reportage_news" => reportage_news_count.fetch_add(1, Ordering::Relaxed),
                                "reportage_attribution" => reportage_attrib_count.fetch_add(1, Ordering::Relaxed),
                                _ => 0,
                            };
                            match r.source_type.as_str() {
                                "state_t1" => state_t1_count.fetch_add(1, Ordering::Relaxed),
                                "sanctioned_proxy" => proxy_t2_count.fetch_add(1, Ordering::Relaxed),
                                "pravda" => pravda_count.fetch_add(1, Ordering::Relaxed),
                                "state_adj" => state_adj_count.fetch_add(1, Ordering::Relaxed),
                                _ => 0,
                            };
                        }
                        "ukraine" => { file_ua += 1; ua_count.fetch_add(1, Ordering::Relaxed); }
                        "disputed" => { disputed_count.fetch_add(1, Ordering::Relaxed); }
                        _ => { file_nosig += 1; }
                    }
                    serde_json::to_writer(&mut *out, r).unwrap();
                    out.write_all(b"\n").unwrap();
                }
                drop(out);

                file_total += chunk.len() as u64;
                total_lines.fetch_add(chunk.len() as u64, Ordering::Relaxed);

                if file_total % (chunk_size as u64 * 2) == 0 {
                    eprintln!(
                        "  [{}] {} lines, ru={} ua={} nosig={}",
                        fname, file_total, file_ru, file_ua, file_nosig
                    );
                }

                chunk.clear();
            }
        }

        // Process remaining lines
        if !chunk.is_empty() {
            let results: Vec<OutputDoc> = chunk.par_chunks(1000).flat_map(|sub| {
                let clf = Classifier::new();
                sub.iter().filter_map(|line| {
                    let doc: InputDoc = serde_json::from_str(line).ok()?;
                    Some(clf.classify(&doc.text, &doc.url))
                }).collect::<Vec<_>>()
            }).collect();

            let mut out = output.lock().unwrap();
            for r in &results {
                match r.label.as_str() {
                    "russia" => {
                        file_ru += 1;
                        ru_count.fetch_add(1, Ordering::Relaxed);
                        if r.is_quoted { quoted_count.fetch_add(1, Ordering::Relaxed); }
                        match r.framing_type.as_str() {
                            "assertive_structured" => assertive_structured_count.fetch_add(1, Ordering::Relaxed),
                            "assertive_pure" => assertive_pure_count.fetch_add(1, Ordering::Relaxed),
                            "reportage_news" => reportage_news_count.fetch_add(1, Ordering::Relaxed),
                            "reportage_attribution" => reportage_attrib_count.fetch_add(1, Ordering::Relaxed),
                            _ => 0,
                        };
                        match r.source_type.as_str() {
                            "state_t1" => state_t1_count.fetch_add(1, Ordering::Relaxed),
                            "sanctioned_proxy" => proxy_t2_count.fetch_add(1, Ordering::Relaxed),
                            "pravda" => pravda_count.fetch_add(1, Ordering::Relaxed),
                            "state_adj" => state_adj_count.fetch_add(1, Ordering::Relaxed),
                            _ => 0,
                        };
                    }
                    "ukraine" => { file_ua += 1; ua_count.fetch_add(1, Ordering::Relaxed); }
                    "disputed" => { disputed_count.fetch_add(1, Ordering::Relaxed); }
                    _ => { file_nosig += 1; }
                }
                serde_json::to_writer(&mut *out, r).unwrap();
                out.write_all(b"\n").unwrap();
            }
            drop(out);

            file_total += chunk.len() as u64;
            total_lines.fetch_add(chunk.len() as u64, Ordering::Relaxed);
        }

        eprintln!(
            "  DONE [{}] {} lines → ru={} ua={} disp={} nosig={}",
            fname, file_total, file_ru, file_ua,
            disputed_count.load(Ordering::Relaxed), file_nosig
        );

    }

    let tot = total_lines.load(Ordering::Relaxed);
    let ru = ru_count.load(Ordering::Relaxed);
    let ua = ua_count.load(Ordering::Relaxed);
    let disp = disputed_count.load(Ordering::Relaxed);
    let nosig = no_signal_count.load(Ordering::Relaxed);
    let quot = quoted_count.load(Ordering::Relaxed);
    let a_struct = assertive_structured_count.load(Ordering::Relaxed);
    let a_pure = assertive_pure_count.load(Ordering::Relaxed);
    let r_news = reportage_news_count.load(Ordering::Relaxed);
    let r_attrib = reportage_attrib_count.load(Ordering::Relaxed);
    let t1 = state_t1_count.load(Ordering::Relaxed);
    let t2 = proxy_t2_count.load(Ordering::Relaxed);
    let prav = pravda_count.load(Ordering::Relaxed);
    let t4 = state_adj_count.load(Ordering::Relaxed);

    eprintln!("\n{}", "=".repeat(72));
    eprintln!("SOVEREIGNTY CLASSIFICATION COMPLETE");
    eprintln!("{}", "=".repeat(72));
    eprintln!("  Total docs:      {:>12}", tot);
    eprintln!("  Russia-framing:  {:>12} ({:.1}%)", ru, ru as f64 / tot as f64 * 100.0);
    let assertive_total = a_struct + a_pure;
    let reportage_total = r_news + r_attrib;
    eprintln!("    ASSERTIVE:     {:>12} ({:.1}%)", assertive_total, assertive_total as f64 / ru as f64 * 100.0);
    eprintln!("      structured:  {:>12}", a_struct);
    eprintln!("      pure:        {:>12}", a_pure);
    eprintln!("    REPORTAGE:     {:>12} ({:.1}%)", reportage_total, reportage_total as f64 / ru as f64 * 100.0);
    eprintln!("      news_domain: {:>12}", r_news);
    eprintln!("      attribution: {:>12}", r_attrib);
    eprintln!("    (legacy quoted:{:>12})", quot);
    eprintln!("  Ukraine-framing: {:>12} ({:.1}%)", ua, ua as f64 / tot as f64 * 100.0);
    eprintln!("  Disputed:        {:>12} ({:.1}%)", disp, disp as f64 / tot as f64 * 100.0);
    eprintln!("  No signal:       {:>12} ({:.1}%)", nosig, nosig as f64 / tot as f64 * 100.0);
    eprintln!();
    eprintln!("  Source breakdown:");
    eprintln!("    state_t1:      {:>12}", t1);
    eprintln!("    proxy_t2:      {:>12}", t2);
    eprintln!("    pravda:        {:>12}", prav);
    eprintln!("    state_adj_t4:  {:>12}", t4);
    eprintln!("    independent:   {:>12}", tot - t1 - t2 - prav - t4);
    eprintln!("\n  Output: {}", args.output);
}
