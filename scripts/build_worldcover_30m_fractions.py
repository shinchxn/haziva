from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import reproject, Resampling
from rasterio.windows import Window


WORLD_COVER = Path(
    "data/raw/landuse/"
    "ESA_WorldCover_10m_2021_v200_N09E075_Map.tif"
)

WAYANAD = Path(
    "data/raw/boundaries/wayanad_boundary.geojson"
)

TARGET = Path(
    "data/processed/terrain/"
    "wayanad_copernicus_slope_degrees.tif"
)

OUTPUT_DIR = Path(
    "data/processed/exposure/worldcover"
)

OUTPUT = OUTPUT_DIR / "wayanad_worldcover_30m_fractions.tif"


CLASSES = {
    10: "tree_fraction",
    20: "shrub_fraction",
    30: "grass_fraction",
    40: "crop_fraction",
    50: "builtup_fraction",
    60: "bare_fraction",
    80: "water_fraction",
    90: "wetland_fraction",
}


def main():

    print("=" * 70)
    print("WorldCover 10 m -> Copernicus 30 m fractions")
    print("ROW-BLOCK / LOW-MEMORY VERSION")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(TARGET) as target:

        width = target.width
        height = target.height

        print("\nTarget:")
        print("CRS:", target.crs)
        print("Shape:", height, "x", width)
        print("Resolution:", target.res)

        boundary = gpd.read_file(WAYANAD)
        boundary = boundary.to_crs(target.crs)

        # Create one full-size boolean mask.
        # bool = 1 byte/pixel, about 27 MB.
        district_mask = geometry_mask(
            boundary.geometry,
            out_shape=(height, width),
            transform=target.transform,
            invert=True,
        )

        profile = target.profile.copy()

        profile.update(
            driver="GTiff",
            dtype="float32",
            count=len(CLASSES),
            nodata=-9999.0,
            compress="deflate",
            predictor=2,
            tiled=False,
            BIGTIFF="IF_SAFER",
        )

    with rasterio.open(TARGET) as target, \
         rasterio.open(WORLD_COVER) as src, \
         rasterio.open(OUTPUT, "w", **profile) as dst:

        # -----------------------------------------------------
        # Set band descriptions
        # -----------------------------------------------------

        for band_number, name in enumerate(CLASSES.values(), 1):
            dst.set_band_description(
                band_number,
                name
            )

        # -----------------------------------------------------
        # Process ONE target row at a time.
        # -----------------------------------------------------

        for row in range(height):

            if row % 100 == 0 or row == height - 1:
                print(
                    f"Processing row {row + 1:,} / {height:,}"
                )

            target_window = Window(
                col_off=0,
                row_off=row,
                width=width,
                height=1,
            )

            target_transform = target.window_transform(
                target_window
            )

            # Target row geographic bounds
            left, bottom, right, top = (
                rasterio.transform.array_bounds(
                    1,
                    width,
                    target_transform,
                )
            )

            # Convert bounds to WorldCover CRS
            from rasterio.warp import transform_bounds

            src_left, src_bottom, src_right, src_top = (
                transform_bounds(
                    target.crs,
                    src.crs,
                    left,
                    bottom,
                    right,
                    top,
                )
            )

            # Calculate source pixel window
            src_window = rasterio.windows.from_bounds(
                src_left,
                src_bottom,
                src_right,
                src_top,
                src.transform,
            )

            # Expand slightly so boundary pixels are covered.
            src_window = src_window.round_offsets().round_lengths()

            # Read only the WorldCover pixels needed for
            # this single target row.
            source_data = src.read(
                1,
                window=src_window,
                boundless=True,
                fill_value=0,
            )

            source_transform = src.window_transform(
                src_window
            )

            mask_row = district_mask[row:row + 1, :]

            # -------------------------------------------------
            # Process one class at a time.
            # -------------------------------------------------

            for band_number, (class_code, name) in enumerate(
                CLASSES.items(),
                1,
            ):

                binary = (
                    source_data == class_code
                ).astype(np.float32)

                fraction = np.zeros(
                    (1, width),
                    dtype=np.float32,
                )

                reproject(
                    source=binary,
                    destination=fraction,
                    src_transform=source_transform,
                    src_crs=src.crs,
                    dst_transform=target_transform,
                    dst_crs=target.crs,
                    resampling=Resampling.average,
                    dst_nodata=0,
                )

                # Outside Wayanad = NoData
                fraction[~mask_row] = -9999.0

                dst.write(
                    fraction,
                    band_number,
                    window=target_window,
                )

    print("\n" + "=" * 70)
    print("SUCCESS")
    print("=" * 70)
    print("Output:")
    print(OUTPUT)
    print("\nBands:")

    for i, name in enumerate(CLASSES.values(), 1):
        print(f"{i}: {name}")


if __name__ == "__main__":
    main()