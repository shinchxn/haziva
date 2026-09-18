import rasterio
import numpy as np
import pandas as pd
from pathlib import Path


# ============================================================
# INPUT FILES
# ============================================================

REFERENCE = Path(
    "data/processed/terrain/wayanad_slope_degrees.tif"
)

GSI = Path(
    "data/processed/landslide/susceptibility/"
    "wayanad_gsi_susceptibility_aligned.tif"
)

WORLD_COVER_DIR = Path(
    "data/processed/exposure/worldcover"
)


# ============================================================
# OUTPUT FILE
# ============================================================

OUTPUT = Path(
    "data/processed/features/wayanad_static_features.parquet"
)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# WORLDCOVER FEATURE FILES
# ============================================================

FEATURE_FILES = {

    "tree_cover_fraction":
        WORLD_COVER_DIR /
        "wayanad_tree_cover_fraction_30m.tif",

    "grassland_fraction":
        WORLD_COVER_DIR /
        "wayanad_grassland_fraction_30m.tif",

    "cropland_fraction":
        WORLD_COVER_DIR /
        "wayanad_cropland_fraction_30m.tif",

    "builtup_fraction":
        WORLD_COVER_DIR /
        "wayanad_builtup_fraction_30m.tif",

    "bare_fraction":
        WORLD_COVER_DIR /
        "wayanad_bare_fraction_30m.tif",

    "water_fraction":
        WORLD_COVER_DIR /
        "wayanad_water_fraction_30m.tif",
}


# ============================================================
# RASTER READER
# ============================================================

def read_raster(path):

    with rasterio.open(path) as src:

        data = src.read(1)

        return data


# ============================================================
# REFERENCE / SLOPE
# ============================================================

print("\n=== REFERENCE GRID ===")

with rasterio.open(REFERENCE) as src:

    slope = src.read(1).astype(
        np.float32
    )

    slope_nodata = src.nodata

    transform = src.transform

    width = src.width
    height = src.height

    reference_crs = src.crs

    reference_bounds = src.bounds

    print(
        "CRS:",
        reference_crs
    )

    print(
        "Size:",
        width,
        height
    )

    print(
        "Transform:",
        transform
    )

    print(
        "Bounds:",
        reference_bounds
    )

    print(
        "Slope NoData:",
        slope_nodata
    )


# ============================================================
# CLEAN SLOPE NODATA
# ============================================================

if slope_nodata is not None:

    slope[slope == slope_nodata] = np.nan


# Additional protection against invalid negative slope values.
# Real slope values should not be negative.

slope[slope < 0] = np.nan


# ============================================================
# GSI SUSCEPTIBILITY
# ============================================================

print("\n=== GSI SUSCEPTIBILITY ===")

with rasterio.open(GSI) as src:

    gsi = src.read(1).astype(
        np.float32
    )

    gsi_nodata = src.nodata

    print(
        "CRS:",
        src.crs
    )

    print(
        "Size:",
        src.width,
        src.height
    )

    print(
        "GSI NoData:",
        gsi_nodata
    )


# ------------------------------------------------------------
# GSI encoding
#
# 0 = No GSI coverage
# 1 = Low
# 2 = Moderate
# 3 = High
# ------------------------------------------------------------

# For this dataset, 0 represents no GSI coverage.
# Therefore it is NOT converted into Low susceptibility.

gsi_coverage = (
    gsi != 0
).astype(
    np.uint8
)


# ============================================================
# CHECK GRID COMPATIBILITY
# ============================================================

print("\n=== GRID CHECK ===")

with rasterio.open(GSI) as src:

    if src.crs != reference_crs:
        raise ValueError(
            "GSI CRS does not match reference CRS."
        )

    if src.width != width or src.height != height:
        raise ValueError(
            "GSI dimensions do not match reference grid."
        )

    if src.transform != transform:
        raise ValueError(
            "GSI transform does not match reference grid."
        )

    if src.bounds != reference_bounds:
        raise ValueError(
            "GSI bounds do not match reference grid."
        )

print(
    "GSI grid: ALIGNED"
)


# ============================================================
# CREATE COORDINATE GRID
# ============================================================

print("\n=== CREATING COORDINATES ===")

rows, cols = np.indices(
    (height, width)
)

xs, ys = rasterio.transform.xy(
    transform,
    rows,
    cols
)

x_coordinates = np.asarray(
    xs,
    dtype=np.float64
).ravel()

y_coordinates = np.asarray(
    ys,
    dtype=np.float64
).ravel()


# ============================================================
# INITIAL FEATURE DATA
# ============================================================

