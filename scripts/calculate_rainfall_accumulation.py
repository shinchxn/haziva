from pathlib import Path
import json

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "rainfall"
    / "observed"
    / "wayanad"
    / "wayanad_daily_rainfall_2015_2025.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "rainfall"
    / "accumulated"
    / "wayanad"
    / "wayanad_rainfall_accumulated_2015_2025.csv"
)


# ============================================================
# LOAD SOURCE JSON
# ============================================================

print("=" * 70)
print("WAYANAD RAINFALL ACCUMULATION REBUILD")
print("=" * 70)

print("\nLoading source:")
print(INPUT_PATH)

if not INPUT_PATH.exists():
    raise FileNotFoundError(
        f"Source rainfall JSON not found:\n{INPUT_PATH}"
    )

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)


# ============================================================
# VALIDATE JSON STRUCTURE
# ============================================================

if not isinstance(data, dict):
    raise ValueError(
        f"Expected JSON object/dict, got {type(data)}"
    )

if "daily" not in data:
    raise ValueError(
        "Source JSON does not contain 'daily'."
    )

daily = data["daily"]

if not isinstance(daily, dict):
    raise ValueError(
        "Expected 'daily' to be a dictionary."
    )

if "time" not in daily:
    raise ValueError(
        "Source JSON daily section does not contain 'time'."
    )

if "precipitation_sum" not in daily:
    raise ValueError(
        "Source JSON daily section does not contain "
        "'precipitation_sum'."
    )

dates = daily["time"]
rain_values = daily["precipitation_sum"]


if len(dates) != len(rain_values):
    raise ValueError(
        "Daily time and rain arrays have different lengths: "
        f"{len(dates)} vs {len(rain_values)}"
    )


print(f"\nSource records: {len(dates)}")


# ============================================================
# BUILD DAILY DATAFRAME
# ============================================================

df = pd.DataFrame({
    "date": pd.to_datetime(
        dates,
        errors="coerce"
    ),
    "rainfall_mm": pd.to_numeric(
        rain_values,
        errors="coerce"
    ),
})


# ============================================================
# DATE VALIDATION
# ============================================================

if df["date"].isna().any():
    count = int(df["date"].isna().sum())

    raise ValueError(
        f"Found {count} invalid dates."
    )


if df["date"].duplicated().any():
    duplicates = (
        df.loc[
            df["date"].duplicated(keep=False),
            "date"
        ]
        .dt.strftime("%Y-%m-%d")
        .tolist()
    )

    raise ValueError(
        "Duplicate dates found:\n"
        + "\n".join(duplicates)
    )


# ============================================================
# RAINFALL VALIDATION
# ============================================================

missing_rainfall = int(
    df["rainfall_mm"].isna().sum()
)

print(
    f"Missing rainfall values: "
    f"{missing_rainfall}"
)

if missing_rainfall > 0:
    raise ValueError(
        "Daily rainfall source contains missing values. "
        "Do not silently replace them."
    )


negative_count = int(
    (df["rainfall_mm"] < 0).sum()
)

if negative_count > 0:
    raise ValueError(
        f"Found {negative_count} negative rainfall values."
    )


# ============================================================
# SORT
# ============================================================

df = (
    df
    .sort_values("date")
    .reset_index(drop=True)
)


# ============================================================
# CHECK CALENDAR CONTINUITY
# ============================================================

expected_dates = pd.date_range(
    start=df["date"].min(),
    end=df["date"].max(),
    freq="D"
)

actual_dates = pd.DatetimeIndex(
    df["date"]
)

missing_dates = expected_dates.difference(
    actual_dates
)

extra_dates = actual_dates.difference(
    expected_dates
)

print(
    f"\nDate range: "
    f"{df['date'].min().date()} "
    f"to "
    f"{df['date'].max().date()}"
)

print(
    f"Expected calendar days: "
    f"{len(expected_dates)}"
)

print(
    f"Observed calendar days: "
    f"{len(actual_dates)}"
)

print(
    f"Missing calendar days: "
    f"{len(missing_dates)}"
)

if len(extra_dates) > 0:
    raise ValueError(
        f"Unexpected dates outside calendar range: "
        f"{extra_dates.tolist()}"
    )

if len(missing_dates) > 0:
    print("\nWARNING: Missing calendar dates:")

    for date in missing_dates[:20]:
        print(
            f"  {date.strftime('%Y-%m-%d')}"
        )

    if len(missing_dates) > 20:
        print(
            f"  ... and "
            f"{len(missing_dates) - 20} more"
        )

    raise ValueError(
        "Daily rainfall series is not calendar-continuous. "
        "Cannot safely calculate 72h/7day accumulation."
    )


