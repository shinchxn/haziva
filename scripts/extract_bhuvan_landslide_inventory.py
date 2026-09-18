from pathlib import Path

import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import from_bounds
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape


# --------------------------------------------------
# INPUTS
# --------------------------------------------------

PNG_FILE = Path(
    "data/raw/landslide/inventory/wayanad_bhuvan_landslides.png"
)

BOUNDARY_FILE = Path(
    "data/raw/boundaries/wayanad_boundary.geojson"
)

MASK_TIF = Path(
    "data/processed/landslide/inventory/"
    "wayanad_bhuvan_landslide_mask.tif"
)

OUTPUT_GEOJSON = Path(
    "data/processed/landslide/inventory/"
    "wayanad_bhuvan_landslides_wms_derived.geojson"
)


# --------------------------------------------------
# WMS MAP EXTENT
# --------------------------------------------------

MIN_LON = 75.7722
MIN_LAT = 11.4427
MAX_LON = 76.4356
MAX_LAT = 11.9706


# --------------------------------------------------
# LOAD IMAGE
# --------------------------------------------------

print("=" * 80)
print("BHUVAN WMS LANDSLIDE INVENTORY EXTRACTION")
print("=" * 80)

img = Image.open(PNG_FILE).convert("RGBA")

width, height = img.size

print()
print(f"Image size: {width} x {height}")


arr = np.array(img)

rgb = arr[:, :, :3].astype(np.float32)
alpha = arr[:, :, 3].astype(np.float32)


# --------------------------------------------------
# IDENTIFY LANDSLIDE COLOR
# --------------------------------------------------

# Dominant landslide rendering colour observed
# in the Bhuvan WMS output.
#
# Main colour:
# RGB = (160, 82, 44)

target = np.array(
    [160, 82, 44],
    dtype=np.float32
)

distance = np.sqrt(
    ((rgb - target) ** 2).sum(axis=2)
)

# Include anti-aliased polygon edges.
landslide_mask = (
    (alpha > 20)
    &
    (distance <= 30)
)


print()
print(
    "Detected landslide pixels:",
    int(landslide_mask.sum())
)

print(
    "Detected percentage:",
    round(
        100 * landslide_mask.mean(),
        4
    ),
    "%"
)


# --------------------------------------------------
# LOAD WAYANAD BOUNDARY
# --------------------------------------------------

boundary = gpd.read_file(
    BOUNDARY_FILE
)

if boundary.crs is None:
    raise ValueError(
        "Wayanad boundary has no CRS."
    )

boundary = boundary.to_crs(
    "EPSG:4326"
)

wayanad_geom = boundary.geometry.union_all()


# --------------------------------------------------
# CREATE GEOTIFF MASK
# --------------------------------------------------

transform = from_bounds(
    MIN_LON,
    MIN_LAT,
    MAX_LON,
    MAX_LAT,
    width,
    height
)


MASK_TIF.parent.mkdir(
    parents=True,
    exist_ok=True
)


with rasterio.open(
    MASK_TIF,
    "w",
    driver="GTiff",
    height=height,
    width=width,
    count=1,
    dtype="uint8",
    crs="EPSG:4326",
    transform=transform,
    nodata=0,
    compress="lzw",
) as dst:

    dst.write(
        landslide_mask.astype("uint8"),
        1
    )


print()
print("Saved mask:")
print(MASK_TIF)


# --------------------------------------------------
# POLYGONIZE
# --------------------------------------------------

print()
print("Polygonizing...")


features = []

for geom, value in shapes(
    landslide_mask.astype("uint8"),
    mask=landslide_mask,
    transform=transform,
):

    if value != 1:
        continue

    polygon = shape(geom)

    if polygon.is_empty:
        continue

    # Clip to actual Wayanad boundary
    clipped = polygon.intersection(
        wayanad_geom
    )

    if clipped.is_empty:
        continue

    features.append(
        {
            "geometry": clipped,
            "source": "Bhuvan WMS kl_landslides_new",
            "source_type": "WMS_derived",
        }
    )


print(
    "Polygons before dissolve:",
    len(features)
)


# --------------------------------------------------
# CREATE GEODATAFRAME
# --------------------------------------------------

if not features:
    raise RuntimeError(
        "No landslide polygons were extracted."
    )


gdf = gpd.GeoDataFrame(
    features,
    geometry="geometry",
    crs="EPSG:4326"
)


# --------------------------------------------------
# REMOVE TINY PIXEL ARTIFACTS
# --------------------------------------------------

# The WMS image is approximately 2,000 x 1,600,
# so very tiny objects can be rendering artifacts.
#
# Keep everything above a very small area threshold.
# Calculate area in metres using the same UTM CRS
# as the rest of the Haziva spatial feature stack.
gdf_projected = gdf.to_crs("EPSG:32643")

gdf["area_m2"] = gdf_projected.geometry.area

gdf = gdf[
    gdf["area_m2"] > 1.0
].copy()


# --------------------------------------------------
# DISSOLVE TOUCHING PIECES
# --------------------------------------------------

print(
    "Polygons after filtering:",
    len(gdf)
)

gdf = gpd.GeoDataFrame(
    {
        "source": [
            "Bhuvan WMS kl_landslides_new"
        ] * len(gdf),

        "source_type": [
            "WMS_derived"
        ] * len(gdf),

        "area_m2": gdf["area_m2"].values,
    },
    geometry=gdf.geometry,
    crs="EPSG:4326"
)

# --------------------------------------------------
# SAVE
# --------------------------------------------------

OUTPUT_GEOJSON.parent.mkdir(
    parents=True,
    exist_ok=True
)

gdf.to_file(
    OUTPUT_GEOJSON,
    driver="GeoJSON"
)


print()
print("=" * 80)
print("EXTRACTION COMPLETE")
print("=" * 80)

print(
    "Final polygons:",
    len(gdf)
)

print()
print("Output:")
print(OUTPUT_GEOJSON)

print()
print(
    "IMPORTANT:"
)

print(
    "This is a WMS-render-derived inventory."
)

print(
    "It is NOT the original NRSC/Bhuvan vector dataset."
)

print(
    "Use it as a historical spatial label/evidence layer "
    "and retain the source metadata."
)