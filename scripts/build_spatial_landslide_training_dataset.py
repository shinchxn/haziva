from pathlib import Path

import numpy as np
import pandas as pd
import rasterio


STATIC_FILE = Path(
    "data/processed/features/"
    "wayanad_static_features.parquet"
)

LABEL_FILE = Path(
    "data/processed/landslide/inventory/"
    "wayanad_historical_landslide_presence_30m.tif"
)

OUTPUT_FILE = Path(
    "data/processed/features/"
    "wayanad_spatial_landslide_training.parquet"
)


print("=" * 80)
print("BUILDING SPATIAL LANDSLIDE TRAINING DATASET")
print("=" * 80)


# --------------------------------------------------
# LOAD STATIC FEATURES
# --------------------------------------------------

df = pd.read_parquet(STATIC_FILE)

print()
print("Static rows:", len(df))
print("Static columns:", len(df.columns))


# --------------------------------------------------
# LOAD LANDSLIDE LABEL
# --------------------------------------------------

with rasterio.open(LABEL_FILE) as src:

    labels = src.read(1)

    width = src.width
    height = src.height

    transform = src.transform

    label_crs = src.crs


expected = width * height

if len(df) != expected:

    raise ValueError(
        f"Static rows ({len(df)}) != "
        f"raster cells ({expected})"
    )


# --------------------------------------------------
# FLATTEN LABEL
# --------------------------------------------------

label_flat = labels.reshape(-1)

df["historical_landslide"] = (
    label_flat.astype(np.uint8)
)


# --------------------------------------------------
# VALID TERRAIN MASK
# --------------------------------------------------

valid = (
    np.isfinite(
        df["slope_degrees"].to_numpy()
    )
    &
    (
        df["slope_degrees"].to_numpy()
        >= 0
    )
)


print()
print("-" * 80)
print("VALIDATION")
print("-" * 80)

print(
    "Valid terrain cells:",
    int(valid.sum())
)

print(
    "Invalid terrain cells:",
    int((~valid).sum())
)


# --------------------------------------------------
# CHECK LABEL VALUES
# --------------------------------------------------

unique_labels = sorted(
    df["historical_landslide"].unique()
)

print()
print(
    "Historical label values:",
    unique_labels
)

if not set(unique_labels).issubset({0, 1}):

    raise ValueError(
        "Historical landslide label contains "
        "unexpected values."
    )


# --------------------------------------------------
# CLASS BALANCE — VALID CELLS ONLY
# --------------------------------------------------

valid_df = df.loc[valid].copy()

positive = (
    valid_df["historical_landslide"] == 1
)

negative = (
    valid_df["historical_landslide"] == 0
)

positive_count = int(positive.sum())
negative_count = int(negative.sum())

total = positive_count + negative_count


print()
print("-" * 80)
print("CLASS BALANCE")
print("-" * 80)

print(
    f"Positive: {positive_count:,}"
)

print(
    f"Negative: {negative_count:,}"
)

print(
    f"Total valid: {total:,}"
)

print(
    f"Positive %: "
    f"{100 * positive_count / total:.4f}%"
)

print(
    f"Negative %: "
    f"{100 * negative_count / total:.4f}%"
)


# --------------------------------------------------
# CHECK GSI COVERAGE
# --------------------------------------------------

print()
print("-" * 80)
print("GSI COVERAGE")
print("-" * 80)

gsi_coverage = (
    valid_df["gsi_coverage"]
    .to_numpy()
)

print(
    "Covered cells:",
    int((gsi_coverage > 0).sum())
)

print(
    "No-coverage cells:",
    int((gsi_coverage == 0).sum())
)


# --------------------------------------------------
# LANDSLIDES WITH GSI COVERAGE
# --------------------------------------------------

positive_gsi = valid_df[
    (valid_df["historical_landslide"] == 1)
    &
    (valid_df["gsi_coverage"] > 0)
]

positive_no_gsi = valid_df[
    (valid_df["historical_landslide"] == 1)
    &
    (valid_df["gsi_coverage"] == 0)
]

print()
print(
    "Historical positive cells with GSI coverage:",
    len(positive_gsi)
)

print(
    "Historical positive cells without GSI coverage:",
    len(positive_no_gsi)
)


# --------------------------------------------------
# SLOPE SANITY
# --------------------------------------------------

slope = valid_df["slope_degrees"]

print()
print("-" * 80)
print("SLOPE")
print("-" * 80)

print(
    f"Min:    {slope.min():.4f}"
)

print(
    f"Max:    {slope.max():.4f}"
)

print(
    f"Mean:   {slope.mean():.4f}"
)

print(
    f"Median: {slope.median():.4f}"
)


# --------------------------------------------------
# WORLD COVER SANITY
# --------------------------------------------------

worldcover_columns = [
    "tree_cover_fraction",
    "grassland_fraction",
    "cropland_fraction",
    "builtup_fraction",
    "bare_fraction",
    "water_fraction",
]

print()
print("-" * 80)
print("WORLDCOVER RANGES")
print("-" * 80)

for column in worldcover_columns:

    values = valid_df[column]

    print(
        f"{column:25s}"
        f"min={values.min():.4f} "
        f"max={values.max():.4f}"
    )

    if (
        values.min() < 0
        or values.max() > 1
    ):

        raise ValueError(
            f"{column} is outside [0,1]"
        )


# --------------------------------------------------
# REMOVE INVALID TERRAIN CELLS
# --------------------------------------------------

training_df = df.loc[
    valid
].copy()


# --------------------------------------------------
# SAVE
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

training_df.to_parquet(
    OUTPUT_FILE,
    index=False
)


print()
print("=" * 80)
print("SPATIAL TRAINING DATASET CREATED")
print("=" * 80)

print()
print(
    f"Rows saved: {len(training_df):,}"
)

print(
    f"Columns saved: {len(training_df.columns)}"
)

print()
print("Output:")
print(OUTPUT_FILE)

print()
print(
    "Historical label:"
)

print(
    "0 = no mapped historical landslide"
)

print(
    "1 = mapped historical landslide"
)

print()
print(
    "Source:"
)

print(
    "Bhuvan WMS kl_landslides_new"
)

print(
    "Representation: WMS-derived"
)