# ============================================================
# CALCULATE ACCUMULATIONS
# ============================================================

#
# Because the dataframe is now verified to contain every
# calendar day exactly once:
#
# 24h  = current day
# 72h  = current + previous 2 calendar days
# 7day = current + previous 6 calendar days
#

df["rainfall_24h_mm"] = (
    df["rainfall_mm"]
)

df["rainfall_72h_mm"] = (
    df["rainfall_mm"]
    .rolling(
        window=3,
        min_periods=3
    )
    .sum()
)

df["rainfall_7day_mm"] = (
    df["rainfall_mm"]
    .rolling(
        window=7,
        min_periods=7
    )
    .sum()
)


# ============================================================
# ROUNDING
# ============================================================

for column in [
    "rainfall_mm",
    "rainfall_24h_mm",
    "rainfall_72h_mm",
    "rainfall_7day_mm",
]:

    df[column] = (
        df[column]
        .round(1)
    )


# ============================================================
# ACCUMULATION QA
# ============================================================

print("\nRunning accumulation QA...")

valid_72h = df[
    df["rainfall_72h_mm"].notna()
]

valid_7day = df[
    df["rainfall_7day_mm"].notna()
]


# 72h must be >= 24h
bad_72h = valid_72h[
    valid_72h["rainfall_72h_mm"]
    < valid_72h["rainfall_24h_mm"]
]

if len(bad_72h) > 0:

    print(
        "\nINVALID 72h ACCUMULATIONS:"
    )

    print(
        bad_72h.to_string(index=False)
    )

    raise ValueError(
        f"Found {len(bad_72h)} rows where "
        "72h rainfall < 24h rainfall."
    )


# 7day must be >= 72h
bad_7day = valid_7day[
    valid_7day["rainfall_7day_mm"]
    < valid_7day["rainfall_72h_mm"]
]

if len(bad_7day) > 0:

    print(
        "\nINVALID 7-DAY ACCUMULATIONS:"
    )

    print(
        bad_7day.to_string(index=False)
    )

    raise ValueError(
        f"Found {len(bad_7day)} rows where "
        "7-day rainfall < 72h rainfall."
    )


# ============================================================
# CHECK KNOWN EVENT DATES
# ============================================================

known_event_dates = [
    "2018-06-14",
    "2018-07-01",
    "2018-08-08",
    "2018-08-09",
    "2018-08-15",
    "2019-08-08",
    "2019-08-09",
]

event_check = df[
    df["date"].isin(
        pd.to_datetime(known_event_dates)
    )
][
    [
        "date",
        "rainfall_mm",
        "rainfall_24h_mm",
        "rainfall_72h_mm",
        "rainfall_7day_mm",
    ]
]


print("\nKnown historical event-date rainfall:")

print(
    event_check.to_string(index=False)
)


if len(event_check) != len(known_event_dates):
    missing_events = set(
        pd.to_datetime(known_event_dates)
    ) - set(event_check["date"])

    raise ValueError(
        "Some known event dates are missing from "
        f"the rainfall dataset: {missing_events}"
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("RAINFALL ACCUMULATION SUMMARY")
print("=" * 70)

print(
    f"Total rows: {len(df)}"
)

print(
    f"24h valid rows: "
    f"{df['rainfall_24h_mm'].notna().sum()}"
)

print(
    f"72h valid rows: "
    f"{df['rainfall_72h_mm'].notna().sum()}"
)

print(
    f"7-day valid rows: "
    f"{df['rainfall_7day_mm'].notna().sum()}"
)

print(
    f"72h violations: {len(bad_72h)}"
)

print(
    f"7-day violations: {len(bad_7day)}"
)


print("\nMaximum values:")

print(
    f"24h: "
    f"{df['rainfall_24h_mm'].max():.1f} mm"
)

print(
    f"72h: "
    f"{df['rainfall_72h_mm'].max():.1f} mm"
)

print(
    f"7-day: "
    f"{df['rainfall_7day_mm'].max():.1f} mm"
)


# ============================================================
# SAVE
# ============================================================

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_PATH,
    index=False
)


print("\nOutput:")
print(OUTPUT_PATH)

print("\n" + "=" * 70)
print("ALL RAINFALL ACCUMULATION QA CHECKS PASSED")
print("=" * 70)