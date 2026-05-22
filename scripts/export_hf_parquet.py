#!/usr/bin/env python3
"""
Export research datasets to Parquet for Hugging Face.

Creates 5 datasets, each in its own directory with a parquet file
and a README (dataset card).

Usage:
    python scripts/export_hf_parquet.py
    # Then: cd hf_export/<dataset> && huggingface-cli upload <org>/<dataset> .

Requires: pandas, pyarrow
"""

import json
import os
import pandas as pd
from pathlib import Path
from datetime import datetime

ROOT = Path("/Users/tati/Desktop/ivan/crimeaisukraine")
PAPER = Path("/Users/tati/Desktop/ivan/crimeaisukraine-paper")
OUT = ROOT / "hf_export"
OUT.mkdir(exist_ok=True)

NOW = datetime.now().strftime("%Y-%m-%d")


def load_jsonl(path, max_rows=None):
    rows = []
    with open(path) as f:
        for i, line in enumerate(f):
            if max_rows and i >= max_rows:
                break
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_dataset(name, df, card_text):
    """Write a parquet file + README.md dataset card."""
    d = OUT / name
    d.mkdir(exist_ok=True)

    # Write parquet
    pq_path = d / "data.parquet"
    df.to_parquet(pq_path, index=False, engine="pyarrow")
    size_mb = pq_path.stat().st_size / 1024 / 1024

    # Write dataset card
    (d / "README.md").write_text(card_text)

    print(f"  {name}: {len(df):,} rows, {len(df.columns)} cols, {size_mb:.1f} MB")
    return pq_path


# ══════════════════════════════════════════════════════════════
# 1. PLATFORM AUDIT
# ══════════════════════════════════════════════════════════════
print("1. Platform audit...")

with open(ROOT / "data" / "platforms.json") as f:
    platforms_data = json.load(f)

findings = platforms_data["findings"]
df_platforms = pd.DataFrame(findings)

# Clean up columns
keep_cols = [c for c in df_platforms.columns if c != "status_icon"]
df_platforms = df_platforms[keep_cols]

platform_card = f"""---
license: cc-by-4.0
language:
- en
task_categories:
- text-classification
tags:
- geopolitics
- sovereignty
- crimea
- ukraine
- digital-platforms
- audit
size_categories:
- n<1K
---

# Crimea Digital Sovereignty: Platform Audit

Systematic audit of {len(df_platforms)} digital platform classifications of Crimea's sovereignty status.

## Description

Each row represents one platform or service tested for how it classifies Crimea — as Ukraine (correct under international law and UNGA Resolution 68/262), as Russia (incorrect), or ambiguously.

## Fields

| Field | Description |
|-------|-------------|
| `platform` | Platform name and specific product/endpoint tested |
| `category` | Category: map_service, weather, travel, search, reference, tech_infrastructure, telecom, ip_geolocation, data_visualization, open_source |
| `status` | Classification: `correct` (Ukraine), `incorrect` (Russia), `ambiguous`, `blocked`, `n/a` |
| `method` | How we tested: api_query, manual_check, source_code, etc. |
| `detail` | What we found, including exact labels/responses |
| `url` | URL to reproduce the finding |
| `evidence` | Supporting evidence |
| `date_checked` | Date of verification |

## Key Findings

- 120 unique platforms audited across 10 categories
- 41 (35.3%) correctly show Crimea as Ukraine
- 26 (22.4%) incorrectly show Crimea as Russia
- 35 (30.2%) use ambiguous or disputed labels

## Citation

```bibtex
@misc{{dobrovolskyi2026digital,
  author = {{Dobrovolskyi, Ivan}},
  title = {{Digital Annexation: A Computational Audit of Crimea's Sovereignty Framing in Large Language Models}},
  year = {{2026}},
  url = {{https://crimeaisukraine.org}}
}}
```

## License

CC-BY-4.0
"""

write_dataset("platform-audit", df_platforms, platform_card)


# ══════════════════════════════════════════════════════════════
# 2. ACADEMIC SOVEREIGNTY
# ══════════════════════════════════════════════════════════════
print("2. Academic sovereignty...")

# Load the full scan (91,670 papers) — but only keep papers with signals
academic_rows = load_jsonl(ROOT / "data" / "academic_full.jsonl")
df_academic_full = pd.DataFrame(academic_rows)

