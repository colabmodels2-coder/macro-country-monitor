from pathlib import Path
from datetime import datetime
import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

COUNTRY_PATH = "egy;rou;civ;nga;gha"

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
        "indicator_code": "GOV_DEBT_GDP",
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

BASE_URL = "https://api.worldbank.org/v2/country/{country_codes}/indicator/{indicator_code}"


def build_session():
    session = requests.Session()

    retry = Retry(
        total=3,
        read=3,
        connect=3,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


def fetch_indicator_for_all_countries(session, indicator):
    url = BASE_URL.format(
        country_codes=COUNTRY_PATH,
        indicator_code=indicator["world_bank_code"]
    )

    params = {
        "format": "json",
        "per_page": 20000,
        "source": 2
    }

    response = session.get(url, params=params, timeout=(20, 120))
    print(f"Request URL: {response.url}")
    print(f"Status code: {response.status_code}")

    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError(f"Unexpected payload for {indicator['indicator_code']}")

    rows = payload[1]
    if rows is None:
        print(f"No rows returned for {indicator['indicator_code']}")
        return []

    output = []

    for row in rows:
        value = row.get("value")
        year = row.get("date")
        country_iso3 = row.get("countryiso3code")

        if value is None or year is None or country_iso3 is None:
            continue

        if country_iso3 not in COUNTRIES:
            continue

        # Skip non-year rows if they ever appear
        if not str(year).isdigit():
            continue

        output.append({
            "country_iso3": country_iso3,
            "country_name": COUNTRIES[country_iso3],
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

    print(f"Rows kept for {indicator['indicator_code']}: {len(output)}")
    return output


def main():
    session = build_session()
    all_rows = []

    for indicator in INDICATORS:
        rows = fetch_indicator_for_all_countries(session, indicator)
        all_rows.extend(rows)

    if not all_rows:
        raise RuntimeError("World Bank fetch returned zero rows.")

    df = pd.DataFrame(all_rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "value"])
    df = df.sort_values(["country_iso3", "indicator_code", "date"]).reset_index(drop=True)

    df.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(df)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
