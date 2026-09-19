from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask


# ============================================================
# WAYANAD DYNAMIC VILLAGE RISK AGGREGATION
# ============================================================
#
# Purpose:
#   Aggregate 30m forecast-conditioned dynamic landslide-risk
#   rasters into the 48 reconciled Wayanad Census villages.
#
# Inputs:
#   - Census + NWDP reconciled village boundaries
#   - Model A 24h dynamic risk raster
#   - Model A 72h dynamic risk raster
#   - Model A 7-day dynamic risk raster
#   - Model A combined dynamic risk raster
#
# Outputs:
#   - Village-level CSV
#   - Village-level GeoPackage
#
# Important:
#   Dynamic risk values are decision-support scores, NOT
#   calibrated probabilities of a landslide.
#
#   Population is Census 2011 and is used as exposure data.
#
#   Priority score is a prototype heuristic:
#
#       70% forecast risk
#       30% population exposure
#
#   It is NOT an evacuation threshold and should be
#   configurable by authorities.
# ============================================================


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]


VILLAGE_GPKG = (
    ROOT
    / "data"
    / "processed"
    / "exposure"
    / "census_nwdp_reconciliation"
    / "wayanad_census_nwdp_village_population_2011.gpkg"
)


PREDICTION_DIR = (
    ROOT
    / "data"
    / "processed"
    / "predictions"
)


OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "exposure"
    / "village_risk"
)


OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# DYNAMIC RISK RASTERS
# ============================================================

RASTERS = {

    "risk_24h": (
        PREDICTION_DIR
        / "wayanad_dynamic_risk_model_a_24h.tif"
    ),

    "risk_72h": (
        PREDICTION_DIR
        / "wayanad_dynamic_risk_model_a_72h.tif"
    ),

    "risk_7day": (
        PREDICTION_DIR
        / "wayanad_dynamic_risk_model_a_7day.tif"
    ),

    "risk_combined": (
        PREDICTION_DIR
        / "wayanad_dynamic_risk_model_a_combined.tif"
    ),

}


# ============================================================
# OUTPUT FILES
# ============================================================

OUTPUT_CSV = (
    OUTPUT_DIR
    / "wayanad_village_dynamic_risk.csv"
)


