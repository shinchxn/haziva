from pathlib import Path
import json
import math

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAINFALL_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "rainfall"
    / "accumulated"
    / "wayanad"
    / "wayanad_rainfall_accumulated_2015_2025.csv"
)

EVENT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "features"
    / "wayanad_temporal_landslide_event_dates.parquet"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "features"
)

RESULTS_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "model_results"
)

REFERENCE_OUTPUT = (
    OUTPUT_DIR
    / "wayanad_rainfall_stress_reference.json"
)

HISTORICAL_OUTPUT = (
    RESULTS_DIR
    / "rainfall_stress_historical_validation.csv"
)

SUMMARY_OUTPUT = (
    RESULTS_DIR
    / "rainfall_stress_validation_summary.csv"
)


RAIN_COLUMNS = [
    "rainfall_24h_mm",
    "rainfall_72h_mm",
    "rainfall_7day_mm",
]


# Percentiles used to describe rainfall stress.
REFERENCE_PERCENTILES = [
    0,
    5,
    10,
    25,
    50,
    75,
    90,
    95,
    99,
    99.5,
    99.9,
    100,
]


# ============================================================
# HELPERS
# ============================================================

def percentile_value(series, percentile):
    """
    Calculate percentile while ignoring missing values.
    """
    values = pd.to_numeric(series, errors="coerce").dropna().to_numpy()

    if len(values) == 0:
        raise ValueError(
            f"No valid values available for percentile calculation: {series.name}"
        )

    return float(np.percentile(values, percentile))


def calculate_percentile_rank(value, reference_values):
    """
    Empirical percentile rank.

    Returns a value between 0 and 1.

    Example:
        0.50 -> approximately 50th percentile
        0.95 -> approximately 95th percentile
    """

    values = np.asarray(reference_values, dtype=float)
    values = values[np.isfinite(values)]

    if len(values) == 0:
        raise ValueError("Reference distribution is empty.")

    rank = np.mean(values <= value)

    return float(np.clip(rank, 0.0, 1.0))


def stress_from_percentile(percentile_rank):
    """
    Convert percentile rank into a continuous 0-1 rainfall stress.

    We intentionally keep this continuous rather than creating
    arbitrary Low / Medium / High operational thresholds.
    """

    return float(np.clip(percentile_rank, 0.0, 1.0))


