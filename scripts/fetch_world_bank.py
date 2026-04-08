from pathlib import Path_code": "GOV_DEBT_GDP",
        "indicator_name": "Central Government Debt (% GDP)",
        "unit": "percent_gdp",
    },
    {
        "world_bank_code": "BN.CAB.XOKA.GD.ZS",
        "indicator_code": "CURRENT_ACCOUNT_GDP",
        "indicator_name": "Current Account Balance (% GDP)",
        "unit": "percent_gdp",
    },
    {
        "world_bank_code": "SP.POP.TOTL",
        "indicator_code": "POPULATION",
        "indicator_name": "Population",
        "unit": "persons",
    },
]

BASE_URL = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"


def fetch_series(country_iso3, country_name, indicator):
    url = BASE_URL.format(
        country=country_iso3,
        indicator=indicator["world_bank_code"]
    )
    params = {
        "format": "json",
        "per_page": 20000
    }

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        return []

    rows = payload[1]
    output = []

    for row in rows:
        value = row.get("value")
        year = row.get("date")

        if value is None or year is None:
            continue

        output.append({
            "country_iso3": country_iso3,
            "country_name": country_name,
            "indicator_code": indicator["indicator_code"],
            "indicator_name": indicator["indicator_name"],
            "date": f"{year}-12-31",
            "value": value,
            "source": "WorldBank",
            "unit": indicator["unit"],
            "dataset": "WDI",
            "frequency": "A",
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
        })

    return output


def main():
    all_rows = []

    for country_iso3, country_name in COUNTRIES.items():
        for indicator in INDICATORS:
            try:
                rows = fetch_series(country_iso3, country_name, indicator)
                all_rows.extend(rows)
                print(f"Fetched {country_iso3} - {indicator['indicator_code']} ({len(rows)} rows)")
            except Exception as e:
                print(f"Failed {country_iso3} - {indicator['indicator_code']}: {e}")

    df = pd.DataFrame(all_rows)

    if df.empty:
        print("No rows fetched.")
        df = pd.DataFrame(columns=[
            "country_iso3",
            "country_name",
            "indicator_code",
            "indicator_name",
            "date",
            "value",
            "source",
            "unit",
            "dataset",
            "frequency",
            "last_updated",
        ])
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values(["country_iso3", "indicator_code", "date"]).reset_index(drop=True)

    df.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(df)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
``
from datetime import datetime
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "data" / "raw" / "world_bank" / "world_bank_real.csv"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

COUNTRIES = {
    "EGY": "Egypt",
    "ROU": "Romania",
    "CIV": "Ivory Coast",
    "NGA": "Nigeria",
    "GHA": "Ghana",
}

INDICATORS = [
    {
        "world_bank_code": "NY.GDP.PCAP.CD",
        "indicator_code": "GDP_PER_CAPITA_USD",
        "indicator_name": "GDP per Capita (Current US$)",
        "unit": "usd",
    },
    {
        "world_bank_code": "FP.CPI.TOTL.ZG",
        "indicator_code": "CPI_YOY",
        "indicator_name": "CPI Inflation YoY",
        "unit": "percent",
    },
    {
        "world_bank_code": "SL.UEM.TOTL.ZS",
        "indicator_code": "UNEMPLOYMENT_RATE",
        "indicator_name": "Unemployment Rate",
        "unit": "percent",
    },
    {
        "world_bank_code": "NE.RSB.GNFS.ZS",
        "indicator_code": "EXPORTS_PCT_GDP",
        "indicator_name": "Exports of Goods and Services (% GDP)",
        "unit": "percent_gdp",
    },
    {
        "world_bank_code": "NE.IMP.GNFS.ZS",
        "indicator_code": "IMPORTS_PCT_GDP",
        "indicator_name": "Imports of Goods and Services (% GDP)",
        "unit": "percent_gdp",
    },
    {
        "world_bank_code": "GC.DOD.TOTL.GD.ZS",
