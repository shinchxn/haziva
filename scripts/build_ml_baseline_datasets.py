from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# WAYANAD ML BASELINE DATASET BUILDER
# ============================================================
#
# Creates two controlled ML datasets:
#
# MODEL A
#   slope
#   + WorldCover fractions
#   + GSI susceptibility
#
# MODEL B
#   slope
#   + WorldCover fractions
#   - GSI susceptibility
#
# Both models use the SAME spatial train/validation/test split.
#
# ============================================================


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

TRAINING_BASE = (
    ROOT
    / "data"
    / "processed"
    / "features"
    / "wayanad_landslide_training_base.parquet"
)

SPATIAL_SPLIT = (
    ROOT
    / "data"
    / "processed"
    / "features"
    / "wayanad_spatial_train_test_split.parquet"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "features"
)

MODEL_A_OUTPUT = (
    OUTPUT_DIR
    / "wayanad_ml_baseline_with_gsi.parquet"
)

MODEL_B_OUTPUT = (
    OUTPUT_DIR
    / "wayanad_ml_baseline_without_gsi.parquet"
)

SUMMARY_OUTPUT = (
    OUTPUT_DIR
    / "wayanad_ml_baseline_dataset_summary.csv"
)


# ============================================================
# FEATURES
# ============================================================

WORLD_COVER_FEATURES = [
    "tree_fraction",
    "shrub_fraction",
    "grass_fraction",
    "crop_fraction",
    "builtup_fraction",
    "bare_fraction",
    "water_fraction",
    "wetland_fraction",
]

GSI_FEATURES = [
    "gsi_susceptibility",
    "gsi_coverage",
]

BASE_FEATURES = [
    "slope_degrees",
] + WORLD_COVER_FEATURES

MODEL_A_FEATURES = (
    BASE_FEATURES
    + GSI_FEATURES
)

MODEL_B_FEATURES = (
    BASE_FEATURES
)

TARGET = "historical_landslide"

KEY_COLUMNS = [
    "row",
    "col",
]


# ============================================================
# HELPER
# ============================================================

def header(title):

    print()
    print("=" * 90)
    print(title)
    print("=" * 90)


# ============================================================
# LOAD TRAINING BASE
# ============================================================

def load_training_base():

    header(
        "LOADING TRAINING BASE"
    )

    if not TRAINING_BASE.exists():

        raise FileNotFoundError(
            f"Training base not found:\n{TRAINING_BASE}"
        )

    df = pd.read_parquet(
        TRAINING_BASE
    )

    print(
        f"Path: {TRAINING_BASE}"
    )

    print(
        f"Shape: {df.shape}"
    )

    required = (
        KEY_COLUMNS
        + [
            "x",
            "y",
            TARGET,
        ]
        + MODEL_A_FEATURES
    )

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Training base is missing columns:\n{missing}"
        )

    # --------------------------------------------------------
    # Duplicate check
    # --------------------------------------------------------

    duplicates = int(
        df.duplicated(
            subset=KEY_COLUMNS
        ).sum()
    )

    print(
        f"Duplicate row/col cells: "
        f"{duplicates:,}"
    )

    if duplicates != 0:

        raise ValueError(
            "Training base contains duplicate cells."
        )

    return df


# ============================================================
# LOAD SPATIAL SPLIT
# ============================================================

def load_spatial_split():

    header(
        "LOADING SPATIAL TRAIN / VALIDATION / TEST SPLIT"
    )

    if not SPATIAL_SPLIT.exists():

        raise FileNotFoundError(
            f"Spatial split not found:\n{SPATIAL_SPLIT}"
        )

    split = pd.read_parquet(
        SPATIAL_SPLIT
    )

    print(
        f"Path: {SPATIAL_SPLIT}"
    )

    print(
        f"Shape: {split.shape}"
    )

    required = [
        "row",
        "col",
        "block_row",
        "block_col",
        "block_id",
        "split",
    ]

    missing = [
        column
        for column in required
        if column not in split.columns
    ]

    if missing:

        raise ValueError(
            f"Spatial split is missing columns:\n{missing}"
        )

    # --------------------------------------------------------
    # Duplicate check
    # --------------------------------------------------------

    duplicates = int(
        split.duplicated(
            subset=KEY_COLUMNS
        ).sum()
    )

    print(
        f"Duplicate split cells: "
        f"{duplicates:,}"
    )

    if duplicates != 0:

        raise ValueError(
            "Spatial split contains duplicate cells."
        )

    # --------------------------------------------------------
    # Split values
    # --------------------------------------------------------

    allowed = {
        "train",
        "validation",
        "test",
    }

    actual = set(
        split[
            "split"
        ].unique()
    )

    print(
        f"Split values: "
        f"{sorted(actual)}"
    )

    if actual != allowed:

        raise ValueError(
            "Spatial split does not contain exactly "
            "train, validation and test."
        )

    return split


