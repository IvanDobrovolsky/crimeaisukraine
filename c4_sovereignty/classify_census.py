#!/usr/bin/env python3
"""
Classify C4 census data for sovereignty framing, quotation detection,
and propaganda source contamination.

Reads JSONL files (c4_en_full_census, c4_uk_full_census, c4_ru_*),
classifies each Crimea-mentioning document via the shared sovereignty
classifier, and outputs per-language results + contamination summary.

Usage:
    python classify_census.py                  # all files, 8 workers
    python classify_census.py --workers 4      # fewer workers
    python classify_census.py --dry-run        # count files, don't classify
"""

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
SHARED_DIR = Path("/Users/tati/Desktop/ivan/crimeaisukraine/pipelines/_shared")

# Make the shared classifier importable
sys.path.insert(0, str(SHARED_DIR))
from sovereignty_classifier import SovereigntyClassifier  # noqa: E402

# ---------------------------------------------------------------------------
# Crimea mention terms (multilingual) for window extraction
# ---------------------------------------------------------------------------
CRIMEA_TERMS = re.compile(
    r"crimea|crimean|крым|крим|симферопол|сімферопол|севастопол|ялт|керч",
    re.IGNORECASE,
)

WINDOW_HALF = 1000  # chars on each side of the match -> 2000-char window


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_lang(filename: str) -> str:
    """Auto-detect language code from filename."""
    name = os.path.basename(filename).lower()
    if name.startswith("c4_en"):
        return "en"
    if name.startswith("c4_uk"):
        return "uk"
    if name.startswith("c4_ru"):
        return "ru"
    return "unknown"


def collect_input_files() -> list[tuple[str, str]]:
    """Return [(filepath, lang), ...] for all target JSONL files.

    Includes: c4_en_full_census.jsonl, c4_uk_full_census.jsonl, c4_ru_*.jsonl
    Excludes: c4_*_crimea.jsonl (older format)
    """
    files = []
    for p in sorted(DATA_DIR.glob("c4_*.jsonl")):
        name = p.name
        # Skip older-format crimea-only files
        if "_crimea" in name:
            continue
        lang = detect_lang(name)
        if lang == "unknown":
            continue
        files.append((str(p), lang))
    return files


def extract_window(text: str) -> str | None:
    """Find the first Crimea mention and return a 2000-char window around it."""
    m = CRIMEA_TERMS.search(text)
    if not m:
        return None
    center = m.start()
    start = max(0, center - WINDOW_HALF)
    end = min(len(text), center + WINDOW_HALF)
    return text[start:end]


# ---------------------------------------------------------------------------
# Worker function (runs in each subprocess)
# ---------------------------------------------------------------------------

# Module-level classifier, initialised once per worker process
_clf: SovereigntyClassifier | None = None


def _init_worker():
    """Initialiser for Pool workers -- create a classifier in each process."""
    global _clf
    _clf = SovereigntyClassifier()


def _classify_line(line: str) -> dict | None:
    """Parse one JSONL line, classify, return result dict or None."""
    global _clf
    try:
        doc = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return None

    text = doc.get("text", "")
    url = doc.get("url", "")

    # Limit to first 3000 chars (already truncated in most files, belt & suspenders)
    text = text[:3000]

    # Extract window around Crimea mention
    window = extract_window(text)
    if window is None:
        return None  # no Crimea mention, skip

    result = _clf.classify(window, url=url)

    return {
        "url": url,
        "label": result.label,
        "is_quoted": result.is_quoted if result.label == "russia" else False,
        "source_type": result.source_type,
        "ua_score": round(result.ua_score, 3),
        "ru_score": round(result.ru_score, 3),
    }


# ---------------------------------------------------------------------------
# Per-file processing
# ---------------------------------------------------------------------------

