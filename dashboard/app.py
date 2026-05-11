from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_PATH = Path(__file__).resolve().parents[1] / "data/processed/jobs_clean.csv"

TRACK_COLORS = {
    "IT": "#B5179E",
    "Data Science": "#FF4FA3",
}

COUNTRY_SCALE = [
    "#FFE5F3",
    "#FFC2E2",
    "#FF9ED3",
    "#FF6DBB",
    "#D6339A",
]

US_STATE_NAMES = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
}

COUNTRY_NAME_FIXES = {
    "UK": "United Kingdom",
    "UAE": "United Arab Emirates",
    "Korea, Republic of": "South Korea",
    "Viet Nam": "Vietnam",
}

st.set_page_config(page_title="DS & IT Jobs Dashboard", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Manrope:wght@400;600;700&display=swap');

    .stApp {
        background:
            radial-gradient(circle at 10% 10%, #ffd6ea 0%, rgba(255,214,234,0) 38%),
            radial-gradient(circle at 90% 8%, #f4d9ff 0%, rgba(244,217,255,0) 35%),
            linear-gradient(140deg, #fff7fb 0%, #fff0f7 48%, #fdf5ff 100%);
    }

    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.02em;
    }

    p, div, label, span {
        font-family: 'Manrope', sans-serif !important;
    }

    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid rgba(25, 25, 25, 0.08);
        border-radius: 14px;
        padding: 14px;
        box-shadow: 0 8px 24px rgba(17, 24, 39, 0.08);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f7fafc 100%);
        border-right: 1px solid rgba(0, 0, 0, 0.08);
    }

    .hero {
        background: linear-gradient(120deg, rgba(255,79,163,0.18) 0%, rgba(181,23,158,0.18) 100%);
        border: 1px solid rgba(0,0,0,0.09);
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 12px;
    }

    .hero h2 {
        margin: 0 0 6px 0;
        font-size: 1.6rem;
    }

    .hero p {
        margin: 0;
        color: #334155;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h2>Data Science & IT Jobs Dashboard</h2>
        <p>Interactive analysis of cleaned job postings with advanced filters and multi-view visual analytics.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_data(path: Path) -> pd.DataFrame:
    df_ = pd.read_csv(path)
    df_["published_at"] = pd.to_datetime(df_["published_at"], errors="coerce", utc=True)
    df_ = df_[df_["published_at"].notna()].copy()
    df_["work_mode"] = df_["is_remote_or_hybrid"].map({True: "Remote/Hybrid", False: "On-site"})
    df_["month"] = df_["published_at"].dt.to_period("M").astype(str)
    df_["level"] = df_["levels_text"].fillna("Unknown").replace("", "Unknown")
    df_["display_country"] = [
        normalize_country_label(country=c, primary_location=loc, work_mode=mode)
        for c, loc, mode in zip(
            df_["country"].fillna("Unknown"),
            df_["primary_location"].fillna("Unknown"),
            df_["work_mode"].fillna("On-site"),
            strict=False,
        )
    ]
    return df_


def normalize_country_label(country: str, primary_location: str, work_mode: str) -> str:
    c = str(country or "").strip()
    loc = str(primary_location or "").strip()
    mode = str(work_mode or "").strip()

    if c in US_STATE_NAMES:
        return f"United States ({US_STATE_NAMES[c]})"

    if c in COUNTRY_NAME_FIXES:
        return COUNTRY_NAME_FIXES[c]

    if c in {"Flexible / Remote", "Remote"}:
        return "Remote (Flexible)"

    if c in {"Unknown", ""}:
        if mode == "Remote/Hybrid":
            return "Remote (Location not specified)"
        return "Location not specified"

    if c == "United States of America":
        return "United States"

    if c == "US":
        return "United States"

    if c == "CA" and ", CA" in loc:
        return "United States (California)"

    return c


if not DATA_PATH.exists():
    st.error(f"Dataset not found: {DATA_PATH}")
    st.stop()

df = load_data(DATA_PATH)

min_date = df["published_at"].dt.date.min()
max_date = df["published_at"].dt.date.max()

st.sidebar.header("Filters")
tracks = sorted(df["track"].dropna().unique().tolist())
track_filter = st.sidebar.multiselect("Track", tracks, default=tracks)

countries = sorted(df["display_country"].fillna("Location not specified").unique().tolist())
country_filter = st.sidebar.multiselect("Country", countries, default=countries)

date_filter = st.sidebar.date_input(
    "Publication date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_filter, tuple) and len(date_filter) == 2:
    start_date, end_date = date_filter
else:
    start_date, end_date = min_date, max_date

f = df[
    (df["track"].isin(track_filter))
    & (df["display_country"].isin(country_filter))
    & (df["published_at"].dt.date >= start_date)
    & (df["published_at"].dt.date <= end_date)
].copy()

if f.empty:
    st.warning("No data for selected filters")
    st.stop()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Postings", f"{len(f):,}")
kpi2.metric("Unique companies", f"{f['company'].nunique():,}")
kpi3.metric("Countries", f"{f['display_country'].nunique():,}")
kpi4.metric("Remote/Hybrid %", f"{(f['is_remote_or_hybrid'].mean() * 100):.1f}%")

row1_left, row1_right = st.columns(2)

with row1_left:
    by_track = f["track"].value_counts().reset_index()
    by_track.columns = ["track", "count"]
    fig_track = px.bar(
        by_track,
        x="track",
        y="count",
        color="track",
        color_discrete_map=TRACK_COLORS,
        title="Postings by Track",
        text_auto=True,
    )
    fig_track.update_layout(plot_bgcolor="rgba(255,255,255,0.86)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_track, use_container_width=True)

with row1_right:
    fig_donut = px.pie(
        by_track,
        names="track",
        values="count",
        hole=0.52,
        color="track",
        color_discrete_map=TRACK_COLORS,
        title="Track Share",
    )
    fig_donut.update_traces(textposition="inside", textinfo="percent+label")
    fig_donut.update_layout(plot_bgcolor="rgba(255,255,255,0.86)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_donut, use_container_width=True)

row2_left, row2_right = st.columns(2)

with row2_left:
    by_country = f["display_country"].value_counts().head(20).reset_index()
    by_country.columns = ["location", "count"]
    fig_country = px.bar(
        by_country,
        x="count",
        y="location",
        orientation="h",
        color="count",
        color_continuous_scale=COUNTRY_SCALE,
        title="Top 20 Locations",
        text_auto=True,
    )
    fig_country.update_layout(
        yaxis={"categoryorder": "total ascending"},
        plot_bgcolor="rgba(255,255,255,0.86)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig_country.update_coloraxes(showscale=False)
    st.plotly_chart(fig_country, use_container_width=True)

with row2_right:
    by_mode = (
        f.groupby(["track", "work_mode"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )
    fig_mode = px.bar(
        by_mode,
        x="track",
        y="count",
        color="work_mode",
        barmode="group",
        color_discrete_map={"Remote/Hybrid": "#FF4FA3", "On-site": "#9D4EDD"},
        title="Remote/Hybrid vs On-site by Track",
        text_auto=True,
    )
    fig_mode.update_layout(plot_bgcolor="rgba(255,255,255,0.86)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_mode, use_container_width=True)

row3_left, row3_right = st.columns(2)

with row3_left:
    monthly = (
        f.groupby(["month", "track"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("month")
    )
    fig_month = px.area(
        monthly,
        x="month",
        y="count",
        color="track",
        color_discrete_map=TRACK_COLORS,
        title="Monthly Hiring Trend",
    )
    fig_month.update_layout(plot_bgcolor="rgba(255,255,255,0.86)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_month, use_container_width=True)

with row3_right:
    top_companies = f["company"].fillna("Unknown").value_counts().head(15).reset_index()
    top_companies.columns = ["company", "count"]
    fig_companies = px.treemap(
        top_companies,
        path=["company"],
        values="count",
        color="count",
        color_continuous_scale="RdPu",
        title="Top Hiring Companies (Treemap)",
    )
    fig_companies.update_layout(plot_bgcolor="rgba(255,255,255,0.86)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_companies, use_container_width=True)

st.subheader("Sample Postings")
st.dataframe(
    f[
        [
            "published_date",
            "track",
            "title",
            "company",
            "level",
            "primary_location",
            "display_country",
            "work_mode",
            "url",
        ]
    ].head(250),
    use_container_width=True,
)