def describe_distribution(values):
    """
    Return useful descriptive statistics.
    """

    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]

    if len(values) == 0:
        raise ValueError("Cannot describe an empty distribution.")

    return {
        "count": int(len(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
        "p50": float(np.percentile(values, 50)),
        "p75": float(np.percentile(values, 75)),
        "p90": float(np.percentile(values, 90)),
        "p95": float(np.percentile(values, 95)),
        "p99": float(np.percentile(values, 99)),
    }


# ============================================================
# LOAD RAINFALL
# ============================================================

print("=" * 70)
print("WAYANAD RAINFALL STRESS CALIBRATION")
print("=" * 70)

print("\nLoading rainfall dataset...")
print(RAINFALL_PATH)

if not RAINFALL_PATH.exists():
    raise FileNotFoundError(
        f"Rainfall dataset not found:\n{RAINFALL_PATH}"
    )

rainfall = pd.read_csv(RAINFALL_PATH)

print(f"Rainfall shape: {rainfall.shape}")
print(f"Columns: {list(rainfall.columns)}")


# ============================================================
# VALIDATE RAINFALL DATASET
# ============================================================

required_columns = [
    "date",
    "rainfall_mm",
    "rainfall_24h_mm",
    "rainfall_72h_mm",
    "rainfall_7day_mm",
]

missing_columns = [
    col for col in required_columns
    if col not in rainfall.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required rainfall columns: {missing_columns}"
    )


rainfall["date"] = pd.to_datetime(
    rainfall["date"],
    errors="coerce"
)

if rainfall["date"].isna().any():
    raise ValueError("Rainfall dataset contains invalid dates.")


if rainfall["date"].duplicated().any():
    duplicate_dates = int(
        rainfall["date"].duplicated().sum()
    )

    raise ValueError(
        f"Rainfall dataset contains {duplicate_dates} duplicate dates."
    )


for column in required_columns[1:]:
    rainfall[column] = pd.to_numeric(
        rainfall[column],
        errors="coerce"
    )


print("\nMissing rainfall values:")

for column in required_columns[1:]:
    print(
        f"  {column}: "
        f"{int(rainfall[column].isna().sum())}"
    )


# ============================================================
# EXPECTED LEADING GAPS
# ============================================================

# The first 2 records cannot have a complete 72h rolling
# accumulation and the first 6 cannot have a complete 7-day
# accumulation.
#
# We do NOT fill these with zero.
#
# They are simply excluded from the corresponding distribution.

for column in RAIN_COLUMNS:

    valid_count = int(
        rainfall[column].notna().sum()
    )

    if valid_count == 0:
        raise ValueError(
            f"No valid observations for {column}."
        )


# ============================================================
# BASIC RAINFALL CONSISTENCY
# ============================================================

valid_72 = rainfall[
    rainfall["rainfall_72h_mm"].notna()
]

if (
    valid_72["rainfall_72h_mm"]
    < valid_72["rainfall_24h_mm"]
).any():

    raise ValueError(
        "Found rainfall_72h_mm < rainfall_24h_mm."
    )


valid_7day = rainfall[
    rainfall["rainfall_7day_mm"].notna()
]

if (
    valid_7day["rainfall_7day_mm"]
    < valid_7day["rainfall_72h_mm"]
).any():

    raise ValueError(
        "Found rainfall_7day_mm < rainfall_72h_mm."
    )


print("\nRainfall consistency checks PASSED")


# ============================================================
# PRINT HISTORICAL DISTRIBUTIONS
# ============================================================

print("\nHistorical rainfall distributions:")

distribution_stats = {}

for column in RAIN_COLUMNS:

    values = (
        rainfall[column]
        .dropna()
        .to_numpy()
    )

    stats = describe_distribution(values)

    distribution_stats[column] = stats

    print(f"\n{column}")

    for key, value in stats.items():

        if key == "count":
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value:.3f}")


# ============================================================
# BUILD PERCENTILE REFERENCE TABLES
# ============================================================

print("\nBuilding percentile reference tables...")

percentile_tables = {}

for column in RAIN_COLUMNS:

    values = (
        rainfall[column]
        .dropna()
        .to_numpy()
    )

    table = {}

    for percentile in REFERENCE_PERCENTILES:

        value = percentile_value(
            rainfall[column],
            percentile
        )

        table[str(percentile)] = value

    percentile_tables[column] = table


# ============================================================
# LOAD HISTORICAL EVENT DATES
# ============================================================

print("\nLoading historical landslide event dates...")
print(EVENT_PATH)

if not EVENT_PATH.exists():
    raise FileNotFoundError(
        f"Historical event dataset not found:\n{EVENT_PATH}"
    )

events = pd.read_parquet(EVENT_PATH)

print(f"Event dataset shape: {events.shape}")
print(f"Event columns: {list(events.columns)}")


# ============================================================
# EVENT DATA VALIDATION
# ============================================================

if "event_date" not in events.columns:
    raise ValueError(
        "Historical event dataset does not contain event_date."
    )


events["event_date"] = pd.to_datetime(
    events["event_date"],
    errors="coerce"
)

events = events[
    events["event_date"].notna()
].copy()

if len(events) == 0:
    raise ValueError(
        "No dated historical landslide events available."
    )


# ============================================================
# JOIN EVENTS WITH RAINFALL
# ============================================================

event_columns = [
    "event_date"
]

for column in RAIN_COLUMNS:
    if column in events.columns:
        event_columns.append(column)


event_dates = (
    events[event_columns]
    .drop_duplicates()
    .sort_values("event_date")
    .reset_index(drop=True)
)


# If rainfall columns aren't already present in the event file,
# join them from the authoritative rainfall dataset.

rainfall_join_columns = [
    "date"
] + RAIN_COLUMNS

rainfall_for_join = rainfall[
    rainfall_join_columns
].copy()

rainfall_for_join = rainfall_for_join.rename(
    columns={"date": "event_date"}
)


for column in RAIN_COLUMNS:

    if column not in event_dates.columns:

        event_dates = event_dates.merge(
            rainfall_for_join,
            on="event_date",
            how="left",
            validate="one_to_one"
        )


# ============================================================
# VERIFY EVENT RAINFALL
# ============================================================

for column in RAIN_COLUMNS:

    if event_dates[column].isna().any():

        missing_dates = event_dates.loc[
            event_dates[column].isna(),
            "event_date"
        ].dt.strftime("%Y-%m-%d").tolist()

        raise ValueError(
            f"Missing {column} for historical event dates: "
            f"{missing_dates}"
        )


# ============================================================
# CALCULATE EVENT RAINFALL STRESS
# ============================================================

print("\nCalculating rainfall stress for historical events...")

for column in RAIN_COLUMNS:

    reference_values = (
        rainfall[column]
        .dropna()
        .to_numpy()
    )

    percentile_column = (
        column.replace("_mm", "_percentile")
    )

    stress_column = (
        column.replace("_mm", "_stress")
    )

    event_dates[percentile_column] = (
        event_dates[column]
        .apply(
            lambda value:
            calculate_percentile_rank(
                value,
                reference_values
            )
        )
    )

    event_dates[stress_column] = (
        event_dates[percentile_column]
        .apply(stress_from_percentile)
    )


# ============================================================
# COMBINED RAINFALL STRESS
# ============================================================

stress_columns = [
    "rainfall_24h_stress",
    "rainfall_72h_stress",
    "rainfall_7day_stress",
]

percentile_columns = [
    "rainfall_24h_percentile",
    "rainfall_72h_percentile",
    "rainfall_7day_percentile",
]


# We intentionally keep this combination transparent.
#
# The 72h and 7-day windows capture accumulated rainfall,
# while the 24h window captures recent intensity.
#
# This is a descriptive stress indicator, NOT a trained
# landslide probability.

event_dates["combined_rainfall_stress"] = (
    0.30 * event_dates["rainfall_24h_stress"]
    + 0.40 * event_dates["rainfall_72h_stress"]
    + 0.30 * event_dates["rainfall_7day_stress"]
)


event_dates["combined_rainfall_stress"] = (
    event_dates["combined_rainfall_stress"]
    .clip(0.0, 1.0)
)


# ============================================================
# HISTORICAL EVENT VALIDATION SUMMARY
# ============================================================

print("\nHistorical event rainfall stress:")

display_columns = [
    "event_date",
    "rainfall_24h_mm",
    "rainfall_72h_mm",
    "rainfall_7day_mm",
    "rainfall_24h_percentile",
    "rainfall_72h_percentile",
    "rainfall_7day_percentile",
    "combined_rainfall_stress",
]

print(
    event_dates[
        display_columns
    ].to_string(index=False)
)


# ============================================================
# EVENT STRESS SUMMARY
# ============================================================

event_summary = []

for column in stress_columns:

    values = (
        event_dates[column]
        .to_numpy()
    )

    event_summary.append({
        "metric": column,
        "event_count": int(len(values)),
        "minimum": float(np.min(values)),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "p75": float(np.percentile(values, 75)),
        "p90": float(np.percentile(values, 90)),
        "maximum": float(np.max(values)),
    })


combined_values = (
    event_dates["combined_rainfall_stress"]
    .to_numpy()
)

event_summary.append({
    "metric": "combined_rainfall_stress",
    "event_count": int(len(combined_values)),
    "minimum": float(np.min(combined_values)),
    "mean": float(np.mean(combined_values)),
    "median": float(np.median(combined_values)),
    "p75": float(np.percentile(combined_values, 75)),
    "p90": float(np.percentile(combined_values, 90)),
    "maximum": float(np.max(combined_values)),
})

event_summary_df = pd.DataFrame(event_summary)


# ============================================================
# SAVE REFERENCE MODEL
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


reference = {
    "project": "Wayanad landslide dynamic risk",
    "method": "Empirical rainfall percentile stress",
    "purpose": (
        "Convert district-level rainfall observations "
        "into a continuous 0-1 rainfall stress indicator "
        "for future-risk decision support."
    ),
    "important_limitation": (
        "This is not a standalone landslide probability "
        "model and does not predict exact landslide "
        "location or timing."
    ),
    "rainfall_source": str(
        RAINFALL_PATH.relative_to(PROJECT_ROOT)
    ),
    "historical_period": {
        "start": rainfall["date"].min().strftime("%Y-%m-%d"),
        "end": rainfall["date"].max().strftime("%Y-%m-%d"),
    },
    "reference_percentiles": REFERENCE_PERCENTILES,
    "distributions": distribution_stats,
    "percentile_tables": percentile_tables,
    "combined_stress_formula": {
        "rainfall_24h_stress": 0.30,
        "rainfall_72h_stress": 0.40,
        "rainfall_7day_stress": 0.30,
    },
    "historical_event_validation": {
        "event_source": str(
            EVENT_PATH.relative_to(PROJECT_ROOT)
        ),
        "dated_event_records_used": int(len(events)),
        "unique_event_dates": int(
            event_dates["event_date"].nunique()
        ),
        "event_date_min": (
            event_dates["event_date"]
            .min()
            .strftime("%Y-%m-%d")
        ),
        "event_date_max": (
            event_dates["event_date"]
            .max()
            .strftime("%Y-%m-%d")
        ),
    },
}


with open(
    REFERENCE_OUTPUT,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        reference,
        f,
        indent=2
    )


# ============================================================
# SAVE HISTORICAL EVENT VALIDATION
# ============================================================

event_dates.to_csv(
    HISTORICAL_OUTPUT,
    index=False
)


event_summary_df.to_csv(
    SUMMARY_OUTPUT,
    index=False
)


# ============================================================
# FINAL QA
# ============================================================

print("\n" + "=" * 70)
print("FINAL QA")
print("=" * 70)

assert len(event_dates) > 0

assert (
    event_dates["combined_rainfall_stress"]
    .between(0, 1)
    .all()
)

for column in stress_columns:

    assert (
        event_dates[column]
        .between(0, 1)
        .all()
    )


assert not event_dates[
    RAIN_COLUMNS
].isna().any().any()


assert (
    event_dates["event_date"]
    .is_unique
)


print("Event dates unique: PASSED")
print("Rainfall completeness: PASSED")
print("Stress values within [0,1]: PASSED")
print("Historical event validation: PASSED")


print("\nOutputs:")

print(
    f"Reference:\n"
    f"  {REFERENCE_OUTPUT}"
)

print(
    f"\nHistorical validation:\n"
    f"  {HISTORICAL_OUTPUT}"
)

print(
    f"\nValidation summary:\n"
    f"  {SUMMARY_OUTPUT}"
)


print("\n" + "=" * 70)
print("RAINFALL STRESS CALIBRATION COMPLETE")
print("=" * 70)