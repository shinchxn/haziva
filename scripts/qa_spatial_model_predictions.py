from pathlib import Path

import numpy as np
import rasterio


BASE_DIR = Path(__file__).resolve().parents[1]

PREDICTION_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "predictions"
)

MODEL_A = (
    PREDICTION_DIR
    / "wayanad_model_a_probability.tif"
)

MODEL_B = (
    PREDICTION_DIR
    / "wayanad_model_b_probability.tif"
)


def inspect_raster(path):
    print("\n" + "=" * 70)
    print(path.name)
    print("=" * 70)

    with rasterio.open(path) as src:

        arr = src.read(1)

        print("CRS:", src.crs)
        print("Shape:", src.height, "x", src.width)
        print("Resolution:", src.res)
        print("Bounds:", src.bounds)
        print("NoData:", src.nodata)
        print("Dtype:", arr.dtype)

        valid = (
            np.isfinite(arr)
            & (arr != src.nodata)
        )

        values = arr[valid]

        print("Valid cells:", int(valid.sum()))
        print("NoData cells:", int((~valid).sum()))

        print("Min:", float(values.min()))
        print("Max:", float(values.max()))
        print("Mean:", float(values.mean()))

        print(
            "NaN:",
            int(np.isnan(values).sum())
        )

        print(
            "Infinite:",
            int(np.isinf(values).sum())
        )

        outside_range = (
            (values < 0)
            | (values > 1)
        )

        print(
            "Values outside [0,1]:",
            int(outside_range.sum())
        )

        # Expected number of valid Wayanad cells
        expected = 2_356_650

        print(
            "Expected valid cells:",
            expected
        )

        if len(values) != expected:
            raise ValueError(
                f"Valid cell count mismatch: "
                f"{len(values)} != {expected}"
            )

        if np.isnan(values).any():
            raise ValueError(
                "Prediction contains NaN values."
            )

        if np.isinf(values).any():
            raise ValueError(
                "Prediction contains infinite values."
            )

        if (values < 0).any() or (values > 1).any():
            raise ValueError(
                "Prediction contains values outside [0,1]."
            )

        if src.crs is None:
            raise ValueError(
                "Prediction raster has no CRS."
            )

        if src.res != (30.0, 30.0):
            raise ValueError(
                f"Unexpected resolution: {src.res}"
            )

        print("\nQA PASSED")


def main():

    if not MODEL_A.exists():
        raise FileNotFoundError(MODEL_A)

    if not MODEL_B.exists():
        raise FileNotFoundError(MODEL_B)

    print("=" * 70)
    print("WAYANAD SPATIAL MODEL PREDICTION QA")
    print("=" * 70)

    inspect_raster(MODEL_A)
    inspect_raster(MODEL_B)

    print("\n" + "=" * 70)
    print("ALL PREDICTION QA CHECKS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()