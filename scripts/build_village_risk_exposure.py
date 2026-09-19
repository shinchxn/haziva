from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask


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

RISK_RASTER = (
    ROOT
    / "data"
    / "processed"
    / "predictions"
    / "wayanad_spatial_model_predictions.parquet"
)

DYNAMIC_RISK_RASTER = (
    ROOT
    / "data"
    / "processed"
    / "predictions"
    / "wayanad_dynamic_risk_combined_model_a.tif"
)

SLOPE_RASTER = (
    ROOT
    / "data"
    / "processed"
    / "terrain"
    / "wayanad_copernicus_slope_degrees.tif"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "exposure"
    / "village_risk"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_GPKG = (
    OUTPUT_DIR
    / "wayanad_village_risk_exposure.gpkg"
)

OUTPUT_CSV = (
    OUTPUT_DIR
    / "wayanad_village_risk_exposure.csv"
)


# ============================================================
# HELPERS
# ============================================================

def print_header(title):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def normalize_code(value):
    """
    Normalize village codes so integer/string representations
    compare consistently.
    """
    if pd.isna(value):
        return None

    text = str(value).strip()

    if text.endswith(".0"):
        text = text[:-2]

    return text


def summarize_raster_by_polygon(
    raster_path,
    villages,
    statistic_name,
):
    """
    Aggregate raster values inside each village polygon.

    Returns:
        DataFrame indexed by village_code
    """

    print()
    print(f"Reading raster:")
    print(f"  {raster_path}")

    if not raster_path.exists():
        raise FileNotFoundError(
            f"Required raster does not exist:\n{raster_path}"
        )

    results = []

    with rasterio.open(raster_path) as src:

        print(f"  CRS       : {src.crs}")
        print(f"  Shape     : {src.height} x {src.width}")
        print(f"  Resolution: {src.res}")

        if villages.crs != src.crs:
            print(
                f"  Reprojecting village boundaries "
                f"{villages.crs} -> {src.crs}"
            )
            working_villages = villages.to_crs(src.crs)
        else:
            working_villages = villages

        for idx, row in working_villages.iterrows():

            village_code = normalize_code(row["village_code"])

            geometry = [row.geometry]

            try:
                data, _ = mask(
                    src,
                    geometry,
                    crop=True,
                    filled=False,
                )

            except ValueError:
                results.append(
                    {
                        "village_code": village_code,
                        f"{statistic_name}_mean": np.nan,
                        f"{statistic_name}_median": np.nan,
                        f"{statistic_name}_p90": np.nan,
                        f"{statistic_name}_p95": np.nan,
                        f"{statistic_name}_max": np.nan,
                        f"{statistic_name}_valid_cells": 0,
                    }
                )
                continue

            values = data[0]

            if np.ma.isMaskedArray(values):
                values = values.compressed()

            values = np.asarray(values, dtype=np.float64)

            values = values[np.isfinite(values)]

            # Ignore raster nodata if present
            if src.nodata is not None:
                values = values[values != src.nodata]

            if len(values) == 0:
                result = {
                    "village_code": village_code,
                    f"{statistic_name}_mean": np.nan,
                    f"{statistic_name}_median": np.nan,
                    f"{statistic_name}_p90": np.nan,
                    f"{statistic_name}_p95": np.nan,
                    f"{statistic_name}_max": np.nan,
                    f"{statistic_name}_valid_cells": 0,
                }

            else:
                result = {
                    "village_code": village_code,
                    f"{statistic_name}_mean": float(np.mean(values)),
                    f"{statistic_name}_median": float(
                        np.median(values)
                    ),
                    f"{statistic_name}_p90": float(
                        np.percentile(values, 90)
                    ),
                    f"{statistic_name}_p95": float(
                        np.percentile(values, 95)
                    ),
                    f"{statistic_name}_max": float(
                        np.max(values)
                    ),
                    f"{statistic_name}_valid_cells": int(
                        len(values)
                    ),
                }

            results.append(result)

    return pd.DataFrame(results)


# ============================================================
# LOAD VILLAGES
# ============================================================

print_header("LOADING WAYANAD VILLAGE EXPOSURE DATA")

if not VILLAGE_GPKG.exists():
    raise FileNotFoundError(
        f"Village GeoPackage not found:\n{VILLAGE_GPKG}"
    )

villages = gpd.read_file(VILLAGE_GPKG)

print(f"Village features: {len(villages)}")
print(f"CRS: {villages.crs}")

required_columns = [
    "village_code",
    "village_name",
    "population_2011",
    "households_2011",
    "male_population_2011",
    "female_population_2011",
    "geometry",
]

missing = [
    c for c in required_columns
    if c not in villages.columns
]

if missing:
    raise ValueError(
        f"Missing required village columns: {missing}"
    )

villages["village_code"] = (
    villages["village_code"]
    .map(normalize_code)
)

villages["population_2011"] = pd.to_numeric(
    villages["population_2011"],
    errors="coerce",
)

villages["households_2011"] = pd.to_numeric(
    villages["households_2011"],
    errors="coerce",
)

villages["male_population_2011"] = pd.to_numeric(
    villages["male_population_2011"],
    errors="coerce",
)

villages["female_population_2011"] = pd.to_numeric(
    villages["female_population_2011"],
    errors="coerce",
)


# ============================================================
# QA VILLAGE DATA
# ============================================================

print_header("VILLAGE EXPOSURE QA")

print(
    f"Population total : "
    f"{villages['population_2011'].sum():,.0f}"
)

print(
    f"Households total : "
    f"{villages['households_2011'].sum():,.0f}"
)

print(
    f"Male total       : "
    f"{villages['male_population_2011'].sum():,.0f}"
)

print(
    f"Female total     : "
    f"{villages['female_population_2011'].sum():,.0f}"
)

assert len(villages) == 48, (
    f"Expected 48 Census villages, found {len(villages)}"
)

assert (
    villages["population_2011"].sum() == 785840
), "Population total mismatch"

assert (
    villages["households_2011"].sum() == 183375
), "Household total mismatch"

assert (
    villages["male_population_2011"].sum()
    +
    villages["female_population_2011"].sum()
    ==
    villages["population_2011"].sum()
), "Male + female does not equal total population"

print("PASS: village exposure QA")


# ============================================================
# LOAD SPATIAL MODEL PREDICTIONS
# ============================================================

print_header("LOADING SPATIAL MODEL PREDICTIONS")

if not RISK_RASTER.exists():
    raise FileNotFoundError(
        f"Prediction parquet not found:\n{RISK_RASTER}"
    )

pred = pd.read_parquet(RISK_RASTER)

print(f"Prediction rows: {len(pred):,}")
print(f"Columns: {list(pred.columns)}")


# ------------------------------------------------------------
# Detect model probability columns
# ------------------------------------------------------------

candidate_columns = [
    "model_a_probability",
    "model_a_score",
    "probability_model_a",
    "model_a",
]

model_a_column = None

for column in candidate_columns:
    if column in pred.columns:
        model_a_column = column
        break


if model_a_column is None:
    # Try automatic detection
    probability_candidates = [
        c for c in pred.columns
        if "model_a" in c.lower()
        and (
            "prob" in c.lower()
            or "score" in c.lower()
        )
    ]

    if probability_candidates:
        model_a_column = probability_candidates[0]


if model_a_column is None:
    raise ValueError(
        "Could not find Model A prediction column.\n"
        f"Available columns:\n{list(pred.columns)}"
    )


print(f"Using Model A column: {model_a_column}")


# ============================================================
# BUILD MODEL A RASTER
# ============================================================

print_header("BUILDING MODEL A RASTER")

required_xy = ["x", "y"]

for col in required_xy:
    if col not in pred.columns:
        raise ValueError(
            f"Prediction parquet missing '{col}'"
        )

pred["x"] = pd.to_numeric(
    pred["x"],
    errors="coerce",
)

pred["y"] = pd.to_numeric(
    pred["y"],
    errors="coerce",
)

pred[model_a_column] = pd.to_numeric(
    pred[model_a_column],
    errors="coerce",
)

pred = pred.dropna(
    subset=["x", "y", model_a_column]
).copy()

print(
    f"Valid prediction rows: {len(pred):,}"
)


# ============================================================
# USE CANONICAL RASTER GRID
# ============================================================

CANONICAL_RASTER = SLOPE_RASTER

if not CANONICAL_RASTER.exists():
    raise FileNotFoundError(
        f"Canonical raster not found:\n{CANONICAL_RASTER}"
    )

with rasterio.open(CANONICAL_RASTER) as src:

    raster_crs = src.crs
    raster_transform = src.transform
    raster_width = src.width
    raster_height = src.height
    raster_nodata = src.nodata

    print(f"CRS: {raster_crs}")
    print(f"Shape: {raster_height} x {raster_width}")
    print(f"Resolution: {src.res}")

    # Coordinates from prediction parquet are cell centres.
    #
    # Convert x/y into raster row/column.
    rows, cols = rasterio.transform.rowcol(
        raster_transform,
        pred["x"].to_numpy(),
        pred["y"].to_numpy(),
    )

    rows = np.asarray(rows)
    cols = np.asarray(cols)

    valid = (
        (rows >= 0)
        & (rows < raster_height)
        & (cols >= 0)
        & (cols < raster_width)
    )

    rows = rows[valid]
    cols = cols[valid]

    values = pred.loc[
        valid,
        model_a_column,
    ].to_numpy(dtype=np.float32)

    model_a_array = np.full(
        (raster_height, raster_width),
        np.nan,
        dtype=np.float32,
    )

    model_a_array[rows, cols] = values


# ============================================================
# WRITE TEMPORARY MODEL A RASTER
# ============================================================

model_a_tif = OUTPUT_DIR / "model_a_village_aggregation_input.tif"

with rasterio.open(
    model_a_tif,
    "w",
    driver="GTiff",
    height=raster_height,
    width=raster_width,
    count=1,
    dtype="float32",
    crs=raster_crs,
    transform=raster_transform,
    nodata=-9999,
    compress="deflate",
) as dst:

    output_array = np.where(
        np.isfinite(model_a_array),
        model_a_array,
        -9999,
    )

    dst.write(
        output_array.astype(np.float32),
        1,
    )

print(
    f"Temporary raster created:\n{model_a_tif}"
)


# ============================================================
# AGGREGATE MODEL A RISK BY VILLAGE
# ============================================================

print_header("AGGREGATING MODEL A RISK BY VILLAGE")

risk_summary = summarize_raster_by_polygon(
    model_a_tif,
    villages,
    "model_a_risk",
)

print(
    f"Village summaries: {len(risk_summary)}"
)


# ============================================================
# OPTIONAL DYNAMIC RISK
# ============================================================

dynamic_summary = pd.DataFrame()

if DYNAMIC_RISK_RASTER.exists():

    print_header("AGGREGATING DYNAMIC FORECAST RISK")

    dynamic_summary = summarize_raster_by_polygon(
        DYNAMIC_RISK_RASTER,
        villages,
        "dynamic_risk",
    )

else:

    print()
    print(
        "Dynamic risk raster not found."
    )
    print(
        "Continuing with spatial susceptibility only."
    )
    print(
        f"Expected:\n{DYNAMIC_RISK_RASTER}"
    )


# ============================================================
# MERGE RESULTS
# ============================================================

print_header("BUILDING FINAL VILLAGE RISK DATASET")

result = villages.copy()

result["village_code"] = (
    result["village_code"]
    .map(normalize_code)
)

result = result.merge(
    risk_summary,
    on="village_code",
    how="left",
    validate="one_to_one",
)

if not dynamic_summary.empty:

    result = result.merge(
        dynamic_summary,
        on="village_code",
        how="left",
        validate="one_to_one",
    )


# ============================================================
# CALCULATE EXPOSURE METRICS
# ============================================================

result["population_density_proxy"] = (
    result["population_2011"]
    /
    result.geometry.to_crs("EPSG:32643").area
    * 1_000_000
)

result["population_share"] = (
    result["population_2011"]
    /
    result["population_2011"].sum()
)


# ============================================================
# RISK × EXPOSURE PRIORITY
# ============================================================

print_header("CALCULATING VILLAGE PRIORITY")

# Important:
# This is a decision-support prioritization score.
# It is NOT an evacuation order and NOT a calibrated
# probability of disaster.

risk_component = (
    result["model_a_risk_p95"]
    .fillna(0)
    .clip(0, 1)
)

population_component = (
    result["population_share"]
    /
    result["population_share"].max()
)

result["priority_score"] = (
    0.70 * risk_component
    +
    0.30 * population_component
)


# ============================================================
# PRIORITY RANK
# ============================================================

result = result.sort_values(
    "priority_score",
    ascending=False,
).reset_index(drop=True)

result["priority_rank"] = (
    np.arange(len(result)) + 1
)


# ============================================================
# ROUND NUMERICAL COLUMNS
# ============================================================

numeric_columns = result.select_dtypes(
    include=[np.number]
).columns

result[numeric_columns] = (
    result[numeric_columns].round(6)
)


# ============================================================
# FINAL QA
# ============================================================

print_header("FINAL QA")

print(
    f"Village count       : {len(result)}"
)

print(
    f"Population          : "
    f"{result['population_2011'].sum():,.0f}"
)

print(
    f"Households          : "
    f"{result['households_2011'].sum():,.0f}"
)

print(
    f"Risk missing        : "
    f"{result['model_a_risk_p95'].isna().sum()}"
)

print(
    f"Priority missing    : "
    f"{result['priority_score'].isna().sum()}"
)

assert len(result) == 48

assert (
    result["population_2011"].sum() == 785840
)

assert (
    result["households_2011"].sum() == 183375
)

assert (
    result["priority_score"].notna().all()
)

print()
print("PASS: village count")
print("PASS: population total")
print("PASS: household total")
print("PASS: risk aggregation")
print("PASS: priority calculation")


# ============================================================
# SAVE CSV
# ============================================================

csv_columns = [
    "village_code",
    "village_name",
    "population_2011",
    "households_2011",
    "male_population_2011",
    "female_population_2011",
    "model_a_risk_mean",
    "model_a_risk_median",
    "model_a_risk_p90",
    "model_a_risk_p95",
    "model_a_risk_max",
    "model_a_risk_valid_cells",
    "population_density_proxy",
    "population_share",
    "priority_score",
    "priority_rank",
]

if "dynamic_risk_mean" in result.columns:

    csv_columns.extend(
        [
            "dynamic_risk_mean",
            "dynamic_risk_median",
            "dynamic_risk_p90",
            "dynamic_risk_p95",
            "dynamic_risk_max",
            "dynamic_risk_valid_cells",
        ]
    )

csv_columns = [
    c for c in csv_columns
    if c in result.columns
]

result[csv_columns].to_csv(
    OUTPUT_CSV,
    index=False,
)


# ============================================================
# SAVE GEOPACKAGE
# ============================================================

# GeoPackage field names are kept reasonably short.
gpkg_result = result.copy()

rename_for_gpkg = {
    "population_2011": "pop_2011",
    "households_2011": "hh_2011",
    "male_population_2011": "male_2011",
    "female_population_2011": "female_2011",
    "model_a_risk_mean": "risk_mean",
    "model_a_risk_median": "risk_median",
    "model_a_risk_p90": "risk_p90",
    "model_a_risk_p95": "risk_p95",
    "model_a_risk_max": "risk_max",
    "model_a_risk_valid_cells": "risk_cells",
    "population_density_proxy": "pop_density",
    "population_share": "pop_share",
    "priority_score": "priority",
    "priority_rank": "rank",
}

gpkg_result = gpkg_result.rename(
    columns=rename_for_gpkg
)

# Drop source columns that are unnecessarily verbose.
keep_columns = [
    "village_code",
    "village_name",
    "pop_2011",
    "hh_2011",
    "male_2011",
    "female_2011",
    "risk_mean",
    "risk_median",
    "risk_p90",
    "risk_p95",
    "risk_max",
    "risk_cells",
    "pop_density",
    "pop_share",
    "priority",
    "rank",
    "geometry",
]

keep_columns = [
    c for c in keep_columns
    if c in gpkg_result.columns
]

gpkg_result = gpkg_result[keep_columns]

if OUTPUT_GPKG.exists():
    OUTPUT_GPKG.unlink()

gpkg_result.to_file(
    OUTPUT_GPKG,
    layer="village_risk_exposure",
    driver="GPKG",
)


# ============================================================
# TOP VILLAGES
# ============================================================

print_header("TOP VILLAGE PRIORITY RESULTS")

display_columns = [
    "rank",
    "village_code",
    "village_name",
    "pop_2011",
    "risk_p95",
    "priority",
]

print(
    gpkg_result[
        display_columns
    ].head(10).to_string(index=False)
)


# ============================================================
# COMPLETE
# ============================================================

print_header("VILLAGE RISK AGGREGATION COMPLETE")

print(
    f"CSV:\n{OUTPUT_CSV}"
)

print(
    f"\nGeoPackage:\n{OUTPUT_GPKG}"
)

print()
print("Final village features:", len(result))
print(
    "Final population:",
    f"{result['population_2011'].sum():,.0f}",
)
print(
    "Final households:",
    f"{result['households_2011'].sum():,.0f}",
)