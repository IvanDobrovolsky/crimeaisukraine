"""
Scan open LLM training corpora for Crimea sovereignty framing.

Streams HuggingFace datasets (C4, RedPajama sample, Dolma, FineWeb,
The Pile) and classifies Crimea-mentioning documents using the
existing 81-signal sovereignty classifier.

Output: per-corpus counts of Ukraine vs Russia framing. This answers
"what framing did open-source LLMs inherit from their training data?"

Usage:
    python scripts/scan_training_corpora.py [--corpus NAME] [--limit N]
"""

import json
import time
import argparse
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

import sys
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "_shared"))
from sovereignty_classifier import SovereigntyClassifier

try:
    from datasets import load_dataset
except ImportError:
    print("Install: pip install datasets")
    raise

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"
OUT_PATH = DATA / "training_corpora_scan.jsonl"
SUMMARY_PATH = DATA / "training_corpora_summary.json"

# Crimea mention filter — cheap substring check before running classifier
CRIMEA_PATTERNS = re.compile(
    r"crimea|кры́?м|крим|simferopol|sevastopol|sebastopol|симферополь|севастополь|"
    r"сімферополь|крым|ялта|yalta|kerch|керч",
    re.IGNORECASE,
)

# Corpora to scan — (HF dataset name, config, split, text field, models that use it)
CORPORA = [
    {
        "name": "c4_en",
        "hf": "allenai/c4",
        "config": "en",
        "split": "train",
        "text_field": "text",
        "models": ["T5", "LLaMA-1", "mT5"],
        "streaming": True,
    },
    {
        "name": "c4_ru",
        "hf": "allenai/c4",
        "config": "ru",
        "split": "train",
        "text_field": "text",
        "models": ["mT5", "multi-lang models"],
        "streaming": True,
    },
    {
        "name": "c4_uk",
        "hf": "allenai/c4",
        "config": "uk",
        "split": "train",
        "text_field": "text",
        "models": ["mT5", "multi-lang models"],
        "streaming": True,
    },
    {
        "name": "redpajama_1t_sample",
        "hf": "togethercomputer/RedPajama-Data-1T-Sample",
        "config": None,
        "split": "train",
        "text_field": "text",
        "models": ["LLaMA-1 repro", "OpenLLaMA", "RedPajama-INCITE"],
        "streaming": True,
    },
    {
        "name": "dolma",
        "hf": "allenai/dolma",
        "config": None,
        "split": "train",
        "text_field": "text",
        "models": ["OLMo", "OLMo-2"],
        "streaming": True,
    },
    {
        "name": "fineweb_edu",
        "hf": "HuggingFaceFW/fineweb-edu",
        "config": "CC-MAIN-2024-10",
        "split": "train",
        "text_field": "text",
        "models": ["SmolLM", "SmolLM-2"],
        "streaming": True,
    },
    {
        "name": "pile_sample",
        "hf": "NeelNanda/pile-10k",
        "config": None,
        "split": "train",
        "text_field": "text",
        "models": ["GPT-J", "GPT-NeoX", "Pythia"],
        "streaming": False,
    },
    {
        "name": "oscar_ru",
        "hf": "oscar-corpus/OSCAR-2301",
        "config": "ru",
        "split": "train",
        "text_field": "text",
        "models": ["multilingual models"],
        "streaming": True,
    },
    {
        "name": "oscar_uk",
        "hf": "oscar-corpus/OSCAR-2301",
        "config": "uk",
        "split": "train",
        "text_field": "text",
        "models": ["multilingual models"],
        "streaming": True,
    },
]