# ============================================================
# JOIN DATASETS
# ============================================================

def join_training_and_split(
    training,
    split,
):

    header(
        "JOINING TRAINING FEATURES WITH SPATIAL SPLIT"
    )

    # --------------------------------------------------------
    # Only bring split metadata into the training base.
    # --------------------------------------------------------

    split_columns = [
        "row",
        "col",
        "block_row",
        "block_col",
        "block_id",
        "split",
    ]

    split_lookup = split[
        split_columns
    ].copy()

    merged = training.merge(
        split_lookup,
        on=KEY_COLUMNS,
        how="left",
        validate="one_to_one",
    )

    # --------------------------------------------------------
    # Validate row count.
    # --------------------------------------------------------

    print(
        f"Training rows: "
        f"{len(training):,}"
    )

    print(
        f"Merged rows: "
        f"{len(merged):,}"
    )

    if len(merged) != len(training):

        raise ValueError(
            "Merge changed the training-base row count."
        )

    # --------------------------------------------------------
    # Missing split check.
    # --------------------------------------------------------

    missing_split = int(
        merged[
            "split"
        ]
        .isna()
        .sum()
    )

    print(
        f"Cells without split: "
        f"{missing_split:,}"
    )

    if missing_split != 0:

        raise ValueError(
            "Some training cells did not receive a spatial split."
        )

    # --------------------------------------------------------
    # Split counts.
    # --------------------------------------------------------

    print()

    print(
        "Merged split distribution:"
    )

    print(
        merged[
            "split"
        ]
        .value_counts()
        .to_string()
    )

    return merged


# ============================================================
# VALIDATE FEATURES
# ============================================================

def validate_feature_columns(
    df,
    features,
    model_name,
):

    header(
        f"VALIDATING FEATURES — {model_name}"
    )

    print(
        "Features:"
    )

    for feature in features:

        print(
            f"  - {feature}"
        )

    # --------------------------------------------------------
    # Missing columns.
    # --------------------------------------------------------

    missing = [
        feature
        for feature in features
        if feature not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Missing features for {model_name}: {missing}"
        )

    # --------------------------------------------------------
    # Missing values.
    # --------------------------------------------------------

    missing_values = (
        df[
            features
        ]
        .isna()
        .sum()
    )

    total_missing = int(
        missing_values.sum()
    )

    print()

    print(
        f"Total missing feature values: "
        f"{total_missing:,}"
    )

    if total_missing != 0:

        print(
            missing_values[
                missing_values > 0
            ]
        )

        raise ValueError(
            f"{model_name} contains missing feature values."
        )

    # --------------------------------------------------------
    # Numeric / finite validation.
    # --------------------------------------------------------

    for feature in features:

        values = pd.to_numeric(
            df[
                feature
            ],
            errors="coerce",
        ).to_numpy()

        if not np.isfinite(
            values
        ).all():

            raise ValueError(
                f"Non-finite values found in {feature}."
            )

    # --------------------------------------------------------
    # Historical target.
    # --------------------------------------------------------

    target_values = set(
        df[
            TARGET
        ].unique()
    )

    if not target_values.issubset(
        {0, 1}
    ):

        raise ValueError(
            "Historical target must contain only 0 and 1."
        )

    print(
        "Feature validation: PASSED"
    )


# ============================================================
# WORLD COVER VALIDATION
# ============================================================

def validate_worldcover(df):

    header(
        "VALIDATING WORLDCOVER FRACTIONS"
    )

    fractions = df[
        WORLD_COVER_FEATURES
    ].to_numpy(
        dtype=np.float64
    )

    if not np.isfinite(
        fractions
    ).all():

        raise ValueError(
            "WorldCover contains non-finite values."
        )

    minimum = float(
        fractions.min()
    )

    maximum = float(
        fractions.max()
    )

    print(
        f"Minimum fraction: {minimum}"
    )

    print(
        f"Maximum fraction: {maximum}"
    )

    if minimum < -1e-6:

        raise ValueError(
            "WorldCover fraction below zero."
        )

    if maximum > 1.000001:

        raise ValueError(
            "WorldCover fraction above one."
        )

    sums = fractions.sum(
        axis=1
    )

    print(
        f"Fraction sum minimum: "
        f"{sums.min()}"
    )

    print(
        f"Fraction sum maximum: "
        f"{sums.max()}"
    )

    if not np.allclose(
        sums,
        1.0,
        atol=1e-4,
    ):

        raise ValueError(
            "WorldCover fractions do not sum to approximately 1."
        )

    print(
        "WorldCover validation: PASSED"
    )


