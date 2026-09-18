import pandas as pd
from pathlib import Path


# ============================================================
# INPUT FILES
# ============================================================

STATIC_FEATURES = Path(
    "data/processed/features/"
    "wayanad_static_features.parquet"
)

HISTORICAL_RAINFALL = Path(
    "data/processed/features/"
    "wayanad_historical_rainfall_features.parquet"
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

DAILY_OUTPUT = (
    OUTPUT_DIR /
    "wayanad_training_daily_features.parquet"
)

SPATIAL_OUTPUT = (
    OUTPUT_DIR /
    "wayanad_training_spatial_features.parquet"
)


# ============================================================
# CHECK INPUT FILES
# ============================================================

print("\n=== INPUT FILE CHECK ===")

for path in [
    STATIC_FEATURES,
    HISTORICAL_RAINFALL
]:

    if not path.exists():

        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    print(
        "FOUND:",
        path
    )


# ============================================================
# LOAD STATIC FEATURES
# ============================================================

print(
    "\n=== LOADING STATIC FEATURES ==="
)

static_df = pd.read_parquet(
    STATIC_FEATURES
)

print(
    "Rows:",
    len(static_df)
)

print(
    "Columns:",
    len(static_df.columns)
)


# ============================================================
# LOAD HISTORICAL RAINFALL
# ============================================================

print(
    "\n=== LOADING HISTORICAL RAINFALL ==="
)

rainfall_df = pd.read_parquet(
    HISTORICAL_RAINFALL
)

print(
    "Rows:",
    len(rainfall_df)
)

print(
    "Columns:"
)

for column in rainfall_df.columns:

    print(
        "-",
        column
    )


# ============================================================
# CONVERT DATE
# ============================================================

rainfall_df["date"] = pd.to_datetime(
    rainfall_df["date"]
)


# ============================================================
# REMOVE REDUNDANT OBSERVED COLUMN
# ============================================================

# Previous validation showed:
#
# observed_rainfall_mm == rainfall_mm
#
# with maximum difference = 0.0 mm.
#
# Therefore rainfall_mm is retained as the canonical
# daily rainfall feature.

if (
    "observed_rainfall_mm"
    in rainfall_df.columns
):

    rainfall_df = rainfall_df.drop(
        columns=[
            "observed_rainfall_mm"
        ]
    )

    print(
        "\nRemoved redundant column:"
        " observed_rainfall_mm"
    )


# ============================================================
# REQUIRED RAINFALL FEATURES
# ============================================================

required_rainfall_columns = [

    "date",

    "rainfall_mm",

    "rainfall_24h_mm",

    "rainfall_72h_mm",

    "rainfall_7day_mm",
]


print(
    "\n=== RAINFALL COLUMN CHECK ==="
)

for column in required_rainfall_columns:

    if column not in rainfall_df.columns:

        raise ValueError(
            f"Missing rainfall feature: {column}"
        )

    print(
        "FOUND:",
        column
    )


# ============================================================
# HISTORICAL WINDOW CHECK
# ============================================================

print(
    "\n=== HISTORICAL WINDOW CHECK ==="
)

print(
    "Missing values before cleaning:"
)

print(
    rainfall_df[
        required_rainfall_columns
    ].isna().sum()
)


before = len(
    rainfall_df
)


# The first few rows cannot have complete
# 72-hour / 7-day rolling histories.
#
# We REMOVE those rows instead of filling them
# with zero.

rainfall_df = rainfall_df.dropna(
    subset=[
        "rainfall_72h_mm",
        "rainfall_7day_mm"
    ]
).copy()


after = len(
    rainfall_df
)


print(
    "\nRows before:",
    before
)

print(
    "Rows after:",
    after
)

print(
    "Removed:",
    before - after
)


# ============================================================
# SORT BY DATE
# ============================================================

rainfall_df = rainfall_df.sort_values(
    "date"
).reset_index(
    drop=True
)


# ============================================================
# RAINFALL DATE RANGE
# ============================================================

print(
    "\n=== HISTORICAL DATE RANGE ==="
)

print(
    "Start:",
    rainfall_df["date"].min()
)

print(
    "End:",
    rainfall_df["date"].max()
)

print(
    "Usable historical days:",
    len(rainfall_df)
)


# ============================================================
# RAINFALL SANITY CHECK
# ============================================================

print(
    "\n=== RAINFALL SANITY CHECK ==="
)

for column in [

    "rainfall_mm",

    "rainfall_24h_mm",

    "rainfall_72h_mm",

    "rainfall_7day_mm",

]:

    values = rainfall_df[
        column
    ].dropna()

    print(
        f"\n{column}"
    )

    print(
        "min:",
        values.min()
    )

    print(
        "max:",
        values.max()
    )

    print(
        "mean:",
        values.mean()
    )

    print(
        "median:",
        values.median()
    )


# ============================================================
# NEGATIVE RAINFALL CHECK
# ============================================================

print(
    "\n=== NEGATIVE RAINFALL CHECK ==="
)

rainfall_columns = [

    "rainfall_mm",

    "rainfall_24h_mm",

    "rainfall_72h_mm",

    "rainfall_7day_mm",

]


for column in rainfall_columns:

    negative_count = (
        rainfall_df[column] < 0
    ).sum()

    print(
        column,
        "negative values:",
        negative_count
    )

    if negative_count > 0:

        raise ValueError(
            f"{column} contains negative rainfall."
        )


# ============================================================
# SAVE DAILY TRAINING FEATURES
# ============================================================

print(
    "\n=== SAVING DAILY RAINFALL FEATURES ==="
)

rainfall_df.to_parquet(
    DAILY_OUTPUT,
    index=False
)

print(
    "Saved:",
    DAILY_OUTPUT
)


# ============================================================
# STATIC FEATURE VALIDATION
# ============================================================

print(
    "\n=== STATIC FEATURE VALIDATION ==="
)

required_static_columns = [

    "x",

    "y",

    "slope_degrees",

    "gsi_susceptibility",

    "gsi_coverage",

    "tree_cover_fraction",

    "grassland_fraction",

    "cropland_fraction",

    "builtup_fraction",

    "bare_fraction",

    "water_fraction",

]


for column in required_static_columns:

    if column not in static_df.columns:

        raise ValueError(
            f"Missing static feature: {column}"
        )

    print(
        "FOUND:",
        column
    )


# ============================================================
# REMOVE INVALID SLOPE CELLS
# ============================================================

print(
    "\n=== STATIC VALIDITY ==="
)

total_static_cells = len(
    static_df
)


valid_slope_mask = (
    static_df[
        "slope_degrees"
    ].notna()
)


valid_static_cells = (
    valid_slope_mask.sum()
)


invalid_static_cells = (
    (~valid_slope_mask).sum()
)


print(
    "Total cells:",
    total_static_cells
)

print(
    "Valid slope cells:",
    valid_static_cells
)

print(
    "Invalid slope cells:",
    invalid_static_cells
)


spatial_df = (
    static_df[
        valid_slope_mask
    ]
    .copy()
    .reset_index(
        drop=True
    )
)


# ============================================================
# GSI COVERAGE CHECK
# ============================================================

print(
    "\n=== GSI COVERAGE ==="
)

gsi_covered = (
    spatial_df[
        "gsi_coverage"
    ] == 1
).sum()


gsi_not_covered = (
    spatial_df[
        "gsi_coverage"
    ] == 0
).sum()


print(
    "GSI-covered cells:",
    gsi_covered
)

print(
    "No-GSI-coverage cells:",
    gsi_not_covered
)


# ============================================================
# WORLDCOVER RANGE CHECK
# ============================================================

print(
    "\n=== WORLDCOVER RANGE CHECK ==="
)

worldcover_columns = [

    "tree_cover_fraction",

    "grassland_fraction",

    "cropland_fraction",

    "builtup_fraction",

    "bare_fraction",

    "water_fraction",

]


for column in worldcover_columns:

    minimum = spatial_df[
        column
    ].min()

    maximum = spatial_df[
        column
    ].max()

    print(
        column,
        "min:",
        minimum,
        "max:",
        maximum
    )

    if minimum < 0 or maximum > 1:

        raise ValueError(
            f"{column} contains values outside 0-1."
        )


# ============================================================
# SAVE SPATIAL FEATURES
# ============================================================

print(
    "\n=== SAVING SPATIAL FEATURES ==="
)

spatial_df.to_parquet(
    SPATIAL_OUTPUT,
    index=False
)

print(
    "Saved:",
    SPATIAL_OUTPUT
)


# ============================================================
# FINAL VALIDATION
# ============================================================

print(
    "\n========================================"
)

print(
    "TRAINING FEATURE PREPARATION COMPLETE"
)

print(
    "========================================"
)

print(
    "\nSpatial cells:",
    len(spatial_df)
)

print(
    "Historical rainfall days:",
    len(rainfall_df)
)

print(
    "\nOutput 1:"
)

print(
    DAILY_OUTPUT
)

print(
    "\nOutput 2:"
)

print(
    SPATIAL_OUTPUT
)

print(
    "\nIMPORTANT:"
)

print(
    "Rainfall is currently a district-level temporal signal."
)

print(
    "It is NOT being treated as a 30m spatial rainfall grid."
)

print(
    "\nNEXT STEP:"
)

print(
    "Build the historical landslide event/label dataset."
)