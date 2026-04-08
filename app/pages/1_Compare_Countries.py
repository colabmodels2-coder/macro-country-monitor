from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "master_dataset.csv"

st.set_page_config(page_title="Compare Countries", layout="wide")

st.title("Compare Countries")

if not DATA_PATH.exists():
    st.error("master_dataset.csv not found")
    st.stop()

df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"], errors="coerce")

if df.empty:
    st.error("No data found in master_dataset.csv")
    st.stop()

available_indicators = sorted(df["indicator_name"].dropna().unique().tolist())

selected_indicator = st.selectbox(
    "Select indicator",
    available_indicators
)

chart_df = df[df["indicator_name"] == selected_indicator].copy()
chart_df = chart_df.sort_values(["country_name", "date"])

st.subheader("Chart")

pivot_df = chart_df.pivot_table(
    index="date",
    columns="country_name",
    values="value"
)

st.line_chart(pivot_df)

st.subheader("Latest ranking")

latest_df = (
    chart_df.sort_values("date")
    .groupby("country_name", as_index=False)
    .tail(1)
    .sort_values("value", ascending=False)
    .reset_index(drop=True)
)

st.dataframe(
    latest_df[["country_name", "indicator_name", "value", "unit", "date"]],
    use_container_width=True
)

st.subheader("Underlying data")
st.dataframe(
    chart_df.sort_values(["country_name", "date"], ascending=[True, False]),
    use_container_width=True
)
