from pathlib import Path

import numpy as np
import pandas as pd
import rasterio


# ============================================================
# WAYANAD STATIC FEATURE MATRIX
# ============================================================
#
# Purpose:
# Build one tabular feature matrix from the three already
# validated 30 m spatial datasets:
#
# 1. Copernicus GLO-30 derived slope
# 2. GSI landslide susceptibility aligned to Copernicus grid
# 3. ESA WorldCover 30 m land-cover fractions
#
# One row = one valid 30 m spatial cell.
#
# IMPORTANT:
# GSI value meaning:
#   0 = No GSI coverage
#   1 = Low
#   2 = Moderate
#   3 = High
#
# gsi_coverage explicitly indicates whether GSI information
# exists for that cell.
#
# WorldCover bands are fractions and must sum to ~1.0.
# ============================================================


# ============================================================
# INPUT FILES
# ============================================================

SLOPE_RASTER = Path(
    "data/processed/terrain/"
    "wayanad_copernicus_slope_degrees.tif"
)

GSI_RASTER = Path(
    "data/processed/landslide/susceptibility/"
    "wayanad_gsi_susceptibility_copernicus_30m.tif"
)

WORLDCOVER_RASTER = Path(
    "data/processed/exposure/worldcover/"
    "wayanad_worldcover_30m_fractions.tif"
)


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_DIR = Path(
    "data/processed/features"
)

OUTPUT_FILE = (
    OUTPUT_DIR /
    "wayanad_static_features.parquet"
)


# ============================================================
# WORLDCOVER BAND NAMES
# ============================================================

WORLDCOVER_BANDS = [
    "tree_fraction",
    "shrub_fraction",
    "grass_fraction",
    "crop_fraction",
    "builtup_fraction",
    "bare_fraction",
    "water_fraction",
    "wetland_fraction",
]


# ============================================================
# GRID VALIDATION
# ============================================================

