from pathlib import Path

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize


# --------------------------------------------------
# INPUTS
# --------------------------------------------------

INVENTORY = Path(
    "data/processed/landslide/inventory/"
    "wayanad_bhuvan_landslides_wms_derived.geojson"
)

REFERENCE = Path(
    "data/processed/terrain/"
    "wayanad_slope_degrees.tif"
)

OUTPUT = Path(
    "data/processed/landslide/inventory/"
    "wayanad_historical_landslide_presence_30m.tif"
)


print("=" * 80)
print("RASTERIZING HISTORICAL LANDSLIDE INVENTORY")
print("=" * 80)


# --------------------------------------------------
# LOAD REFERENCE GRID
# --------------------------------------------------

with rasterio.open(REFERENCE) as src:

    profile = src.profile.copy()

    height = src.height
    width = src.width
    transform = src.transform
    crs = src.crs

    slope = src.read(1)

    nodata = src.nodata

    valid_reference = np.ones(
        slope.shape,
        dtype=bool
    )

    if nodata is not None:
        valid_reference &= slope != nodata

    valid_reference &= np.isfinite(slope)


print()
print("Reference grid:")
print(f"CRS:       {crs}")
print(f"Size:      {width} x {height}")
print(f"Valid:     {valid_reference.sum():,}")


# --------------------------------------------------
# LOAD INVENTORY
# --------------------------------------------------

gdf = gpd.read_file(INVENTORY)

print()
print("Inventory polygons:", len(gdf))
print("Inventory CRS:", gdf.crs)


if gdf.crs is None:
    raise ValueError(
        "Inventory has no CRS."
    )


# Reproject to exact reference CRS
gdf = gdf.to_crs(crs)


# --------------------------------------------------
# RASTERIZE
# --------------------------------------------------

shapes = [
    (geom, 1)
    for geom in gdf.geometry
    if geom is not None
    and not geom.is_empty
]


landslide = rasterize(
    shapes=shapes,
    out_shape=(height, width),
    transform=transform,
    fill=0,
    dtype="uint8",
    all_touched=False,
)


# Don't label NoData terrain pixels
landslide[~valid_reference] = 0


# --------------------------------------------------
# STATISTICS
# --------------------------------------------------

positive_pixels = int(
    (landslide == 1).sum()
)

valid_pixels = int(
    valid_reference.sum()
)

positive_fraction = (
    100 * positive_pixels / valid_pixels
)


pixel_width = abs(transform.a)
pixel_height = abs(transform.e)

pixel_area_m2 = (
    pixel_width * pixel_height
)

positive_area_km2 = (
    positive_pixels
    * pixel_area_m2
    / 1_000_000
)


print()
print("-" * 80)
print("LANDSLIDE LABEL STATISTICS")
print("-" * 80)

print(
    f"Positive 30m cells: {positive_pixels:,}"
)

print(
    f"Valid reference cells: {valid_pixels:,}"
)

print(
    f"Positive fraction: {positive_fraction:.4f}%"
)

print(
    f"Approx. rasterized positive area: "
    f"{positive_area_km2:.4f} km²"
)


# --------------------------------------------------
# SAVE
# --------------------------------------------------

profile.update(
    dtype="uint8",
    count=1,
    nodata=0,
    compress="lzw",
)


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)


with rasterio.open(
    OUTPUT,
    "w",
    **profile
) as dst:

    dst.write(
        landslide,
        1
    )


print()
print("=" * 80)
print("COMPLETE")
print("=" * 80)

print()
print("Output:")
print(OUTPUT)

print()
print(
    "Encoding:"
)

print(
    "0 = no mapped historical landslide"
)

print(
    "1 = mapped historical landslide"
)

print()
print(
    "Source: Bhuvan WMS kl_landslides_new"
)

print(
    "Representation: WMS-derived"
)