OUTPUT_GPKG = (
    OUTPUT_DIR
    / "wayanad_village_dynamic_risk.gpkg"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def header(title):
    """Print a readable section header."""

    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def normalize_code(value):
    """
    Normalize village codes so joins work reliably.

    Example:
        627296.0 -> "627296"
        "627296" -> "627296"
    """

    if pd.isna(value):
        return None

    value = str(value).strip()

    if value.endswith(".0"):
        value = value[:-2]

    return value


def aggregate_raster(
    raster_path,
    villages,
    prefix,
):
    """
    Calculate zonal statistics for every village.

    Statistics:
        mean
        median
        p90
        p95
        max
        valid cell count

    P95 is retained as the principal village-level
    risk statistic because it captures the upper-risk
    portion of the village without allowing one extreme
    cell to dominate the entire village.
    """

    header(
        f"AGGREGATING {prefix.upper()}"
    )

    # --------------------------------------------------------
    # Check raster
    # --------------------------------------------------------

    if not raster_path.exists():

        raise FileNotFoundError(
            f"Raster not found:\n{raster_path}"
        )


    results = []


    # --------------------------------------------------------
    # Open raster
    # --------------------------------------------------------

    with rasterio.open(raster_path) as src:

        print(
            f"Raster : {raster_path.name}"
        )

        print(
            f"CRS    : {src.crs}"
        )

        print(
            f"Shape  : "
            f"{src.height} x {src.width}"
        )

        print(
            f"Pixel  : {src.res}"
        )

        print(
            f"NoData : {src.nodata}"
        )


        # ----------------------------------------------------
        # Reproject village polygons if required
        # ----------------------------------------------------

        if villages.crs != src.crs:

            print(
                f"Reprojecting villages "
                f"{villages.crs} -> {src.crs}"
            )

            working_villages = villages.to_crs(
                src.crs
            )

        else:

            working_villages = villages


        # ----------------------------------------------------
        # Process every village
        # ----------------------------------------------------

        for _, village in working_villages.iterrows():

            code = normalize_code(
                village["village_code"]
            )


            # ------------------------------------------------
            # Extract raster cells inside village
            # ------------------------------------------------

            try:

                data, _ = mask(
                    src,
                    [village.geometry],
                    crop=True,
                    filled=False,
                )

            except ValueError:

                results.append(
                    {
                        "village_code": code,

                        f"{prefix}_mean": np.nan,
                        f"{prefix}_median": np.nan,
                        f"{prefix}_p90": np.nan,
                        f"{prefix}_p95": np.nan,
                        f"{prefix}_max": np.nan,
                        f"{prefix}_valid_cells": 0,
                    }
                )

                continue


            # ------------------------------------------------
            # First raster band
            # ------------------------------------------------

            values = data[0]


            # ------------------------------------------------
            # Remove masked cells
            # ------------------------------------------------

            if np.ma.isMaskedArray(values):

                values = values.compressed()


            values = np.asarray(
                values,
                dtype=np.float64,
            )


            # ------------------------------------------------
            # Remove NaN / Inf
            # ------------------------------------------------

            values = values[
                np.isfinite(values)
            ]


            # ------------------------------------------------
            # Remove raster NoData
            # ------------------------------------------------

            if src.nodata is not None:

                values = values[
                    values != src.nodata
                ]


            # ------------------------------------------------
            # Empty village
            # ------------------------------------------------

            if len(values) == 0:

                result = {

                    "village_code": code,

                    f"{prefix}_mean": np.nan,

                    f"{prefix}_median": np.nan,

                    f"{prefix}_p90": np.nan,

                    f"{prefix}_p95": np.nan,

                    f"{prefix}_max": np.nan,

                    f"{prefix}_valid_cells": 0,

                }


            # ------------------------------------------------
            # Calculate statistics
            # ------------------------------------------------

            else:

                result = {

                    "village_code": code,

                    f"{prefix}_mean": float(
                        np.mean(values)
                    ),

                    f"{prefix}_median": float(
                        np.median(values)
                    ),

                    f"{prefix}_p90": float(
                        np.percentile(
                            values,
                            90,
                        )
                    ),

                    f"{prefix}_p95": float(
                        np.percentile(
                            values,
                            95,
                        )
                    ),

                    f"{prefix}_max": float(
                        np.max(values)
                    ),

                    f"{prefix}_valid_cells": int(
                        len(values)
                    ),

                }


            results.append(
                result
            )


    # --------------------------------------------------------
    # Convert to DataFrame
    # --------------------------------------------------------

    return pd.DataFrame(
        results
    )


# ============================================================
# LOAD VILLAGE DATA
# ============================================================

header(
    "LOADING RECONCILED VILLAGES"
)


if not VILLAGE_GPKG.exists():

    raise FileNotFoundError(
        "Village GeoPackage not found:\n"
        f"{VILLAGE_GPKG}"
    )


villages = gpd.read_file(
    VILLAGE_GPKG
)


print(
    f"Village features: {len(villages)}"
)


print(
    f"Village CRS: {villages.crs}"
)


# We expect exactly the 48 rural Census villages.
assert len(villages) == 48, (
    f"Expected 48 villages, "
    f"found {len(villages)}"
)


# ============================================================
# NORMALIZE VILLAGE CODES
# ============================================================

villages["village_code"] = (
    villages["village_code"]
    .map(normalize_code)
)


# ============================================================
# NUMERIC POPULATION FIELDS
# ============================================================

for column in [
    "population_2011",
    "households_2011",
]:

    villages[column] = pd.to_numeric(
        villages[column],
        errors="coerce",
    )


# ============================================================
# BASIC VILLAGE QA
# ============================================================

header(
    "VILLAGE DATA QA"
)


population_total = (
    villages["population_2011"]
    .sum()
)


household_total = (
    villages["households_2011"]
    .sum()
)


print(
    "Population :",
    f"{population_total:,.0f}",
)


print(
    "Households :",
    f"{household_total:,.0f}",
)


# Expected Census 2011 rural Wayanad totals.
assert population_total == 785840, (
    "Unexpected population total"
)


assert household_total == 183375, (
    "Unexpected household total"
)


# ============================================================
# AGGREGATE ALL DYNAMIC RISK HORIZONS
# ============================================================

header(
    "AGGREGATING FORECAST RISK"
)


all_results = villages[
    [
        "village_code",
    ]
].copy()


for prefix, raster_path in RASTERS.items():

    summary = aggregate_raster(
        raster_path,
        villages,
        prefix,
    )


    # Every raster must produce one row per village.

    assert len(summary) == 48, (
        f"{prefix}: expected 48 rows, "
        f"found {len(summary)}"
    )


    # Merge statistics.

    all_results = all_results.merge(
        summary,
        on="village_code",
        how="left",
        validate="one_to_one",
    )


# ============================================================
# MERGE RISK WITH VILLAGE EXPOSURE
# ============================================================

header(
    "MERGING RISK + POPULATION"
)


result = villages.merge(
    all_results,
    on="village_code",
    how="left",
    validate="one_to_one",
)


# ============================================================
# POPULATION EXPOSURE
# ============================================================

result["population_share"] = (
    result["population_2011"]
    /
    result["population_2011"].sum()
)


population_share_max = (
    result["population_share"].max()
)


result["population_exposure_index"] = (
    result["population_share"]
    /
    population_share_max
)


# ============================================================
# FORECAST RISK
# ============================================================
#
# Principal village-level forecast risk:
#
#     combined forecast P95
#
# This is a score, not a probability.
# ============================================================

result["forecast_risk_p95"] = (
    result["risk_combined_p95"]
    .clip(0, 1)
)


# ============================================================
# FORECAST PRIORITY
# ============================================================
#
# Prototype decision-support formulation:
#
#     70% forecast risk
#     30% population exposure
#
# This weighting is configurable.
#
# It must NOT be interpreted as:
#     - evacuation threshold
#     - government policy
#     - calibrated probability
# ============================================================

result["forecast_priority_score"] = (

    0.70
    *
    result["forecast_risk_p95"]

    +

    0.30
    *
    result["population_exposure_index"]

)


# ============================================================
# FORECAST PRIORITY RANK
# ============================================================

result = result.sort_values(
    "forecast_priority_score",
    ascending=False,
).reset_index(
    drop=True
)


result["forecast_priority_rank"] = (
    np.arange(
        len(result)
    )
    + 1
)


# ============================================================
# ROUND NUMERIC VALUES
# ============================================================

numeric_columns = (
    result
    .select_dtypes(
        include=[np.number]
    )
    .columns
)


result[numeric_columns] = (
    result[numeric_columns]
    .round(6)
)


# ============================================================
# FINAL QA
# ============================================================

header(
    "FINAL DYNAMIC VILLAGE QA"
)


print(
    "Village count:",
    len(result),
)


print(
    "Population:",
    f"{result['population_2011'].sum():,.0f}",
)


print(
    "Households:",
    f"{result['households_2011'].sum():,.0f}",
)


# ------------------------------------------------------------
# Required risk fields
# ------------------------------------------------------------

required_risk_columns = [

    "risk_24h_p95",

    "risk_72h_p95",

    "risk_7day_p95",

    "risk_combined_p95",

    "forecast_risk_p95",

    "forecast_priority_score",

]


for column in required_risk_columns:

    missing = int(
        result[column]
        .isna()
        .sum()
    )


    print(
        f"{column} missing: {missing}"
    )


    assert missing == 0, (
        f"{column} contains missing values"
    )


# ------------------------------------------------------------
# Village count QA
# ------------------------------------------------------------

assert len(result) == 48


# ------------------------------------------------------------
# Population QA
# ------------------------------------------------------------

assert (
    result["population_2011"].sum()
    == 785840
)


# ------------------------------------------------------------
# Household QA
# ------------------------------------------------------------

assert (
    result["households_2011"].sum()
    == 183375
)


# ------------------------------------------------------------
# Priority score range
# ------------------------------------------------------------

assert (
    result["forecast_priority_score"]
    .between(0, 1)
    .all()
)


# ------------------------------------------------------------
# Risk score range
# ------------------------------------------------------------

for column in [

    "risk_24h_p95",
    "risk_72h_p95",
    "risk_7day_p95",
    "risk_combined_p95",

]:

    assert (
        result[column]
        .between(0, 1)
        .all()
    )


# ------------------------------------------------------------
# Success messages
# ------------------------------------------------------------

print()
print(
    "PASS: 48 villages"
)

print(
    "PASS: population total"
)

print(
    "PASS: household total"
)

print(
    "PASS: 24h dynamic risk"
)

print(
    "PASS: 72h dynamic risk"
)

print(
    "PASS: 7-day dynamic risk"
)

print(
    "PASS: combined dynamic risk"
)

print(
    "PASS: forecast priority"
)


# ============================================================
# CSV OUTPUT
# ============================================================

header(
    "WRITING CSV"
)


csv_columns = [

    "village_code",

    "village_name",

    "population_2011",

    "households_2011",

    # 24h
    "risk_24h_mean",
    "risk_24h_p90",
    "risk_24h_p95",
    "risk_24h_max",

    # 72h
    "risk_72h_mean",
    "risk_72h_p90",
    "risk_72h_p95",
    "risk_72h_max",

    # 7-day
    "risk_7day_mean",
    "risk_7day_p90",
    "risk_7day_p95",
    "risk_7day_max",

    # Combined
    "risk_combined_mean",
    "risk_combined_p90",
    "risk_combined_p95",
    "risk_combined_max",

    # Exposure
    "population_share",
    "population_exposure_index",

    # Decision support
    "forecast_risk_p95",
    "forecast_priority_score",
    "forecast_priority_rank",

]


# Keep only columns that exist.

csv_columns = [
    column
    for column in csv_columns
    if column in result.columns
]


result[
    csv_columns
].to_csv(
    OUTPUT_CSV,
    index=False,
)


print(
    f"CSV written:\n{OUTPUT_CSV}"
)


# ============================================================
# GEOPACKAGE OUTPUT
# ============================================================

header(
    "WRITING GEOPACKAGE"
)


gpkg = result.copy()


# ------------------------------------------------------------
# Short field names for GeoPackage compatibility
# ------------------------------------------------------------

rename_columns = {

    "population_2011":
        "pop_2011",

    "households_2011":
        "hh_2011",

    # 24h
    "risk_24h_mean":
        "r24_mean",

    "risk_24h_p90":
        "r24_p90",

    "risk_24h_p95":
        "r24_p95",

    "risk_24h_max":
        "r24_max",

    # 72h
    "risk_72h_mean":
        "r72_mean",

    "risk_72h_p90":
        "r72_p90",

    "risk_72h_p95":
        "r72_p95",

    "risk_72h_max":
        "r72_max",

    # 7-day
    "risk_7day_mean":
        "r7_mean",

    "risk_7day_p90":
        "r7_p90",

    "risk_7day_p95":
        "r7_p95",

    "risk_7day_max":
        "r7_max",

    # Combined
    "risk_combined_mean":
        "rc_mean",

    "risk_combined_p90":
        "rc_p90",

    "risk_combined_p95":
        "rc_p95",

    "risk_combined_max":
        "rc_max",

    # Exposure
    "population_share":
        "pop_share",

    "population_exposure_index":
        "pop_exp",

    # Decision support
    "forecast_risk_p95":
        "fc_risk",

    "forecast_priority_score":
        "priority",

    "forecast_priority_rank":
        "rank",

}


gpkg = gpkg.rename(
    columns=rename_columns
)


# ------------------------------------------------------------
# GeoPackage fields
# ------------------------------------------------------------

gpkg_columns = [

    "village_code",

    "village_name",

    "pop_2011",

    "hh_2011",

    # 24h
    "r24_mean",
    "r24_p90",
    "r24_p95",
    "r24_max",

    # 72h
    "r72_mean",
    "r72_p90",
    "r72_p95",
    "r72_max",

    # 7-day
    "r7_mean",
    "r7_p90",
    "r7_p95",
    "r7_max",

    # Combined
    "rc_mean",
    "rc_p90",
    "rc_p95",
    "rc_max",

    # Exposure
    "pop_share",
    "pop_exp",

    # Decision support
    "fc_risk",
    "priority",
    "rank",

    "geometry",

]


gpkg_columns = [
    column
    for column in gpkg_columns
    if column in gpkg.columns
]


gpkg = gpkg[
    gpkg_columns
]


# ------------------------------------------------------------
# Remove previous output if present
# ------------------------------------------------------------

if OUTPUT_GPKG.exists():

    OUTPUT_GPKG.unlink()


# ------------------------------------------------------------
# Write GeoPackage
# ------------------------------------------------------------

gpkg.to_file(
    OUTPUT_GPKG,
    layer="village_dynamic_risk",
    driver="GPKG",
)


print(
    f"GeoPackage written:\n{OUTPUT_GPKG}"
)


# ============================================================
# TOP VILLAGE TABLE
# ============================================================

header(
    "TOP FORECAST PRIORITY VILLAGES"
)


display_columns = [

    "rank",

    "village_code",

    "village_name",

    "pop_2011",

    "r24_p95",

    "r72_p95",

    "r7_p95",

    "rc_p95",

    "fc_risk",

    "priority",

]


print(
    gpkg[
        display_columns
    ]
    .head(10)
    .to_string(
        index=False
    )
)


# ============================================================
# COMPLETE
# ============================================================

header(
    "DYNAMIC VILLAGE RISK COMPLETE"
)


print(
    f"CSV:\n{OUTPUT_CSV}"
)


print(
    f"\nGeoPackage:\n{OUTPUT_GPKG}"
)


print()
print(
    "48 villages successfully aggregated."
)


print()
print(
    "Interpretation:"
)


print(
    "24h / 72h / 7-day / combined values are "
    "forecast-conditioned risk scores."
)


print(
    "They are NOT calibrated probabilities."
)


print(
    "Population exposure uses Census 2011 data."
)


print(
    "Priority is a prototype decision-support "
    "score for authority review."
)