data = {

    "x":
        x_coordinates,

    "y":
        y_coordinates,

    "slope_degrees":
        slope.ravel(),

    "gsi_susceptibility":
        gsi.ravel(),

    "gsi_coverage":
        gsi_coverage.ravel(),
}


# ============================================================
# WORLDCOVER FEATURES
# ============================================================

print("\n=== WORLDCOVER FEATURES ===")

for name, path in FEATURE_FILES.items():

    print(
        "Reading:",
        name
    )

    if not path.exists():

        raise FileNotFoundError(
            f"WorldCover file not found: {path}"
        )

    with rasterio.open(path) as src:

        # Check CRS
        if src.crs != reference_crs:

            raise ValueError(
                f"{name}: CRS mismatch."
            )

        # Check dimensions
        if (
            src.width != width
            or src.height != height
        ):

            raise ValueError(
                f"{name}: dimension mismatch."
            )

        # Check transform
        if src.transform != transform:

            raise ValueError(
                f"{name}: transform mismatch."
            )

        # Check bounds
        if src.bounds != reference_bounds:

            raise ValueError(
                f"{name}: bounds mismatch."
            )

        feature = src.read(1).astype(
            np.float32
        )

    data[name] = feature.ravel()

    print(
        "  Grid: ALIGNED"
    )


# ============================================================
# BUILD DATAFRAME
# ============================================================

print("\n=== BUILDING FEATURE STACK ===")

df = pd.DataFrame(
    data
)


# ============================================================
# BASIC CLEANING
# ============================================================

df = df.replace(
    [np.inf, -np.inf],
    np.nan
)


# ============================================================
# VALIDATE SLOPE
# ============================================================

print("\n=== SLOPE SANITY CHECK ===")

valid_slope = df[
    "slope_degrees"
].dropna()

print(
    "Valid slope pixels:",
    len(valid_slope)
)

print(
    "Missing slope pixels:",
    df["slope_degrees"].isna().sum()
)

print(
    "Slope min:",
    valid_slope.min()
)

print(
    "Slope max:",
    valid_slope.max()
)

print(
    "Slope mean:",
    valid_slope.mean()
)

print(
    "Slope median:",
    valid_slope.median()
)

print(
    "Slope 95th percentile:",
    valid_slope.quantile(0.95)
)


# ============================================================
# VALIDATE GSI
# ============================================================

print("\n=== GSI SANITY CHECK ===")

print(
    "GSI coverage:",
    round(
        df["gsi_coverage"].mean() * 100,
        2
    ),
    "%"
)

print(
    "GSI values:"
)

print(
    df["gsi_susceptibility"]
    .value_counts()
    .sort_index()
)


# ============================================================
# WORLDCOVER SANITY CHECK
# ============================================================

print("\n=== WORLDCOVER SANITY CHECK ===")

worldcover_columns = [

    "tree_cover_fraction",

    "grassland_fraction",

    "cropland_fraction",

    "builtup_fraction",

    "bare_fraction",

    "water_fraction",
]


for column in worldcover_columns:

    values = df[column]

    print(
        f"{column}: "
        f"min={values.min():.4f}, "
        f"max={values.max():.4f}, "
        f"mean={values.mean():.4f}"
    )

    # Fraction values should normally be between 0 and 1.

    if values.min() < 0 or values.max() > 1:

        raise ValueError(
            f"{column} contains values outside 0-1."
        )


# ============================================================
# FEATURE STACK INFORMATION
# ============================================================

print("\n=== FEATURE STACK ===")

print(
    "Rows:",
    len(df)
)

print(
    "Columns:",
    len(df.columns)
)

print(
    "\nColumns:"
)

for column in df.columns:

    print(
        "-",
        column
    )


# ============================================================
# FULL STATISTICS
# ============================================================

print(
    "\n=== FEATURE STATISTICS ==="
)

print(
    df.describe().transpose()
)


# ============================================================
# FINAL VALIDATION
# ============================================================

print(
    "\n=== FINAL VALIDATION ==="
)

expected_rows = (
    width * height
)

if len(df) != expected_rows:

    raise ValueError(
        "Unexpected number of rows."
    )

print(
    "Expected rows:",
    expected_rows
)

print(
    "Actual rows:",
    len(df)
)

print(
    "Row count: PASS"
)

print(
    "Spatial grid: PASS"
)

print(
    "Slope validation: PASS"
)

print(
    "WorldCover validation: PASS"
)


# ============================================================
# SAVE PARQUET
# ============================================================

print(
    "\n=== SAVING FEATURE STACK ==="
)

df.to_parquet(
    OUTPUT,
    index=False
)

print(
    "Saved:",
    OUTPUT
)

print(
    "\nSTATIC FEATURE STACK COMPLETE."
)
