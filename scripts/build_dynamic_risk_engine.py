"""
Build forecast-based dynamic landslide risk maps for Wayanad.

Method
------
Spatial susceptibility:
    Existing Model A / Model B raster

Rainfall stress:
    Empirical percentile interpolation using the existing
    wayanad_rainfall_stress_reference.json percentile tables.

Dynamic risk:
    spatial_susceptibility × rainfall_stress

IMPORTANT
---------
This produces a forecast dynamic-risk score.

It is NOT:
- a calibrated probability,
- an exact landslide prediction,
- an evacuation threshold,
- an autonomous relocation decision.

No 2026 observed rainfall is fabricated.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio


# =====================================================================
# PATHS
# =====================================================================

MODEL_A_RASTER = Path(
    "data/processed/predictions/wayanad_model_a_probability.tif"
)

MODEL_B_RASTER = Path(
    "data/processed/predictions/wayanad_model_b_probability.tif"
)

FORECAST_JSON = Path(
    "data/raw/rainfall/forecast/wayanad/"
    "wayanad_rainfall_forecast_7day.json"
)

STRESS_REFERENCE_JSON = Path(
    "data/processed/features/"
    "wayanad_rainfall_stress_reference.json"
)

OUTPUT_DIR = Path(
    "data/processed/predictions"
)

SUMMARY_PARQUET = (
    OUTPUT_DIR /
    "wayanad_dynamic_risk_summary.parquet"
)

METADATA_JSON = (
    OUTPUT_DIR /
    "wayanad_dynamic_risk_metadata.json"
)


# =====================================================================
# CONFIGURATION
# =====================================================================

STRESS_WEIGHTS = {
    "24h": 0.30,
    "72h": 0.40,
    "7day": 0.30,
}

HORIZONS = {
    "24h": 24,
    "72h": 72,
    "7day": 168,
}


# =====================================================================
# BASIC UTILITIES
# =====================================================================

def require_file(path: Path) -> None:

    if not path.exists():
        raise FileNotFoundError(
            f"Required input file not found:\n{path}"
        )


def load_json(path: Path) -> dict:

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


# =====================================================================
# FORECAST VALIDATION
# =====================================================================

def load_and_validate_forecast(
    path: Path,
) -> pd.DataFrame:

    data = load_json(path)

    if "hourly" not in data:
        raise ValueError(
            "Forecast JSON does not contain 'hourly'."
        )

    hourly = data["hourly"]

    required = {
        "time",
        "precipitation",
    }

    missing = required - set(hourly.keys())

    if missing:
        raise ValueError(
            "Forecast is missing fields: "
            f"{sorted(missing)}"
        )

    df = pd.DataFrame(
        {
            "time": pd.to_datetime(
                hourly["time"],
                errors="raise",
            ),
            "precipitation_mm": pd.to_numeric(
                hourly["precipitation"],
                errors="coerce",
            ),
        }
    )

    if df.empty:
        raise ValueError(
            "Forecast contains no records."
        )

    if df["precipitation_mm"].isna().any():
        raise ValueError(
            "Forecast contains missing precipitation values."
        )

    if (df["precipitation_mm"] < 0).any():
        raise ValueError(
            "Forecast contains negative precipitation."
        )

    df = (
        df
        .sort_values("time")
        .reset_index(drop=True)
    )

    if df["time"].duplicated().any():

        raise ValueError(
            "Forecast contains duplicate timestamps."
        )

    deltas = (
        df["time"]
        .diff()
        .dropna()
    )

    expected = pd.Timedelta(hours=1)

    if not (deltas == expected).all():

        bad = deltas[deltas != expected]

        raise ValueError(
            "Forecast timestamps are not hourly-continuous.\n"
            f"Invalid intervals:\n{bad.head(10)}"
        )

    return df


# =====================================================================
# FORECAST AGGREGATION
# =====================================================================

def calculate_forecast_totals(
    forecast_df: pd.DataFrame,
) -> dict:

    totals = {}

    for horizon, hours in HORIZONS.items():

        if len(forecast_df) < hours:

            raise ValueError(
                f"{horizon} requires {hours} hourly records, "
                f"but only {len(forecast_df)} exist."
            )

        total = forecast_df[
            "precipitation_mm"
        ].iloc[:hours].sum()

        totals[horizon] = float(total)

    return totals


# =====================================================================
# PERCENTILE TABLE
# =====================================================================

def get_percentile_table(
    reference: dict,
    horizon: str,
) -> tuple[np.ndarray, np.ndarray]:

    distributions = reference.get(
        "percentile_tables"
    )

    if not isinstance(
        distributions,
        dict,
    ):
        raise ValueError(
            "Reference file does not contain "
            "'percentile_tables'."
        )

    key_map = {
        "24h": "rainfall_24h_mm",
        "72h": "rainfall_72h_mm",
        "7day": "rainfall_7day_mm",
    }

    key = key_map[horizon]

    table = distributions.get(key)

    if not isinstance(
        table,
        dict,
    ):
        raise ValueError(
            f"Missing percentile table: {key}"
        )

    percentiles = []
    rainfall = []

    for p, value in table.items():

        try:
            percentile = float(p)
            rainfall_value = float(value)

        except (TypeError, ValueError):

            continue

        if (
            not np.isfinite(percentile)
            or not np.isfinite(rainfall_value)
        ):
            continue

        percentiles.append(percentile)
        rainfall.append(rainfall_value)

    if len(percentiles) < 2:

        raise ValueError(
            f"Insufficient percentile points for {horizon}."
        )

    percentiles = np.asarray(
        percentiles,
        dtype=float,
    )

    rainfall = np.asarray(
        rainfall,
        dtype=float,
    )

    order = np.argsort(
        rainfall
    )

    rainfall = rainfall[order]
    percentiles = percentiles[order]

    # Remove duplicate rainfall values.
    #
    # This matters because several lower percentiles can have
    # exactly 0 mm rainfall.

    unique_rainfall, unique_indices = np.unique(
        rainfall,
        return_index=True,
    )

    rainfall = unique_rainfall
    percentiles = percentiles[
        unique_indices
    ]

    return rainfall, percentiles


def rainfall_to_stress(
    rainfall_mm: float,
    reference: dict,
    horizon: str,
) -> float:
    """
    Convert rainfall amount into a 0-1 empirical percentile stress.

    Uses linear interpolation between the existing percentile-table
    points.

    Values outside the historical range are clipped to [0, 1].
    """

    rainfall_reference, percentile_reference = (
        get_percentile_table(
            reference,
            horizon,
        )
    )

    stress = np.interp(
        rainfall_mm,
        rainfall_reference,
        percentile_reference / 100.0,
    )

    return float(
        np.clip(
            stress,
            0.0,
            1.0,
        )
    )


# =====================================================================
# RASTER VALIDATION
# =====================================================================

def validate_rasters(
    src_a,
    src_b,
) -> None:

    checks = [
        (
            src_a.width == src_b.width,
            "Raster widths differ.",
        ),
        (
            src_a.height == src_b.height,
            "Raster heights differ.",
        ),
        (
            src_a.crs == src_b.crs,
            "Raster CRS differs.",
        ),
        (
            src_a.transform == src_b.transform,
            "Raster transforms differ.",
        ),
        (
            src_a.bounds == src_b.bounds,
            "Raster bounds differ.",
        ),
    ]

    for passed, message in checks:

        if not passed:
            raise ValueError(message)


# =====================================================================
# RISK CALCULATION
# =====================================================================

def calculate_risk(
    susceptibility: np.ndarray,
    rainfall_stress: float,
    nodata: float | None,
) -> np.ndarray:

    risk = (
        susceptibility *
        rainfall_stress
    ).astype(
        np.float32
    )

    if nodata is not None:

        risk[
            susceptibility == nodata
        ] = -9999.0

    return risk


# =====================================================================
# RASTER WRITER
# =====================================================================

def write_raster(
    path: Path,
    template,
    risk: np.ndarray,
    rainfall_stress: float,
    horizon: str,
) -> None:

    profile = template.profile.copy()

    profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        nodata=-9999.0,
        compress="deflate",
        predictor=3,
    )

    with rasterio.open(
        path,
        "w",
        **profile,
    ) as dst:

        dst.write(
            risk.astype(
                np.float32
            ),
            1,
        )

        dst.update_tags(
            risk_type=(
                "forecast_dynamic_landslide_risk"
            ),
            horizon=horizon,
            rainfall_stress=(
                f"{rainfall_stress:.8f}"
            ),
            formula=(
                "spatial_susceptibility * "
                "rainfall_stress"
            ),
            warning=(
                "Not a calibrated probability."
            ),
        )


# =====================================================================
# SUMMARY STATISTICS
# =====================================================================

def calculate_statistics(
    susceptibility: np.ndarray,
    risk: np.ndarray,
    nodata: float | None,
) -> dict:

    valid = (
        np.isfinite(
            susceptibility
        )
        &
        np.isfinite(
            risk
        )
    )

    if nodata is not None:

        valid &= (
            susceptibility != nodata
        )

    values_s = susceptibility[
        valid
    ]

    values_r = risk[
        valid
    ]

    if len(values_r) == 0:

        raise ValueError(
            "No valid cells available for statistics."
        )

    return {
        "valid_cells": int(
            len(values_r)
        ),

        "susceptibility_min": float(
            np.min(values_s)
        ),

        "susceptibility_mean": float(
            np.mean(values_s)
        ),

        "susceptibility_max": float(
            np.max(values_s)
        ),

        "risk_min": float(
            np.min(values_r)
        ),

        "risk_mean": float(
            np.mean(values_r)
        ),

        "risk_max": float(
            np.max(values_r)
        ),

        "risk_p50": float(
            np.percentile(
                values_r,
                50,
            )
        ),

        "risk_p90": float(
            np.percentile(
                values_r,
                90,
            )
        ),

        "risk_p95": float(
            np.percentile(
                values_r,
                95,
            )
        ),

        "risk_p99": float(
            np.percentile(
                values_r,
                99,
            )
        ),
    }


# =====================================================================
# MAIN
# =====================================================================

def main():

    print("=" * 72)
    print(
        "WAYANAD FORECAST DYNAMIC LANDSLIDE RISK ENGINE"
    )
    print("=" * 72)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Check inputs
    # ---------------------------------------------------------------

    for path in [
        MODEL_A_RASTER,
        MODEL_B_RASTER,
        FORECAST_JSON,
        STRESS_REFERENCE_JSON,
    ]:

        require_file(path)

    # ---------------------------------------------------------------
    # Load rainfall forecast
    # ---------------------------------------------------------------

    forecast_df = (
        load_and_validate_forecast(
            FORECAST_JSON
        )
    )

    forecast_reference_time = (
        forecast_df["time"].iloc[0]
    )

    forecast_end_time = (
        forecast_df["time"].iloc[-1]
    )

    print()
    print("FORECAST")
    print("-" * 72)

    print(
        f"Reference: {forecast_reference_time}"
    )

    print(
        f"End:       {forecast_end_time}"
    )

    print(
        f"Hours:     {len(forecast_df)}"
    )

    # ---------------------------------------------------------------
    # Aggregate rainfall
    # ---------------------------------------------------------------

    forecast_totals = (
        calculate_forecast_totals(
            forecast_df
        )
    )

    print()
    print("FORECAST RAINFALL")
    print("-" * 72)

    for horizon in [
        "24h",
        "72h",
        "7day",
    ]:

        print(
            f"{horizon:>5}: "
            f"{forecast_totals[horizon]:.1f} mm"
        )

    # ---------------------------------------------------------------
    # Load stress reference
    # ---------------------------------------------------------------

    reference = (
        load_json(
            STRESS_REFERENCE_JSON
        )
    )

    # ---------------------------------------------------------------
    # Convert rainfall to stress
    # ---------------------------------------------------------------

    rainfall_stress = {}

    print()
    print("RAINFALL STRESS")
    print("-" * 72)

    for horizon in [
        "24h",
        "72h",
        "7day",
    ]:

        stress = rainfall_to_stress(
            forecast_totals[horizon],
            reference,
            horizon,
        )

        rainfall_stress[horizon] = stress

        print(
            f"{horizon:>5}: "
            f"{stress:.6f}"
        )

    # ---------------------------------------------------------------
    # Combined stress
    # ---------------------------------------------------------------

    combined_stress = (
        STRESS_WEIGHTS["24h"]
        * rainfall_stress["24h"]

        +

        STRESS_WEIGHTS["72h"]
        * rainfall_stress["72h"]

        +

        STRESS_WEIGHTS["7day"]
        * rainfall_stress["7day"]
    )

    combined_stress = float(
        np.clip(
            combined_stress,
            0.0,
            1.0,
        )
    )

    print()
    print(
        f"COMBINED STRESS: "
        f"{combined_stress:.6f}"
    )

    # ---------------------------------------------------------------
    # Open susceptibility rasters
    # ---------------------------------------------------------------

    rows = []

    with rasterio.open(
        MODEL_A_RASTER
    ) as src_a, rasterio.open(
        MODEL_B_RASTER
    ) as src_b:

        validate_rasters(
            src_a,
            src_b,
        )

        susceptibility_a = (
            src_a.read(1)
            .astype(np.float32)
        )

        susceptibility_b = (
            src_b.read(1)
            .astype(np.float32)
        )

        nodata_a = src_a.nodata
        nodata_b = src_b.nodata

        # -----------------------------------------------------------
        # Models
        # -----------------------------------------------------------

        models = {
            "model_a_with_gsi": (
                susceptibility_a,
                src_a,
                nodata_a,
            ),

            "model_b_without_gsi": (
                susceptibility_b,
                src_b,
                nodata_b,
            ),
        }

        # -----------------------------------------------------------
        # Horizon risk maps
        # -----------------------------------------------------------

        for model_name, (
            susceptibility,
            template,
            nodata,
        ) in models.items():

            print()
            print(
                f"MODEL: {model_name}"
            )

            for horizon in [
                "24h",
                "72h",
                "7day",
            ]:

                stress = (
                    rainfall_stress[
                        horizon
                    ]
                )

                risk = calculate_risk(
                    susceptibility,
                    stress,
                    nodata,
                )

                output = (
                    OUTPUT_DIR /
                    (
                        "wayanad_dynamic_risk_"
                        f"{model_name.replace('model_a_with_gsi', 'model_a')}"
                        f"{'_'.join(['', horizon])}.tif"
                    )
                )

                # Cleaner explicit filenames.
                output = (
                    OUTPUT_DIR /
                    f"wayanad_dynamic_risk_"
                    f"{'model_a' if model_name == 'model_a_with_gsi' else 'model_b'}"
                    f"_{horizon}.tif"
                )

                write_raster(
                    output,
                    template,
                    risk,
                    stress,
                    horizon,
                )

                statistics = (
                    calculate_statistics(
                        susceptibility,
                        risk,
                        nodata,
                    )
                )

                rows.append(
                    {
                        "model": model_name,
                        "horizon": horizon,
                        "forecast_reference_time":
                            forecast_reference_time.isoformat(),
                        "forecast_end_time":
                            forecast_end_time.isoformat(),
                        "forecast_rainfall_mm":
                            forecast_totals[
                                horizon
                            ],
                        "rainfall_stress":
                            stress,
                        **statistics,
                    }
                )

                print(
                    f"  {horizon}: "
                    f"stress={stress:.6f} "
                    f"mean_risk="
                    f"{statistics['risk_mean']:.6f}"
                )

            # -------------------------------------------------------
            # Combined risk
            # -------------------------------------------------------

            combined_risk = calculate_risk(
                susceptibility,
                combined_stress,
                nodata,
            )

            output = (
                OUTPUT_DIR /
                f"wayanad_dynamic_risk_"
                f"{'model_a' if model_name == 'model_a_with_gsi' else 'model_b'}"
                "_combined.tif"
            )

            write_raster(
                output,
                template,
                combined_risk,
                combined_stress,
                "combined",
            )

            statistics = (
                calculate_statistics(
                    susceptibility,
                    combined_risk,
                    nodata,
                )
            )

            rows.append(
                {
                    "model": model_name,
                    "horizon": "combined",
                    "forecast_reference_time":
                        forecast_reference_time.isoformat(),
                    "forecast_end_time":
                        forecast_end_time.isoformat(),
                    "forecast_rainfall_24h_mm":
                        forecast_totals["24h"],
                    "forecast_rainfall_72h_mm":
                        forecast_totals["72h"],
                    "forecast_rainfall_7day_mm":
                        forecast_totals["7day"],
                    "rainfall_stress":
                        combined_stress,
                    **statistics,
                }
            )

            print(
                f"  combined: "
                f"stress={combined_stress:.6f} "
                f"mean_risk="
                f"{statistics['risk_mean']:.6f}"
            )

    # ---------------------------------------------------------------
    # Save summary
    # ---------------------------------------------------------------

    summary = pd.DataFrame(
        rows
    )

    summary.to_parquet(
        SUMMARY_PARQUET,
        index=False,
    )

    # ---------------------------------------------------------------
    # Save metadata
    # ---------------------------------------------------------------

    metadata = {
        "project": (
            "Wayanad AI-powered dynamic "
            "landslide risk"
        ),

        "risk_type": (
            "forecast_dynamic_landslide_risk"
        ),

        "forecast_reference_time":
            forecast_reference_time.isoformat(),

        "forecast_end_time":
            forecast_end_time.isoformat(),

        "forecast_hours":
            int(len(forecast_df)),

        "forecast_rainfall_mm":
            forecast_totals,

        "rainfall_stress":
            rainfall_stress,

        "combined_stress":
            combined_stress,

        "combined_stress_weights":
            STRESS_WEIGHTS,

        "formula":
            (
                "dynamic_risk = "
                "spatial_susceptibility "
                "* rainfall_stress"
            ),

        "spatial_model_a":
            str(MODEL_A_RASTER),

        "spatial_model_b":
            str(MODEL_B_RASTER),

        "rainfall_reference":
            str(STRESS_REFERENCE_JSON),

        "historical_period":
            reference.get(
                "historical_period"
            ),

        "historical_event_validation":
            reference.get(
                "historical_event_validation"
            ),

        "limitations": [
            (
                "No 2026 observed rainfall dataset "
                "is currently available."
            ),
            (
                "Outputs represent forecast-risk "
                "scenarios rather than live current risk."
            ),
            (
                "Risk scores are not calibrated "
                "landslide probabilities."
            ),
            (
                "Risk scores are not evacuation "
                "or relocation thresholds."
            ),
            (
                "Rainfall is currently a "
                "district-level temporal signal."
            ),
        ],
    }

    with METADATA_JSON.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            metadata,
            f,
            indent=2,
        )

    # ---------------------------------------------------------------
    # Final QA
    # ---------------------------------------------------------------

    print()
    print("=" * 72)
    print(
        "DYNAMIC RISK ENGINE COMPLETE"
    )
    print("=" * 72)

    print()
    print("Summary:")
    print(summary.to_string(index=False))

    print()
    print(
        f"Summary file: {SUMMARY_PARQUET}"
    )

    print(
        f"Metadata file: {METADATA_JSON}"
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "These are forecast dynamic-risk scores, "
        "not calibrated probabilities."
    )


if __name__ == "__main__":
    main()