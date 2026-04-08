from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "master_dataset.csv"

st.set_page_config(page_title="Compare Countries", layout="wide")


def format_value(value, unit):
    if pd.isna(value):
        return "N/A"

    if unit == "percent":
        return f"{value:.1f}%"
    elif unit == "percent_gdp":
        return f"{value:.1f}%"
    elif unit == "usd":
        return f"${value:,.0f}"
    elif unit == "local_currency_per_usd":
        return f"{value:,.2f}"
    elif unit == "persons":
        return f"{value:,.0f}"
    else:
        return f"{value:,.2f}"


st.title("Compare Countries")

st.info(
    "Compare the same indicator across all countries in the current universe."
)

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

if chart_df.empty:
    st.warning("No data available for the selected indicator.")
    st.stop()

# --- Latest data by country ---
latest_df = (
    chart_df.sort_values("date")
    .groupby("country_name", as_index=False)
    .tail(1)
    .sort_values("value", ascending=False)
    .reset_index(drop=True)
)

latest_df["formatted_value"] = latest_df.apply(
    lambda row: format_value(row["value"], row["unit"]),
    axis=1
)

latest_date = chart_df["date"].max()

# --- Summary row ---
left, right = st.columns([2, 1])

with left:
    st.subheader(selected_indicator)

with right:
    if pd.notna(latest_date):
        st.metric("Latest date in chart", latest_date.strftime("%Y-%m-%d"))
    else:
        st.metric("Latest date in chart", "N/A")

# --- Historical line chart ---
st.subheader("Historical comparison")

pivot_df = chart_df.pivot_table(
    index="date",
    columns="country_name",
    values="value"
).sort_index()

st.line_chart(pivot_df)

# --- Latest bar chart ---
st.subheader("Latest values")

bar_df = latest_df[["country_name", "value"]].copy()
bar_df = bar_df.set_index("country_name")

st.bar_chart(bar_df)

# --- Latest ranking table ---
st.subheader("Latest ranking")

display_df = latest_df.copy()
display_df["date"] = pd.to_datetime(display_df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
display_df.insert(0, "rank", range(1, len(display_df) + 1))

st.dataframe(
    display_df[["rank", "country_name", "formatted_value", "date", "source"]].rename(
        columns={
            "rank": "Rank",
            "country_name": "Country",
            "formatted_value": "Latest value",
            "date": "Date",
            "source": "Source",
        }
    ),
    use_container_width=True,
    hide_index=True
)

# --- Underlying data ---
st.subheader("Underlying data")
st.dataframe(
    chart_df.sort_values(["country_name", "date"], ascending=[True, False]),
    use_container_width=True,
    hide_index=True
)
