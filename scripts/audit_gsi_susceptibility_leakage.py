from pathlib import Path

import numpy as np
import pandas as pd
import rasterio


# ============================================================
# GSI SUSCEPTIBILITY LEAKAGE AUDIT
# ============================================================
#
# Purpose:
#
# Determine how strongly the GSI susceptibility layer overlaps
# with the historical landslide labels used as the ML target.
#
# IMPORTANT:
#
# This script does NOT automatically declare the GSI layer
# "leaked".
#
# It performs a quantitative audit:
#
#   1. Grid alignment
#   2. Class distribution
#   3. Historical-positive distribution by GSI class
#   4. Historical-positive rate by GSI class
#   5. GSI coverage vs no-coverage comparison
#   6. Simple enrichment statistics
#
# Interpretation:
#
# GSI susceptibility is an expert/geoscientific susceptibility
# layer. It may legitimately contain information related to
# historical landslides.
#
# The question is whether it is sufficiently dependent on the
# same inventory used for our target that including it would
# make the ML evaluation misleading.
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

GSI_RASTER = (
    ROOT
    / "data"
    / "processed"
    / "landslide"
    / "susceptibility"
    / "wayanad_gsi_susceptibility_copernicus_30m.tif"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "features"
)

OUTPUT_SUMMARY = (
    OUTPUT_DIR
    / "wayanad_gsi_susceptibility_leakage_audit.csv"
)


# ============================================================
# EXPECTED GSI CLASSES
# ============================================================

# Based on our canonical GSI raster:
#
# 0 = no GSI coverage
# 1 = Low
# 2 = Moderate
# 3 = High

