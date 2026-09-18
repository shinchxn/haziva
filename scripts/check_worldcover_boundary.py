import rasterio
import geopandas as gpd
from rasterio.mask import mask
from pathlib import Path

RASTER = Path(
    "data/processed/exposure/wayanad_worldcover_10m.tif"
)

BOUNDARY = Path(
    "data/raw/boundaries/wayanad_boundary.geojson"
)

with rasterio.open(RASTER) as src:
    boundary = gpd.read_file(BOUNDARY)

    boundary = boundary.to_crs(src.crs)

    clipped, transform = mask(
        src,
        boundary.geometry,
        crop=False,
        nodata=0
    )

    data = clipped[0]

    total = data.size
    valid = (data != 0).sum()
    nodata = total - valid

    print("\n=== WORLD COVER / WAYANAD COVERAGE ===")
    print("Raster CRS:", src.crs)
    print("Boundary CRS:", boundary.crs)
    print("Total raster pixels:", total)
    print("Valid pixels inside Wayanad:", valid)
    print("NoData pixels:", nodata)

    print(
        "Valid percentage:",
        round(100 * valid / total, 2),
        "%"
    )

    print(
        "NoData percentage:",
        round(100 * nodata / total, 2),
        "%"
    )
