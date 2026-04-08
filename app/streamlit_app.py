from pathlib import Path
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES_PATH = ROOT / "config" / "countries.yaml"
INDICATORS_PATH = ROOT / "config" / "indicators.yaml"

st.set_page_config(page_title="Macro Country Monitor", layout="wide")


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


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

# --- Sidebar selector ---
country_names = [country["display_name"] for country in countries]
selected_country_name = st.sidebar.selectbox("Select country", country_names)

selected_country = next(
    country for country in countries
    if country["display_name"] == selected_country_name
)

# --- Main page ---
st.title("Macro Country Monitor")

st.subheader("Selected country")
st.write(f"**Name:** {selected_country['display_name']}")
st.write(f"**ISO3:** {selected_country['iso3']}")

st.subheader("Indicators in scope")
st.write(f"Total indicators: **{len(indicators)}**")

for indicator in indicators:
    st.write(
        f"- {indicator['name']} "
        f"({indicator['app_code']}) | "
        f"{indicator['preferred_source']} | "
        f"{indicator['frequency']}"
    )

st.write("")
st.write("Next step: show only the selected country's future data.")
