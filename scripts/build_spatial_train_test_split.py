from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# WAYANAD SPATIAL TRAIN / VALIDATION / TEST SPLIT
# ============================================================
#
# Purpose:
# Create a spatially separated train / validation / test split
# from the canonical Wayanad landslide training base.
#
# Important:
# - Individual 30 m cells are NOT randomly split.
# - Entire spatial blocks are assigned to one split.
# - This reduces spatial leakage.
#
# Canonical grid:
#   30 m
#
# Spatial block:
#   64 x 64 cells
#   64 * 30 m = 1,920 m
#   approximately 1.92 km x 1.92 km
#
# Split:
#   70% train
#   15% validation
#   15% test
#
# ============================================================


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

INPUT_DATASET = (
    ROOT
    / "data"
    / "processed"
    / "features"
    / "wayanad_landslide_training_base.parquet"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "features"
)

OUTPUT_DATASET = (
    OUTPUT_DIR
    / "wayanad_spatial_train_test_split.parquet"
)

OUTPUT_SUMMARY = (
    OUTPUT_DIR
    / "wayanad_spatial_train_test_split_summary.csv"
)


# ============================================================
# SPATIAL SPLIT SETTINGS
# ============================================================

BLOCK_SIZE = 64

TRAIN_FRACTION = 0.70
VALIDATION_FRACTION = 0.15
TEST_FRACTION = 0.15

RANDOM_SEED = 42


# ============================================================
# REQUIRED INPUT COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "row",
    "col",
    "x",
    "y",
    "historical_landslide",
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
# LOAD DATA
# ============================================================

def load_training_base():

    header("LOADING CANONICAL TRAINING BASE")

    if not INPUT_DATASET.exists():
        raise FileNotFoundError(
            f"Training base not found:\n{INPUT_DATASET}"
        )

    df = pd.read_parquet(
        INPUT_DATASET
    )

    print(
        f"Path: {INPUT_DATASET}"
    )

    print(
        f"Shape: {df.shape}"
    )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    return df


# ============================================================
# VALIDATE INPUT
# ============================================================

def validate_input(df):

    header("VALIDATING INPUT DATA")

    # --------------------------------------------------------
    # Duplicate raster cells
    # --------------------------------------------------------

    duplicate_cells = int(
        df.duplicated(
            subset=[
                "row",
                "col",
            ]
        ).sum()
    )

    print(
        f"Duplicate row/col cells: "
        f"{duplicate_cells:,}"
    )

    if duplicate_cells != 0:
        raise ValueError(
            "Duplicate raster cells detected."
        )

    # --------------------------------------------------------
    # Coordinate validation
    # --------------------------------------------------------

    for column in [
        "x",
        "y",
        "row",
        "col",
    ]:

        values = df[column].to_numpy()

        if not np.isfinite(values).all():
            raise ValueError(
                f"Non-finite values detected in {column}."
            )

    # --------------------------------------------------------
    # Historical label validation
    # --------------------------------------------------------

    labels = set(
        df[
            "historical_landslide"
        ].unique()
    )

    print(
        f"Historical label values: "
        f"{sorted(labels)}"
    )

    if not labels.issubset({0, 1}):
        raise ValueError(
            "historical_landslide must contain only 0 and 1."
        )

    print(
        f"Row range: "
        f"{df['row'].min()} - "
        f"{df['row'].max()}"
    )

    print(
        f"Column range: "
        f"{df['col'].min()} - "
        f"{df['col'].max()}"
    )

    print(
        "Input validation: PASSED"
    )


# ============================================================
# CREATE SPATIAL BLOCKS
# ============================================================

