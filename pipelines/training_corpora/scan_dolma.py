"""
Scan Dolma (OLMo / OLMo-2 training corpus) via direct HTTP download.

HF's `datasets` library no longer loads allenai/dolma (script-based).
Dolma publishes an 8B-token sample as 103 json.gz files at olmo-data.org;
this scanner streams them one at a time, filters for Crimea mentions,
and runs the sovereignty classifier.

Writes rows to data/training_corpora_scan.jsonl with corpus="dolma" so
rebuild_summary.py picks them up.
"""

import gzip
import io
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "_shared"))
from sovereignty_classifier import SovereigntyClassifier
from huggingface_hub import hf_hub_download

PROJECT = Path(__file__).parent.parent.parent
OUT_PATH = PROJECT / "data" / "training_corpora_scan.jsonl"

CRIMEA_PATTERNS = re.compile(
    r"crimea|кры́?м|крим|simferopol|sevastopol|sebastopol|симферополь|севастополь|"
    r"сімферополь|крым|ялта|yalta|kerch|керч",
    re.IGNORECASE,
)

MAX_CRIMEA = 2000


def load_urls():
    path = hf_hub_download("allenai/dolma", "urls/v1_6-sample.txt", repo_type="dataset")
    with open(path) as f:
        return [l.strip() for l in f if l.strip()]


def stream_gz_url(url):
    """Stream-decompress a remote gzip file line by line without buffering whole file."""
    req = urllib.request.Request(url, headers={"User-Agent": "crimeaisukraine-research/1.0"})
    resp = urllib.request.urlopen(req, timeout=120)
    # GzipFile over a streaming HTTP response
    gz = gzip.GzipFile(fileobj=resp)
    text = io.TextIOWrapper(gz, encoding="utf-8", errors="ignore")
    for line in text:
        yield line


def scan(clf, outf):
    urls = load_urls()
    print(f"loaded {len(urls)} dolma sample urls")

    stats = {"ukraine": 0, "russia": 0, "disputed": 0, "no_signal": 0}
    crimea_hits = 0
    total = 0
    start = time.time()

    for i, url in enumerate(urls):
        print(f"\n--- file {i+1}/{len(urls)}: {url.split('/')[-1]} ---")
        try:
            for line in stream_gz_url(url):
                total += 1
                try:
                    doc = json.loads(line)
                except json.JSONDecodeError:
                    continue
                text = doc.get("text", "")
                if not text or not CRIMEA_PATTERNS.search(text[:5000]):
                    continue

                crimea_hits += 1
                match = CRIMEA_PATTERNS.search(text)
                start_idx = max(0, match.start() - 500)
                end_idx = min(len(text), match.end() + 1500)
                context = text[start_idx:end_idx]

                result = clf.classify(context)
                stats[result.label] = stats.get(result.label, 0) + 1

                row = {
                    "corpus": "dolma",
                    "doc_idx": total,
                    "label": result.label,
                    "ua_score": round(result.ua_score, 3),
                    "ru_score": round(result.ru_score, 3),
                    "signals": [s.matched for s in result.signals[:5]],
                    "snippet": context[:400],
                    "source": (doc.get("metadata") or {}).get("url", "") or doc.get("source", ""),
                }
                outf.write(json.dumps(row, ensure_ascii=False) + "\n")
                outf.flush()

                if crimea_hits % 50 == 0:
                    elapsed = time.time() - start
                    rate = total / max(elapsed, 0.1)
                    print(f"  {crimea_hits} crimea / {total:,} docs ({rate:.0f}/s) — "
                          f"UA={stats['ukraine']} RU={stats['russia']} DISP={stats['disputed']}")

                if crimea_hits >= MAX_CRIMEA:
                    print(f"  reached MAX_CRIMEA={MAX_CRIMEA}, stopping")
                    return stats, crimea_hits, total
        except Exception as e:
            print(f"  ERROR on file: {e}")
            continue

    return stats, crimea_hits, total


def main():
    clf = SovereigntyClassifier()
    outf = open(OUT_PATH, "a")
    stats, hits, total = scan(clf, outf)
    outf.close()
    print(f"\nDONE: {hits} crimea mentions in {total:,} docs. "
          f"UA={stats['ukraine']} RU={stats['russia']} DISP={stats['disputed']}")
    print("Run rebuild_summary.py to refresh summary.json")


if __name__ == "__main__":
    main()
