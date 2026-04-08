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


def latest_value_for_code(latest_df, code):
    temp = latest_df[latest_df["indicator_code"] == code]
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

# --- Sidebar country selector ---
country_names = [country["display_name"] for country in countries]
selected_country_name = st.sidebar.selectbox("Select country", country_names)

selected_country = next(
    country for country in countries
    if country["display_name"] == selected_country_name
)

country_df = df[df["country_iso3"] == selected_country["iso3"]].copy()

st.title("Macro Country Monitor")

st.subheader("Selected country")
st.write(f"**Name:** {selected_country['display_name']}")
st.write(f"**ISO3:** {selected_country['iso3']}")

if country_df.empty:
    st.warning("No data found for selected country.")
    st.stop()

# --- Latest snapshot ---
latest_df = (
    country_df.sort_values("date")
    .groupby("indicator_code", as_index=False)
    .tail(1)
    .sort_values("indicator_name")
)

st.subheader("Key metrics")

c1, c2, c3 = st.columns(3)

cpi_value, cpi_unit = latest_value_for_code(latest_df, "CPI_YOY")
policy_value, policy_unit = latest_value_for_code(latest_df, "POLICY_RATE")
fx_value, fx_unit = latest_value_for_code(latest_df, "FX_USD")

with c1:
    st.metric(
        label="CPI Inflation YoY",
        value=format_value(cpi_value, cpi_unit) if cpi_value is not None else "N/A"
    )

with c2:
    st.metric(
        label="Policy Rate",
        value=format_value(policy_value, policy_unit) if policy_value is not None else "N/A"
    )

with c3:
    st.metric(
        label="FX vs USD",
        value=format_value(fx_value, fx_unit) if fx_value is not None else "N/A"
    )

st.subheader("Latest snapshot table")
st.dataframe(
    latest_df[["indicator_name", "value", "unit", "date", "source"]],
    use_container_width=True
)

# --- Indicator selector ---
available_indicators = country_df["indicator_name"].dropna().unique().tolist()
selected_indicator = st.selectbox("Select indicator to chart", available_indicators)

chart_df = country_df[country_df["indicator_name"] == selected_indicator].copy()
chart_df = chart_df.sort_values("date")

st.subheader("Chart")
st.line_chart(
    chart_df.set_index("date")["value"]
)

st.subheader("Underlying data")
st.dataframe(
    country_df.sort_values(["indicator_name", "date"], ascending=[True, False]),
    use_container_width=True
)

st.write("")
st.write("Next step: add a second page to compare countries.")