def validate_same_grid(
    reference_crs,
    reference_transform,
    reference_width,
    reference_height,
    dataset,
    dataset_name,
):
    """
    Verify that a raster uses exactly the same spatial grid
    as the canonical Copernicus slope raster.
    """

    if dataset.crs != reference_crs:
        raise ValueError(
            f"{dataset_name} CRS mismatch.\n"
            f"Reference: {reference_crs}\n"
            f"{dataset_name}: {dataset.crs}"
        )

    if dataset.width != reference_width:
        raise ValueError(
            f"{dataset_name} width mismatch.\n"
            f"Reference: {reference_width}\n"
            f"{dataset_name}: {dataset.width}"
        )

    if dataset.height != reference_height:
        raise ValueError(
            f"{dataset_name} height mismatch.\n"
            f"Reference: {reference_height}\n"
            f"{dataset_name}: {dataset.height}"
        )

    if not np.allclose(
        dataset.transform,
        reference_transform,
        atol=1e-6,
    ):
        raise ValueError(
            f"{dataset_name} transform mismatch."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print("WAYANAD STATIC FEATURE MATRIX")
    print("=" * 72)

    # --------------------------------------------------------
    # Check input files
    # --------------------------------------------------------

    print("\nChecking input files...")

    input_files = [
        SLOPE_RASTER,
        GSI_RASTER,
        WORLDCOVER_RASTER,
    ]

    for path in input_files:

        if not path.exists():
            raise FileNotFoundError(
                f"Required input file not found:\n{path}"
            )

        print(f"  OK: {path}")

    # --------------------------------------------------------
    # 1. Read canonical Copernicus slope
    # --------------------------------------------------------

    print("\n" + "-" * 72)
    print("[1/6] Reading canonical Copernicus slope")
    print("-" * 72)

    with rasterio.open(SLOPE_RASTER) as slope_src:

        slope = slope_src.read(1)

        reference_crs = slope_src.crs
        reference_transform = slope_src.transform

        reference_width = slope_src.width
        reference_height = slope_src.height

        reference_bounds = slope_src.bounds
        reference_res = slope_src.res

        slope_nodata = slope_src.nodata

    print(f"CRS:         {reference_crs}")
    print(
        f"Shape:       "
        f"{reference_height} x {reference_width}"
    )
    print(f"Resolution:  {reference_res}")
    print(f"Bounds:      {reference_bounds}")
    print(f"Nodata:      {slope_nodata}")

    print(
        f"Slope array memory: "
        f"{slope.nbytes / (1024 ** 2):.2f} MB"
    )

    # --------------------------------------------------------
    # 2. Read aligned GSI
    # --------------------------------------------------------

    print("\n" + "-" * 72)
    print("[2/6] Reading aligned GSI susceptibility")
    print("-" * 72)

    with rasterio.open(GSI_RASTER) as gsi_src:

        validate_same_grid(
            reference_crs=reference_crs,
            reference_transform=reference_transform,
            reference_width=reference_width,
            reference_height=reference_height,
            dataset=gsi_src,
            dataset_name="GSI",
        )

        gsi = gsi_src.read(1)

        gsi_nodata = gsi_src.nodata

    print("GSI grid validation: PASSED")
    print(f"GSI nodata: {gsi_nodata}")

    gsi_values, gsi_counts = np.unique(
        gsi,
        return_counts=True,
    )

    print("\nGSI classes:")

    gsi_labels = {
        0: "No GSI coverage",
        1: "Low",
        2: "Moderate",
        3: "High",
    }

    for value, count in zip(
        gsi_values,
        gsi_counts,
    ):

        value_int = int(value)

        print(
            f"  {value_int} = "
            f"{gsi_labels.get(value_int, 'UNKNOWN')}: "
            f"{int(count):,}"
        )

    allowed_gsi_values = {0, 1, 2, 3}

    actual_gsi_values = {
        int(value)
        for value in gsi_values
    }

    unexpected_gsi_values = (
        actual_gsi_values - allowed_gsi_values
    )

    if unexpected_gsi_values:

        raise ValueError(
            "Unexpected GSI values found: "
            f"{unexpected_gsi_values}"
        )

    # --------------------------------------------------------
    # 3. Read WorldCover fractions
    # --------------------------------------------------------

    print("\n" + "-" * 72)
    print("[3/6] Reading WorldCover 30 m fractions")
    print("-" * 72)

    with rasterio.open(WORLDCOVER_RASTER) as wc_src:

        validate_same_grid(
            reference_crs=reference_crs,
            reference_transform=reference_transform,
            reference_width=reference_width,
            reference_height=reference_height,
            dataset=wc_src,
            dataset_name="WorldCover",
        )

        worldcover = wc_src.read()

        worldcover_nodata = wc_src.nodata

        worldcover_descriptions = (
            wc_src.descriptions
        )

    print("WorldCover grid validation: PASSED")

    print(
        f"WorldCover bands: "
        f"{worldcover.shape[0]}"
    )

    print(
        f"WorldCover shape: "
        f"{worldcover.shape[1]} x "
        f"{worldcover.shape[2]}"
    )

    if worldcover.shape[0] != 8:

        raise ValueError(
            "Expected exactly 8 WorldCover bands, "
            f"found {worldcover.shape[0]}."
        )

    print("\nWorldCover descriptions:")

    for index, description in enumerate(
        worldcover_descriptions,
        start=1,
    ):

        print(
            f"  Band {index}: {description}"
        )

    # --------------------------------------------------------
    # 4. Build valid-cell mask
    # --------------------------------------------------------

    print("\n" + "-" * 72)
    print("[4/6] Building valid spatial-cell mask")
    print("-" * 72)

    valid = np.ones(
        (
            reference_height,
            reference_width,
        ),
        dtype=bool,
    )

    # Slope validity

    if slope_nodata is not None:

        valid &= (
            slope != slope_nodata
        )

    # WorldCover validity

    if worldcover_nodata is not None:

        valid &= (
            worldcover[0] != worldcover_nodata
        )

    valid_cell_count = int(
        valid.sum()
    )

    total_cell_count = (
        reference_height *
        reference_width
    )

    invalid_cell_count = (
        total_cell_count -
        valid_cell_count
    )

    print(
        f"Total raster cells:   "
        f"{total_cell_count:,}"
    )

    print(
        f"Valid cells:          "
        f"{valid_cell_count:,}"
    )

    print(
        f"Invalid cells:        "
        f"{invalid_cell_count:,}"
    )

    if valid_cell_count == 0:

        raise ValueError(
            "No valid cells found."
        )

    # --------------------------------------------------------
    # Get row/column indexes
    # --------------------------------------------------------

    rows, cols = np.where(valid)

    # --------------------------------------------------------
    # Convert pixel positions to projected coordinates
    # --------------------------------------------------------

    xs, ys = rasterio.transform.xy(
        reference_transform,
        rows,
        cols,
        offset="center",
    )

    xs = np.asarray(
        xs,
        dtype=np.float64,
    )

    ys = np.asarray(
        ys,
        dtype=np.float64,
    )

    # --------------------------------------------------------
    # 5. Construct feature matrix
    # --------------------------------------------------------

    print("\n" + "-" * 72)
    print("[5/6] Constructing feature matrix")
    print("-" * 72)

    data = {
        "x": xs,

        "y": ys,

        "slope_degrees": (
            slope[rows, cols]
            .astype(np.float32)
        ),

        "gsi_susceptibility": (
            gsi[rows, cols]
            .astype(np.uint8)
        ),

        "gsi_coverage": (
            gsi[rows, cols] > 0
        ).astype(np.uint8),
    }

    # Add all eight WorldCover fractions.

    for band_index, band_name in enumerate(
        WORLDCOVER_BANDS
    ):

        data[band_name] = (
            worldcover[
                band_index,
                rows,
                cols,
            ]
            .astype(np.float32)
        )

    df = pd.DataFrame(data)

    print(
        f"Rows created:    {len(df):,}"
    )

    print(
        f"Columns created: {len(df.columns)}"
    )

    # --------------------------------------------------------
    # Expected columns
    # --------------------------------------------------------

    expected_columns = [
        "x",
        "y",
        "slope_degrees",
        "gsi_susceptibility",
        "gsi_coverage",
        "tree_fraction",
        "shrub_fraction",
        "grass_fraction",
        "crop_fraction",
        "builtup_fraction",
        "bare_fraction",
        "water_fraction",
        "wetland_fraction",
    ]

    if list(df.columns) != expected_columns:

        raise ValueError(
            "Feature columns do not match expected schema.\n"
            f"Expected:\n{expected_columns}\n"
            f"Actual:\n{list(df.columns)}"
        )

    # --------------------------------------------------------
    # 6. Feature QA
    # --------------------------------------------------------

    print("\n" + "-" * 72)
    print("[6/6] Running feature QA")
    print("-" * 72)

    # --------------------------------------------------------
    # Coordinate QA
    # --------------------------------------------------------

    if not np.all(
        np.isfinite(df["x"].to_numpy())
    ):

        raise ValueError(
            "Non-finite X coordinate found."
        )

    if not np.all(
        np.isfinite(df["y"].to_numpy())
    ):

        raise ValueError(
            "Non-finite Y coordinate found."
        )

    print("Coordinate QA: PASSED")

    # --------------------------------------------------------
    # Slope QA
    # --------------------------------------------------------

    slope_values = (
        df["slope_degrees"]
        .to_numpy(dtype=np.float64)
    )

    if not np.all(
        np.isfinite(slope_values)
    ):

        raise ValueError(
            "Non-finite slope values found."
        )

    if np.any(
        slope_values < 0
    ):

        raise ValueError(
            "Negative slope values found."
        )

    print("Slope QA: PASSED")

    print(
        f"  Min:  {slope_values.min():.4f}"
    )

    print(
        f"  Max:  {slope_values.max():.4f}"
    )

    print(
        f"  Mean: {slope_values.mean():.4f}"
    )

    # --------------------------------------------------------
    # GSI QA
    # --------------------------------------------------------

    gsi_values_df = (
        df["gsi_susceptibility"]
        .to_numpy(dtype=np.uint8)
    )

    gsi_coverage_df = (
        df["gsi_coverage"]
        .to_numpy(dtype=np.uint8)
    )

    expected_gsi_coverage = (
        gsi_values_df > 0
    ).astype(np.uint8)

    if not np.array_equal(
        gsi_coverage_df,
        expected_gsi_coverage,
    ):

        raise ValueError(
            "gsi_coverage does not match "
            "gsi_susceptibility."
        )

    print("GSI QA: PASSED")

    # --------------------------------------------------------
    # WorldCover QA
    # --------------------------------------------------------

    fraction_array = (
        df[WORLDCOVER_BANDS]
        .to_numpy(dtype=np.float64)
    )

    if not np.all(
        np.isfinite(fraction_array)
    ):

        raise ValueError(
            "Non-finite WorldCover fraction found."
        )

    if np.any(
        fraction_array < -1e-6
    ):

        raise ValueError(
            "Negative WorldCover fraction found."
        )

    if np.any(
        fraction_array > 1.000001
    ):

        raise ValueError(
            "WorldCover fraction greater than 1 found."
        )

    fraction_sum = (
        fraction_array.sum(axis=1)
    )

    if not np.allclose(
        fraction_sum,
        1.0,
        atol=1e-5,
    ):

        raise ValueError(
            "WorldCover fractions do not sum "
            "to approximately 1."
        )

    print("WorldCover QA: PASSED")

    print(
        f"  Sum min:  {fraction_sum.min():.8f}"
    )

    print(
        f"  Sum max:  {fraction_sum.max():.8f}"
    )

    print(
        f"  Sum mean: {fraction_sum.mean():.8f}"
    )

    # --------------------------------------------------------
    # Missing-value QA
    # --------------------------------------------------------

    missing_counts = (
        df.isna()
        .sum()
    )

    total_missing = int(
        missing_counts.sum()
    )

    if total_missing != 0:

        print("\nMissing values:")

        print(
            missing_counts[
                missing_counts > 0
            ]
        )

        raise ValueError(
            "Missing values detected."
        )

    print("Missing-value QA: PASSED")

    # --------------------------------------------------------
    # Save Parquet
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------------
    # Final report
    # --------------------------------------------------------

    print("\n" + "=" * 72)
    print("STATIC FEATURE MATRIX CREATED SUCCESSFULLY")
    print("=" * 72)

    print("\nOutput:")
    print(OUTPUT_FILE)

    print(
        f"\nRows:    {len(df):,}"
    )

    print(
        f"Columns: {len(df.columns)}"
    )

    print("\nFeature schema:")

    for column in df.columns:

        print(
            f"  {column:<22} "
            f"{df[column].dtype}"
        )

    print("\nGSI distribution:")

    gsi_distribution = (
        df["gsi_susceptibility"]
        .value_counts()
        .sort_index()
    )

    for value, count in (
        gsi_distribution.items()
    ):

        label = gsi_labels.get(
            int(value),
            "UNKNOWN",
        )

        print(
            f"  {int(value)} = "
            f"{label:<18} "
            f"{int(count):,}"
        )

    print("\nGSI coverage:")

    coverage_distribution = (
        df["gsi_coverage"]
        .value_counts()
        .sort_index()
    )

    for value, count in (
        coverage_distribution.items()
    ):

        label = (
            "No coverage"
            if int(value) == 0
            else "Coverage"
        )

        print(
            f"  {int(value)} = "
            f"{label:<15} "
            f"{int(count):,}"
        )

    print("\nWorldCover fraction QA:")

    print(
        f"  Minimum sum: "
        f"{fraction_sum.min():.8f}"
    )

    print(
        f"  Maximum sum: "
        f"{fraction_sum.max():.8f}"
    )

    print(
        f"  Mean sum:    "
        f"{fraction_sum.mean():.8f}"
    )

    print("\nAll QA checks: PASSED")

    print("\nNext dataset:")
    print(
        "Historical landslide event/label dataset"
    )

    print("\n" + "=" * 72)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()