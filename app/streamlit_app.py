from pathlib import Path
import pandas as pd
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES_PATH = ROOT / "config" / "countries.yaml"
INDICATORS_PATH = ROOT / "config" / "indicators.yaml"
DATA_PATH = ROOT / "data" / "processed" / "master_dataset.csv"

st.set_page_config(page_title="Macro Country Monitor", layout="wide")


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


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


def latest_value_for_name(latest_df, indicator_name):
    temp = latest_df[latest_df["indicator_name"] == indicator_name]
    if temp.empty:
        return None, None
    row = temp.iloc[0]
    return row["value"], row["unit"]


# --- Load countries ---
if not COUNTRIES_PATH.exists():
    st.error("countries.yaml not found")
    st.stop()

country_config = load_yaml(COUNTRIES_PATH)
countries = country_config.get("countries", [])

if not countries:
    st.error("No countries found in countries.yaml")
    st.stop()

# --- Load indicators ---
if not INDICATORS_PATH.exists():
    st.error("indicators.yaml not found")
    st.stop()

indicator_config = load_yaml(INDICATORS_PATH)
indicators = indicator_config.get("indicators", [])

if not indicators:
    st.error("No indicators found in indicators.yaml")
    st.stop()

# --- Load data ---
if not DATA_PATH.exists():
    st.error("master_dataset.csv not found")
    st.stop()

df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# --- Sidebar: country selector ---
country_names = [country["display_name"] for country in countries]
selected_country_name = st.sidebar.selectbox("Select country", country_names)

selected_country = next(
    country for country in countries
    if country["display_name"] == selected_country_name
)

country_df = df[df["country_iso3"] == selected_country["iso3"]].copy()

st.title("Macro Country Monitor")

st.info(
    "Starter macro dashboard for five countries. "
    "This version uses a small repo-based dataset so the app structure is in place before live API automation."
)

if country_df.empty:
    st.warning("No data found for selected country.")
    st.stop()

latest_df = (
    country_df.sort_values("date")
    .groupby("indicator_code", as_index=False)
    .tail(1)
    .sort_values("indicator_name")
)

latest_date = country_df["date"].max()

# --- Sidebar: KPI selector ---
available_kpis = sorted(latest_df["indicator_name"].dropna().unique().tolist())

default_kpis = []
for name in ["CPI Inflation YoY", "Policy Rate", "Exchange Rate vs USD"]:
    if name in available_kpis:
        default_kpis.append(name)

selected_kpis = st.sidebar.multiselect(
    "Select up to 3 KPI indicators",
    options=available_kpis,
    default=default_kpis
)

selected_kpis = selected_kpis[:3]

# --- Header block ---
left, right = st.columns([2, 1])

with left:
    st.subheader(selected_country["display_name"])
    st.caption(f"ISO3: {selected_country['iso3']}")

with right:
    if pd.notna(latest_date):
        st.metric("Latest observation date", latest_date.strftime("%Y-%m-%d"))
    else:
        st.metric("Latest observation date", "N/A")

# --- KPI row ---
st.subheader("Key metrics")

if not selected_kpis:
    st.warning("Please select at least 1 KPI indicator in the sidebar.")
else:
    kpi_columns = st.columns(len(selected_kpis))

    for i, indicator_name in enumerate(selected_kpis):
        value, unit = latest_value_for_name(latest_df, indicator_name)
        with kpi_columns[i]:
            st.metric(
                label=indicator_name,
                value=format_value(value, unit) if value is not None else "N/A"
            )

# --- Chart section ---
st.subheader("Indicator chart")

available_indicators = sorted(country_df["indicator_name"].dropna().unique().tolist())
selected_indicator = st.selectbox("Select indicator", available_indicators)

chart_df = country_df[country_df["indicator_name"] == selected_indicator].copy()
chart_df = chart_df.sort_values("date")

if not chart_df.empty:
    st.line_chart(chart_df.set_index("date")["value"])
    source_list = sorted(chart_df["source"].dropna().unique().tolist())
    st.caption(f"Source(s): {', '.join(source_list)}")
else:
    st.warning("No data available for selected indicator.")

# --- Snapshot table ---
st.subheader("Latest snapshot")

display_latest = latest_df.copy()
display_latest["formatted_value"] = display_latest.apply(
    lambda row: format_value(row["value"], row["unit"]),
    axis=1
)
display_latest["date"] = display_latest["date"].dt.strftime("%Y-%m-%d")

st.dataframe(
    display_latest[["indicator_name", "formatted_value", "date", "source"]].rename(
        columns={
            "indicator_name": "Indicator",
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
    country_df.sort_values(["indicator_name", "date"], ascending=[True, False]),
    use_container_width=True,
    hide_index=True
)

st.caption("Next step: add a simple country notes panel on the main page.")
