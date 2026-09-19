import rasterio
import geopandas as gpd
import numpy as np
from rasterio.features import geometry_mask


SLOPE = (
    "data/processed/terrain/"
    "wayanad_copernicus_slope_degrees.tif"
)

BOUNDARY = (
    "data/raw/boundaries/"
    "wayanad_boundary.geojson"
)


gdf = gpd.read_file(BOUNDARY)

with rasterio.open(SLOPE) as src:

    print("Slope:", SLOPE)
    print("CRS:", src.crs)
    print("Shape:", (src.height, src.width))
    print("Resolution:", src.res)
    print("Bounds:", src.bounds)
    print("NoData:", src.nodata)

    boundary = gdf.to_crs(src.crs)

    inside = geometry_mask(
        boundary.geometry,
        transform=src.transform,
        invert=True,
        out_shape=(src.height, src.width),
    )

    data = src.read(1)

    values = data[inside]

    valid = (
        np.isfinite(values) &
        (values != src.nodata)
    )

    valid_values = values[valid]

    print()
    print("=" * 60)
    print("WAYANAD SLOPE QA")
    print("=" * 60)

    print("Wayanad pixels:", values.size)
    print("Valid pixels:", int(valid.sum()))
    print("Invalid pixels:", int((~valid).sum()))

    coverage = 100 * valid.sum() / values.size

    print(
        f"Valid coverage inside Wayanad: "
        f"{coverage:.4f}%"
    )

    if valid.any():

        print()
        print("Slope statistics")

        print(
            "Min:",
            float(valid_values.min()),
            "degrees"
        )

        print(
            "Max:",
            float(valid_values.max()),
            "degrees"
        )

        print(
            "Mean:",
            float(valid_values.mean()),
            "degrees"
        )

        for p in [1, 5, 25, 50, 75, 95, 99]:

            print(
                f"P{p:02d}:",
                float(np.percentile(valid_values, p))
            )

        print()
        print("Slope distribution")

        for name, low, high in [
            ("0-5°", 0, 5),
            ("5-15°", 5, 15),
            ("15-30°", 15, 30),
            ("30-45°", 30, 45),
            ("45°+", 45, np.inf),
        ]:

            count = np.sum(
                (valid_values >= low) &
                (valid_values < high)
            )

            print(
                f"{name}: "
                f"{count:,} pixels "
                f"({100 * count / valid_values.size:.2f}%)"
            )

    print("=" * 60)