# Convert signals list to string for parquet compatibility
if "signals" in df_academic_full.columns:
    df_academic_full["signals"] = df_academic_full["signals"].apply(
        lambda x: json.dumps(x) if isinstance(x, (list, dict)) else str(x) if x else ""
    )

# Load stage-3 confirmed (manually verified Russia-framing papers)
stage3_path = PAPER / "docs" / "stage3_russia_confirmed.csv"
if stage3_path.exists():
    df_stage3 = pd.read_csv(stage3_path)
    df_stage3["stage3_verified"] = True
    # Merge stage3 verification into full dataset
    if "doi" in df_academic_full.columns and "doi" in df_stage3.columns:
        verified_dois = set(df_stage3["doi"].dropna().tolist())
        df_academic_full["stage3_russia_confirmed"] = df_academic_full["doi"].isin(verified_dois)
    # Also convert stage3 signals
    if "signals" in df_stage3.columns:
        df_stage3["signals"] = df_stage3["signals"].apply(
            lambda x: str(x) if x else ""
        )

academic_card = f"""---
license: cc-by-4.0
language:
- en
- ru
- uk
task_categories:
- text-classification
tags:
- geopolitics
- sovereignty
- crimea
- ukraine
- academic-publishing
- metadata-analysis
size_categories:
- 10K<n<100K
---

# Crimea Digital Sovereignty: Academic Paper Sovereignty Framing

{len(df_academic_full):,} academic papers mentioning Crimea (OpenAlex, 2010\u20132025), scanned by an 81-signal regex classifier across 3 languages.

## Description

Three-stage pipeline: (1) regex classifier identifies 5,151 candidates from 91,670 papers, (2) LLM verification (Claude Haiku) narrows to 1,611, (3) manual annotation confirms 1,581 Russia-framing papers (98.3% precision). 161 Western publisher papers verified via CrossRef DOI prefix matching.

84% are mundane science (viticulture, ecology, medicine) \u2014 sovereignty is normalised through institutional metadata, not explicit political claims.

## Fields

| Field | Description |
|-------|-------------|
| `doi` | Digital Object Identifier |
| `openalex_id` | OpenAlex paper ID |
| `title` | Paper title |
| `abstract` | Paper abstract (when available) |
| `year` | Publication year |
| `journal` | Journal name |
| `language` | Paper language |
| `label` | LLM-assigned sovereignty label |
| `ua_score` | Ukraine sovereignty score (0\u20131) |
| `ru_score` | Russia sovereignty score (0\u20131) |
| `signals` | Sovereignty signals found (JSON string) |
| `stage3_russia_confirmed` | Boolean \u2014 manually verified as Russia-framing in Stage 3 |

## Key Findings

- 91,670 papers scanned, 5,151 with sovereignty signals
- 1,581 manually verified as Russia-framing (Stage 3, 98.3% precision)
- 161 papers published by Western/international publishers (Elsevier, Springer, Wiley, MDPI, IEEE, etc.)
- Russia-framing absent before 2014, rises to rival Ukraine-framing by 2021

## Citation

```bibtex
@misc{{dobrovolskyi2026digital,
  author = {{Dobrovolskyi, Ivan}},
  title = {{Digital Annexation: A Computational Audit of Crimea's Sovereignty Framing in Large Language Models}},
  year = {{2026}},
  url = {{https://crimeaisukraine.org}}
}}
```

## License

CC-BY-4.0
"""

write_dataset("academic-sovereignty", df_academic_full, academic_card)

# Also write stage3 as a separate split
if stage3_path.exists():
    write_dataset("academic-sovereignty-verified", df_stage3, academic_card.replace(
        "# Crimea Digital Sovereignty: Academic Paper Sovereignty Framing",
        "# Crimea Digital Sovereignty: Stage-3 Manually Verified Russia-Framing Papers"
    ).replace(
        f"{len(df_academic_full):,} academic papers",
        f"{len(df_stage3):,} manually verified papers"
    ))


# ══════════════════════════════════════════════════════════════
# 3. MEDIA FRAMING
# ══════════════════════════════════════════════════════════════
print("3. Media framing...")

media_csv = ROOT / "data" / "media_russia_endorses.csv"
if media_csv.exists():
    df_media = pd.read_csv(media_csv)
else:
    df_media = pd.DataFrame()

