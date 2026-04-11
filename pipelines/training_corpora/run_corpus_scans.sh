#!/bin/bash
# Run each corpus scan as a separate Python process to avoid shared HTTP state
set -u
cd "$(dirname "$0")/.."

CORPORA=(
    c4_ru
    c4_uk
    redpajama_1t_sample
    pile_sample
    dolma
    fineweb_edu
    oscar_ru
    oscar_uk
)

for corpus in "${CORPORA[@]}"; do
    echo "==========================================="
    echo "[$(date +%H:%M:%S)] Scanning $corpus"
    echo "==========================================="
    python3 scripts/scan_training_corpora.py --corpus "$corpus" --max-crimea 2000 2>&1
    echo ""
done

echo "All corpora complete"
