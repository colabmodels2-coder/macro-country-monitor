from pathlib import Path
import pandas as pd
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES_PATH = ROOT / "config" / "countries.yaml"
INDICATORS_PATH = ROOT / "config" / "indicators.yaml"
COUNTRY_NOTES_PATH = ROOT / "config" / "country_notes.yaml"
DATA_PATH = ROOT / "data" / "processed" / "master_dataset.csv"

st.set_page_config(page_title="Macro Country Monitor", layout="wide")


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def format_value(value, unit):
    if value is None or pd.isna(value):
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


def latest_and_previous_for_name(country_df, indicator_name):
    temp = country_df[country_df["indicator_name"] == indicator_name].copy()
    temp = temp.sort_values("date")

    if temp.empty:
        return None, None, None

    latest_row = temp.iloc[-1]
    latest_value = latest_row["value"]
    unit = latest_row["unit"]

    if len(temp) >= 2:
        previous_value = temp.iloc[-2]["value"]
    else:
        previous_value = None

    return latest_value, previous_value, unit


def direction_label(latest_value, previous_value):
    if previous_value is None or pd.isna(previous_value):
        return "N/A"

    if latest_value > previous_value:
        return "Up"
    elif latest_value < previous_value:
        return "Down"
    else:
        return "Flat"


def status_label(indicator_name, latest_value, previous_value):
    if previous_value is None or pd.isna(previous_value):
        return "N/A"

    if indicator_name == "CPI Inflation YoY":
        if latest_value < previous_value:
            return "Cooling"
        elif latest_value > previous_value:
            return "Heating"
        else:
            return "Stable"

    if indicator_name == "Policy Rate":
        if latest_value < previous_value:
            return "Easing"
        elif latest_value > previous_value:
            return "Tightening"
        else:
            return "Flat"

    if indicator_name == "Exchange Rate vs USD":
        if latest_value < previous_value:
            return "Stronger"
        elif latest_value > previous_value:
            return "Weaker"
        else:
            return "Flat"

    if latest_value > previous_value:
        return "Rising"
    elif latest_value < previous_value:
        return "Falling"
    else:
        return "Stable"


def source_type_label(source):
    if source == "WorldBank":
        return "Real"
    return "Manual"


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

# --- Load country notes ---
country_notes = {}
if COUNTRY_NOTES_PATH.exists():
    notes_config = load_yaml(COUNTRY_NOTES_PATH)
    country_notes = notes_config.get("country_notes", {})

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
    "This version now combines real World Bank data with manual placeholders for indicators not yet automated."
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

# --- Country notes panel ---
country_note = country_notes.get(selected_country["iso3"], {})

st.subheader("Country note")

if country_note:
    st.write(country_note.get("summary", "No summary available."))

    watch_items = country_note.get("watch_items", [])
    if watch_items:
        st.write("**Watch items**")
        for item in watch_items:
            st.write(f"- {item}")
else:
    st.caption("No country note found yet for this country.")

# --- Data status panel ---
st.subheader("Data status")

status_df = latest_df.copy()
status_df["Source type"] = status_df["source"].apply(source_type_label)
status_df["Latest date"] = pd.to_datetime(status_df["date"], errors="coerce").dt.strftime("%Y-%m-%d")

real_count = (status_df["Source type"] == "Real").sum()
manual_count = (status_df["Source type"] == "Manual").sum()

d1, d2, d3 = st.columns(3)

with d1:
    st.metric("Real indicators", int(real_count))

with d2:
    st.metric("Manual indicators", int(manual_count))

with d3:
    if pd.notna(latest_date):
        st.metric("Max date in country data", latest_date.strftime("%Y-%m-%d"))
    else:
        st.metric("Max date in country data", "N/A")

st.dataframe(
    status_df[["indicator_name", "Source type", "source", "Latest date"]].rename(
        columns={
            "indicator_name": "Indicator",
            "source": "Source",
        }
    ),
    use_container_width=True,
    hide_index=True
)

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

# --- Country scorecard ---
st.subheader("Country scorecard")

scorecard_rows = []

for indicator_name in selected_kpis:
    latest_value, previous_value, unit = latest_and_previous_for_name(country_df, indicator_name)

    scorecard_rows.append({
        "Indicator": indicator_name,
        "Latest": format_value(latest_value, unit) if latest_value is not None else "N/A",
        "Previous": format_value(previous_value, unit) if previous_value is not None else "N/A",
        "Direction": direction_label(latest_value, previous_value) if latest_value is not None else "N/A",
        "Status": status_label(indicator_name, latest_value, previous_value) if latest_value is not None else "N/A"
    })

if scorecard_rows:
    scorecard_df = pd.DataFrame(scorecard_rows)
    st.dataframe(scorecard_df, use_container_width=True, hide_index=True)
    st.caption(
        "Direction compares the latest observation with the immediately previous observation. "
        "Status adds a simple macro interpretation."
    )
else:
    st.caption("No KPI scorecard available yet.")

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

st.caption("Next step: replace manual policy rate / FX / reserves with IMF data.")
