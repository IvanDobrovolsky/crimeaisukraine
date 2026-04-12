#!/usr/bin/env python3
"""
C4 Sovereignty Study — Full census scan of C4 EN/RU/UK for Crimea sovereignty framing.

No sampling cap. Streams the entire corpus and classifies every Crimea-mentioning document.
Estimated: C4 RU ~20 min, C4 UK ~2 min, C4 EN ~10 hours.

Usage:
    python c4_sovereignty/scan.py --lang ru    # Russian (fastest)
    python c4_sovereignty/scan.py --lang uk    # Ukrainian
    python c4_sovereignty/scan.py --lang en    # English (longest)
    python c4_sovereignty/scan.py --lang all   # All three sequentially
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# Add shared classifier
sys.path.insert(0, str(Path(__file__).parent.parent / "pipelines" / "_shared"))
from sovereignty_classifier import SovereigntyClassifier

# Crimea-related terms for pre-filtering (fast substring match)
CRIMEA_TERMS_EN = [
    "crimea", "crimean", "simferopol", "sevastopol", "yalta", "kerch",
    "feodosia", "evpatoria", "bakhchisarai", "dzhankoi", "alushta",
]
CRIMEA_TERMS_RU = [
    "крым", "крымск", "симферопол", "севастопол", "ялт", "керч",
    "феодоси", "евпатори", "бахчисара", "джанкой", "алушт",
    "республика крым", "крымский",
]
CRIMEA_TERMS_UK = [
    "крим", "кримськ", "сімферопол", "севастопол", "ялт", "керч",
    "феодосі", "євпаторі", "бахчисара", "джанкой", "алушт",
    "автономна республіка крим",
]

LANG_TERMS = {
    "en": CRIMEA_TERMS_EN,
    "ru": CRIMEA_TERMS_RU,
    "uk": CRIMEA_TERMS_UK,
}


def has_crimea_mention(text: str, terms: list[str]) -> bool:
    """Fast pre-filter: does the text mention any Crimea-related term?"""
    text_lower = text.lower()
    return any(term in text_lower for term in terms)


def classify_document(text: str, classifier) -> dict:
    """Run sovereignty classifier on a document."""
    # Use a window around the first Crimea mention
    text_lower = text.lower()
    for term in CRIMEA_TERMS_EN + CRIMEA_TERMS_RU + CRIMEA_TERMS_UK:
        idx = text_lower.find(term)
        if idx >= 0:
            start = max(0, idx - 500)
            end = min(len(text), idx + 1500)
            window = text[start:end]
            break
    else:
        window = text[:2000]

    result = classifier.classify(window)
    return {
        "label": result.label,
        "signals": [s.matched for s in result.signals],
        "signal_count": len(result.signals),
        "confidence": result.confidence,
    }


def scan_c4(lang: str, output_path: str):
    """Stream the full C4 corpus for a language and classify all Crimea mentions."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("pip install datasets")
        sys.exit(1)

    clf = SovereigntyClassifier()
    terms = LANG_TERMS[lang]

    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting C4 {lang} full scan (NO CAP)")
    print(f"  Terms: {terms[:5]}...")
    print(f"  Output: {output_path}")

    dataset = load_dataset("allenai/c4", lang, split="train", streaming=True)

    total_docs = 0
    crimea_docs = 0
    russia_count = 0
    ukraine_count = 0
    disputed_count = 0
    no_signal_count = 0
    start_time = time.time()

    with open(output_path, "a") as outf:  # append mode to resume
        for doc in dataset:
            try:
                total_docs += 1
                text = doc.get("text", "")

                if not has_crimea_mention(text, terms):
                    if total_docs % 500_000 == 0:
                        elapsed = time.time() - start_time
                        rate = total_docs / elapsed
                        print(
                            f"  [{lang}] {total_docs:,} docs scanned, "
                            f"{crimea_docs:,} Crimea mentions, "
                            f"{rate:.0f} docs/sec, "
                            f"RU={russia_count} UA={ukraine_count}"
                        )
                    continue

                crimea_docs += 1
                result = classify_document(text, clf)
                label = result.get("label", "no_signal")

                if label == "russia":
                    russia_count += 1
                elif label == "ukraine":
                    ukraine_count += 1
                elif label == "disputed":
                    disputed_count += 1
                else:
                    no_signal_count += 1

                ts = doc.get("timestamp", "")
                if hasattr(ts, "isoformat"):
                    ts = ts.isoformat()

                record = {
                    "corpus": f"c4_{lang}",
                    "url": doc.get("url", ""),
                    "timestamp": str(ts),
                    "text": text[:3000],
                    "label": label,
                    "signals": result.get("signals", []),
                    "signal_count": result.get("signal_count", 0),
                }
                outf.write(json.dumps(record, ensure_ascii=False) + "\n")

                if crimea_docs % 1000 == 0:
                    elapsed = time.time() - start_time
                    rate = total_docs / elapsed
                    print(
                        f"  [{lang}] {total_docs:,} docs, "
                        f"{crimea_docs:,} Crimea, "
                        f"RU={russia_count} UA={ukraine_count} "
                        f"({rate:.0f} docs/sec)"
                    )
            except Exception as e:
                if total_docs % 100_000 == 0:
                    print(f"  [{lang}] Skipped bad record at {total_docs:,}: {e}")
                continue

    elapsed = time.time() - start_time
    summary = {
        "corpus": f"c4_{lang}",
        "scan_date": datetime.now(timezone.utc).isoformat(),
        "total_docs_scanned": total_docs,
        "crimea_mentions": crimea_docs,
        "russia_framing": russia_count,
        "ukraine_framing": ukraine_count,
        "disputed": disputed_count,
        "no_signal": no_signal_count,
        "elapsed_seconds": round(elapsed, 1),
        "docs_per_second": round(total_docs / elapsed, 1),
        "sampling": "FULL CENSUS (no cap)",
    }

    # Save summary
    summary_path = output_path.replace(".jsonl", "_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*60}")
    print(f"C4 {lang} COMPLETE")
    print(f"  Total docs scanned: {total_docs:,}")
    print(f"  Crimea mentions: {crimea_docs:,}")
    print(f"  Russia-framing: {russia_count}")
    print(f"  Ukraine-framing: {ukraine_count}")
    print(f"  Disputed: {disputed_count}")
    print(f"  No signal: {no_signal_count}")
    if crimea_docs > 0:
        signaled = russia_count + ukraine_count + disputed_count
        if signaled > 0:
            ru_pct = russia_count / signaled * 100
            print(f"  RU share of signaled: {ru_pct:.1f}%")
    print(f"  Time: {elapsed/3600:.1f} hours ({elapsed:.0f} sec)")
    print(f"  Rate: {total_docs/elapsed:.0f} docs/sec")
    print(f"{'='*60}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="C4 Sovereignty Full Census Scan")
    parser.add_argument("--lang", choices=["en", "ru", "uk", "all"], default="all")
    args = parser.parse_args()

    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)

    langs = ["ru", "uk", "en"] if args.lang == "all" else [args.lang]

    all_summaries = []
    for lang in langs:
        output = str(data_dir / f"c4_{lang}_crimea.jsonl")
        summary = scan_c4(lang, output)
        all_summaries.append(summary)

    # Save combined summary
    with open(str(data_dir / "summary.json"), "w") as f:
        json.dump(all_summaries, f, indent=2)

    print("\nAll scans complete. Results in c4_sovereignty/data/")