def process_file(
    filepath: str,
    lang: str,
    pool: Pool,
    chunk_size: int = 2000,
) -> tuple[list[dict], dict]:
    """Process one JSONL file. Returns (results_list, stats_dict)."""
    results = []
    stats: dict = {
        "file": os.path.basename(filepath),
        "lang": lang,
        "total_lines": 0,
        "crimea_mentions": 0,
        "labels": Counter(),
        "russia_quoted": 0,
        "russia_asserted": 0,
        "source_types": Counter(),
        "cross_tab": defaultdict(Counter),  # source_type -> label -> count
    }

    print(f"\n  Processing {stats['file']} ...", flush=True)
    t0 = time.time()

    # Read all lines (handles partial/incomplete files)
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError as e:
        print(f"    WARN: Could not read {filepath}: {e}")
        return results, stats

    stats["total_lines"] = len(lines)

    # Process in chunks through the pool
    processed = 0
    for batch_start in range(0, len(lines), chunk_size):
        batch = lines[batch_start : batch_start + chunk_size]
        batch_results = pool.map(_classify_line, batch)

        for r in batch_results:
            if r is None:
                continue
            results.append(r)
            stats["crimea_mentions"] += 1
            stats["labels"][r["label"]] += 1
            st = r["source_type"] or "independent"
            stats["source_types"][st] += 1
            stats["cross_tab"][st][r["label"]] += 1

            if r["label"] == "russia":
                if r["is_quoted"]:
                    stats["russia_quoted"] += 1
                else:
                    stats["russia_asserted"] += 1

        processed += len(batch)
        if processed % 100_000 < chunk_size:
            elapsed = time.time() - t0
            rate = processed / elapsed if elapsed > 0 else 0
            print(
                f"    {processed:>10,} / {stats['total_lines']:,}  "
                f"({processed / stats['total_lines'] * 100:.1f}%)  "
                f"crimea={stats['crimea_mentions']:,}  "
                f"[{rate:,.0f} docs/s]",
                flush=True,
            )

    elapsed = time.time() - t0
    rate = stats["total_lines"] / elapsed if elapsed > 0 else 0
    print(
        f"    Done: {stats['total_lines']:,} lines, "
        f"{stats['crimea_mentions']:,} Crimea mentions, "
        f"{elapsed:.1f}s ({rate:,.0f} docs/s)",
        flush=True,
    )

    return results, stats


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_results(results: list[dict], lang: str):
    """Write classified results to data/classified_c4_{lang}.jsonl"""
    out_path = DATA_DIR / f"classified_c4_{lang}.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"  Wrote {len(results):,} results to {out_path.name}")


