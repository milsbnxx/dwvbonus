#!/usr/bin/env bash
set -euo pipefail

python3 scripts/scrape_themuse_jobs.py \
  --out data/raw/themuse_jobs_raw.jsonl \
  --max-pages-per-category 99 \
  --target-unique 9000 \
  --sleep-seconds 0.25

python3 scripts/preprocess_jobs.py \
  --input data/raw/themuse_jobs_raw.jsonl \
  --output-csv data/processed/jobs_clean.csv \
  --output-parquet data/processed/jobs_clean.parquet \
  --summary data/processed/summary.json \
  --min-rows 5000
