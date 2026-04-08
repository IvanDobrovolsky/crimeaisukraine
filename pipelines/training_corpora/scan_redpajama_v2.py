"""
Scan RedPajama-V2 via direct file download (bypasses broken loader script).

HF's `datasets` library no longer supports script-based loading, so
`load_dataset("togethercomputer/RedPajama-Data-V2")` fails. This scanner
downloads the `sample/documents/*.json.gz` files directly through
huggingface_hub and streams them.

Writes rows to data/training_corpora_scan.jsonl with corpus="redpajama_v2"
so the existing rebuild_summary.py picks them up.
"""

import gzip
import json
import re
import sys
import time
from pathlib import Path
from huggingface_hub import hf_hub_download

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "_shared"))
from sovereignty_classifier import SovereigntyClassifier

PROJECT = Path(__file__).parent.parent.parent
OUT_PATH = PROJECT / "data" / "training_corpora_scan.jsonl"

CRIMEA_PATTERNS = re.compile(
    r"crimea|кры́?м|крим|simferopol|sevastopol|sebastopol|симферополь|севастополь|"
    r"сімферополь|крым|ялта|yalta|kerch|керч",
    re.IGNORECASE,
)

# English head + middle quality tiers from the 2023-06 snapshot
TARGET_FILES = [
    "sample/documents/2023-06/0000/en_head.json.gz",
    "sample/documents/2023-06/0000/en_middle.json.gz",
]

REPO = "togethercomputer/RedPajama-Data-V2"


def scan_file(local_path, clf, outf, max_crimea=1500):
    crimea_hits = 0
    total = 0
    stats = {"ukraine": 0, "russia": 0, "disputed": 0, "no_signal": 0}
    start = time.time()

    with gzip.open(local_path, "rt", encoding="utf-8", errors="ignore") as f:
        for line in f:
            total += 1
            try:
                doc = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = doc.get("raw_content") or doc.get("text") or ""
            if not text:
                continue
            if not CRIMEA_PATTERNS.search(text[:5000]):
                continue

            crimea_hits += 1
            match = CRIMEA_PATTERNS.search(text)
            start_idx = max(0, match.start() - 500)
            end_idx = min(len(text), match.end() + 1500)
            context = text[start_idx:end_idx]

            result = clf.classify(context)
            stats[result.label] = stats.get(result.label, 0) + 1

            row = {
                "corpus": "redpajama_v2",
                "doc_idx": total,
                "label": result.label,
                "ua_score": round(result.ua_score, 3),
                "ru_score": round(result.ru_score, 3),
                "signals": [s.matched for s in result.signals[:5]],
                "snippet": context[:400],
                "source": doc.get("url", ""),
            }
            outf.write(json.dumps(row, ensure_ascii=False) + "\n")
            outf.flush()

            if crimea_hits % 100 == 0:
                elapsed = time.time() - start
                rate = total / max(elapsed, 0.1)
                print(f"  {crimea_hits} crimea / {total:,} docs ({rate:.0f}/s) — "
                      f"UA={stats['ukraine']} RU={stats['russia']} DISP={stats['disputed']}")

            if crimea_hits >= max_crimea:
                print(f"  reached max_crimea={max_crimea}, stopping file")
                break

    return stats, crimea_hits, total


def main():
    clf = SovereigntyClassifier()
    outf = open(OUT_PATH, "a")

    for target in TARGET_FILES:
        print(f"\n--- {target} ---")
        print("  downloading…")
        local = hf_hub_download(repo_id=REPO, filename=target, repo_type="dataset")
        print(f"  {local}")
        stats, hits, total = scan_file(local, clf, outf)
        print(f"  done: {hits} crimea in {total:,} docs. UA={stats['ukraine']} "
              f"RU={stats['russia']} DISP={stats['disputed']}")

    outf.close()
    print("\nDone. Run rebuild_summary.py to refresh summary.json")


if __name__ == "__main__":
    main()