def print_summary_table(all_stats: list[dict]):
    """Print a formatted summary table."""
    # Aggregate by language
    by_lang: dict[str, dict] = {}
    for s in all_stats:
        lang = s["lang"]
        if lang not in by_lang:
            by_lang[lang] = {
                "total_lines": 0,
                "crimea_mentions": 0,
                "labels": Counter(),
                "russia_quoted": 0,
                "russia_asserted": 0,
                "source_types": Counter(),
                "cross_tab": defaultdict(Counter),
            }
        agg = by_lang[lang]
        agg["total_lines"] += s["total_lines"]
        agg["crimea_mentions"] += s["crimea_mentions"]
        agg["labels"] += s["labels"]
        agg["russia_quoted"] += s["russia_quoted"]
        agg["russia_asserted"] += s["russia_asserted"]
        agg["source_types"] += s["source_types"]
        for st, label_counts in s["cross_tab"].items():
            agg["cross_tab"][st] += label_counts

    # Also compute grand total
    grand = {
        "total_lines": 0,
        "crimea_mentions": 0,
        "labels": Counter(),
        "russia_quoted": 0,
        "russia_asserted": 0,
        "source_types": Counter(),
        "cross_tab": defaultdict(Counter),
    }
    for agg in by_lang.values():
        grand["total_lines"] += agg["total_lines"]
        grand["crimea_mentions"] += agg["crimea_mentions"]
        grand["labels"] += agg["labels"]
        grand["russia_quoted"] += agg["russia_quoted"]
        grand["russia_asserted"] += agg["russia_asserted"]
        grand["source_types"] += agg["source_types"]
        for st, label_counts in agg["cross_tab"].items():
            grand["cross_tab"][st] += label_counts

    sep = "=" * 72
    thin = "-" * 72

    print(f"\n{sep}")
    print("  C4 SOVEREIGNTY CENSUS -- CLASSIFICATION SUMMARY")
    print(sep)

    for lang in sorted(by_lang.keys()):
        agg = by_lang[lang]
        _print_lang_block(lang.upper(), agg)

    if len(by_lang) > 1:
        _print_lang_block("TOTAL", grand)

    # Cross-tab: source_type x label
    print(f"\n{sep}")
    print("  CROSS-TAB: Source Type x Framing Label (all languages)")
    print(sep)
    labels_order = ["russia", "ukraine", "disputed", "no_signal"]
    source_order = ["state_t1", "proxy_t2", "pravda", "state_adj_t4", "independent"]
    header = f"  {'Source Type':<16s}"
    for lb in labels_order:
        header += f" {lb:>11s}"
    header += f" {'TOTAL':>9s}"
    print(header)
    print(f"  {thin}")

    for st in source_order:
        if st not in grand["cross_tab"]:
            continue
        row = grand["cross_tab"][st]
        total_row = sum(row.values())
        line = f"  {st:<16s}"
        for lb in labels_order:
            line += f" {row.get(lb, 0):>11,}"
        line += f" {total_row:>9,}"
        print(line)

    # Grand total row
    total_line = f"  {'TOTAL':<16s}"
    for lb in labels_order:
        total_line += f" {grand['labels'].get(lb, 0):>11,}"
    total_line += f" {grand['crimea_mentions']:>9,}"
    print(f"  {thin}")
    print(total_line)
    print()


def _print_lang_block(title: str, agg: dict):
    """Print one language block of the summary."""
    thin = "-" * 72
    cm = agg["crimea_mentions"]
    labels = agg["labels"]
    pct = lambda n: f"{n / cm * 100:.1f}%" if cm else "0.0%"

    print(f"\n  {title}")
    print(f"  {thin}")
    print(f"  Total docs scanned:     {agg['total_lines']:>12,}")
    print(f"  Crimea mentions:        {cm:>12,}")
    if agg["total_lines"]:
        print(
            f"  Crimea mention rate:    "
            f"{cm / agg['total_lines'] * 100:>11.2f}%"
        )
    print()
    print(f"    russia:               {labels.get('russia', 0):>10,}  ({pct(labels.get('russia', 0))})")
    print(f"      - asserted:         {agg['russia_asserted']:>10,}")
    print(f"      - quoted:           {agg['russia_quoted']:>10,}")
    print(f"    ukraine:              {labels.get('ukraine', 0):>10,}  ({pct(labels.get('ukraine', 0))})")
    print(f"    disputed:             {labels.get('disputed', 0):>10,}  ({pct(labels.get('disputed', 0))})")
    print(f"    no_signal:            {labels.get('no_signal', 0):>10,}  ({pct(labels.get('no_signal', 0))})")
    print()
    print(f"  Source type breakdown:")
    for st in ["state_t1", "proxy_t2", "pravda", "state_adj_t4", "independent"]:
        count = agg["source_types"].get(st, 0)
        print(f"    {st:<20s} {count:>10,}  ({pct(count)})")