media_card = f"""---
license: cc-by-4.0
language:
- en
task_categories:
- text-classification
tags:
- geopolitics
- sovereignty
- crimea
- ukraine
- media-analysis
- gdelt
size_categories:
- 1K<n<10K
---

# Crimea Digital Sovereignty: Media Sovereignty Endorsement

{len(df_media):,} news articles that genuinely endorse Russian sovereignty over Crimea (LLM-verified from 153,937 GDELT articles).

## Description

Articles identified from GDELT's global news monitoring that frame Crimea as Russian territory — not merely reporting on Russia's claim, but endorsing or normalising it. Each article was verified by LLM classification with human review of disagreements.

## Fields

| Field | Description |
|-------|-------------|
| `url` | Article URL |
| `domain` | Publishing domain |
| `country` | Domain country |
| `signals` | Sovereignty signals detected |
| `llm_explanation` | LLM reasoning for classification |

## Key Findings

- 153,937 GDELT articles analysed (2014–2025)
- 4,714 genuinely endorse Russian sovereignty (LLM-verified)
- Non-Russian media endorsement rate: 9.1%
- International media reports on, but rarely endorses, Russian claims

## Citation

```bibtex
@misc{{dobrovolskyi2026digital,
  author = {{Dobrovolskyi, Ivan}},
  title = {{Digital Annexation: A Computational Audit of Crimea's Sovereignty Framing in Large Language Models}},
  year = {{2026}},
  url = {{https://crimeaisukraine.org}}
}}
```

## License

CC-BY-4.0
"""

write_dataset("media-framing", df_media, media_card)


# ══════════════════════════════════════════════════════════════
# 4. LLM SOVEREIGNTY AUDIT
# ══════════════════════════════════════════════════════════════
print("4. LLM sovereignty audit...")

llm_rows = load_jsonl(ROOT / "data" / "llm_sovereignty_full.jsonl")
df_llm = pd.DataFrame(llm_rows)

# Load SAS scores as a separate table
with open(ROOT / "data" / "sas_scores.json") as f:
    sas_data = json.load(f)

# Extract per-model scores
sas_models = sas_data.get("per_model", {})
sas_rows = []
for model, scores in sas_models.items():
    row = {"model": model}
    if isinstance(scores, dict):
        row.update(scores)
    sas_rows.append(row)
df_sas = pd.DataFrame(sas_rows)

# Flatten any nested dicts/lists in df_llm
for col in df_llm.columns:
    if df_llm[col].apply(lambda x: isinstance(x, (dict, list))).any():
        df_llm[col] = df_llm[col].apply(
            lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
        )

