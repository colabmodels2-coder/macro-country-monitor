from pathlib import Path
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES_PATH = ROOT / "config" / "countries.yaml"
INDICATORS_PATH = ROOT / "config" / "indicators.yaml"

st.set_page_config(page_title="Macro Country Monitor", layout="wide")

st.title("Macro Country Monitor")

# --- Countries ---
st.subheader("Country universe")

if not COUNTRIES_PATH.exists():
    st.error("countries.yaml not found")
    st.stop()

with open(COUNTRIES_PATH, "r", encoding="utf-8") as f:
    country_config = yaml.safe_load(f)

countries = country_config.get("countries", [])

if not countries:
    st.warning("No countries found in config")
    st.stop()

for country in countries:
    st.write(f"- {country['display_name']} ({country['iso3']})")

# --- Indicators ---
st.subheader("Indicator universe")

if not INDICATORS_PATH.exists():
    st.error("indicators.yaml not found")
    st.stop()

with open(INDICATORS_PATH, "r", encoding="utf-8") as f:
    indicator_config = yaml.safe_load(f)

indicators = indicator_config.get("indicators", [])

if not indicators:
    st.warning("No indicators found in config")
    st.stop()

for indicator in indicators:
    st.write(
        f"- {indicator['name']} | "
        f"Code: {indicator['app_code']} | "
        f"Source: {indicator['preferred_source']} | "
        f"Frequency: {indicator['frequency']}"
    )

st.write("")
st.write("Next step: add a country selector in the sidebar.")