def save_summary_json(all_stats: list[dict]):
    """Save machine-readable summary to data/contamination_summary.json"""
    by_lang: dict[str, dict] = {}
    for s in all_stats:
        lang = s["lang"]
        if lang not in by_lang:
            by_lang[lang] = {
                "total_lines": 0,
                "crimea_mentions": 0,
                "labels": Counter(),
                "russia_quoted": 0,
                "russia_asserted": 0,
                "source_types": Counter(),
                "cross_tab": defaultdict(Counter),
            }
        agg = by_lang[lang]
        agg["total_lines"] += s["total_lines"]
        agg["crimea_mentions"] += s["crimea_mentions"]
        agg["labels"] += s["labels"]
        agg["russia_quoted"] += s["russia_quoted"]
        agg["russia_asserted"] += s["russia_asserted"]
        agg["source_types"] += s["source_types"]
        for st, label_counts in s["cross_tab"].items():
            agg["cross_tab"][st] += label_counts

    summary = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    for lang, agg in sorted(by_lang.items()):
        summary[lang] = {
            "total_lines": agg["total_lines"],
            "crimea_mentions": agg["crimea_mentions"],
            "labels": dict(agg["labels"]),
            "russia_asserted": agg["russia_asserted"],
            "russia_quoted": agg["russia_quoted"],
            "source_types": dict(agg["source_types"]),
            "cross_tab": {
                st: dict(lc) for st, lc in agg["cross_tab"].items()
            },
        }

    # Grand total
    grand_labels = Counter()
    grand_source = Counter()
    grand_cross = defaultdict(Counter)
    grand_lines = 0
    grand_mentions = 0
    grand_asserted = 0
    grand_quoted = 0
    for agg in by_lang.values():
        grand_lines += agg["total_lines"]
        grand_mentions += agg["crimea_mentions"]
        grand_labels += agg["labels"]
        grand_asserted += agg["russia_asserted"]
        grand_quoted += agg["russia_quoted"]
        grand_source += agg["source_types"]
        for st, lc in agg["cross_tab"].items():
            grand_cross[st] += lc

    summary["total"] = {
        "total_lines": grand_lines,
        "crimea_mentions": grand_mentions,
        "labels": dict(grand_labels),
        "russia_asserted": grand_asserted,
        "russia_quoted": grand_quoted,
        "source_types": dict(grand_source),
        "cross_tab": {st: dict(lc) for st, lc in grand_cross.items()},
    }

    out_path = DATA_DIR / "contamination_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  Summary saved to {out_path.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Classify C4 census data for sovereignty framing."
    )
    parser.add_argument(
        "--workers", type=int, default=8,
        help="Number of multiprocessing workers (default: 8)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="List files and counts without classifying",
    )
    parser.add_argument(
        "--lang", choices=["en", "uk", "ru"],
        help="Process only this language (default: all)",
    )
    args = parser.parse_args()

    print("C4 Sovereignty Census Classifier")
    print("=" * 72)

    # Collect input files
    input_files = collect_input_files()
    if args.lang:
        input_files = [(fp, lg) for fp, lg in input_files if lg == args.lang]
    if not input_files:
        print("ERROR: No matching JSONL files found in", DATA_DIR)
        sys.exit(1)

    print(f"\nFound {len(input_files)} file(s):")
    for fp, lang in input_files:
        print(f"  [{lang}] {os.path.basename(fp)}")

    if args.dry_run:
        print("\n--dry-run: exiting without classification.")
        return

    # Group by language for output
    lang_results: dict[str, list[dict]] = defaultdict(list)
    all_stats: list[dict] = []

    t_start = time.time()

    with Pool(processes=args.workers, initializer=_init_worker) as pool:
        for filepath, lang in input_files:
            results, stats = process_file(filepath, lang, pool)
            lang_results[lang].extend(results)
            all_stats.append(stats)

    t_elapsed = time.time() - t_start

    # Write per-language output files
    print(f"\n{'=' * 72}")
    print("  Writing output files...")
    for lang, results in sorted(lang_results.items()):
        write_results(results, lang)

    # Print and save summary
    print_summary_table(all_stats)
    save_summary_json(all_stats)

    total_docs = sum(s["total_lines"] for s in all_stats)
    total_mentions = sum(s["crimea_mentions"] for s in all_stats)
    print(f"  Total time: {t_elapsed:.1f}s for {total_docs:,} docs ({total_mentions:,} Crimea mentions)")
    print(f"  Throughput: {total_docs / t_elapsed:,.0f} docs/s")
    print()


if __name__ == "__main__":
    main()
