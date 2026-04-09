from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

RAW_WB_PATH = ROOT / "data" / "raw" / "world_bank" / "world_bank_real.csv"
MASTER_PATH = ROOT / "data" / "processed" / "master_dataset.csv"

KEEP_MANUAL_CODES = ["POLICY_RATE", "FX_USD", "FX_RESERVES"]


def main():
    if not MASTER_PATH.exists():
        raise FileNotFoundError(f"master_dataset.csv not found at {MASTER_PATH}")

    if not RAW_WB_PATH.exists():
        raise FileNotFoundError(f"world_bank_real.csv not found at {RAW_WB_PATH}")

    master_df = pd.read_csv(MASTER_PATH)
    wb_df = pd.read_csv(RAW_WB_PATH)

    # Keep only the manual indicators that World Bank does not currently replace
    manual_keep_df = master_df[master_df["indicator_code"].isin(KEEP_MANUAL_CODES)].copy()

    # Keep only the columns used by the app
    needed_columns = [
        "country_iso3",
        "country_name",
        "indicator_code",
        "indicator_name",
        "date",
        "value",
        "source",
        "unit",
    ]

    manual_keep_df = manual_keep_df[needed_columns]
    wb_df = wb_df[needed_columns]

    combined_df = pd.concat([manual_keep_df, wb_df], ignore_index=True)

    combined_df["date"] = pd.to_datetime(combined_df["date"], errors="coerce")
    combined_df["value"] = pd.to_numeric(combined_df["value"], errors="coerce")

    combined_df = combined_df.dropna(subset=["date", "value"])
    combined_df = combined_df.sort_values(
        ["country_iso3", "indicator_code", "date"]
    ).reset_index(drop=True)

    combined_df.to_csv(MASTER_PATH, index=False)

    print(f"Saved rebuilt master dataset to {MASTER_PATH}")
    print(f"Rows in combined dataset: {len(combined_df)}")


if __name__ == "__main__":
    main()
