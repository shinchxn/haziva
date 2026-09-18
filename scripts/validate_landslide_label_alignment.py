from pathlib import Path

import numpy as np
import rasterio


REFERENCE = Path(
    "data/processed/terrain/"
    "wayanad_slope_degrees.tif"
)

LABEL = Path(
    "data/processed/landslide/inventory/"
    "wayanad_historical_landslide_presence_30m.tif"
)

STATIC = Path(
    "data/processed/features/"
    "wayanad_static_features.parquet"
)


print("=" * 80)
print("HISTORICAL LANDSLIDE LABEL ALIGNMENT CHECK")
print("=" * 80)


# --------------------------------------------------
# REFERENCE
# --------------------------------------------------

with rasterio.open(REFERENCE) as ref:

    ref_crs = ref.crs
    ref_width = ref.width
    ref_height = ref.height
    ref_transform = ref.transform
    ref_bounds = ref.bounds
    ref_nodata = ref.nodata

    slope = ref.read(1)

    valid_reference = np.isfinite(slope)

    if ref_nodata is not None:
        valid_reference &= slope != ref_nodata


# --------------------------------------------------
# LABEL
# --------------------------------------------------

with rasterio.open(LABEL) as lab:

    label_crs = lab.crs
    label_width = lab.width
    label_height = lab.height
    label_transform = lab.transform
    label_bounds = lab.bounds
    label_nodata = lab.nodata

    labels = lab.read(1)


print()
print("-" * 80)
print("GRID ALIGNMENT")
print("-" * 80)

print("CRS identical:",
      ref_crs == label_crs)

print("Width identical:",
      ref_width == label_width)

print("Height identical:",
      ref_height == label_height)

print(
    "Transform identical:",
    ref_transform == label_transform
)

print(
    "Bounds identical:",
    ref_bounds == label_bounds
)


# --------------------------------------------------
# LABEL VALUES
# --------------------------------------------------

unique, counts = np.unique(
    labels,
    return_counts=True
)

print()
print("-" * 80)
print("LABEL VALUES")
print("-" * 80)

for value, count in zip(unique, counts):

    print(
        f"Value {value}: {count:,} pixels"
    )


# --------------------------------------------------
# VALID REFERENCE CELLS
# --------------------------------------------------

positive = (
    labels == 1
) & valid_reference

negative = (
    labels == 0
) & valid_reference

positive_count = int(
    positive.sum()
)

negative_count = int(
    negative.sum()
)

valid_count = positive_count + negative_count


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
    f"Valid:    {valid_count:,}"
)

if valid_count > 0:

    print(
        f"Positive %: "
        f"{100 * positive_count / valid_count:.4f}%"
    )

    print(
        f"Negative %: "
        f"{100 * negative_count / valid_count:.4f}%"
    )


# --------------------------------------------------
# STATIC PARQUET
# --------------------------------------------------

print()
print("-" * 80)
print("STATIC FEATURE TABLE")
print("-" * 80)

try:

    import pandas as pd

    df = pd.read_parquet(STATIC)

    print(
        f"Rows:    {len(df):,}"
    )

    print(
        f"Columns: {len(df.columns)}"
    )

    print(
        "Columns:",
        ", ".join(df.columns)
    )

    expected_rows = ref_width * ref_height

    print(
        f"Expected raster cells: "
        f"{expected_rows:,}"
    )

    print(
        "Row count matches raster:",
        len(df) == expected_rows
    )

except Exception as e:

    print(
        "Could not inspect parquet:"
    )

    print(e)


# --------------------------------------------------
# FINAL VERDICT
# --------------------------------------------------

alignment_ok = (
    ref_crs == label_crs
    and ref_width == label_width
    and ref_height == label_height
    and ref_transform == label_transform
    and ref_bounds == label_bounds
)

print()
print("=" * 80)

if alignment_ok:

    print(
        "ALIGNMENT STATUS: PASS"
    )

else:

    print(
        "ALIGNMENT STATUS: FAIL"
    )

print("=" * 80)