import json
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# INPUT FILES
# ============================================================

OBSERVED = Path(
    "data/raw/rainfall/observed/wayanad/"
    "wayanad_daily_rainfall_2015_2025.json"
)

ACCUMULATED = Path(
    "data/raw/rainfall/accumulated/wayanad/"
    "wayanad_rainfall_accumulated_2015_2025.csv"
)

FORECAST = Path(
    "data/raw/rainfall/forecast/wayanad/"
    "wayanad_rainfall_forecast_7day.json"
)


# ============================================================
# OUTPUT FILES
# ============================================================

OUTPUT_DIR = Path(
    "data/processed/features"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

HISTORICAL_OUTPUT = (
    OUTPUT_DIR /
    "wayanad_historical_rainfall_features.parquet"
)

FORECAST_OUTPUT = (
    OUTPUT_DIR /
    "wayanad_forecast_rainfall_features.parquet"
)

COMBINED_OUTPUT = (
    OUTPUT_DIR /
    "wayanad_dynamic_rainfall_features.parquet"
)


# ============================================================
# FILE CHECK
# ============================================================

print("\n=== FILE CHECK ===")

for path in [
    OBSERVED,
    ACCUMULATED,
    FORECAST
]:

    if not path.exists():

        raise FileNotFoundError(
            f"File not found: {path}"
        )

    print(
        "FOUND:",
        path
    )


# ============================================================
# 1. LOAD OBSERVED RAINFALL
# ============================================================

print(
    "\n=== LOADING OBSERVED RAINFALL ==="
)

with open(
    OBSERVED,
    "r",
    encoding="utf-8"
) as f:

    observed_json = json.load(f)


daily = observed_json["daily"]

print(
    "Observed keys:"
)

for key in daily.keys():

    print(
        "-",
        key
    )


# ------------------------------------------------------------
# Open-Meteo daily data normally contains:
#
# time
# precipitation_sum
#
# We explicitly check instead of assuming.
# ------------------------------------------------------------

if "time" not in daily:

    raise ValueError(
        "Observed rainfall JSON does not contain daily time."
    )

if "precipitation_sum" not in daily:

    raise ValueError(
        "Observed rainfall JSON does not contain "
        "daily precipitation_sum."
    )


observed_df = pd.DataFrame(
    {
        "date":
            daily["time"],

        "observed_rainfall_mm":
            daily["precipitation_sum"],
    }
)


observed_df["date"] = pd.to_datetime(
    observed_df["date"]
)


# ============================================================
# 2. LOAD ACCUMULATED RAINFALL
# ============================================================

print(
    "\n=== LOADING ACCUMULATED RAINFALL ==="
)

accumulated_df = pd.read_csv(
    ACCUMULATED
)


accumulated_df["date"] = pd.to_datetime(
    accumulated_df["date"]
)


required_columns = [

    "date",

    "rainfall_mm",

    "rainfall_24h_mm",

    "rainfall_72h_mm",

    "rainfall_7day_mm",
]


for column in required_columns:

    if column not in accumulated_df.columns:

        raise ValueError(
            f"Missing required column: {column}"
        )


# ============================================================
# 3. MERGE OBSERVED + ACCUMULATED
# ============================================================

print(
    "\n=== MERGING HISTORICAL RAINFALL ==="
)

historical_df = pd.merge(
    observed_df,
    accumulated_df,
    on="date",
    how="outer"
)


historical_df = historical_df.sort_values(
    "date"
).reset_index(
    drop=True
)


# ============================================================
# 4. REMOVE DUPLICATE OBSERVATIONS
# ============================================================

if historical_df["date"].duplicated().any():

    print(
        "WARNING: duplicate dates found."
    )

    historical_df = (
        historical_df
        .drop_duplicates(
            subset=["date"],
            keep="first"
        )
    )


# ============================================================
# 5. HANDLE INITIAL ROLLING-WINDOW NaN VALUES
# ============================================================

# The first few days naturally cannot have a complete
# 72-hour or 7-day history.
#
# We DO NOT replace these with zero.
#
# Missing means "insufficient historical window".

print(
    "\n=== HISTORICAL MISSING VALUES ==="
)

print(
    historical_df.isna().sum()
)


# ============================================================
# 6. HISTORICAL RAINFALL QUALITY CHECK
# ============================================================

print(
    "\n=== HISTORICAL RAINFALL CHECK ==="
)

for column in [
    "observed_rainfall_mm",
    "rainfall_mm",
    "rainfall_24h_mm",
    "rainfall_72h_mm",
    "rainfall_7day_mm",
]:

    values = historical_df[column]

    valid = values.dropna()

    print(
        f"\n{column}"
    )

    print(
        "valid:",
        len(valid)
    )

    if len(valid) > 0:

        print(
            "min:",
            valid.min()
        )

        print(
            "max:",
            valid.max()
        )

        print(
            "mean:",
            valid.mean()
        )

        print(
            "median:",
            valid.median()
        )


# ============================================================
# 7. CHECK OBSERVED VS ACCUMULATED DAILY RAINFALL
# ============================================================

print(
    "\n=== OBSERVED VS ACCUMULATED CHECK ==="
)

comparison = (
    historical_df[
        [
            "observed_rainfall_mm",
            "rainfall_mm"
        ]
    ]
    .dropna()
)

if len(comparison) > 0:

    difference = (
        comparison["observed_rainfall_mm"]
        -
        comparison["rainfall_mm"]
    )

    print(
        "Number of comparable days:",
        len(comparison)
    )

    print(
        "Maximum absolute difference:",
        difference.abs().max()
    )

    print(
        "Mean absolute difference:",
        difference.abs().mean()
    )


# ============================================================
# 8. SAVE HISTORICAL FEATURES
# ============================================================

historical_df.to_parquet(
    HISTORICAL_OUTPUT,
    index=False
)

print(
    "\nSaved historical rainfall features:"
)

print(
    HISTORICAL_OUTPUT
)


# ============================================================
# 9. LOAD FORECAST
# ============================================================

print(
    "\n=== LOADING FORECAST ==="
)

with open(
    FORECAST,
    "r",
    encoding="utf-8"
) as f:

    forecast_json = json.load(f)


hourly = forecast_json["hourly"]


print(
    "Forecast keys:"
)

for key in hourly.keys():

    print(
        "-",
        key
    )


# ============================================================
# 10. CHECK FORECAST STRUCTURE
# ============================================================

if "time" not in hourly:

    raise ValueError(
        "Forecast JSON does not contain hourly time."
    )


if "precipitation" not in hourly:

    raise ValueError(
        "Forecast JSON does not contain hourly precipitation."
    )


# ============================================================
# 11. BUILD HOURLY FORECAST DATAFRAME
# ============================================================

forecast_df = pd.DataFrame(
    {
        "datetime":
            hourly["time"],

        "forecast_rainfall_mm":
            hourly["precipitation"],
    }
)


forecast_df["datetime"] = pd.to_datetime(
    forecast_df["datetime"]
)


forecast_df = forecast_df.sort_values(
    "datetime"
).reset_index(
    drop=True
)


# ============================================================
# 12. CLEAN FORECAST VALUES
# ============================================================

forecast_df["forecast_rainfall_mm"] = (
    pd.to_numeric(
        forecast_df[
            "forecast_rainfall_mm"
        ],
        errors="coerce"
    )
)


if (
    forecast_df[
        "forecast_rainfall_mm"
    ] < 0
).any():

    raise ValueError(
        "Forecast rainfall contains negative values."
    )


# ============================================================
# 13. FORECAST TIME RANGE
# ============================================================

print(
    "\n=== FORECAST TIME RANGE ==="
)

print(
    "Start:",
    forecast_df["datetime"].min()
)

print(
    "End:",
    forecast_df["datetime"].max()
)

print(
    "Forecast hours:",
    len(forecast_df)
)


# ============================================================
# 14. CREATE FORECAST HORIZONS
# ============================================================

print(
    "\n=== CALCULATING FORECAST HORIZONS ==="
)


forecast_start = (
    forecast_df["datetime"].min()
)


# ------------------------------------------------------------
# 24-hour forecast rainfall
# ------------------------------------------------------------

forecast_24h = (
    forecast_df[
        "forecast_rainfall_mm"
    ]
    .iloc[:24]
    .sum()
)


# ------------------------------------------------------------
# 72-hour forecast rainfall
# ------------------------------------------------------------

forecast_72h = (
    forecast_df[
        "forecast_rainfall_mm"
    ]
    .iloc[:72]
    .sum()
)


# ------------------------------------------------------------
# 7-day forecast rainfall
# ------------------------------------------------------------

forecast_7day = (
    forecast_df[
        "forecast_rainfall_mm"
    ]
    .iloc[:168]
    .sum()
)


print(
    "Forecast start:",
    forecast_start
)

print(
    "Next 24h rainfall:",
    forecast_24h,
    "mm"
)

print(
    "Next 72h rainfall:",
    forecast_72h,
    "mm"
)

print(
    "Next 7-day rainfall:",
    forecast_7day,
    "mm"
)


# ============================================================
# 15. CREATE FORECAST SUMMARY
# ============================================================

forecast_summary = pd.DataFrame(
    [
        {
            "forecast_start":
                forecast_start,

            "forecast_rainfall_24h_mm":
                forecast_24h,

            "forecast_rainfall_72h_mm":
                forecast_72h,

            "forecast_rainfall_7day_mm":
                forecast_7day,

            "forecast_source_latitude":
                forecast_json.get(
                    "latitude"
                ),

            "forecast_source_longitude":
                forecast_json.get(
                    "longitude"
                ),

            "timezone":
                forecast_json.get(
                    "timezone"
                ),
        }
    ]
)


# ============================================================
# 16. SAVE FORECAST FEATURES
# ============================================================

forecast_summary.to_parquet(
    FORECAST_OUTPUT,
    index=False
)

print(
    "\nSaved forecast rainfall features:"
)

print(
    FORECAST_OUTPUT
)


# ============================================================
# 17. CREATE A SINGLE DYNAMIC FEATURE TABLE
# ============================================================

print(
    "\n=== CREATING DYNAMIC FEATURE TABLE ==="
)


# Historical table contains one row per day.
#
# Forecast table contains the current forecast snapshot.
#
# We keep them conceptually separate instead of pretending
# that forecast values are historical observations.

dynamic_df = historical_df.copy()


# Add the current forecast snapshot as metadata columns.
#
# These columns will be useful for the NOW / 24H / 72H
# operational risk pipeline.

dynamic_df[
    "current_forecast_24h_mm"
] = forecast_24h

dynamic_df[
    "current_forecast_72h_mm"
] = forecast_72h

dynamic_df[
    "current_forecast_7day_mm"
] = forecast_7day


dynamic_df[
    "forecast_generated_at"
] = forecast_start


# ============================================================
# 18. SAVE COMBINED TABLE
# ============================================================

dynamic_df.to_parquet(
    COMBINED_OUTPUT,
    index=False
)


print(
    "\nSaved combined dynamic rainfall features:"
)

print(
    COMBINED_OUTPUT
)


# ============================================================
# 19. FINAL SUMMARY
# ============================================================

print(
    "\n========================================"
)

print(
    "DYNAMIC RAINFALL FEATURE BUILD COMPLETE"
)

print(
    "========================================"
)

print(
    "\nHistorical rows:",
    len(historical_df)
)

print(
    "Forecast hours:",
    len(forecast_df)
)

print(
    "\nHistorical columns:"
)

for column in historical_df.columns:

    print(
        "-",
        column
    )


print(
    "\nForecast summary:"
)

print(
    forecast_summary.to_string(
        index=False
    )
)


print(
    "\nOutput files:"
)

print(
    "-",
    HISTORICAL_OUTPUT
)

print(
    "-",
    FORECAST_OUTPUT
)

print(
    "-",
    COMBINED_OUTPUT
)

print(
    "\nREADY FOR DYNAMIC FEATURE VALIDATION."
)