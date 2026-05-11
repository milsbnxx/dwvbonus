#!/usr/bin/env python3
"""Clean scraped jobs and build analysis-ready dataset."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

DS_KEYWORDS = [
    r"\bdata science\b",
    r"\bdata scientist\b",
    r"\bmachine learning\b",
    r"\bml engineer\b",
    r"\bai engineer\b",
    r"\bdata engineer\b",
    r"\banalytics\b",
    r"\bbusiness intelligence\b",
    r"\bbi analyst\b",
    r"\bnlp\b",
    r"\bcomputer vision\b",
    r"\bstatistician\b",
    r"\bdeep learning\b",
]

IT_KEYWORDS = [
    r"\bsoftware\b",
    r"\bdeveloper\b",
    r"\bengineer\b",
    r"\bdevops\b",
    r"\bcloud\b",
    r"\bsecurity\b",
    r"\binformation technology\b",
    r"\bit support\b",
    r"\bsystem administrator\b",
    r"\bfrontend\b",
    r"\bbackend\b",
    r"\bfull stack\b",
    r"\bqa\b",
    r"\btest automation\b",
    r"\bsite reliability\b",
    r"\bsre\b",
    r"\bnetwork\b",
    r"\bdatabase\b",
    r"\bpython\b",
    r"\bjava\b",
    r"\bjavascript\b",
    r"\btypescript\b",
    r"\bproduct manager\b",
    r"\bcomputer and it\b",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/raw/themuse_jobs_raw.jsonl"))
    parser.add_argument("--output-csv", type=Path, default=Path("data/processed/jobs_clean.csv"))
    parser.add_argument("--output-parquet", type=Path, default=Path("data/processed/jobs_clean.parquet"))
    parser.add_argument("--summary", type=Path, default=Path("data/processed/summary.json"))
    parser.add_argument("--min-rows", type=int, default=5000)
    return parser.parse_args()


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def compact_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    return re.sub(r"\s+", " ", text).strip()


def keyword_score(text: str, patterns: list[str]) -> int:
    score = 0
    for p in patterns:
        if re.search(p, text, flags=re.IGNORECASE):
            score += 1
    return score


def infer_track(text: str) -> str | None:
    ds_score = keyword_score(text, DS_KEYWORDS)
    it_score = keyword_score(text, IT_KEYWORDS)

    if ds_score == 0 and it_score == 0:
        return None
    if ds_score >= it_score and ds_score > 0:
        return "Data Science"
    return "IT"


def parse_primary_location(locations: list[str]) -> str:
    if not locations:
        return "Unknown"
    return compact_text(locations[0])


def infer_country(location: str) -> str:
    if not location or location == "Unknown":
        return "Unknown"
    if "," in location:
        country = location.split(",")[-1].strip()
        return country or "Unknown"
    return location


def infer_remote_flag(text: str, location: str) -> bool:
    combined = f"{text} {location}".lower()
    return any(token in combined for token in ["remote", "hybrid", "work from home", "удал", "дистанц"])


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    raw_rows = load_jsonl(args.input)
    df = pd.DataFrame(raw_rows)

    if df.empty:
        raise RuntimeError("No rows found in raw dataset")

    df["title"] = df["title"].map(compact_text)
    df["company"] = df["company"].map(compact_text)
    df["url"] = df["url"].map(compact_text)
    df["description"] = df["description_html"].map(lambda x: strip_html(str(x or "")))

    df["categories_text"] = df["categories"].map(lambda x: " | ".join(x) if isinstance(x, list) else "")
    df["levels_text"] = df["levels"].map(lambda x: " | ".join(x) if isinstance(x, list) else "")
    df["tags_text"] = df["tags"].map(lambda x: " | ".join(x) if isinstance(x, list) else "")
    df["primary_location"] = df["locations"].map(lambda x: parse_primary_location(x if isinstance(x, list) else []))
    df["country"] = df["primary_location"].map(infer_country)

    df["published_at"] = pd.to_datetime(df["publication_date"], errors="coerce", utc=True)
    df["published_date"] = df["published_at"].dt.date.astype("string")
    df["published_month"] = df["published_at"].dt.to_period("M").astype("string")

    relevance_text = (
        df["title"].fillna("")
        + " "
        + df["categories_text"].fillna("")
        + " "
        + df["description"].fillna("")
    )

    df["track"] = relevance_text.map(infer_track)
    df = df[df["track"].notna()].copy()

    df["is_remote_or_hybrid"] = [
        infer_remote_flag(text=t, location=loc)
        for t, loc in zip(relevance_text.loc[df.index], df["primary_location"], strict=False)
    ]

    before_dedup = len(df)
    df = df[df["title"] != ""]
    df = df[df["url"] != ""]

    df["source_job_id"] = df["source_job_id"].astype("string")
    df = df.drop_duplicates(subset=["source", "source_job_id"], keep="first")
    df = df.drop_duplicates(subset=["title", "company", "primary_location"], keep="first")

    df = df.sort_values("published_at", ascending=False)

    keep_cols = [
        "source",
        "source_job_id",
        "title",
        "company",
        "track",
        "published_at",
        "published_date",
        "published_month",
        "primary_location",
        "country",
        "is_remote_or_hybrid",
        "categories_text",
        "levels_text",
        "tags_text",
        "url",
        "description",
    ]
    df = df[keep_cols].reset_index(drop=True)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    df.to_parquet(args.output_parquet, index=False)

    summary = {
        "raw_rows": len(raw_rows),
        "rows_after_relevance_filter": before_dedup,
        "rows_after_cleaning": len(df),
        "unique_companies": int(df["company"].nunique()),
        "date_min": str(df["published_at"].min()),
        "date_max": str(df["published_at"].max()),
        "tracks": df["track"].value_counts().to_dict(),
        "top_countries": df["country"].value_counts().head(15).to_dict(),
    }

    with args.summary.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("[done] cleaned_rows=", len(df))
    print("[done] csv=", args.output_csv)
    print("[done] parquet=", args.output_parquet)
    print("[done] summary=", args.summary)

    if len(df) < args.min_rows:
        raise RuntimeError(
            f"Cleaned dataset has {len(df)} rows, which is below required minimum {args.min_rows}."
        )


if __name__ == "__main__":
    main()
