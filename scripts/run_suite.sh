#!/usr/bin/env bash
# Run the full measurement suite for the given models, one at a time (one model resident at once).
# Usage: scripts/run_suite.sh gemma4:26b-mlx qwen3.8:27b-mlx
# Results go to benchmarks/results/<date>/. Close other heavy applications first.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="benchmarks/results/$(date +%Y-%m-%d)"
SIZES="${LADDER_SIZES:-4096,8192,16384,32768}"
for model in "$@"; do
  slug="${model//[:\/]/_}"
  echo "== $model"
  python3 -m labbench throughput "$model" --runs 5 --out "$OUT/$slug.throughput.json"
  python3 -m labbench workloads "$model" --repeats 3 --out "$OUT/$slug.workloads.json"
  python3 -m labbench ladder "$model" --sizes "$SIZES" --out "$OUT/$slug.ladder.json"
done