def create_spatial_blocks(df):

    header("CREATING SPATIAL BLOCKS")

    working = df.copy()

    # --------------------------------------------------------
    # Calculate block row/column.
    #
    # Raster cells are grouped into 64 x 64 blocks.
    # --------------------------------------------------------

    working["block_row"] = (
        working["row"]
        .astype(np.int64)
        // BLOCK_SIZE
    )

    working["block_col"] = (
        working["col"]
        .astype(np.int64)
        // BLOCK_SIZE
    )

    # --------------------------------------------------------
    # Create unique readable block ID.
    # --------------------------------------------------------

    working["block_id"] = (
        working["block_row"]
        .astype(str)
        + "_"
        + working["block_col"]
        .astype(str)
    )

    # --------------------------------------------------------
    # Extract unique blocks.
    # --------------------------------------------------------

    blocks = (
        working[
            [
                "block_row",
                "block_col",
                "block_id",
            ]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    print(
        f"Block size: "
        f"{BLOCK_SIZE} x {BLOCK_SIZE} cells"
    )

    print(
        f"Approximate block size: "
        f"{BLOCK_SIZE * 30 / 1000:.2f} km x "
        f"{BLOCK_SIZE * 30 / 1000:.2f} km"
    )

    print(
        f"Unique spatial blocks: "
        f"{len(blocks):,}"
    )

    return working, blocks


# ============================================================
# ASSIGN BLOCKS TO TRAIN / VALIDATION / TEST
# ============================================================

def assign_block_splits(blocks):

    header(
        "ASSIGNING BLOCKS TO TRAIN / VALIDATION / TEST"
    )

    blocks = blocks.copy()

    # --------------------------------------------------------
    # Validate fractions.
    # --------------------------------------------------------

    fraction_sum = (
        TRAIN_FRACTION
        + VALIDATION_FRACTION
        + TEST_FRACTION
    )

    if not np.isclose(
        fraction_sum,
        1.0,
    ):
        raise ValueError(
            "Train/validation/test fractions must sum to 1.0."
        )

    # --------------------------------------------------------
    # Reproducible random generator.
    # --------------------------------------------------------

    rng = np.random.default_rng(
        RANDOM_SEED
    )

    # --------------------------------------------------------
    # Shuffle BLOCKS, not cells.
    # --------------------------------------------------------

    permutation = rng.permutation(
        len(blocks)
    )

    blocks = (
        blocks
        .iloc[permutation]
        .reset_index(drop=True)
    )

    n_blocks = len(blocks)

    # --------------------------------------------------------
    # Calculate block counts.
    # --------------------------------------------------------

    n_train = int(
        round(
            n_blocks
            * TRAIN_FRACTION
        )
    )

    n_validation = int(
        round(
            n_blocks
            * VALIDATION_FRACTION
        )
    )

    n_test = (
        n_blocks
        - n_train
        - n_validation
    )

    if min(
        n_train,
        n_validation,
        n_test,
    ) <= 0:
        raise ValueError(
            "At least one split received zero blocks."
        )

    # --------------------------------------------------------
    # Assign.
    # --------------------------------------------------------

    blocks["split"] = "test"

    blocks.loc[
        0 : n_train - 1,
        "split",
    ] = "train"

    validation_start = n_train

    validation_end = (
        n_train
        + n_validation
        - 1
    )

    blocks.loc[
        validation_start : validation_end,
        "split",
    ] = "validation"

    # --------------------------------------------------------
    # Report.
    # --------------------------------------------------------

    print(
        f"Total blocks: {n_blocks:,}"
    )

    print(
        f"Train blocks: {n_train:,}"
    )

    print(
        f"Validation blocks: {n_validation:,}"
    )

    print(
        f"Test blocks: {n_test:,}"
    )

    print()

    print(
        "Block distribution:"
    )

    print(
        blocks[
            "split"
        ]
        .value_counts()
        .to_string()
    )

    return blocks


# ============================================================
# VERIFY BLOCK ASSIGNMENT
# ============================================================

def verify_block_assignment(blocks):

    header(
        "VERIFYING BLOCK ASSIGNMENT"
    )

    # --------------------------------------------------------
    # Each block must appear once.
    # --------------------------------------------------------

    duplicate_blocks = int(
        blocks.duplicated(
            subset=[
                "block_row",
                "block_col",
            ]
        ).sum()
    )

    print(
        f"Duplicate spatial blocks: "
        f"{duplicate_blocks:,}"
    )

    if duplicate_blocks != 0:
        raise ValueError(
            "Duplicate spatial blocks detected."
        )

    # --------------------------------------------------------
    # Validate split values.
    # --------------------------------------------------------

    expected_splits = {
        "train",
        "validation",
        "test",
    }

    actual_splits = set(
        blocks[
            "split"
        ].unique()
    )

    print(
        f"Split values: "
        f"{sorted(actual_splits)}"
    )

    if actual_splits != expected_splits:
        raise ValueError(
            "Unexpected split values detected."
        )

    print(
        "Block assignment validation: PASSED"
    )


# ============================================================
# ASSIGN BLOCK SPLITS TO CELLS
# ============================================================

def assign_cell_splits(
    working,
    blocks,
):

    header("ASSIGNING SPLITS TO CELLS")

    # --------------------------------------------------------
    # Authoritative block lookup.
    #
    # Use block_row + block_col as the join keys.
    # --------------------------------------------------------

    lookup = blocks[
        [
            "block_row",
            "block_col",
            "block_id",
            "split",
        ]
    ].copy()

    split_df = working.merge(
        lookup,
        on=[
            "block_row",
            "block_col",
        ],
        how="left",
        validate="many_to_one",
    )

    # --------------------------------------------------------
    # Every cell must receive a split.
    # --------------------------------------------------------

    missing_split = int(
        split_df[
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
            "Some cells did not receive a split."
        )

    # --------------------------------------------------------
    # Report cell counts.
    # --------------------------------------------------------

    print()

    print(
        "Cell counts:"
    )

    print(
        split_df[
            "split"
        ]
        .value_counts()
        .to_string()
    )

    return split_df


# ============================================================
# SPATIAL LEAKAGE CHECK
# ============================================================

def check_spatial_leakage(
    blocks,
    split_df,
):

    header("CHECKING FOR SPATIAL LEAKAGE")

    # --------------------------------------------------------
    # Check 1:
    #
    # Every block must belong to exactly one split.
    # --------------------------------------------------------

    block_split_counts = (
        blocks
        .groupby(
            [
                "block_row",
                "block_col",
            ]
        )[
            "split"
        ]
        .nunique()
    )

    leaking_blocks = int(
        (
            block_split_counts
            > 1
        ).sum()
    )

    print(
        f"Blocks assigned to multiple splits: "
        f"{leaking_blocks:,}"
    )

    if leaking_blocks != 0:
        raise ValueError(
            "Spatial leakage detected: "
            "a block belongs to multiple splits."
        )

    # --------------------------------------------------------
    # Check 2:
    #
    # Every cell's split must match its block's split.
    # --------------------------------------------------------

    expected_split = (
        blocks[
            [
                "block_row",
                "block_col",
                "split",
            ]
        ]
        .drop_duplicates()
    )

    verification = split_df.merge(
        expected_split,
        on=[
            "block_row",
            "block_col",
        ],
        how="left",
        suffixes=(
            "_cell",
            "_block",
        ),
        validate="many_to_one",
    )

    missing_expected = int(
        verification[
            "split_block"
        ]
        .isna()
        .sum()
    )

    print(
        f"Cells without authoritative block split: "
        f"{missing_expected:,}"
    )

    if missing_expected != 0:
        raise ValueError(
            "Some cells could not be matched "
            "to their spatial block."
        )

    # --------------------------------------------------------
    # Compare.
    # --------------------------------------------------------

    mismatches = int(
        (
            verification[
                "split_cell"
            ]
            != verification[
                "split_block"
            ]
        ).sum()
    )

    print(
        f"Cell/block split mismatches: "
        f"{mismatches:,}"
    )

    if mismatches != 0:
        raise ValueError(
            "Cell split does not match its spatial block."
        )

    print()

    print(
        "Spatial leakage check: PASSED"
    )


# ============================================================
# HISTORICAL LABEL DISTRIBUTION
# ============================================================

def calculate_class_balance(split_df):

    header(
        "CALCULATING HISTORICAL LABEL DISTRIBUTION"
    )

    results = []

    for split_name in [
        "train",
        "validation",
        "test",
    ]:

        subset = split_df[
            split_df[
                "split"
            ]
            == split_name
        ]

        total = len(
            subset
        )

        positive = int(
            (
                subset[
                    "historical_landslide"
                ]
                == 1
            ).sum()
        )

        negative = int(
            (
                subset[
                    "historical_landslide"
                ]
                == 0
            ).sum()
        )

        positive_fraction = (
            positive / total
            if total > 0
            else 0.0
        )

        results.append(
            {
                "split": split_name,
                "cells": total,
                "positive_cells": positive,
                "negative_cells": negative,
                "positive_fraction": positive_fraction,
            }
        )

        print()

        print(
            split_name.upper()
        )

        print(
            f"  cells: {total:,}"
        )

        print(
            f"  historical-positive: "
            f"{positive:,}"
        )

        print(
            f"  background: "
            f"{negative:,}"
        )

        print(
            f"  positive fraction: "
            f"{positive_fraction:.6%}"
        )

    return pd.DataFrame(
        results
    )


# ============================================================
# HISTORICAL EVENT COVERAGE BY BLOCK
# ============================================================

def check_positive_blocks(split_df):

    header(
        "CHECKING HISTORICAL-EVENT COVERAGE BY BLOCK"
    )

    # --------------------------------------------------------
    # Aggregate cells within each spatial block.
    #
    # We deliberately use block_row + block_col instead of
    # relying on block_id.
    # --------------------------------------------------------

    block_stats = (
        split_df
        .groupby(
            [
                "block_row",
                "block_col",
                "split",
            ],
            as_index=False,
        )[
            "historical_landslide"
        ]
        .agg(
            cells="size",
            positive_cells="sum",
        )
    )

    # --------------------------------------------------------
    # Identify blocks containing positive cells.
    # --------------------------------------------------------

    block_stats[
        "has_positive"
    ] = (
        block_stats[
            "positive_cells"
        ]
        > 0
    )

    # --------------------------------------------------------
    # Summarize by split.
    # --------------------------------------------------------

    summary = (
        block_stats
        .groupby(
            "split",
            as_index=False,
        )
        .agg(
            blocks=(
                "block_row",
                "count",
            ),
            positive_blocks=(
                "has_positive",
                "sum",
            ),
            positive_cells=(
                "positive_cells",
                "sum",
            ),
        )
    )

    # --------------------------------------------------------
    # Positive-block fraction.
    # --------------------------------------------------------

    summary[
        "positive_block_fraction"
    ] = (
        summary[
            "positive_blocks"
        ]
        / summary[
            "blocks"
        ]
    )

    print()

    print(
        summary.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Warning only.
    # --------------------------------------------------------

    for _, row in summary.iterrows():

        if int(
            row[
                "positive_cells"
            ]
        ) == 0:

            print()

            print(
                f"WARNING: {row['split']} has "
                f"zero historical-positive cells."
            )

    return summary


# ============================================================
# FINAL QA
# ============================================================

def final_qa(
    original_df,
    split_df,
):

    header("FINAL QA")

    # --------------------------------------------------------
    # Row count.
    # --------------------------------------------------------

    input_rows = len(
        original_df
    )

    output_rows = len(
        split_df
    )

    print(
        f"Input cells: {input_rows:,}"
    )

    print(
        f"Output cells: {output_rows:,}"
    )

    if input_rows != output_rows:
        raise ValueError(
            "Input/output cell count changed."
        )

    # --------------------------------------------------------
    # Duplicate cells.
    # --------------------------------------------------------

    duplicate_cells = int(
        split_df.duplicated(
            subset=[
                "row",
                "col",
            ]
        ).sum()
    )

    print(
        f"Duplicate output cells: "
        f"{duplicate_cells:,}"
    )

    if duplicate_cells != 0:
        raise ValueError(
            "Duplicate output cells detected."
        )

    # --------------------------------------------------------
    # Missing split.
    # --------------------------------------------------------

    missing_split = int(
        split_df[
            "split"
        ]
        .isna()
        .sum()
    )

    print(
        f"Missing split values: "
        f"{missing_split:,}"
    )

    if missing_split != 0:
        raise ValueError(
            "Missing split values detected."
        )

    # --------------------------------------------------------
    # Split values.
    # --------------------------------------------------------

    expected_splits = {
        "train",
        "validation",
        "test",
    }

    actual_splits = set(
        split_df[
            "split"
        ].unique()
    )

    if actual_splits != expected_splits:
        raise ValueError(
            "Unexpected split values."
        )

    # --------------------------------------------------------
    # Coordinate preservation.
    # --------------------------------------------------------

    original_coords = (
        original_df[
            [
                "row",
                "col",
                "x",
                "y",
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

    output_coords = (
        split_df[
            [
                "row",
                "col",
                "x",
                "y",
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

    x_match = np.allclose(
        original_coords[
            "x"
        ].to_numpy(),
        output_coords[
            "x"
        ].to_numpy(),
        atol=1e-6,
    )

    y_match = np.allclose(
        original_coords[
            "y"
        ].to_numpy(),
        output_coords[
            "y"
        ].to_numpy(),
        atol=1e-6,
    )

    if not x_match:
        raise ValueError(
            "X coordinates changed."
        )

    if not y_match:
        raise ValueError(
            "Y coordinates changed."
        )

    print(
        "Coordinate preservation: PASSED"
    )

    # --------------------------------------------------------
    # Historical label preservation.
    # --------------------------------------------------------

    original_labels = (
        original_df[
            [
                "row",
                "col",
                "historical_landslide",
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

    output_labels = (
        split_df[
            [
                "row",
                "col",
                "historical_landslide",
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

    labels_match = np.array_equal(
        original_labels[
            "historical_landslide"
        ].to_numpy(),
        output_labels[
            "historical_landslide"
        ].to_numpy(),
    )

    if not labels_match:
        raise ValueError(
            "Historical labels changed."
        )

    print(
        "Historical-label preservation: PASSED"
    )

    print()

    print(
        "ALL FINAL QA CHECKS PASSED"
    )


# ============================================================
# WRITE OUTPUTS
# ============================================================

def write_outputs(
    split_df,
    class_summary,
    block_summary,
):

    header("WRITING OUTPUTS")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Build the final output dataframe.
    #
    # block_id is recreated here deliberately.
    # This prevents the earlier KeyError problem.
    # --------------------------------------------------------

    output = split_df[
        [
            "row",
            "col",
            "x",
            "y",
            "block_row",
            "block_col",
            "split",
        ]
    ].copy()

    output["block_id"] = (
        output["block_row"]
        .astype(str)
        + "_"
        + output["block_col"]
        .astype(str)
    )

    # --------------------------------------------------------
    # Arrange columns.
    # --------------------------------------------------------

    output = output[
        [
            "row",
            "col",
            "x",
            "y",
            "block_row",
            "block_col",
            "block_id",
            "split",
        ]
    ]

    # --------------------------------------------------------
    # Save dataset.
    # --------------------------------------------------------

    output.to_parquet(
        OUTPUT_DATASET,
        index=False,
    )

    # --------------------------------------------------------
    # Create summary.
    # --------------------------------------------------------

    summary = class_summary.copy()

    block_lookup = (
        block_summary
        .set_index(
            "split"
        )
    )

    summary[
        "total_blocks"
    ] = (
        summary[
            "split"
        ]
        .map(
            block_lookup[
                "blocks"
            ]
        )
    )

    summary[
        "positive_blocks"
    ] = (
        summary[
            "split"
        ]
        .map(
            block_lookup[
                "positive_blocks"
            ]
        )
    )

    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
    )

    # --------------------------------------------------------
    # Report.
    # --------------------------------------------------------

    print(
        "Dataset:"
    )

    print(
        OUTPUT_DATASET
    )

    print()

    print(
        "Summary:"
    )

    print(
        OUTPUT_SUMMARY
    )

    print()

    print(
        f"Output shape: "
        f"{output.shape}"
    )

    print()

    print(
        "Saved columns:"
    )

    print(
        output.columns.tolist()
    )


# ============================================================
# MAIN
# ============================================================

def main():

    header(
        "WAYANAD SPATIAL TRAIN / VALIDATION / TEST SPLIT"
    )

    print(
        "This pipeline assigns entire spatial blocks "
        "to train, validation, or test."
    )

    print()

    print(
        "Individual 30 m cells are NEVER randomly "
        "distributed between splits."
    )

    # --------------------------------------------------------
    # 1. Load.
    # --------------------------------------------------------

    df = load_training_base()

    # --------------------------------------------------------
    # 2. Validate.
    # --------------------------------------------------------

    validate_input(
        df
    )

    # --------------------------------------------------------
    # 3. Create spatial blocks.
    # --------------------------------------------------------

    working, blocks = (
        create_spatial_blocks(
            df
        )
    )

    # --------------------------------------------------------
    # 4. Assign blocks.
    # --------------------------------------------------------

    blocks = assign_block_splits(
        blocks
    )

    # --------------------------------------------------------
    # 5. Verify block assignment.
    # --------------------------------------------------------

    verify_block_assignment(
        blocks
    )

    # --------------------------------------------------------
    # 6. Assign cell splits.
    # --------------------------------------------------------

    split_df = assign_cell_splits(
        working,
        blocks,
    )

    # --------------------------------------------------------
    # 7. Check spatial leakage.
    # --------------------------------------------------------

    check_spatial_leakage(
        blocks,
        split_df,
    )

    # --------------------------------------------------------
    # 8. Calculate class balance.
    # --------------------------------------------------------

    class_summary = (
        calculate_class_balance(
            split_df
        )
    )

    # --------------------------------------------------------
    # 9. Check positive-event distribution.
    # --------------------------------------------------------

    block_summary = (
        check_positive_blocks(
            split_df
        )
    )

    # --------------------------------------------------------
    # 10. Final QA.
    # --------------------------------------------------------

    final_qa(
        df,
        split_df,
    )

    # --------------------------------------------------------
    # 11. Write outputs.
    # --------------------------------------------------------

    write_outputs(
        split_df,
        class_summary,
        block_summary,
    )

    # --------------------------------------------------------
    # Complete.
    # --------------------------------------------------------

    header("COMPLETE")

    print(
        "Spatial train/validation/test split "
        "created successfully."
    )

    print()

    print(
        "Training base was not modified."
    )

    print()

    print(
        "Next step:"
    )

    print(
        "Audit the GSI susceptibility feature "
        "for possible historical-inventory leakage "
        "before training the ML model."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()