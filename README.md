# Bonus Task Project: Data Science & IT Job Postings Dashboard

## Project Overview
This project was completed for the extra-credit task on labor market analytics.  
The goal was to collect, clean, and visualize at least 5,000 job postings in Data Science and IT.

The final solution includes:
- automated data collection from a public API;
- preprocessing and deduplication pipeline;
- interactive dashboard for exploratory analysis;
- reproducible codebase ready for GitHub and deployment.

## Data Source
The dataset is collected from the **The Muse Public Jobs API**:  
https://www.themuse.com/developers/api/v2

Jobs are requested from categories relevant to IT and DS:
- `Software Engineering`
- `Data and Analytics`
- `Science and Engineering`
- `Computer and IT`
- `Product Management`

## Methodology
The pipeline consists of two stages:
1. **Scraping**
   - Requests paginated vacancy data.
   - Saves raw records to JSONL format.
2. **Preprocessing**
   - Cleans HTML and normalizes text fields.
   - Removes duplicates (`source + job_id`, then `title + company + location`).
   - Filters only relevant Data Science / IT postings using keyword matching.
   - Builds analytical features (`track`, `country`, `remote/hybrid flag`, `publication month`).

## Final Dataset
The processed dataset satisfies the task requirement:
- **Raw collected postings:** 9,011
- **Cleaned postings:** 7,507
- **Minimum required:** 5,000

Track distribution:
- **IT:** 5,794
- **Data Science:** 1,713

## Dashboard Description
The dashboard is built with **Streamlit + Plotly** and provides:
- headline KPIs (postings, companies, countries, remote/hybrid share);
- distribution by track (IT vs Data Science);
- top countries by number of postings;
- monthly trend of publication activity;
- top hiring companies;
- interactive filtered table with vacancy examples.

Filters:
- track;
- country;
- publication date range.

## Repository Structure
- `scripts/scrape_themuse_jobs.py` — scraping script
- `scripts/preprocess_jobs.py` — cleaning and feature engineering
- `scripts/run_pipeline.sh` — full reproducible pipeline
- `dashboard/app.py` — dashboard application
- `data/raw/` — raw scraped data
- `data/processed/` — cleaned analytical dataset

## How to Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash scripts/run_pipeline.sh
streamlit run dashboard/app.py
```