def scan_corpus(corpus_def, classifier, max_crimea_docs=3000, max_total_docs=5_000_000, outf=None):
    """Stream a corpus and classify every Crimea-mentioning doc."""
    name = corpus_def["name"]
    hf_name = corpus_def["hf"]
    config = corpus_def.get("config")
    split = corpus_def.get("split", "train")
    text_field = corpus_def.get("text_field", "text")

    print(f"\n--- {name} ({hf_name}{':'+config if config else ''}) ---")
    print(f"  Models using this corpus: {', '.join(corpus_def['models'])}")

    # Force reset any HF HTTP session state from previous corpus
    try:
        import huggingface_hub
        # Reset session to avoid "client closed" errors between corpora
        if hasattr(huggingface_hub, "_client"):
            huggingface_hub._client = None
        # Also clear any fsspec filesystem cache
        import fsspec
        fsspec.filesystem("hf").clear_instance_cache() if hasattr(fsspec.filesystem("hf"), "clear_instance_cache") else None
    except Exception:
        pass

    try:
        if config:
            ds = load_dataset(hf_name, config, split=split, streaming=corpus_def.get("streaming", True))
        else:
            ds = load_dataset(hf_name, split=split, streaming=corpus_def.get("streaming", True))
    except Exception as e:
        print(f"  ERROR loading: {e}")
        return {
            "corpus": name,
            "error": str(e)[:200],
            "ukraine_frame": 0,
            "russia_frame": 0,
            "disputed": 0,
            "no_signal": 0,
            "crimea_mentions": 0,
            "total_scanned": 0,
        }

    stats = {"ukraine": 0, "russia": 0, "disputed": 0, "no_signal": 0}
    total_scanned = 0
    crimea_hits = 0
    start = time.time()

    try:
        for doc in ds:
            total_scanned += 1

            text = doc.get(text_field, "") if isinstance(doc, dict) else ""
            if not text:
                continue

            # Cheap prefilter: skip anything without Crimea mention
            if not CRIMEA_PATTERNS.search(text[:5000]):
                if total_scanned >= max_total_docs:
                    break
                continue

            crimea_hits += 1

            # Run full classifier on the Crimea mention context
            # Use a window around the first Crimea mention to keep it fast
            match = CRIMEA_PATTERNS.search(text)
            if match:
                start_idx = max(0, match.start() - 500)
                end_idx = min(len(text), match.end() + 1500)
                context = text[start_idx:end_idx]
            else:
                context = text[:2000]

            result = classifier.classify(context)
            label = result.label
            stats[label] = stats.get(label, 0) + 1

            # Write to JSONL
            if outf:
                row = {
                    "corpus": name,
                    "doc_idx": total_scanned,
                    "label": label,
                    "ua_score": round(result.ua_score, 3),
                    "ru_score": round(result.ru_score, 3),
                    "signals": [s.matched for s in result.signals[:5]],
                    "snippet": context[:400],
                    "source": doc.get("url", "") if isinstance(doc, dict) else "",
                }
                outf.write(json.dumps(row, ensure_ascii=False) + "\n")
                outf.flush()

            if crimea_hits % 100 == 0:
                elapsed = time.time() - start
                rate = total_scanned / max(elapsed, 0.1)
                print(f"  [{name}] {crimea_hits} crimea mentions / {total_scanned:,} docs ({rate:.0f} doc/s) — UA={stats['ukraine']} RU={stats['russia']} DISP={stats['disputed']}")

            if crimea_hits >= max_crimea_docs:
                print(f"  Reached max_crimea_docs={max_crimea_docs}, stopping")
                break
            if total_scanned >= max_total_docs:
                print(f"  Reached max_total_docs={max_total_docs}, stopping")
                break
    except Exception as e:
        print(f"  ERROR during scan: {e}")

    return {
        "corpus": name,
        "hf_dataset": hf_name,
        "config": config,
        "models_using": corpus_def["models"],
        "total_scanned": total_scanned,
        "crimea_mentions": crimea_hits,
        "ukraine_frame": stats["ukraine"],
        "russia_frame": stats["russia"],
        "disputed": stats["disputed"],
        "no_signal": stats["no_signal"],
        "russia_pct": round(100 * stats["russia"] / max(crimea_hits, 1), 1),
        "ukraine_pct": round(100 * stats["ukraine"] / max(crimea_hits, 1), 1),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", help="Scan only this corpus by name")
    parser.add_argument("--max-crimea", type=int, default=3000)
    parser.add_argument("--max-total", type=int, default=5_000_000)
    args = parser.parse_args()

    clf = SovereigntyClassifier()
    OUT_PATH.parent.mkdir(exist_ok=True)
    outf = open(OUT_PATH, "a")

    corpora_to_scan = CORPORA
    if args.corpus:
        corpora_to_scan = [c for c in CORPORA if c["name"] == args.corpus]
        if not corpora_to_scan:
            print(f"Unknown corpus: {args.corpus}")
            print(f"Available: {', '.join(c['name'] for c in CORPORA)}")
            return

    results = []
    for corpus in corpora_to_scan:
        result = scan_corpus(corpus, clf, args.max_crimea, args.max_total, outf)
        results.append(result)

        # Save summary after each corpus
        with open(SUMMARY_PATH, "w") as f:
            json.dump({
                "date": datetime.now().isoformat()[:19],
                "results": results,
            }, f, indent=2, ensure_ascii=False)

    outf.close()

    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"{'corpus':25s} {'docs':>10s} {'crimea':>8s} {'UA':>6s} {'RU':>6s} {'RU%':>6s}")
    print("-" * 70)
    for r in results:
        if "error" in r:
            print(f"{r['corpus']:25s} ERROR: {r['error'][:50]}")
            continue
        print(f"{r['corpus']:25s} {r['total_scanned']:>10,} {r['crimea_mentions']:>8,} {r['ukraine_frame']:>6d} {r['russia_frame']:>6d} {r['russia_pct']:>5.1f}%")

    print(f"\nSaved to {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