# ============================================================
# GSI VALIDATION
# ============================================================

def validate_gsi(df):

    header(
        "VALIDATING GSI FEATURES"
    )

    classes = set(
        df[
            "gsi_susceptibility"
        ].unique()
    )

    print(
        f"GSI susceptibility classes: "
        f"{sorted(classes)}"
    )

    if not classes.issubset(
        {0, 1, 2, 3}
    ):

        raise ValueError(
            "Unexpected GSI susceptibility class."
        )

    coverage = set(
        df[
            "gsi_coverage"
        ].unique()
    )

    print(
        f"GSI coverage values: "
        f"{sorted(coverage)}"
    )

    if not coverage.issubset(
        {0, 1}
    ):

        raise ValueError(
            "GSI coverage must contain 0/1."
        )

    expected = (
        df[
            "gsi_susceptibility"
        ]
        > 0
    ).astype(
        np.uint8
    )

    mismatch = int(
        (
            expected
            != df[
                "gsi_coverage"
            ]
        ).sum()
    )

    print(
        f"GSI coverage mismatches: "
        f"{mismatch:,}"
    )

    if mismatch != 0:

        raise ValueError(
            "GSI coverage is inconsistent with GSI susceptibility."
        )

    print(
        "GSI validation: PASSED"
    )


# ============================================================
# CREATE MODEL DATASET
# ============================================================

def create_model_dataset(
    merged,
    features,
    model_name,
):

    header(
        f"CREATING {model_name}"
    )

    columns = (
        KEY_COLUMNS
        + [
            "x",
            "y",
            "block_row",
            "block_col",
            "block_id",
            "split",
        ]
        + features
        + [
            TARGET,
        ]
    )

    dataset = merged[
        columns
    ].copy()

    # --------------------------------------------------------
    # Deterministic ordering.
    # --------------------------------------------------------

    dataset = dataset.sort_values(
        [
            "row",
            "col",
        ]
    ).reset_index(
        drop=True
    )

    print(
        f"Rows: {len(dataset):,}"
    )

    print(
        f"Features: {len(features)}"
    )

    print(
        f"Feature columns: {features}"
    )

    # --------------------------------------------------------
    # Check target balance.
    # --------------------------------------------------------

    positives = int(
        (
            dataset[
                TARGET
            ]
            == 1
        ).sum()
    )

    negatives = int(
        (
            dataset[
                TARGET
            ]
            == 0
        ).sum()
    )

    positive_fraction = (
        positives
        / len(dataset)
    )

    print()

    print(
        f"Positive cells: "
        f"{positives:,}"
    )

    print(
        f"Negative cells: "
        f"{negatives:,}"
    )

    print(
        f"Positive fraction: "
        f"{positive_fraction:.6%}"
    )

    # --------------------------------------------------------
    # Split balance.
    # --------------------------------------------------------

    print()

    print(
        "Target distribution by split:"
    )

    split_summary = (
        dataset
        .groupby(
            "split"
        )[
            TARGET
        ]
        .agg(
            [
                "count",
                "sum",
                "mean",
            ]
        )
        .rename(
            columns={
                "count": "cells",
                "sum": "positive_cells",
                "mean": "positive_fraction",
            }
        )
    )

    print(
        split_summary.to_string()
    )

    # --------------------------------------------------------
    # Final missing-value check.
    # --------------------------------------------------------

    missing = int(
        dataset[
            features
            + [
                TARGET
            ]
        ]
        .isna()
        .sum()
        .sum()
    )

    print()

    print(
        f"Missing feature/target values: "
        f"{missing:,}"
    )

    if missing != 0:

        raise ValueError(
            f"{model_name} contains missing values."
        )

    return dataset, split_summary


# ============================================================
# WRITE MODEL DATASETS
# ============================================================

