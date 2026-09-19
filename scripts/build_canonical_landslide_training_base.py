from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

STATIC_FEATURES = (
    ROOT
    / "data"
    / "processed"
    / "features"
    / "wayanad_static_features.parquet"
)

HISTORICAL_PROVENANCE = (
    ROOT
    / "data"
    / "processed"
    / "landslide"
    / "inventory"
    / "wayanad_historical_landslide_provenance_copernicus_30m.parquet"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "features"
)

OUTPUT_DATASET = (
    OUTPUT_DIR
    / "wayanad_landslide_training_base.parquet"
)

OUTPUT_SUMMARY = (
    OUTPUT_DIR
    / "wayanad_landslide_training_base_summary.csv"
)


# ============================================================
# EXPECTED SCHEMA
# ============================================================

EXPECTED_STATIC_COLUMNS = [
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

EXPECTED_PROVENANCE_COLUMNS = [
    "row",
    "col",
    "x",
    "y",
    "bhuvan_evidence",
    "gsi_evidence",
    "historical_landslide",
    "evidence_source",
]

OUTPUT_COLUMNS = [
    "row",
    "col",
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
    "bhuvan_evidence",
    "gsi_evidence",
    "historical_landslide",
    "evidence_source",
]


# ============================================================
# HELPERS
# ============================================================

def print_header(title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def validate_file(path, description):
    if not path.exists():
        raise FileNotFoundError(
            f"{description} not found:\n{path}"
        )


def validate_columns(df, expected, dataset_name):
    missing = [
        column
        for column in expected
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{dataset_name} is missing columns: {missing}"
        )


# ============================================================
# LOAD STATIC FEATURES
# ============================================================

def load_static_features():
    print_header("LOADING STATIC FEATURE MATRIX")

    validate_file(
        STATIC_FEATURES,
        "Static feature matrix",
    )

    df = pd.read_parquet(STATIC_FEATURES)

    print(f"Path: {STATIC_FEATURES}")
    print(f"Shape: {df.shape}")

    validate_columns(
        df,
        EXPECTED_STATIC_COLUMNS,
        "Static feature matrix",
    )

    # The current static matrix was generated from the canonical
    # Copernicus 30 m grid and therefore contains x/y but not row/col.
    #
    # We derive row/col from the fact that the matrix's ordering
    # follows the canonical raster's valid-cell extraction.
    #
    # To avoid relying on ordering assumptions, row/col will be
    # reconstructed from x/y only after validating the coordinate
    # grid against the canonical raster transform.

    return df


# ============================================================
# LOAD PROVENANCE
# ============================================================

def load_provenance():
    print_header("LOADING HISTORICAL LANDSLIDE PROVENANCE")

    validate_file(
        HISTORICAL_PROVENANCE,
        "Historical landslide provenance table",
    )

    df = pd.read_parquet(HISTORICAL_PROVENANCE)

    print(f"Path: {HISTORICAL_PROVENANCE}")
    print(f"Shape: {df.shape}")

    validate_columns(
        df,
        EXPECTED_PROVENANCE_COLUMNS,
        "Historical provenance table",
    )

    return df


# ============================================================
# VALIDATE PROVENANCE
# ============================================================

def validate_provenance(df):
    print_header("VALIDATING PROVENANCE TABLE")

    # --------------------------------------------------------
    # Duplicate cells
    # --------------------------------------------------------

    duplicate_count = int(
        df.duplicated(
            subset=["row", "col"]
        ).sum()
    )

    print(
        f"Duplicate row/col cells: {duplicate_count:,}"
    )

    if duplicate_count != 0:
        raise ValueError(
            "Historical provenance contains duplicate "
            "(row, col) cells."
        )

    # --------------------------------------------------------
    # Binary fields
    # --------------------------------------------------------

    binary_columns = [
        "bhuvan_evidence",
        "gsi_evidence",
        "historical_landslide",
    ]

    for column in binary_columns:
        values = set(
            df[column]
            .dropna()
            .astype(int)
            .unique()
        )

        print(
            f"{column} unique values: {sorted(values)}"
        )

        if not values.issubset({0, 1}):
            raise ValueError(
                f"{column} contains values other than 0/1: "
                f"{values}"
            )

    # --------------------------------------------------------
    # Evidence consistency
    # --------------------------------------------------------

    expected_label = (
        (
            df["bhuvan_evidence"] == 1
        )
        |
        (
            df["gsi_evidence"] == 1
        )
    ).astype(np.uint8)

    actual_label = (
        df["historical_landslide"]
        .astype(np.uint8)
    )

    mismatch = int(
        (expected_label != actual_label).sum()
    )

    print(
        f"Historical-label mismatches: {mismatch:,}"
    )

    if mismatch != 0:
        raise ValueError(
            "historical_landslide is inconsistent with "
            "Bhuvan/GSI evidence."
        )

    # --------------------------------------------------------
    # Evidence-source consistency
    # --------------------------------------------------------

    expected_source = np.full(
        len(df),
        "NONE",
        dtype=object,
    )

    bhuvan = df["bhuvan_evidence"].eq(1)
    gsi = df["gsi_evidence"].eq(1)

    expected_source[bhuvan & ~gsi] = "BHUVAN"
    expected_source[~bhuvan & gsi] = "GSI"
    expected_source[bhuvan & gsi] = "BOTH"

    source_mismatch = int(
        (
            df["evidence_source"].astype(str)
            != expected_source
        ).sum()
    )

    print(
        f"Evidence-source mismatches: "
        f"{source_mismatch:,}"
    )

    if source_mismatch != 0:
        raise ValueError(
            "evidence_source is inconsistent with "
            "Bhuvan/GSI evidence."
        )

    print("Provenance validation: PASSED")


# ============================================================
# VALIDATE STATIC FEATURES
# ============================================================

def validate_static_features(df):
    print_header("VALIDATING STATIC FEATURES")

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    missing = df[EXPECTED_STATIC_COLUMNS].isna().sum()

    missing_total = int(
        missing.sum()
    )

    print(
        f"Total missing feature values: "
        f"{missing_total:,}"
    )

    if missing_total != 0:
        print("\nMissing values by column:")
        print(
            missing[
                missing > 0
            ].to_string()
        )

        raise ValueError(
            "Static feature matrix contains missing values."
        )

    # --------------------------------------------------------
    # Coordinate validity
    # --------------------------------------------------------

    if not np.isfinite(
        df["x"].to_numpy()
    ).all():
        raise ValueError(
            "Static x coordinates contain non-finite values."
        )

    if not np.isfinite(
        df["y"].to_numpy()
    ).all():
        raise ValueError(
            "Static y coordinates contain non-finite values."
        )

    # --------------------------------------------------------
    # GSI
    # --------------------------------------------------------

    gsi_values = set(
        df["gsi_susceptibility"]
        .astype(int)
        .unique()
    )

    print(
        f"GSI susceptibility classes: "
        f"{sorted(gsi_values)}"
    )

    if not gsi_values.issubset({0, 1, 2, 3}):
        raise ValueError(
            "Unexpected GSI susceptibility class."
        )

    # --------------------------------------------------------
    # GSI coverage
    # --------------------------------------------------------

    coverage_values = set(
        df["gsi_coverage"]
        .astype(int)
        .unique()
    )

    print(
        f"GSI coverage values: "
        f"{sorted(coverage_values)}"
    )

    if not coverage_values.issubset({0, 1}):
        raise ValueError(
            "GSI coverage contains values other than 0/1."
        )

    # --------------------------------------------------------
    # WorldCover fractions
    # --------------------------------------------------------

    fraction_columns = [
        "tree_fraction",
        "shrub_fraction",
        "grass_fraction",
        "crop_fraction",
        "builtup_fraction",
        "bare_fraction",
        "water_fraction",
        "wetland_fraction",
    ]

    fractions = df[fraction_columns]

    fraction_array = fractions.to_numpy(
        dtype=np.float64
    )

    if not np.isfinite(
        fraction_array
    ).all():
        raise ValueError(
            "WorldCover fractions contain non-finite values."
        )

    fraction_min = float(
        fraction_array.min()
    )

    fraction_max = float(
        fraction_array.max()
    )

    print(
        f"WorldCover fraction minimum: "
        f"{fraction_min}"
    )

    print(
        f"WorldCover fraction maximum: "
        f"{fraction_max}"
    )

    if fraction_min < -1e-6:
        raise ValueError(
            "WorldCover fraction below zero."
        )

    if fraction_max > 1.000001:
        raise ValueError(
            "WorldCover fraction above one."
        )

    fraction_sum = fractions.sum(axis=1)

    print(
        f"Fraction-sum minimum: "
        f"{fraction_sum.min()}"
    )

    print(
        f"Fraction-sum maximum: "
        f"{fraction_sum.max()}"
    )

    if not np.allclose(
        fraction_sum.to_numpy(),
        1.0,
        atol=1e-4,
    ):
        raise ValueError(
            "WorldCover fractions do not sum to approximately 1."
        )

    # --------------------------------------------------------
    # Slope
    # --------------------------------------------------------

    slope = df["slope_degrees"]

    if not np.isfinite(
        slope.to_numpy()
    ).all():
        raise ValueError(
            "Slope contains non-finite values."
        )

    if (slope < 0).any():
        raise ValueError(
            "Slope contains negative values."
        )

    print(
        f"Slope range: "
        f"{slope.min():.4f} - {slope.max():.4f} degrees"
    )

    print("Static-feature validation: PASSED")


# ============================================================
# MATCH STATIC COORDINATES TO PROVENANCE
# ============================================================

def validate_coordinate_alignment(
    static_df,
    provenance_df,
):
    print_header("VALIDATING SPATIAL ALIGNMENT")

    if len(static_df) != len(provenance_df):
        raise ValueError(
            "Static feature and provenance datasets have "
            "different row counts."
        )

    print(
        f"Static rows: {len(static_df):,}"
    )

    print(
        f"Provenance rows: {len(provenance_df):,}"
    )

    # Both datasets should represent exactly the same set
    # of canonical cells.
    #
    # Sort copies by coordinate and compare x/y.
    static_sorted = (
        static_df[["x", "y"]]
        .sort_values(["y", "x"])
        .reset_index(drop=True)
    )

    provenance_sorted = (
        provenance_df[["x", "y"]]
        .sort_values(["y", "x"])
        .reset_index(drop=True)
    )

    x_difference = np.abs(
        static_sorted["x"].to_numpy()
        -
        provenance_sorted["x"].to_numpy()
    )

    y_difference = np.abs(
        static_sorted["y"].to_numpy()
        -
        provenance_sorted["y"].to_numpy()
    )

    max_x_difference = float(
        x_difference.max()
    )

    max_y_difference = float(
        y_difference.max()
    )

    print(
        f"Maximum X coordinate difference: "
        f"{max_x_difference}"
    )

    print(
        f"Maximum Y coordinate difference: "
        f"{max_y_difference}"
    )

    # Same raster-derived coordinates should match essentially
    # exactly.
    tolerance = 1e-6

    if max_x_difference > tolerance:
        raise ValueError(
            "Static and provenance X coordinates do not align."
        )

    if max_y_difference > tolerance:
        raise ValueError(
            "Static and provenance Y coordinates do not align."
        )

    print(
        "Coordinate alignment: PASSED"
    )


# ============================================================
# BUILD TRAINING BASE
# ============================================================

def build_training_base(
    static_df,
    provenance_df,
):
    print_header("BUILDING CANONICAL TRAINING BASE")

    # --------------------------------------------------------
    # Validate coordinate alignment first.
    # --------------------------------------------------------

    validate_coordinate_alignment(
        static_df,
        provenance_df,
    )

    # --------------------------------------------------------
    # Add canonical row/col information to the static matrix.
    #
    # The provenance table contains the canonical raster
    # row/col. We assign them after sorting both datasets by
    # their exact raster-derived center coordinates.
    # --------------------------------------------------------

    static_sorted = (
        static_df
        .sort_values(["y", "x"])
        .reset_index(drop=True)
    )

    provenance_sorted = (
        provenance_df
        .sort_values(["y", "x"])
        .reset_index(drop=True)
    )

    # Verify exact coordinate correspondence again.
    if not np.allclose(
        static_sorted["x"].to_numpy(),
        provenance_sorted["x"].to_numpy(),
        atol=1e-6,
    ):
        raise ValueError(
            "X coordinates do not match during join."
        )

    if not np.allclose(
        static_sorted["y"].to_numpy(),
        provenance_sorted["y"].to_numpy(),
        atol=1e-6,
    ):
        raise ValueError(
            "Y coordinates do not match during join."
        )

    # --------------------------------------------------------
    # Build output.
    # --------------------------------------------------------

    output = static_sorted.copy()

    output.insert(
        0,
        "row",
        provenance_sorted["row"].to_numpy(
            dtype=np.int32
        ),
    )

    output.insert(
        1,
        "col",
        provenance_sorted["col"].to_numpy(
            dtype=np.int32
        ),
    )

    output["bhuvan_evidence"] = (
        provenance_sorted["bhuvan_evidence"]
        .to_numpy(dtype=np.uint8)
    )

    output["gsi_evidence"] = (
        provenance_sorted["gsi_evidence"]
        .to_numpy(dtype=np.uint8)
    )

    output["historical_landslide"] = (
        provenance_sorted["historical_landslide"]
        .to_numpy(dtype=np.uint8)
    )

    output["evidence_source"] = (
        provenance_sorted["evidence_source"]
        .astype(str)
        .to_numpy()
    )

    # --------------------------------------------------------
    # Reorder columns.
    # --------------------------------------------------------

    output = output[
        OUTPUT_COLUMNS
    ]

    return output


# ============================================================
# FINAL DATASET QA
# ============================================================

def run_final_qa(df):
    print_header("FINAL TRAINING-BASE QA")

    # --------------------------------------------------------
    # Row count
    # --------------------------------------------------------

    print(
        f"Rows: {len(df):,}"
    )

    if len(df) != 2_356_650:
        raise ValueError(
            "Unexpected training-base row count. "
            "Expected 2,356,650."
        )

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    missing_columns = [
        column
        for column in OUTPUT_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing output columns: {missing_columns}"
        )

    # --------------------------------------------------------
    # Duplicate cells
    # --------------------------------------------------------

    duplicates = int(
        df.duplicated(
            subset=["row", "col"]
        ).sum()
    )

    print(
        f"Duplicate raster cells: {duplicates:,}"
    )

    if duplicates != 0:
        raise ValueError(
            "Duplicate raster cells detected."
        )

    # --------------------------------------------------------
    # Historical label
    # --------------------------------------------------------

    label_counts = (
        df["historical_landslide"]
        .value_counts()
        .sort_index()
    )

    print("\nHistorical label distribution:")

    for label, count in label_counts.items():
        print(
            f"  {label}: {count:,}"
        )

    if set(label_counts.index).difference({0, 1}):
        raise ValueError(
            "Historical label contains values other than 0/1."
        )

    positive = int(
        (df["historical_landslide"] == 1).sum()
    )

    negative = int(
        (df["historical_landslide"] == 0).sum()
    )

    positive_fraction = (
        positive / len(df)
    )

    print(
        f"\nPositive fraction: "
        f"{positive_fraction:.6%}"
    )

    print(
        f"Background fraction: "
        f"{negative / len(df):.6%}"
    )

    # --------------------------------------------------------
    # Evidence sources
    # --------------------------------------------------------

    print("\nEvidence source distribution:")

    print(
        df["evidence_source"]
        .value_counts()
        .to_string()
    )

    # --------------------------------------------------------
    # Evidence consistency
    # --------------------------------------------------------

    expected_label = (
        (
            df["bhuvan_evidence"] == 1
        )
        |
        (
            df["gsi_evidence"] == 1
        )
    ).astype(np.uint8)

    if not np.array_equal(
        expected_label.to_numpy(),
        df["historical_landslide"]
        .to_numpy(),
    ):
        raise ValueError(
            "Final historical label is inconsistent "
            "with evidence columns."
        )

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    missing_total = int(
        df[OUTPUT_COLUMNS]
        .isna()
        .sum()
        .sum()
    )

    print(
        f"\nMissing values: {missing_total:,}"
    )

    if missing_total != 0:
        raise ValueError(
            "Training base contains missing values."
        )

    # --------------------------------------------------------
    # Coordinate validity
    # --------------------------------------------------------

    if not np.isfinite(
        df["x"].to_numpy()
    ).all():
        raise ValueError(
            "X contains non-finite values."
        )

    if not np.isfinite(
        df["y"].to_numpy()
    ).all():
        raise ValueError(
            "Y contains non-finite values."
        )

    # --------------------------------------------------------
    # Print feature summary
    # --------------------------------------------------------

    print("\nNumeric feature summary:")

    numeric_columns = [
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

    print(
        df[numeric_columns]
        .describe()
        .transpose()
        .to_string()
    )

    print("\nALL FINAL QA CHECKS PASSED")


# ============================================================
# WRITE SUMMARY
# ============================================================

def write_summary(df):
    print_header("WRITING DATASET SUMMARY")

    positive = int(
        (df["historical_landslide"] == 1).sum()
    )

    negative = int(
        (df["historical_landslide"] == 0).sum()
    )

    summary = pd.DataFrame(
        [
            {
                "metric": "total_cells",
                "value": len(df),
            },
            {
                "metric": "positive_historical_cells",
                "value": positive,
            },
            {
                "metric": "background_cells",
                "value": negative,
            },
            {
                "metric": "positive_fraction",
                "value": positive / len(df),
            },
            {
                "metric": "bhuvan_cells",
                "value": int(
                    (df["bhuvan_evidence"] == 1).sum()
                ),
            },
            {
                "metric": "gsi_cells",
                "value": int(
                    (df["gsi_evidence"] == 1).sum()
                ),
            },
            {
                "metric": "both_source_cells",
                "value": int(
                    (
                        (df["bhuvan_evidence"] == 1)
                        &
                        (df["gsi_evidence"] == 1)
                    ).sum()
                ),
            },
        ]
    )

    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
    )

    print(
        summary.to_string(index=False)
    )

    print(
        f"\nSummary written to:"
        f"\n{OUTPUT_SUMMARY}"
    )


# ============================================================
# MAIN
# ============================================================

def main():
    print_header(
        "WAYANAD CANONICAL LANDSLIDE TRAINING BASE BUILDER"
    )

    print(
        "This script joins the validated static feature matrix "
        "with the canonical historical landslide provenance."
    )

    print(
        "\nIt does NOT modify:"
    )

    print(
        "  - Copernicus slope"
    )
    print(
        "  - GSI susceptibility"
    )
    print(
        "  - WorldCover fractions"
    )
    print(
        "  - Historical inventory"
    )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    static_df = load_static_features()

    provenance_df = load_provenance()

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validate_static_features(
        static_df
    )

    validate_provenance(
        provenance_df
    )

    # --------------------------------------------------------
    # Build
    # --------------------------------------------------------

    training_df = build_training_base(
        static_df,
        provenance_df,
    )

    # --------------------------------------------------------
    # QA
    # --------------------------------------------------------

    run_final_qa(
        training_df
    )

    # --------------------------------------------------------
    # Write
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    training_df.to_parquet(
        OUTPUT_DATASET,
        index=False,
    )

    print_header(
        "TRAINING BASE WRITTEN"
    )

    print(
        f"Output: {OUTPUT_DATASET}"
    )

    print(
        f"Size: {OUTPUT_DATASET.stat().st_size:,} bytes"
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    write_summary(
        training_df
    )

    print_header(
        "COMPLETE"
    )

    print(
        "Canonical spatial ML training base created "
        "successfully."
    )

    print(
        "\nNext stage:"
    )

    print(
        "Construct the temporal rainfall/event dataset."
    )


if __name__ == "__main__":
    main()