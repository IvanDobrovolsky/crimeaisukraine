#!/usr/bin/env bash
set -euo pipefail

# Push Parquet datasets to HuggingFace
# Requires: HF_TOKEN env var (or huggingface-cli login)
# Usage:
#   export HF_TOKEN=hf_xxx
#   bash scripts/push_hf.sh
#   # or push a single dataset:
#   bash scripts/push_hf.sh academic-sovereignty

ORG="CrimeaIsUkraineOrg"
EXPORT_DIR="hf_export"

# Prefix all dataset names for consistency
PREFIX="crimea-sovereignty"

# Map export folder names to HF dataset names
declare -A DATASET_MAP=(
  ["platform-audit"]="${PREFIX}-platforms"
  ["academic-sovereignty"]="${PREFIX}-academic"
  ["academic-sovereignty-verified"]="${PREFIX}-academic-verified"
  ["media-framing"]="${PREFIX}-media"
  ["llm-sovereignty-audit"]="${PREFIX}-llm"
  ["training-corpora-framing"]="${PREFIX}-corpora"
)

# Check HF auth
if ! huggingface-cli whoami &>/dev/null; then
  if [ -z "${HF_TOKEN:-}" ]; then
    echo "ERROR: Not logged in. Set HF_TOKEN or run: huggingface-cli login"
    exit 1
  fi
fi

# Generate parquet if not present
if [ ! -d "$EXPORT_DIR" ] || [ -z "$(ls -A $EXPORT_DIR 2>/dev/null)" ]; then
  echo "Generating Parquet files..."
  python3 scripts/export_hf_parquet.py
fi

# Filter to single dataset if argument provided
TARGETS="${1:-all}"

for folder in "$EXPORT_DIR"/*/; do
  name=$(basename "$folder")
  hf_name="${DATASET_MAP[$name]:-}"

  if [ -z "$hf_name" ]; then
    echo "SKIP: $name (no mapping)"
    continue
  fi

  if [ "$TARGETS" != "all" ] && [ "$TARGETS" != "$name" ] && [ "$TARGETS" != "$hf_name" ]; then
    continue
  fi

  repo="${ORG}/${hf_name}"
  echo ""
  echo "=========================================="
  echo "Uploading: $repo"
  echo "=========================================="

  huggingface-cli upload "$repo" "$folder" . \
    --repo-type dataset \
    ${HF_TOKEN:+--token "$HF_TOKEN"} \
    || echo "FAILED: $repo"
done

echo ""
echo "Done. Datasets at: https://huggingface.co/${ORG}"