llm_card = f"""---
license: cc-by-4.0
language:
- multilingual
task_categories:
- text-classification
- question-answering
tags:
- geopolitics
- sovereignty
- crimea
- ukraine
- llm-evaluation
- benchmark
size_categories:
- 10K<n<100K
---

# Crimea Digital Sovereignty: LLM Sovereignty Audit

{len(df_llm):,} forced-choice sovereignty queries across 16 models (+ 4 instruct variants) and 50 languages.

## Description

16 frontier LLMs from eight laboratories were tested on 23 sovereignty probes (14 forced-choice + 9 free-recall) across 50 languages at temperature=0, seed=42. Responses were classified as Ukraine (correct under international law), Russia (incorrect), or ambiguous. The Sovereignty Alignment Score (SAS) is a weighted composite: SAS = w^T s, where s = (d, l, i, r)^T and w = (0.10, 0.50, 0.20, 0.20)^T.

Four open-weight models were additionally tested as base vs. instruct pairs to isolate the effect of instruction tuning.

## Files

- `data.parquet` — Raw query-level results ({len(df_llm):,} rows)
- `sas_scores.parquet` — Per-model Sovereignty Alignment Scores ({len(df_sas)} models)

## Fields (data.parquet)

| Field | Description |
|-------|-------------|
| `model` | Model identifier (e.g., opus-4.6, gpt-5.4, gemini-2.5-pro) |
| `question_id` | Question identifier (23 probes: q1-q15 + oq1-oq9) |
| `question_type` | forced_choice or open_ended |
| `city` | Crimean city tested (Simferopol, Sevastopol, Yalta, Kerch, etc.) |
| `language` | ISO language code (50 languages) |
| `language_name` | Language name |
| `prompt` | Exact prompt sent |
| `raw_answer` | Raw model response |
| `classified` | Classified answer: ukraine, russia, ambiguous |
| `expected` | Expected answer |
| `correct` | Boolean — did model answer correctly |
| `timestamp` | Query timestamp |

## Key Findings

- **Top models (SAS):** Gemini 2.5 Pro (0.902), Claude Opus 4.6 (0.894), Claude Sonnet 4.6 (0.894), GPT-5.4 (0.868), Gemini 2.5 Flash (0.856)
- **Bottom models (SAS):** Qwen 3 (0.652), OLMo 2 (0.656), Gemma 4 (0.684), Mistral Small (0.715), GPT-5.4 Nano (0.737)
- **Declarative-generative gap:** 7 closed-source models show positive gaps (+0.04 to +0.27 on a 0\u20131 scale); all 9 remaining models show negative gaps
- **Instruct effect:** instruction tuning improves forced-choice (d) in 3/4 models but decreases free-recall (r) in all 4 (avg \u22128.0 pp)

## Models (16 main + 4 instruct variants)

| Model | Lab | SAS | d | r | \u0394 (d\u2212r) |
|-------|-----|-----|---|---|------|
| Gemini 2.5 Pro | Google | 0.902 | 0.926 | 0.654 | +0.272 |
| Claude Opus 4.6 | Anthropic | 0.894 | 0.890 | 0.803 | +0.087 |
| Claude Sonnet 4.6 | Anthropic | 0.894 | 0.920 | 0.802 | +0.118 |
| GPT-5.4 | OpenAI | 0.868 | 0.925 | 0.726 | +0.200 |
| Gemini 2.5 Flash | Google | 0.856 | 0.864 | 0.708 | +0.156 |
| Grok 4.20 | xAI | 0.832 | 0.645 | 0.602 | +0.042 |
| Grok 3 | xAI | 0.802 | 0.549 | 0.712 | \u22120.163 |
| GPT-5.4 Mini | OpenAI | 0.801 | 0.714 | 0.730 | \u22120.016 |
| Llama 4 Scout | Meta | 0.796 | 0.561 | 0.852 | \u22120.291 |
| Claude Haiku 4.5 | Anthropic | 0.770 | 0.629 | 0.745 | \u22120.116 |
| Grok 4 Fast | xAI | 0.767 | 0.715 | 0.661 | +0.054 |
| GPT-5.4 Nano | OpenAI | 0.737 | 0.537 | 0.797 | \u22120.260 |
| Mistral Small | Mistral | 0.715 | 0.484 | 0.789 | \u22120.305 |
| Gemma 4 | Google | 0.684 | 0.396 | 0.877 | \u22120.481 |
| OLMo 2 | AI2 | 0.656 | 0.436 | 0.897 | \u22120.461 |
| Qwen 3 | Alibaba | 0.652 | 0.241 | 0.793 | \u22120.552 |

## Citation

```bibtex
@misc{{dobrovolskyi2026digital,
  author = {{Dobrovolskyi, Ivan}},
  title = {{Digital Annexation: A Computational Audit of Crimea's Sovereignty Framing in Large Language Models}},
  year = {{2026}},
  url = {{https://crimeaisukraine.org}}
}}
```

## License

CC-BY-4.0
"""

write_dataset("llm-sovereignty-audit", df_llm, llm_card)

# SAS scores as separate file in same dataset dir
sas_dir = OUT / "llm-sovereignty-audit"
# Flatten nested values in SAS
for col in df_sas.columns:
    if df_sas[col].apply(lambda x: isinstance(x, (dict, list))).any():
        df_sas[col] = df_sas[col].apply(
            lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
        )
df_sas.to_parquet(sas_dir / "sas_scores.parquet", index=False, engine="pyarrow")
print(f"  sas_scores: {len(df_sas)} models")


# ══════════════════════════════════════════════════════════════
# 5. TRAINING CORPORA FRAMING
# ══════════════════════════════════════════════════════════════
print("5. Training corpora framing...")

# C4-EN Crimea mentions (small enough: 30MB jsonl → parquet)
c4en_path = ROOT / "c4_sovereignty" / "data" / "c4_en_crimea.jsonl"
if c4en_path.exists():
    c4en_rows = load_jsonl(c4en_path)
    df_c4en = pd.DataFrame(c4en_rows)
    # Flatten any complex columns
    for col in df_c4en.columns:
        if df_c4en[col].apply(lambda x: isinstance(x, (dict, list))).any():
            df_c4en[col] = df_c4en[col].apply(
                lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
            )
else:
    df_c4en = pd.DataFrame()

