from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import rasterio


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

TRAINING_BASE = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "wayanad_landslide_training_base.parquet"
)

SLOPE_RASTER = (
    BASE_DIR
    / "data"
    / "processed"
    / "terrain"
    / "wayanad_copernicus_slope_degrees.tif"
)

MODEL_DIR = (
    BASE_DIR
    / "models"
    / "spatial_baseline"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "predictions"
)

MODEL_A_PATH = MODEL_DIR / "model_a_with_gsi.joblib"
MODEL_B_PATH = MODEL_DIR / "model_b_without_gsi.joblib"


# ============================================================
# HELPERS
# ============================================================

def check_file(path: Path, description: str):
    if not path.exists():
        raise FileNotFoundError(
            f"{description} not found:\n{path}"
        )


def write_prediction_raster(
    output_path: Path,
    predictions: np.ndarray,
    reference_raster_path: Path,
):
    """
    Write 1D predictions back to the valid Wayanad cells
    using the exact reference raster grid.
    """

    with rasterio.open(reference_raster_path) as src:
        profile = src.profile.copy()
        height = src.height
        width = src.width
        transform = src.transform
        crs = src.crs

        slope = src.read(1)

        # Valid cells are cells where slope is not nodata
        if src.nodata is None:
            valid_mask = np.isfinite(slope)
        else:
            valid_mask = (
                np.isfinite(slope)
                & (slope != src.nodata)
            )

        expected_count = int(valid_mask.sum())

        if len(predictions) != expected_count:
            raise ValueError(
                f"Prediction count mismatch.\n"
                f"Predictions: {len(predictions)}\n"
                f"Valid raster cells: {expected_count}"
            )

        output_array = np.full(
            (height, width),
            -9999.0,
            dtype=np.float32,
        )

        output_array[valid_mask] = predictions.astype(
            np.float32
        )

        profile.update(
            driver="GTiff",
            dtype="float32",
            count=1,
            nodata=-9999.0,
            compress="deflate",
            predictor=2,
        )

        with rasterio.open(
            output_path,
            "w",
            **profile,
        ) as dst:
            dst.write(output_array, 1)

            dst.set_band_description(
                1,
                "Landslide susceptibility probability"
            )

            dst.update_tags(
                MODEL_OUTPUT="Random Forest probability",
                DESCRIPTION=(
                    "Spatial landslide susceptibility "
                    "prediction probability"
                ),
                CRS=str(crs),
                RESOLUTION="30m",
            )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("WAYANAD SPATIAL MODEL INFERENCE")
    print("=" * 70)

    # --------------------------------------------------------
    # Check inputs
    # --------------------------------------------------------

    check_file(
        TRAINING_BASE,
        "Training feature dataset"
    )

    check_file(
        SLOPE_RASTER,
        "Reference slope raster"
    )

    check_file(
        MODEL_A_PATH,
        "Model A"
    )

    check_file(
        MODEL_B_PATH,
        "Model B"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Load models
    # --------------------------------------------------------

    print("\nLoading trained models...")

    model_a_bundle = joblib.load(MODEL_A_PATH)
    model_b_bundle = joblib.load(MODEL_B_PATH)

    model_a = model_a_bundle["model"]
    model_b = model_b_bundle["model"]

    features_a = model_a_bundle["features"]
    features_b = model_b_bundle["features"]

    print("Model A loaded")
    print("Model B loaded")

    print("\nModel A features:")
    print(features_a)

    print("\nModel B features:")
    print(features_b)

    # --------------------------------------------------------
    # Load feature dataset
    # --------------------------------------------------------

    print("\nLoading Wayanad feature dataset...")

    df = pd.read_parquet(TRAINING_BASE)

    print("Dataset shape:", df.shape)

    # --------------------------------------------------------
    # Validate required features
    # --------------------------------------------------------

    missing_a = [
        f for f in features_a
        if f not in df.columns
    ]

    missing_b = [
        f for f in features_b
        if f not in df.columns
    ]

    if missing_a:
        raise ValueError(
            f"Model A missing features: {missing_a}"
        )

    if missing_b:
        raise ValueError(
            f"Model B missing features: {missing_b}"
        )

    # --------------------------------------------------------
    # Check row count
    # --------------------------------------------------------

    if len(df) == 0:
        raise ValueError("Feature dataset is empty.")

    # --------------------------------------------------------
    # Prepare model inputs
    # --------------------------------------------------------

    print("\nPreparing Model A input...")

    X_a = df[features_a].copy()

    print(
        "Model A input shape:",
        X_a.shape
    )

    print("\nPreparing Model B input...")

    X_b = df[features_b].copy()

    print(
        "Model B input shape:",
        X_b.shape
    )

    # --------------------------------------------------------
    # Validate numeric values
    # --------------------------------------------------------

    if not np.isfinite(X_a.to_numpy()).all():
        raise ValueError(
            "Model A input contains NaN or infinite values."
        )

    if not np.isfinite(X_b.to_numpy()).all():
        raise ValueError(
            "Model B input contains NaN or infinite values."
        )

    # --------------------------------------------------------
    # Model A prediction
    # --------------------------------------------------------

    print("\nRunning Model A inference...")

    probability_a = model_a.predict_proba(
        X_a
    )[:, 1]

    print(
        "Model A probability range:",
        float(probability_a.min()),
        "to",
        float(probability_a.max())
    )

    print(
        "Model A mean probability:",
        float(probability_a.mean())
    )

    # --------------------------------------------------------
    # Model B prediction
    # --------------------------------------------------------

    print("\nRunning Model B inference...")

    probability_b = model_b.predict_proba(
        X_b
    )[:, 1]

    print(
        "Model B probability range:",
        float(probability_b.min()),
        "to",
        float(probability_b.max())
    )

    print(
        "Model B mean probability:",
        float(probability_b.mean())
    )

    # --------------------------------------------------------
    # Save tabular predictions
    # --------------------------------------------------------

    prediction_table = df[
        ["row", "col", "x", "y"]
    ].copy()

    prediction_table[
        "model_a_probability"
    ] = probability_a

    prediction_table[
        "model_b_probability"
    ] = probability_b

    prediction_parquet = (
        OUTPUT_DIR
        / "wayanad_spatial_model_predictions.parquet"
    )

    prediction_table.to_parquet(
        prediction_parquet,
        index=False
    )

    print(
        "\nPrediction table saved:",
        prediction_parquet
    )

    # --------------------------------------------------------
    # Save Model A raster
    # --------------------------------------------------------

    model_a_raster = (
        OUTPUT_DIR
        / "wayanad_model_a_probability.tif"
    )

    write_prediction_raster(
        model_a_raster,
        probability_a,
        SLOPE_RASTER,
    )

    print(
        "Model A raster saved:",
        model_a_raster
    )

    # --------------------------------------------------------
    # Save Model B raster
    # --------------------------------------------------------

    model_b_raster = (
        OUTPUT_DIR
        / "wayanad_model_b_probability.tif"
    )

    write_prediction_raster(
        model_b_raster,
        probability_b,
        SLOPE_RASTER,
    )

    print(
        "Model B raster saved:",
        model_b_raster
    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("INFERENCE COMPLETE")
    print("=" * 70)

    print(
        "Cells processed:",
        len(df)
    )

    print("\nOutputs:")

    print(model_a_raster)
    print(model_b_raster)
    print(prediction_parquet)

    print("\nBoth models successfully generated spatial predictions.")


if __name__ == "__main__":
    main()