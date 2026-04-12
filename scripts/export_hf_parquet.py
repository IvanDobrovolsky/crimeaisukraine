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

Dobrovolskyi, I. (2026). Digital Sovereignty of Crimea: A Systematic Audit of Platform Classifications. *Working paper.*

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

{len(df_academic_full):,} academic papers mentioning Crimea, scanned for sovereignty framing signals.

## Description

Academic papers from OpenAlex (2014–2025) that mention Crimea, classified by whether their institutional metadata, affiliations, or text frames Crimea as Ukrainian or Russian territory. Stage-3 manual annotation confirms 1,581 papers with Russian sovereignty framing.

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
| `ua_score` | Ukraine sovereignty score (0–1) |
| `ru_score` | Russia sovereignty score (0–1) |
| `signals` | Sovereignty signals found (JSON string) |
| `stage3_russia_confirmed` | Boolean — manually verified as Russia-framing in Stage 3 |

## Key Findings

- 91,670 papers scanned, 5,151 with sovereignty signals
- 1,581 manually verified as Russia-framing (Stage 3)
- 84% are mundane science (viticulture, ecology, medicine) — sovereignty is normalised through institutional metadata
- LLM precision: 98.3% against manual annotation

## Citation

Dobrovolskyi, I. (2026). Digital Sovereignty of Crimea: A Systematic Audit. *Working paper.*

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

Dobrovolskyi, I. (2026). Digital Sovereignty of Crimea. *Working paper.*

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

{len(df_llm):,} forced-choice sovereignty queries across 18 LLM models and 50 languages.

## Description

Each major LLM was asked "Which country is [Crimean city] in?" in 50 languages at temperature=0. Responses were classified as Ukraine (correct), Russia (incorrect), or ambiguous. The Sovereignty Alignment Score (SAS) is a composite metric using tiered weighting.

## Files

- `data.parquet` — Raw query-level results ({len(df_llm):,} rows)
- `sas_scores.parquet` — Per-model Sovereignty Alignment Scores ({len(df_sas)} models)

## Fields (data.parquet)

| Field | Description |
|-------|-------------|
| `model` | Model identifier (e.g., claude-sonnet-4-20250514, gpt-4o) |
| `question_id` | Question identifier |
| `question_type` | forced_choice or open_ended |
| `city` | Crimean city tested (Simferopol, Sevastopol, Yalta, Kerch) |
| `language` | ISO language code |
| `language_name` | Language name |
| `prompt` | Exact prompt sent |
| `raw_answer` | Raw model response |
| `classified` | Classified answer: ukraine, russia, ambiguous |
| `expected` | Expected answer (ukraine) |
| `correct` | Boolean — did model answer correctly |
| `timestamp` | Query timestamp |

## Key Findings

- Top 5: Gemini 2.5 Pro (0.947), Claude Opus (0.907), GPT-4o (0.906), Claude Sonnet (0.893), Gemini Flash (0.833)
- Bottom 5: OLMo 3 (0.562), Qwen 3 (0.580), Gemma 4 (0.631), OLMo 2 (0.642), SmolLM 3 (0.642)
- RLHF gap: flagship models score +0.22–0.33 higher than their base counterparts
- 8 open/small models show negative RLHF gap (alignment training worsened sovereignty accuracy)

## Citation

Dobrovolskyi, I. (2026). Digital Sovereignty of Crimea. *Working paper.*

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

Analysis of how LLM training corpora (C4, Dolma, RedPajama) frame Crimea's sovereignty.

## Description

Documents from major LLM training corpora that mention Crimea, classified by sovereignty framing. This dataset demonstrates how pre-training data influences model outputs on disputed territory questions.

## Files

- `data.parquet` — C4-English Crimea mentions ({len(df_c4en):,} documents)
- `sovereignty_training.parquet` — Curated sovereignty training examples ({len(df_sov):,} examples)

## Key Findings

- C4-Russian: 58.7% Russia-framed
- Dolma: 12.2% Russia-framed
- C4-English: 10.0% Russia-framed
- Models trained on higher Russia-framing corpora produce more incorrect sovereignty answers
- OLMo (trained on Dolma) → lowest SAS scores, demonstrating the causal chain

## Citation

Dobrovolskyi, I. (2026). Digital Sovereignty of Crimea. *Working paper.*

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