# Also load the sovereignty training dataset (synthetic + curated)
sov_train_path = ROOT / "c4_sovereignty" / "data" / "sovereignty_training_data.jsonl"
if sov_train_path.exists():
    sov_rows = load_jsonl(sov_train_path)
    df_sov = pd.DataFrame(sov_rows)
    for col in df_sov.columns:
        if df_sov[col].apply(lambda x: isinstance(x, (dict, list))).any():
            df_sov[col] = df_sov[col].apply(
                lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
            )
else:
    df_sov = pd.DataFrame()

corpora_card = f"""---
license: cc-by-4.0
language:
- en
- ru
- uk
task_categories:
- text-classification
tags:
- geopolitics
- sovereignty
- crimea
- ukraine
- training-data
- c4
- corpus-analysis
size_categories:
- 1K<n<10K
---

# Crimea Digital Sovereignty: Training Corpora Sovereignty Framing

Analysis of how LLM training corpora frame Crimea's sovereignty. A Rust-based classifier with 90 legal-grounded signals scanned 34.1M Crimea-mentioning documents across three C4 language splits.

## Description

Documents from Google's C4 corpus that mention Crimea, classified by sovereignty framing using a deterministic regex classifier (no ML/learned parameters). 90 signals across English, Russian, and Ukrainian, each grounded in legal provenance (OFAC SDN, EU Regulations, GEC reports).

## Files

- `data.parquet` — C4-English Crimea mentions ({len(df_c4en):,} documents)
- `sovereignty_training.parquet` — Curated sovereignty training examples ({len(df_sov):,} examples)

## Key Findings (full C4 census)

| Split | Total docs | Russia-framing | % |
|-------|-----------|----------------|---|
| English | 286,117 | 3,607 | 1.26% |
| Ukrainian | 3,639,461 | 6,271 | 0.17% |
| Russian | 30,207,220 | 881,644 | 2.92% |
| **Total** | **34,132,798** | **891,522** | **2.61%** |

- 95.3% of Russia-framing documents originate from independent (non-state) sources
- Only 4.7% from state-controlled or sanctioned sources (OFAC/EU/UK lists)
- Validated by two independent annotators on 300 samples (100 per split): weighted precision 93.9%

## Source classification

| Source tier | Count | % | Legal provenance |
|------------|-------|---|-----------------|
| Independent | 849,761 | 95.3% | No state ties identified |
| State-adjacent | 16,772 | 1.9% | Sberbank/Gazprom, EU Pkg 16 |
| State media (T1) | 14,406 | 1.6% | OFAC SDN, EU Regulations |
| Sanctioned proxy | 4,928 | 0.6% | GEC 2020, OFAC EO14024 |
| Government | 3,156 | 0.4% | Russian federal law |
| State-controlled (T2) | 2,470 | 0.3% | Gazprom Media/NMG |
| Pravda network | 29 | <0.1% | VIGINUM/SGDSN 2024 |

## Classifier source code

[github.com/IvanDobrovolsky/crimeaisukraine/c4_sovereignty/scanner](https://github.com/IvanDobrovolsky/crimeaisukraine/tree/main/c4_sovereignty/scanner)

## Citation

```bibtex
@misc{{dobrovolskyi2026digital,
  author = {{Dobrovolskyi, Ivan}},
  title = {{Digital Annexation: A Computational Audit of Crimea's Sovereignty Framing in Large Language Models}},
  year = {{2026}},
  url = {{https://crimeaisukraine.org}}
}}
```

## License

CC-BY-4.0
"""

write_dataset("training-corpora-framing", df_c4en, corpora_card)

if len(df_sov) > 0:
    sov_dir = OUT / "training-corpora-framing"
    df_sov.to_parquet(sov_dir / "sovereignty_training.parquet", index=False, engine="pyarrow")
    print(f"  sovereignty_training: {len(df_sov)} examples")


# ══════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("EXPORT COMPLETE")
print("=" * 60)

for d in sorted(OUT.iterdir()):
    if d.is_dir():
        files = list(d.glob("*.parquet"))
        total = sum(f.stat().st_size for f in files)
        print(f"  {d.name}/")
        for f in files:
            print(f"    {f.name}: {f.stat().st_size/1024/1024:.1f} MB")

print(f"\nOutput: {OUT}")
print("""
To upload (after creating the org):

  pip install huggingface-hub
  huggingface-cli login

  # For each dataset:
  cd hf_export/<dataset-name>
  huggingface-cli upload <your-org>/<dataset-name> . --repo-type dataset
""")
