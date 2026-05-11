#!/usr/bin/env python3
"""Scrape Data Science and IT job postings from The Muse public API."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

API_URL = "https://www.themuse.com/api/public/jobs"
DEFAULT_CATEGORIES = [
    "Software Engineering",
    "Data and Analytics",
    "Science and Engineering",
    "Computer and IT",
    "Product Management",
]


@dataclass
class ScrapeStats:
    fetched_rows: int = 0
    unique_rows: int = 0
    pages_requested: int = 0
    pages_success: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/raw/themuse_jobs_raw.jsonl"),
        help="Output JSONL file",
    )
    parser.add_argument(
        "--max-pages-per-category",
        type=int,
        default=99,
        help="Maximum number of pages to fetch per category",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.25,
        help="Pause between successful requests",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=5,
        help="Retries for transient HTTP/network failures",
    )
    parser.add_argument(
        "--categories",
        type=str,
        default=",".join(DEFAULT_CATEGORIES),
        help="Comma-separated list of categories",
    )
    parser.add_argument(
        "--target-unique",
        type=int,
        default=9000,
        help="Stop early after this many unique jobs",
    )
    return parser.parse_args()


def normalize_job(raw: dict[str, Any], category_requested: str) -> dict[str, Any]:
    return {
        "source": "the_muse",
        "source_job_id": raw.get("id"),
        "title": raw.get("name"),
        "company": (raw.get("company") or {}).get("name"),
        "publication_date": raw.get("publication_date"),
        "locations": [x.get("name") for x in raw.get("locations", []) if x.get("name")],
        "categories": [x.get("name") for x in raw.get("categories", []) if x.get("name")],
        "levels": [x.get("name") for x in raw.get("levels", []) if x.get("name")],
        "tags": [x.get("name") for x in raw.get("tags", []) if x.get("name")],
        "url": (raw.get("refs") or {}).get("landing_page"),
        "description_html": raw.get("contents"),
        "api_category": category_requested,
    }


def fetch_page(
    session: requests.Session,
    category: str,
    page: int,
    max_retries: int,
) -> list[dict[str, Any]]:
    params = {"category": category, "page": page}

    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(API_URL, params=params, timeout=45)
        except requests.RequestException:
            sleep_for = min(2**attempt, 20)
            time.sleep(sleep_for)
            continue

        if resp.status_code == 200:
            payload = resp.json()
            return payload.get("results", [])

        # The API returns 400 for out-of-range pages.
        if resp.status_code == 400:
            return []

        # Handle rate limiting and temporary failures.
        if resp.status_code in (403, 429, 500, 502, 503, 504):
            print(
                f"  - retry category={category} page={page} status={resp.status_code} attempt={attempt}"
            )
            sleep_for = min(2**attempt, 30)
            time.sleep(sleep_for)
            continue

        # Unexpected status: treat as empty to keep pipeline resilient.
        print(
            f"  - unexpected category={category} page={page} status={resp.status_code}"
        )
        return []

    return []


def main() -> None:
    args = parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    categories = [x.strip() for x in args.categories.split(",") if x.strip()]
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
        }
    )

    stats = ScrapeStats()
    seen_ids: set[str] = set()

    with args.out.open("w", encoding="utf-8") as f:
        for category in categories:
            print(f"[collect] category={category}")
            for page in range(1, args.max_pages_per_category + 1):
                stats.pages_requested += 1
                jobs = fetch_page(session, category, page, args.max_retries)

                if not jobs:
                    print(f"  - stop at page={page} (empty or out of range)")
                    break

                stats.pages_success += 1
                stats.fetched_rows += len(jobs)

                for raw in jobs:
                    source_job_id = str(raw.get("id"))
                    if not source_job_id or source_job_id in seen_ids:
                        continue
                    seen_ids.add(source_job_id)

                    normalized = normalize_job(raw, category_requested=category)
                    f.write(json.dumps(normalized, ensure_ascii=False) + "\n")
                    stats.unique_rows += 1

                if stats.unique_rows >= args.target_unique:
                    print(f"[collect] reached target_unique={args.target_unique}")
                    break

                time.sleep(args.sleep_seconds)

            if stats.unique_rows >= args.target_unique:
                break

    print("[done] raw_rows=", stats.fetched_rows)
    print("[done] unique_rows=", stats.unique_rows)
    print("[done] pages_requested=", stats.pages_requested)
    print("[done] pages_success=", stats.pages_success)
    print("[done] output=", args.out)


if __name__ == "__main__":
    main()
