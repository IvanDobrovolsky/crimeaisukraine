#!/bin/bash
# Deploy Dolma sovereignty scan to a cloud instance (Hetzner, DigitalOcean, any Linux box)
#
# Usage:
#   1. Create a Hetzner CX32 (4 vCPU, 8GB RAM, ~€0.02/hr)
#   2. scp this entire c4_sovereignty/ folder to the instance
#   3. ssh into the instance and run: bash deploy_dolma.sh
#   4. Results will be in data/dolma_*.jsonl
#   5. scp results back when done
#
# Estimated: 4 parallel workers = ~20 hours = ~€0.40 total

set -e

echo "=== Installing dependencies ==="
apt-get update -qq && apt-get install -y -qq python3-pip python3-venv > /dev/null 2>&1 || true
python3 -m pip install --quiet datasets

echo "=== Creating scan script ==="
cat > /tmp/dolma_scan.py << 'PYSCAN'
#!/usr/bin/env python3
"""Dolma sovereignty scan — single shard range worker."""
import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone

# Inline classifier (no external dependencies)
CRIMEA_TERMS = [
    "crimea", "crimean", "крым", "крымск", "крим", "кримськ",
    "simferopol", "симферопол", "сімферопол",
    "sevastopol", "севастопол",
    "yalta", "ялт", "kerch", "керч",
    "feodosia", "феодоси", "феодосі",
    "evpatoria", "євпаторі", "евпатори",
]

RU_SIGNALS = [
    r"republic of crimea", r"республика крым", r"крымский федеральн",
    r"crimea,?\s*russia", r"крым,?\s*росси", r"sevastopol,?\s*russia",
    r"симферополь,?\s*росси", r"севастополь,?\s*росси",
    r"rejoined russia", r"reunifi\w+ with russia", r"reunifi\w+ of crimea",
    r"воссоединени\w+ крым", r"присоединени\w+ крым",
    r"crimea joined russia", r"крым вошел в состав",
    r"crimean federal district", r"крымский федеральный округ",
    r"annexed by rus", r"Republic of Crimea",
]

UA_SIGNALS = [
    r"autonomous republic of crimea", r"автономна республіка крим",
    r"автономная республика крым",
    r"annexed crimea", r"illegally annexed", r"occupation of crimea",
    r"окупаці\w+ крим", r"анексі\w+ крим", r"аннекси\w+ крым",
    r"crimea,?\s*ukraine", r"крим,?\s*україн", r"крым,?\s*украин",
    r"UA-43", r"ukrainian crimea",
]

def classify(text):
    text_lower = text.lower()
    ru = sum(1 for p in RU_SIGNALS if re.search(p, text_lower))
    ua = sum(1 for p in UA_SIGNALS if re.search(p, text_lower))
    if ru > ua: return "russia", ru, ua
    if ua > ru: return "ukraine", ru, ua
    if ru > 0: return "disputed", ru, ua
    return "no_signal", 0, 0

def has_crimea(text):
    t = text.lower()
    return any(term in t for term in CRIMEA_TERMS)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-start", type=int, required=True)
    parser.add_argument("--shard-end", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    from datasets import load_dataset

    print(f"[{datetime.now(timezone.utc).isoformat()}] Dolma shards {args.shard_start}-{args.shard_end}")

    total = 0
    crimea = 0
    ru_count = 0
    ua_count = 0
    start_time = time.time()

    with open(args.output, "w") as outf:
        for shard_idx in range(args.shard_start, args.shard_end + 1):
            shard_name = f"v1_6-sample/0{shard_idx:03d}.json.gz" if shard_idx < 100 else f"v1_6-sample/{shard_idx:04d}.json.gz"
            try:
                ds = load_dataset("allenai/dolma", data_files=shard_name, split="train", streaming=True)
            except Exception as e:
                print(f"  Shard {shard_idx}: {e}")
                continue

            shard_crimea = 0
            for doc in ds:
                total += 1
                text = doc.get("text", "")
                if not has_crimea(text):
                    continue

                crimea += 1
                shard_crimea += 1

                # Classify using window around first mention
                idx = min(text.lower().find(t) for t in CRIMEA_TERMS if t in text.lower())
                window = text[max(0, idx-500):idx+1500]
                label, ru, ua = classify(window)

                if label == "russia": ru_count += 1
                elif label == "ukraine": ua_count += 1

                record = {
                    "corpus": "dolma",
                    "shard": shard_idx,
                    "text": text[:3000],
                    "label": label,
                    "ru_signals": ru,
                    "ua_signals": ua,
                }
                outf.write(json.dumps(record, ensure_ascii=False) + "\n")

            elapsed = time.time() - start_time
            print(f"  Shard {shard_idx}: {shard_crimea} Crimea docs (total: {crimea}, RU={ru_count}, UA={ua_count}, {total:,} docs, {elapsed:.0f}s)")

    elapsed = time.time() - start_time
    summary = {
        "shards": f"{args.shard_start}-{args.shard_end}",
        "total_docs": total,
        "crimea_docs": crimea,
        "russia": ru_count,
        "ukraine": ua_count,
        "elapsed_hours": round(elapsed/3600, 2),
    }
    with open(args.output.replace(".jsonl", "_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nDone: {crimea} Crimea docs, RU={ru_count}, UA={ua_count}, {elapsed/3600:.1f} hours")

if __name__ == "__main__":
    main()
PYSCAN

echo "=== Starting 4 parallel workers ==="
mkdir -p data

# Dolma v1.6 sample has 103 shards (0-102)
# 16 parallel workers — ~5 hours on a machine with 16+ cores
WORKERS=16
SHARDS=103
PER_WORKER=$((SHARDS / WORKERS))

for i in $(seq 0 $((WORKERS - 1))); do
    START=$((i * PER_WORKER))
    if [ $i -eq $((WORKERS - 1)) ]; then
        END=102
    else
        END=$(((i + 1) * PER_WORKER - 1))
    fi
    python3 /tmp/dolma_scan.py --shard-start $START --shard-end $END --output data/dolma_${START}_${END}.jsonl &
    echo "  Worker $((i+1)): shards $START-$END (PID: $!)"
done

echo "$WORKERS workers launched. Monitor with: ls -la data/dolma_*.jsonl"
echo "Merge when done: cat data/dolma_*.jsonl > data/dolma_full.jsonl"
wait
echo "=== ALL WORKERS COMPLETE ==="
cat data/dolma_*_summary.json