def write_outputs(
    model_a,
    model_b,
    summary_rows,
):

    header(
        "WRITING ML BASELINE DATASETS"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Model A.
    # --------------------------------------------------------

    model_a.to_parquet(
        MODEL_A_OUTPUT,
        index=False,
    )

    print(
        f"Model A:\n{MODEL_A_OUTPUT}"
    )

    print(
        f"Shape: {model_a.shape}"
    )

    # --------------------------------------------------------
    # Model B.
    # --------------------------------------------------------

    model_b.to_parquet(
        MODEL_B_OUTPUT,
        index=False,
    )

    print()

    print(
        f"Model B:\n{MODEL_B_OUTPUT}"
    )

    print(
        f"Shape: {model_b.shape}"
    )

    # --------------------------------------------------------
    # Summary.
    # --------------------------------------------------------

    summary = pd.DataFrame(
        summary_rows
    )

    summary.to_csv(
        SUMMARY_OUTPUT,
        index=False,
    )

    print()

    print(
        f"Summary:\n{SUMMARY_OUTPUT}"
    )

    print(
        f"Summary rows: {len(summary):,}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    header(
        "WAYANAD ML BASELINE DATASET BUILDER"
    )

    print(
        "Two controlled datasets will be created:"
    )

    print()

    print(
        "MODEL A:"
    )

    print(
        "  slope + WorldCover + GSI"
    )

    print()

    print(
        "MODEL B:"
    )

    print(
        "  slope + WorldCover"
    )

    print()

    print(
        "Both use the SAME spatial train/validation/test split."
    )

    # --------------------------------------------------------
    # 1. Load.
    # --------------------------------------------------------

    training = load_training_base()

    split = load_spatial_split()

    # --------------------------------------------------------
    # 2. Join.
    # --------------------------------------------------------

    merged = join_training_and_split(
        training,
        split,
    )

    # --------------------------------------------------------
    # 3. Validate common features.
    # --------------------------------------------------------

    validate_feature_columns(
        merged,
        BASE_FEATURES,
        "COMMON FEATURES",
    )

    validate_worldcover(
        merged
    )

    # --------------------------------------------------------
    # 4. Validate GSI.
    # --------------------------------------------------------

    validate_gsi(
        merged
    )

    # --------------------------------------------------------
    # 5. Validate Model A.
    # --------------------------------------------------------

    validate_feature_columns(
        merged,
        MODEL_A_FEATURES,
        "MODEL A — WITH GSI",
    )

    # --------------------------------------------------------
    # 6. Validate Model B.
    # --------------------------------------------------------

    validate_feature_columns(
        merged,
        MODEL_B_FEATURES,
        "MODEL B — WITHOUT GSI",
    )

    # --------------------------------------------------------
    # 7. Create Model A.
    # --------------------------------------------------------

    model_a, summary_a = (
        create_model_dataset(
            merged,
            MODEL_A_FEATURES,
            "MODEL A — WITH GSI",
        )
    )

    # --------------------------------------------------------
    # 8. Create Model B.
    # --------------------------------------------------------

    model_b, summary_b = (
        create_model_dataset(
            merged,
            MODEL_B_FEATURES,
            "MODEL B — WITHOUT GSI",
        )
    )

    # --------------------------------------------------------
    # 9. Ensure both datasets have identical cells/splits.
    # --------------------------------------------------------

    header(
        "COMPARING MODEL A AND MODEL B"
    )

    keys_a = (
        model_a[
            [
                "row",
                "col",
                "split",
            ]
        ]
        .sort_values(
            [
                "row",
                "col",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    keys_b = (
        model_b[
            [
                "row",
                "col",
                "split",
            ]
        ]
        .sort_values(
            [
                "row",
                "col",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    identical = (
        keys_a.equals(
            keys_b
        )
    )

    print(
        f"Identical cells and split assignments: "
        f"{identical}"
    )

    if not identical:

        raise ValueError(
            "Model A and Model B do not use identical "
            "cells/split assignments."
        )

    print(
        "Controlled comparison validation: PASSED"
    )

    # --------------------------------------------------------
    # 10. Summary rows.
    # --------------------------------------------------------

    summary_rows = []

    for model_name, features, summary in [
        (
            "with_gsi",
            MODEL_A_FEATURES,
            summary_a,
        ),
        (
            "without_gsi",
            MODEL_B_FEATURES,
            summary_b,
        ),
    ]:

        for _, row in summary.iterrows():

            summary_rows.append(
                {
                    "model": model_name,
                    "features": ", ".join(
                        features
                    ),
                    "split": row.name,
                    "cells": row["cells"],
                    "positive_cells": row[
                        "positive_cells"
                    ],
                    "positive_fraction": row[
                        "positive_fraction"
                    ],
                }
            )

    # --------------------------------------------------------
    # 11. Write.
    # --------------------------------------------------------

    write_outputs(
        model_a,
        model_b,
        summary_rows,
    )

    # --------------------------------------------------------
    # Complete.
    # --------------------------------------------------------

    header(
        "COMPLETE"
    )

    print(
        "Both controlled ML baseline datasets "
        "were created successfully."
    )

    print()

    print(
        "MODEL A = slope + WorldCover + GSI"
    )

    print(
        "MODEL B = slope + WorldCover"
    )

    print()

    print(
        "Both datasets use identical spatial splits."
    )

    print()

    print(
        "Next step:"
    )

    print(
        "Train the first baseline models using "
        "PR-AUC as the primary evaluation metric."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()