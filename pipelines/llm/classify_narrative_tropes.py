#!/usr/bin/env python3
"""
Narrative-trope sub-classifier for the six Russian "Crimea is special" tropes.

Motivation
----------
The binary "Russia-framing vs Ukraine-framing" classification tells us
how a paper or article positions Crimea politically. It does not tell us
*which* component of the Russian imperial-historical narrative the text
invokes. This script adds that layer.

The six tropes we detect:

  catherine_1783      — Catherine II's annexation from the Ottoman Empire
  khrushchev_1954     — the "gift" narrative of the 1954 Soviet transfer
  black_sea_fleet     — Sevastopol as Russia's warm-water naval base
  hero_city_sevastopol — WWII siege / hero-city status
  baptism_of_rus      — Chersonesos as birthplace of Russian Orthodoxy
  russian_speaking_majority — demographic self-determination claim

Each trope is detected via a multi-language (EN / RU / UK) regex set.
A paper may invoke zero, one, or several tropes independently of its
overall classification.

Inputs
------
This script can run on three separate data sources:

  --source academic      data/academic_full.jsonl  (91,670 papers with abstracts)
  --source media         data/crimea_full.jsonl    (GDELT media articles)
  --source training      data/training_corpora_scan.jsonl  (LLM corpora snippets)

Outputs
-------
data/narrative_tropes_{source}.jsonl
    One line per document where at least one trope was detected. Fields:
    doi/url, title, journal/domain, year, language, tropes (list), hits (dict)

data/narrative_tropes_{source}_summary.json
    Aggregate counts: total docs scanned, docs with at least one trope,
    per-trope counts, per-trope × per-year counts (academic only).

Usage
-----
    python3 scripts/classify_narrative_tropes.py --source academic
    python3 scripts/classify_narrative_tropes.py --source academic --limit 5000
    python3 scripts/classify_narrative_tropes.py --source media
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


# ─── Trope patterns ────────────────────────────────────────────────
#
# Each trope is a list of regex patterns. A hit on ANY pattern in the
# list flags the trope. Patterns are compiled case-insensitive. We
# deliberately avoid overly generic patterns (e.g. just "Crimea") — we
# want patterns that specifically invoke the imperial-historical trope.
#
# EN + RU + UK variants. Russian regexes use Cyrillic; Ukrainian
# variants are included where the spelling differs.
#
# Conservative by design: each pattern must be unambiguously about the
# trope (not a general Crimea mention).

TROPES = {
    "catherine_1783": [
        # English
        r"\bCatherine\s+(?:the\s+Great|II)\b.*\b(?:Crimea|Crimean)",
        r"\b(?:Crimea|Crimean)\b.*\bCatherine\s+(?:the\s+Great|II)\b",
        r"\b1783\b.*\b(?:annex|conquer|incorporat|Ottoman)",
        r"\b(?:Ottoman|Tauric|Khanate)\b.*\b1783\b",
        r"\bannexation\s+of\s+(?:the\s+)?Crimean\s+Khanate\b",
        # Russian
        r"\bЕкатерин[аы]\s+(?:Велик|II)",
        r"\b1783\s+год\b.*\b(?:Крым|Тавр)",
        r"\bпокорен[иья]\s+Крым",
        # Ukrainian
        r"\bКатерин[аи]\s+(?:II|Велик)",
    ],

    "khrushchev_1954": [
        # English
        r"\bKhrushchev\b.*\b(?:Crimea|gift|transfer)",
        r"\b(?:transfer|gifted|gift)\b.*\b1954\b.*\bCrimea",
        r"\bCrimea\b.*\b1954\b.*\b(?:transfer|gift)",
        r"\b1954\s+transfer\s+of\s+Crimea",
        r"\broyal\s+gift\b.*\bCrimea",
        # Russian
        r"\bХрущ[её]в\b.*\b(?:Крым|передач|подарок)",
        r"\bпередач[аи]\s+Крыма",
        r"\b1954\s+год\b.*\b(?:Крым|передач)",
        # Ukrainian
        r"\bХрущов\b.*\b(?:Крим|передач)",
        r"\bпередача\s+Криму",
    ],

    "black_sea_fleet": [
        # English
        r"\bBlack\s+Sea\s+Fleet\b",
        r"\bSevastopol\b.*\b(?:naval\s+base|warm.water|fleet\s+headquarters)",
        r"\bRussia'?s?\s+only\s+warm.water\s+port",
        r"\b(?:strategic|vital)\s+port\b.*\bSevastopol",
        # Russian
        r"\bЧерноморск(?:ий|ого)\s+флот",
        r"\bСевастополь\b.*\b(?:военно-морск|флот|база)",
        # Ukrainian
        r"\bЧорноморськ(?:ий|ого)\s+флот",
    ],

    "hero_city_sevastopol": [
        # English — WWII siege / hero city status
        r"\bhero\s+city\b.*\bSevastopol",
        r"\bSevastopol\b.*\bhero\s+city",
        r"\b(?:siege|defence|defense)\s+of\s+Sevastopol\b",
        r"\bSevastopol\s+(?:siege|defence|defense)",
        r"\bSevastopol\b.*\b(?:194[1-5]|Second\s+World\s+War|Great\s+Patriotic)",
        # Russian
        r"\bгород[ау]?\s+[-–]?\s*геро[йя]",
        r"\bоборон[ае]?\s+Севастополя",
        r"\bСевастополь\b.*\bВеликой\s+Отечественной",
        # Ukrainian
        r"\bмісто\s+[-–]?\s*геро",
        r"\bоборона\s+Севастополя",
    ],

    "baptism_of_rus_chersonesos": [
        # English — religious narrative
        r"\bChersonesos\b",
        r"\bChersonese\b",
        r"\bKhersones\b",
        r"\bbaptism\s+of\s+(?:Rus'?|Vladimir)",
        r"\b(?:Prince|St\.?|Saint)\s+Vladimir\b.*\b(?:Crimea|Chersones|baptism)",
        r"\bcradle\s+of\s+(?:Russian\s+)?Orthodox",
        r"\bsacred\s+land\b.*\b(?:Crimea|Sevastopol|Russia)",
        r"\bspiritual\s+home(?:land)?\b.*\b(?:Crimea|Russia)",
        # Russian
        r"\bХерсонес",
        r"\bкрещени[ея]\s+Руси",
        r"\b(?:князь|святой)\s+Владимир\b.*\b(?:Крым|Херсонес|крещени)",
        r"\bдуховн[ао][яе]?\s+(?:родин|колыбель)",
        # Ukrainian
        r"\bХерсонес",
        r"\bхрещенн[яі]\s+Русі",
    ],

    "russian_speaking_majority": [
        # English
        r"\bRussian.speaking\s+(?:majority|population|inhabitants)",
        r"\bmajority\s+(?:of|are)\s+(?:ethnic\s+)?Russians",
        r"\bethnic\s+Russians?\s+(?:majority|make\s+up|comprise)",
        r"\bwill\s+of\s+the\s+(?:Crimean\s+)?people\b",
        r"\bself.determination\b.*\b(?:Crimea|Russian)",
        # Russian
        r"\bрусскоязычн[оы][еяи]\s+(?:большинств|насел)",
        r"\bэтническ[иоы][еях]\s+русские\b.*\b(?:большинств|насел)",
        r"\bсамоопределени",
        r"\bволеизъявлени[ея]",
        # Ukrainian
        r"\bросійськомовн[аеі]",
    ],
}


# Compile all patterns
COMPILED = {
    trope: [re.compile(p, re.IGNORECASE) for p in pats]
    for trope, pats in TROPES.items()
}


def detect_tropes(text: str) -> dict[str, int]:
    """Return {trope: hit_count} for tropes that hit at least once."""
    if not text:
        return {}
    hits: dict[str, int] = {}
    for trope, patterns in COMPILED.items():
        count = 0
        for p in patterns:
            matches = p.findall(text)
            count += len(matches)
        if count > 0:
            hits[trope] = count
    return hits


# ─── Source-specific loaders ────────────────────────────────────────

def iter_academic(limit: int | None):
    path = DATA / "academic_full.jsonl"
    print(f"[load] {path}")
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            title = r.get("title", "") or ""
            abstract = r.get("abstract", "") or ""
            yield {
                "id": r.get("doi") or r.get("openalex_id") or f"academic_{i}",
                "title": title,
                "text": f"{title}\n\n{abstract}",
                "journal": r.get("journal", ""),
                "year": r.get("year", ""),
                "language": r.get("language", ""),
                "stage1_label": r.get("label", ""),
            }


def iter_media(limit: int | None):
    path = DATA / "crimea_full.jsonl"
    if not path.exists():
        print(f"[warn] {path} not found — skipping media", file=sys.stderr)
        return
    print(f"[load] {path}")
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = r.get("title", "") + "\n\n" + (r.get("snippet", "") or r.get("content", "") or "")
            yield {
                "id": r.get("url") or f"media_{i}",
                "title": r.get("title", "") or "",
                "text": text,
                "domain": r.get("domain", "") or r.get("source_domain", ""),
                "year": r.get("year", "") or (r.get("date", "")[:4] if r.get("date") else ""),
                "language": r.get("language", ""),
                "stage1_label": r.get("label", ""),
            }


def iter_training(limit: int | None):
    path = DATA / "training_corpora_scan.jsonl"
    if not path.exists():
        print(f"[warn] {path} not found — skipping training", file=sys.stderr)
        return
    print(f"[load] {path}")
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            yield {
                "id": f"training_{r.get('corpus', 'unknown')}_{r.get('doc_idx', i)}",
                "title": "",
                "text": r.get("snippet", "") or "",
                "corpus": r.get("corpus", ""),
                "source_url": r.get("source", ""),
                "language": "",  # corpus_scan doesn't record per-doc language
                "stage1_label": r.get("label", ""),
            }


# ─── Main scan ──────────────────────────────────────────────────────

def scan(source: str, limit: int | None):
    loaders = {
        "academic": iter_academic,
        "media": iter_media,
        "training": iter_training,
    }
    if source not in loaders:
        print(f"Unknown source: {source}", file=sys.stderr)
        sys.exit(1)

    out_jsonl = DATA / f"narrative_tropes_{source}.jsonl"
    out_summary = DATA / f"narrative_tropes_{source}_summary.json"

    total = 0
    with_any = 0
    trope_counts = Counter()
    trope_by_year = defaultdict(Counter)       # year → trope → count
    trope_by_venue = defaultdict(Counter)      # journal/domain/corpus → trope → count
    stage1_cross = defaultdict(Counter)        # stage1_label → trope → count
    cooccurrence = Counter()                    # tuple(sorted tropes) → count

    with open(out_jsonl, "w", encoding="utf-8") as out:
        for doc in loaders[source](limit):
            total += 1
            if total % 5000 == 0:
                print(f"[scan] {total} processed, {with_any} with at least one trope")

            hits = detect_tropes(doc["text"])
            if not hits:
                continue

            with_any += 1
            for trope in hits:
                trope_counts[trope] += 1
                year = doc.get("year", "") or "unknown"
                trope_by_year[str(year)][trope] += 1
                venue = doc.get("journal") or doc.get("domain") or doc.get("corpus") or "unknown"
                trope_by_venue[venue][trope] += 1
                stage1 = doc.get("stage1_label", "") or "unknown"
                stage1_cross[stage1][trope] += 1

            cooccur_key = tuple(sorted(hits.keys()))
            cooccurrence[cooccur_key] += 1

            row = {
                "id": doc["id"],
                "title": doc.get("title", ""),
                "venue": doc.get("journal") or doc.get("domain") or doc.get("corpus", ""),
                "year": doc.get("year", ""),
                "language": doc.get("language", ""),
                "stage1_label": doc.get("stage1_label", ""),
                "tropes": sorted(hits.keys()),
                "hits": hits,
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[done] {total} documents scanned, {with_any} invoke at least one trope")

    # Aggregate summary
    top_venues = {
        venue: dict(t)
        for venue, t in sorted(
            trope_by_venue.items(),
            key=lambda kv: -sum(kv[1].values()),
        )[:50]
    }

    summary = {
        "source": source,
        "total_documents_scanned": total,
        "documents_with_at_least_one_trope": with_any,
        "per_trope": dict(trope_counts),
        "per_year": {y: dict(t) for y, t in sorted(trope_by_year.items())},
        "top_venues": top_venues,
        "by_stage1_label": {k: dict(v) for k, v in stage1_cross.items()},
        "trope_co-occurrence_top20": [
            {"tropes": list(k), "count": v}
            for k, v in cooccurrence.most_common(20)
        ],
    }
    with open(out_summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"[done] wrote {out_jsonl}")
    print(f"[done] wrote {out_summary}")
    print()
    print("Per-trope totals:")
    for trope, n in trope_counts.most_common():
        print(f"  {n:6d}  {trope}")
    if with_any > 0:
        print()
        print("Top 10 venues (by total trope hits):")
        for venue, t in list(top_venues.items())[:10]:
            total_hits = sum(t.values())
            print(f"  {total_hits:4d}  {venue[:60]}: {', '.join(t.keys())}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["academic", "media", "training"], required=True)
    ap.add_argument("--limit", type=int, default=0, help="Scan only the first N rows (0 = all)")
    args = ap.parse_args()

    scan(args.source, args.limit or None)


if __name__ == "__main__":
    main()
