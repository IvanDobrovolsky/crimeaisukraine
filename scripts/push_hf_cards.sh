#!/usr/bin/env zsh
set -eo pipefail

# Push ONLY README.md dataset cards to HuggingFace (no parquet data).
# Usage:
#   bash scripts/push_hf_cards.sh
#   bash scripts/push_hf_cards.sh crimea-sovereignty-llm

ORG="CrimeaIsUkraineOrg"
EXPORT_DIR="hf_export"
TARGET="${1:-all}"

pairs=(
  "platform-audit:crimea-sovereignty-platforms"
  "academic-sovereignty:crimea-sovereignty-academic"
  "academic-sovereignty-verified:crimea-sovereignty-academic-verified"
  "media-framing:crimea-sovereignty-media"
  "llm-sovereignty-audit:crimea-sovereignty-llm"
  "training-corpora-framing:crimea-sovereignty-corpora"
  "validation:crimea-sovereignty-validation"
  "c4-analysis:crimea-sovereignty-c4-analysis"
  "grounding:crimea-sovereignty-grounding"
  "source-domains:crimea-sovereignty-source-domains"
)

for pair in "${pairs[@]}"; do
  folder="${pair%%:*}"
  hf_name="${pair##*:}"

  if [ "$TARGET" != "all" ] && [ "$TARGET" != "$folder" ] && [ "$TARGET" != "$hf_name" ]; then
    continue
  fi

  readme="$EXPORT_DIR/$folder/README.md"
  if [ ! -f "$readme" ]; then
    echo "SKIP: $folder (no README.md)"
    continue
  fi

  repo="${ORG}/${hf_name}"
  echo "Uploading README.md → $repo"

  HF_TOKEN=$(cat /etc/secrets/hf) hf upload "$repo" "$readme" README.md \
    --type dataset \
    --commit-message "Update dataset card with correct paper numbers" \
    || echo "FAILED: $repo"
done

echo ""
echo "Done. Cards updated at: https://huggingface.co/${ORG}"
