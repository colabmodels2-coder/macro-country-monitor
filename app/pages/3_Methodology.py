from pathlib import Path
import streamlit as st
import yaml
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
IMF_TARGETS_PATH = ROOT / "config" / "imf_targets.yaml"

st.set_page_config(page_title="Methodology", layout="wide")

st.title("Methodology")

st.info(
    "This page documents how the app is currently built, which data are already live, "
    "and which IMF indicators are still being prepared for automation."
)

st.subheader("Current build state")

st.write("- World Bank indicators: live")
st.write("- IMF monitoring indicators: still partly manual")
st.write("- App structure: dashboard, compare page, data explorer, methodology")

st.subheader("Why IMF is the next source")

st.write(
    "The remaining manual indicators are policy rate, FX vs USD, and FX reserves. "
    "These are the next automation targets."
)

if not IMF_TARGETS_PATH.exists():
    st.warning("imf_targets.yaml not found")
    st.stop()

with open(IMF_TARGETS_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

targets = config.get("imf_targets", [])

if not targets:
    st.warning("No IMF targets found")
    st.stop()

targets_df = pd.DataFrame(targets)

st.subheader("IMF automation targets")
st.dataframe(targets_df, use_container_width=True, hide_index=True)

st.caption(
    "Next step: replace the manual IMF-style indicators with live IMF data starting from this target list."
)
