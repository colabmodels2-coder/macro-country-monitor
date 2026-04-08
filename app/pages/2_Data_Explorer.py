from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "master_dataset.csv"

st.set_page_config(page_title="Data Explorer", layout="wide")

st.title("Data Explorer")

st.info(
    "Filter the underlying dataset by country, indicator, source, and date range."
)

if not DATA_PATH.exists():
    st.error("master_dataset.csv not found")
    st.stop()

df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"], errors="coerce")

if df.empty:
    st.error("No data found in master_dataset.csv")
    st.stop()

# --- Clean date field ---
df = df.dropna(subset=["date"]).copy()

# --- Filter options ---
all_countries = sorted(df["country_name"].dropna().unique().tolist())
all_indicators = sorted(df["indicator_name"].dropna().unique().tolist())
all_sources = sorted(df["source"].dropna().unique().tolist())

min_date = df["date"].min().date()
max_date = df["date"].max().date()

# --- Filters ---
st.subheader("Filters")

f1, f2 = st.columns(2)

with f1:
    selected_countries = st.multiselect(
        "Filter countries",
        all_countries,
        default=all_countries
    )

with f2:
    selected_indicators = st.multiselect(
        "Filter indicators",
        all_indicators,
        default=all_indicators
    )

f3, f4 = st.columns(2)

with f3:
    selected_sources = st.multiselect(
        "Filter sources",
        all_sources,
        default=all_sources
    )

with f4:
    selected_dates = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

# --- Handle date range safely ---
if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date, end_date = min_date, max_date

# --- Apply filters ---
filtered_df = df[
    df["country_name"].isin(selected_countries) &
    df["indicator_name"].isin(selected_indicators) &
    df["source"].isin(selected_sources) &
    (df["date"].dt.date >= start_date) &
    (df["date"].dt.date <= end_date)
].copy()

filtered_df = filtered_df.sort_values(
    ["country_name", "indicator_name", "date"],
    ascending=[True, True, False]
)

# --- Summary row ---
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Filtered rows", len(filtered_df))

with c2:
    st.metric("Countries selected", len(selected_countries))

with c3:
    st.metric("Indicators selected", len(selected_indicators))

# --- Table ---
st.subheader("Filtered data")

display_df = filtered_df.copy()
display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")

st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- Download ---
csv_data = filtered_df.copy()
csv_data["date"] = csv_data["date"].dt.strftime("%Y-%m-%d")
csv_bytes = csv_data.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered data as CSV",
    data=csv_bytes,
    file_name="filtered_macro_data.csv",
    mime="text/csv"
)
