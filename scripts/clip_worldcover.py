import rasterio
from rasterio.mask import mask
import geopandas as gpd
from pathlib import Path

INPUT = Path(
    "data/raw/landuse/ESA_WorldCover_10m_2021_v200_N09E075_Map.tif"
)

BOUNDARY = Path(
    "data/raw/boundaries/wayanad_boundary.geojson"
)

OUTPUT = Path(
    "data/processed/exposure/wayanad_worldcover_10m.tif"
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# Load Wayanad boundary
boundary = gpd.read_file(BOUNDARY)

with rasterio.open(INPUT) as src:

    # Make boundary CRS match raster CRS
    boundary = boundary.to_crs(src.crs)

    geometries = boundary.geometry.values

    clipped, transform = mask(
        src,
        geometries,
        crop=True,
        nodata=0
    )

    profile = src.profile.copy()

    profile.update({
        "height": clipped.shape[1],
        "width": clipped.shape[2],
        "transform": transform,
        "nodata": 0,
        "compress": "lzw"
    })

    with rasterio.open(OUTPUT, "w", **profile) as dst:
        dst.write(clipped)

print("WorldCover clipped successfully.")
print("Output:", OUTPUT)
print("CRS:", profile["crs"])
print("Size:", profile["width"], profile["height"])
print("Resolution:", profile["transform"].a, abs(profile["transform"].e))