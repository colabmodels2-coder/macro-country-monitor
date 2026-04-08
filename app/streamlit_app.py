from pathlib import Path
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES_PATH = ROOT / "config" / "countries.yaml"

st.set_page_config(page_title="Macro Country Monitor", layout="wide")

st.title("Macro Country Monitor")
st.subheader("Country universe")

if not COUNTRIES_PATH.exists():
    st.error("countries.yaml not found")
    st.stop()

with open(COUNTRIES_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

countries = config.get("countries", [])

if not countries:
    st.warning("No countries found in config")
    st.stop()

for country in countries:
    st.write(f"- {country['display_name']} ({country['iso3']})")

st.write("")
st.write("Next step: add the indicator configuration.")
