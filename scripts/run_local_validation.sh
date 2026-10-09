#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

FULL=0
SKIP_INSTALL=0
for arg in "$@"; do
  case "$arg" in
    --full) FULL=1 ;;
    --skip-install) SKIP_INSTALL=1 ;;
    *) echo "Unknown argument: $arg"; exit 2 ;;
  esac
done

PYTHON_BIN="python3"
if command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="python3.11"
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "==> Creating Python virtual environment"
  "$PYTHON_BIN" -m venv .venv
fi

PY=".venv/bin/python"

if [ "$SKIP_INSTALL" -eq 0 ]; then
  echo "==> Installing NEXUS + DEV dependencies"
  "$PY" -m pip install --upgrade pip
  "$PY" -m pip install -e '.[dev]'
fi

echo "==> Focused Planning + Causal DEV / regressions"
"$PY" -m pytest -q   tests/crc_r1/test_post_second_blind_planning_budget.py   tests/crc_r1/test_post_second_blind_cognitive_loop_planning.py   tests/crc_r1/test_post_second_blind_signed_causal.py   tests/crc_r1/test_post_far_oos_planning_depth.py   tests/crc_r1/test_learned_future.py   tests/crc_r1/test_causal_model.py   tests/crc_r1/test_cognitive_causal_integration.py   tests/crc_r1/test_planning_causal_dev_benchmark.py   tests/crc_r1/test_crc_statistics.py   tests/crc_r1/test_crc_scm_oracle.py   tests/crc_r1/test_crc_scm_dev.py

mkdir -p artifacts

echo "==> Stratified Planning H2-H8 + signed causal DEV"
"$PY" -m benchmarks.crc_planning_causal_dev.run   --seed 20261003   --out artifacts/crc_planning_causal_dev.json

echo "==> Independent random SCM DEV"
"$PY" -m benchmarks.crc_scm_dev.run   --seed 2026100303   --cases-per-regime 70   --out artifacts/crc_scm_dev.json

echo "==> Compile focused cognitive/benchmark surface"
"$PY" -m compileall   src/nexus_gllm/unified_v3/cognitive   benchmarks/crc_planning_causal_dev   benchmarks/crc_scm_dev   benchmarks/crc_statistics.py   benchmarks/crc_scm_oracle.py

if [ "$FULL" -eq 1 ]; then
  echo "==> FULL repository pytest"
  "$PY" -m pytest -q
  echo "==> FULL compileall"
  "$PY" -m compileall src training benchmarks
fi

echo
echo "NEXUS LOCAL VALIDATION COMPLETED."
echo "Artifacts:"
echo "  artifacts/crc_planning_causal_dev.json"
echo "  artifacts/crc_scm_dev.json"
if [ "$FULL" -eq 0 ]; then
  echo "Run again with --full for the full repository pytest + compileall gate."
fi
