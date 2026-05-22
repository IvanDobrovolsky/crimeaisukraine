# C4 Sovereignty Classifier

Rust scanner for sovereignty framing in training corpora. Deterministic regex, no ML.

## Results

```
Split        Total docs    Russia-framing      %
─────────────────────────────────────────────────
English         286,117          3,607      1.26%
Ukrainian     3,639,461          6,271      0.17%
Russian      30,207,220        881,644      2.92%
─────────────────────────────────────────────────
Total        34,132,798        891,522      2.61%
```

Source classification of 891,522 Russia-framing docs:

```
Tier                 Count       %   Legal provenance
────────────────────────────────────────────────────────────
Independent        849,761   95.3%   No state ties identified
State-adjacent      16,772    1.9%   Sberbank/Gazprom, EU Pkg 16
State media (T1)    14,406    1.6%   OFAC SDN, EU Regulations
Sanctioned proxy     4,928    0.6%   GEC 2020, OFAC EO14024
Government           3,156    0.4%   Russian federal law
State-controlled     2,470    0.3%   Gazprom Media/NMG
Pravda network          29   <0.1%   VIGINUM/SGDSN 2024
```

Validation: 300-sample dual-blind annotation (100 per split).

```
Split    κ      Precision   95% Wilson CI
──────────────────────────────────────────
EN       0.942  89.6%       81.9–94.2%
UK       0.559  95.0%       88.8–97.8%
RU       0.490  97.0%       91.5–99.0%
──────────────────────────────────────────
Weighted        93.9%       (278/296)
```

## Architecture

```
scanner/src/
├── main.rs        # CLI: download-scan-delete from HuggingFace or scan local .jsonl.gz
├── classify.rs    # 90 regex signals → russia/ukraine/neutral per document
├── categorize.rs  # Domain → source tier (64 curated domains, OFAC/EU/UK/GEC lists)
└── doi_grep.rs    # Extract DOIs from classified documents
```

Four binaries:

| Binary | Purpose | Input | Output |
|--------|---------|-------|--------|
| `crimea-scanner` | Filter Crimea-mentioning docs from C4 shards | `allenai/c4` JSONL.gz | `c4_{lang}_crimea_filtered.jsonl` |
| `crimea-classify` | Apply 90 signals, classify each doc | filtered JSONL | `c4_{lang}_classified.jsonl` |
| `crimea-categorize` | Assign source tier per domain | classified JSONL | tier counts in `c4_final_numbers.json` |
| `crimea-doi-grep` | Extract DOIs from classified docs | classified JSONL | `russia_framing_dois_in_c4.jsonl` |

## Signals

90 deterministic regex patterns across 3 languages. Each signal has:
- `direction`: russia or ukraine
- `language`: en, ru, uk, or structural
- `legal_source`: legal instrument grounding the pattern (e.g., "Russian Federal Law No. 6-FKZ")
- `weight`: 1.0 (standard) or 0.5 (ambiguous context)

Full signal inventory with legal provenance: [`SIGNAL_SOURCES.md`](SIGNAL_SOURCES.md)

Exported as parquet: [`data/classifier_signals.parquet`](../data/classifier_signals.parquet)

## Usage

```bash
cd scanner

# Build
cargo build --release

# Scan local files
./target/release/crimea-scanner --input "../data/c4_raw/c4-en-*.json.gz" --output ../data/c4_en_crimea_filtered.jsonl

# Download-scan from HuggingFace (streams, doesn't store full corpus)
./target/release/crimea-scanner --download ru --shards 4096 --output ../data/c4_ru_crimea_filtered.jsonl

# Classify
./target/release/crimea-classify --input ../data/c4_en_crimea_filtered.jsonl --output ../data/c4_en_classified.jsonl

# Categorize by source tier
./target/release/crimea-categorize --input ../data/c4_en_classified.jsonl
```

## Dependencies

```toml
[dependencies]
flate2 = "1"          # gzip decompression
serde = "1"           # JSON parsing
serde_json = "1"
rayon = "1"           # parallel processing
regex = "1"           # signal matching
clap = "4"            # CLI
reqwest = "0.12"      # HuggingFace download
```