EXPECTED_CLASSES = {
    0,
    1,
    2,
    3,
}


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
        "LOADING CANONICAL TRAINING BASE"
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

    required = [
        "x",
        "y",
        "slope_degrees",
        "gsi_susceptibility",
        "gsi_coverage",
        "historical_landslide",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    return df


# ============================================================
# LOAD GSI RASTER
# ============================================================

def inspect_gsi_raster():

    header(
        "INSPECTING GSI SUSCEPTIBILITY RASTER"
    )

    if not GSI_RASTER.exists():
        raise FileNotFoundError(
            f"GSI raster not found:\n{GSI_RASTER}"
        )

    with rasterio.open(
        GSI_RASTER
    ) as src:

        print(
            f"CRS: {src.crs}"
        )

        print(
            f"Width: {src.width}"
        )

        print(
            f"Height: {src.height}"
        )

        print(
            f"Resolution: {src.res}"
        )

        print(
            f"Bounds: {src.bounds}"
        )

        print(
            f"NoData: {src.nodata}"
        )

        values = src.read(
            1
        )

    unique, counts = np.unique(
        values,
        return_counts=True,
    )

    print()

    print(
        "Raster-wide class distribution:"
    )

    for value, count in zip(
        unique,
        counts,
    ):

        print(
            f"  {value}: {count:,}"
        )

    return values


# ============================================================
# VALIDATE TRAINING-BASE GSI VALUES
# ============================================================

def validate_training_base(df):

    header(
        "VALIDATING GSI VALUES IN TRAINING BASE"
    )

    gsi_values = set(
        df[
            "gsi_susceptibility"
        ].unique()
    )

    print(
        f"GSI susceptibility classes: "
        f"{sorted(gsi_values)}"
    )

    if not gsi_values.issubset(
        EXPECTED_CLASSES
    ):
        raise ValueError(
            "Unexpected GSI susceptibility classes detected."
        )

    coverage_values = set(
        df[
            "gsi_coverage"
        ].unique()
    )

    print(
        f"GSI coverage values: "
        f"{sorted(coverage_values)}"
    )

    if not coverage_values.issubset(
        {0, 1}
    ):
        raise ValueError(
            "gsi_coverage must contain only 0 and 1."
        )

    # --------------------------------------------------------
    # Verify semantic relationship.
    #
    # Class 0 = no GSI coverage.
    # Classes 1/2/3 = GSI coverage.
    # --------------------------------------------------------

    expected_coverage = (
        df[
            "gsi_susceptibility"
        ]
        > 0
    ).astype(
        np.uint8
    )

    mismatch = int(
        (
            expected_coverage
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
            "gsi_coverage does not match "
            "gsi_susceptibility."
        )

    print(
        "GSI training-base validation: PASSED"
    )


# ============================================================
# ANALYZE GSI CLASS VS HISTORICAL TARGET
# ============================================================

def analyze_gsi_vs_target(df):

    header(
        "ANALYZING GSI SUSCEPTIBILITY VS HISTORICAL TARGET"
    )

    rows = []

    total_positive = int(
        (
            df[
                "historical_landslide"
            ]
            == 1
        ).sum()
    )

    total_cells = len(
        df
    )

    overall_positive_rate = (
        total_positive
        / total_cells
    )

    print(
        f"Total cells: {total_cells:,}"
    )

    print(
        f"Historical-positive cells: "
        f"{total_positive:,}"
    )

    print(
        f"Overall positive rate: "
        f"{overall_positive_rate:.6%}"
    )

    print()

    print(
        "GSI class statistics:"
    )

    for gsi_class in [
        0,
        1,
        2,
        3,
    ]:

        subset = df[
            df[
                "gsi_susceptibility"
            ]
            == gsi_class
        ]

        cells = len(
            subset
        )

        positives = int(
            (
                subset[
                    "historical_landslide"
                ]
                == 1
            ).sum()
        )

        positive_rate = (
            positives / cells
            if cells > 0
            else 0.0
        )

        prevalence_enrichment = (
            positive_rate
            / overall_positive_rate
            if overall_positive_rate > 0
            else np.nan
        )

        positive_capture = (
            positives
            / total_positive
            if total_positive > 0
            else np.nan
        )

        rows.append(
            {
                "analysis": "gsi_class",
                "gsi_class": gsi_class,
                "cells": cells,
                "positive_cells": positives,
                "positive_rate": positive_rate,
                "prevalence_enrichment": prevalence_enrichment,
                "positive_capture_fraction": positive_capture,
            }
        )

        class_name = {
            0: "NO_COVERAGE",
            1: "LOW",
            2: "MODERATE",
            3: "HIGH",
        }[
            gsi_class
        ]

        print(
            f"\n  {gsi_class} = {class_name}"
        )

        print(
            f"    cells: {cells:,}"
        )

        print(
            f"    historical positives: "
            f"{positives:,}"
        )

        print(
            f"    positive rate: "
            f"{positive_rate:.6%}"
        )

        print(
            f"    enrichment vs overall: "
            f"{prevalence_enrichment:.3f}x"
        )

        print(
            f"    fraction of all positives: "
            f"{positive_capture:.3%}"
        )

    return rows


# ============================================================
# ANALYZE GSI COVERAGE
# ============================================================

def analyze_gsi_coverage(df):

    header(
        "ANALYZING GSI COVERAGE VS NO-COVERAGE"
    )

    rows = []

    total_positive = int(
        (
            df[
                "historical_landslide"
            ]
            == 1
        ).sum()
    )

    for coverage in [
        0,
        1,
    ]:

        subset = df[
            df[
                "gsi_coverage"
            ]
            == coverage
        ]

        cells = len(
            subset
        )

        positives = int(
            (
                subset[
                    "historical_landslide"
                ]
                == 1
            ).sum()
        )

        positive_rate = (
            positives / cells
            if cells > 0
            else 0.0
        )

        positive_capture = (
            positives
            / total_positive
            if total_positive > 0
            else np.nan
        )

        rows.append(
            {
                "analysis": "gsi_coverage",
                "gsi_class": coverage,
                "cells": cells,
                "positive_cells": positives,
                "positive_rate": positive_rate,
                "prevalence_enrichment": np.nan,
                "positive_capture_fraction": positive_capture,
            }
        )

        name = (
            "NO_GSI_COVERAGE"
            if coverage == 0
            else "GSI_COVERAGE"
        )

        print(
            f"\n  {name}"
        )

        print(
            f"    cells: {cells:,}"
        )

        print(
            f"    historical positives: "
            f"{positives:,}"
        )

        print(
            f"    positive rate: "
            f"{positive_rate:.6%}"
        )

        print(
            f"    fraction of all positives: "
            f"{positive_capture:.3%}"
        )

    return rows


# ============================================================
# RANK-ORDER CHECK
# ============================================================

def check_monotonicity(df):

    header(
        "CHECKING GSI CLASS ORDERING"
    )

    rates = {}

    for gsi_class in [
        1,
        2,
        3,
    ]:

        subset = df[
            df[
                "gsi_susceptibility"
            ]
            == gsi_class
        ]

        if len(subset) == 0:
            rates[gsi_class] = np.nan
        else:
            rates[gsi_class] = (
                subset[
                    "historical_landslide"
                ]
                == 1
            ).mean()

    print(
        "Historical-positive rate by covered GSI class:"
    )

    for gsi_class, rate in rates.items():

        print(
            f"  class {gsi_class}: "
            f"{rate:.6%}"
        )

    valid_rates = [
        rate
        for rate in rates.values()
        if np.isfinite(rate)
    ]

    monotonic = (
        valid_rates
        == sorted(valid_rates)
    )

    print()

    print(
        f"Monotonically increasing: "
        f"{monotonic}"
    )

    return rates, monotonic


# ============================================================
# TARGET / GSI ASSOCIATION
# ============================================================

def calculate_association(df):

    header(
        "CALCULATING SIMPLE GSI / TARGET ASSOCIATION"
    )

    # --------------------------------------------------------
    # Binary GSI indicator:
    #
    # 1 = GSI-covered
    # 0 = no GSI coverage
    # --------------------------------------------------------

    gsi_present = (
        df[
            "gsi_coverage"
        ]
        .astype(int)
    )

    target = (
        df[
            "historical_landslide"
        ]
        .astype(int)
    )

    table = pd.crosstab(
        gsi_present,
        target,
    )

    print(
        "Contingency table:"
    )

    print(
        table.to_string()
    )

    # --------------------------------------------------------
    # Calculate positive rates.
    # --------------------------------------------------------

    rates = (
        df
        .groupby(
            "gsi_coverage"
        )[
            "historical_landslide"
        ]
        .mean()
    )

    no_gsi_rate = rates.get(
        0,
        np.nan,
    )

    gsi_rate = rates.get(
        1,
        np.nan,
    )

    if (
        np.isfinite(no_gsi_rate)
        and no_gsi_rate > 0
    ):

        coverage_rate_ratio = (
            gsi_rate
            / no_gsi_rate
        )

    else:

        coverage_rate_ratio = np.nan

    print()

    print(
        f"Historical-positive rate without GSI coverage: "
        f"{no_gsi_rate:.6%}"
    )

    print(
        f"Historical-positive rate with GSI coverage: "
        f"{gsi_rate:.6%}"
    )

    print(
        f"Rate ratio: "
        f"{coverage_rate_ratio:.3f}x"
    )

    return coverage_rate_ratio


# ============================================================
# WRITE AUDIT
# ============================================================

def write_audit(
    class_rows,
    coverage_rows,
):

    header(
        "WRITING AUDIT RESULTS"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = (
        class_rows
        + coverage_rows
    )

    audit_df = pd.DataFrame(
        rows
    )

    audit_df.to_csv(
        OUTPUT_SUMMARY,
        index=False,
    )

    print(
        f"Output: {OUTPUT_SUMMARY}"
    )

    print()

    print(
        audit_df.to_string(
            index=False
        )
    )


# ============================================================
# FINAL INTERPRETATION
# ============================================================

def interpretation(
    class_rows,
    coverage_rate_ratio,
):

    header(
        "AUDIT INTERPRETATION"
    )

    print(
        "IMPORTANT:"
    )

    print(
        "This audit does NOT prove that GSI susceptibility "
        "is independent or dependent on the historical inventory."
    )

    print()

    print(
        "It quantifies how strongly the GSI layer is associated "
        "with our historical target."
    )

    print()

    print(
        "A strong association is expected for a susceptibility "
        "layer and is not, by itself, proof of leakage."
    )

    print()

    print(
        "The provenance/methodology of the specific GSI Wayanad "
        "product must be checked before making the final decision "
        "about using it as an ML feature."
    )

    print()

    if np.isfinite(
        coverage_rate_ratio
    ):

        print(
            f"Observed GSI-coverage rate ratio: "
            f"{coverage_rate_ratio:.3f}x"
        )

    print()

    print(
        "DO NOT remove GSI automatically."
    )

    print(
        "DO NOT declare the model valid automatically."
    )

    print(
        "Use this audit together with the GSI product provenance."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    header(
        "WAYANAD GSI SUSCEPTIBILITY LEAKAGE AUDIT"
    )

    # --------------------------------------------------------
    # 1. Load training data.
    # --------------------------------------------------------

    df = load_training_base()

    # --------------------------------------------------------
    # 2. Inspect raster.
    # --------------------------------------------------------

    inspect_gsi_raster()

    # --------------------------------------------------------
    # 3. Validate training-base values.
    # --------------------------------------------------------

    validate_training_base(
        df
    )

    # --------------------------------------------------------
    # 4. Analyze GSI classes.
    # --------------------------------------------------------

    class_rows = (
        analyze_gsi_vs_target(
            df
        )
    )

    # --------------------------------------------------------
    # 5. Analyze GSI coverage.
    # --------------------------------------------------------

    coverage_rows = (
        analyze_gsi_coverage(
            df
        )
    )

    # --------------------------------------------------------
    # 6. Check ordering.
    # --------------------------------------------------------

    check_monotonicity(
        df
    )

    # --------------------------------------------------------
    # 7. Association.
    # --------------------------------------------------------

    coverage_rate_ratio = (
        calculate_association(
            df
        )
    )

    # --------------------------------------------------------
    # 8. Save audit.
    # --------------------------------------------------------

    write_audit(
        class_rows,
        coverage_rows,
    )

    # --------------------------------------------------------
    # 9. Interpretation.
    # --------------------------------------------------------

    interpretation(
        class_rows,
        coverage_rate_ratio,
    )

    header(
        "COMPLETE"
    )

    print(
        "GSI susceptibility audit completed."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()