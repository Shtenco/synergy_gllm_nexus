#!/usr/bin/env bash
set -Eeuo pipefail

: "${NEXUS_LLAMA_SERVER:?Set path to llama-server}"
: "${NEXUS_QWEN3_14B_GGUF:?Set path to Qwen3-14B-Q4_K_M.gguf}"

EXPECTED_SHA256="500a8806e85ee9c83f3ae08420295592451379b4f8cf2d0f41c15dffeb6b81f0"
ACTUAL_SHA256="$(sha256sum "$NEXUS_QWEN3_14B_GGUF" | awk '{print $1}')"

if [[ "$ACTUAL_SHA256" != "$EXPECTED_SHA256" ]]; then
  echo "NEXUS V8: Qwen3-14B checksum mismatch" >&2
  echo "expected=$EXPECTED_SHA256" >&2
  echo "actual=$ACTUAL_SHA256" >&2
  exit 2
fi

SIZE="$(stat -c%s "$NEXUS_QWEN3_14B_GGUF")"
if [[ "$SIZE" -lt 8000000000 ]]; then
  echo "NEXUS V8: suspicious Qwen3-14B file size: $SIZE" >&2
  exit 3
fi

exec "$NEXUS_LLAMA_SERVER" \
  -m "$NEXUS_QWEN3_14B_GGUF" \
  --alias Qwen3-14B-Q4_K_M \
  --host "${LLAMA_HOST:-127.0.0.1}" \
  --port "${LLAMA_PORT:-8080}" \
  -c "${NEXUS_CONTEXT:-16384}" \
  -t "${NEXUS_THREADS:-8}" \
  --parallel "${NEXUS_PARALLEL:-1}" \
  --jinja --metrics --slots
