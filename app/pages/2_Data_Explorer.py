from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "master_dataset.csv"

st.set_page_config(page_title="Data Explorer", layout="wide")

st.title("Data Explorer")

if not DATA_PATH.exists():
    st.error("master_dataset.csv not found")
    st.stop()

df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"], errors="coerce")

if df.empty:
    st.error("No data found in master_dataset.csv")
    st.stop()

# --- Filters ---
all_countries = sorted(df["country_name"].dropna().unique().tolist())
all_indicators = sorted(df["indicator_name"].dropna().unique().tolist())

selected_countries = st.multiselect(
    "Filter countries",
    all_countries,
    default=all_countries
)

selected_indicators = st.multiselect(
    "Filter indicators",
    all_indicators,
    default=all_indicators
)

filtered_df = df[
    df["country_name"].isin(selected_countries) &
    df["indicator_name"].isin(selected_indicators)
].copy()

filtered_df = filtered_df.sort_values(
    ["country_name", "indicator_name", "date"],
    ascending=[True, True, False]
)

st.subheader("Filtered data")
st.dataframe(filtered_df, use_container_width=True)

csv_data = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered data as CSV",
    data=csv_data,
    file_name="filtered_macro_data.csv",
    mime="text/csv"
)
