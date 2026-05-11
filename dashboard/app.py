#!/usr/bin/env python3
"""Streamlit dashboard for DS/IT job market analytics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_PATH = Path(__file__).resolve().parents[1] / "data/processed/jobs_clean.csv"

st.set_page_config(page_title="DS & IT Jobs Dashboard", layout="wide")
st.title("Data Science & IT Jobs Dashboard")
st.caption("Dataset: cleaned postings scraped from The Muse public API")

if not DATA_PATH.exists():
    st.error(f"Dataset not found: {DATA_PATH}")
    st.stop()


df = pd.read_csv(DATA_PATH)
df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
df = df[df["published_at"].notna()].copy()

min_date = df["published_at"].dt.date.min()
max_date = df["published_at"].dt.date.max()

st.sidebar.header("Filters")
tracks = sorted(df["track"].dropna().unique().tolist())
track_filter = st.sidebar.multiselect("Track", tracks, default=tracks)

countries = sorted(df["country"].fillna("Unknown").unique().tolist())
country_filter = st.sidebar.multiselect("Country", countries, default=countries[:25] if len(countries) > 25 else countries)

date_filter = st.sidebar.date_input("Publication date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

if isinstance(date_filter, tuple) and len(date_filter) == 2:
    start_date, end_date = date_filter
else:
    start_date, end_date = min_date, max_date

f = df[
    (df["track"].isin(track_filter))
    & (df["country"].isin(country_filter))
    & (df["published_at"].dt.date >= start_date)
    & (df["published_at"].dt.date <= end_date)
].copy()

if f.empty:
    st.warning("No data for selected filters")
    st.stop()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Postings", f"{len(f):,}")
kpi2.metric("Unique companies", f"{f['company'].nunique():,}")
kpi3.metric("Countries", f"{f['country'].nunique():,}")
kpi4.metric("Remote/Hybrid %", f"{(f['is_remote_or_hybrid'].mean() * 100):.1f}%")

left, right = st.columns(2)

with left:
    by_track = f["track"].value_counts().reset_index()
    by_track.columns = ["track", "count"]
    fig_track = px.bar(by_track, x="track", y="count", title="Postings by Track", color="track")
    st.plotly_chart(fig_track, use_container_width=True)

with right:
    by_country = f["country"].value_counts().head(15).reset_index()
    by_country.columns = ["country", "count"]
    fig_country = px.bar(by_country, x="count", y="country", orientation="h", title="Top 15 Countries")
    fig_country.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_country, use_container_width=True)

m1, m2 = st.columns(2)

with m1:
    monthly = (
        f.assign(month=f["published_at"].dt.to_period("M").astype(str))
        .groupby(["month", "track"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("month")
    )
    fig_month = px.line(monthly, x="month", y="count", color="track", markers=True, title="Monthly Trend")
    st.plotly_chart(fig_month, use_container_width=True)

with m2:
    top_companies = f["company"].fillna("Unknown").value_counts().head(15).reset_index()
    top_companies.columns = ["company", "count"]
    fig_comp = px.bar(top_companies, x="count", y="company", orientation="h", title="Top 15 Hiring Companies")
    fig_comp.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_comp, use_container_width=True)

st.subheader("Sample rows")
st.dataframe(
    f[
        [
            "published_date",
            "track",
            "title",
            "company",
            "primary_location",
            "country",
            "is_remote_or_hybrid",
            "url",
        ]
    ].head(200),
    use_container_width=True,
)
