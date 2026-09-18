import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from rasterio.warp import reproject, Resampling


SHP = "data/raw/landslide/susceptibility/gsi_2022/Wayanad/Wayanad_GSI_LS.shp"
REFERENCE = "data/processed/terrain/wayanad_slope_degrees.tif"
OUTPUT = "data/processed/landslide/susceptibility/wayanad_gsi_susceptibility_aligned.tif"

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# --------------------------------------------------
# 1. Read reference slope grid
# --------------------------------------------------

with rasterio.open(REFERENCE) as ref:
    ref_crs = ref.crs
    ref_transform = ref.transform
    ref_width = ref.width
    ref_height = ref.height
    ref_bounds = ref.bounds

print("Reference CRS:", ref_crs)
print("Reference size:", ref_width, "x", ref_height)
print("Reference bounds:", ref_bounds)

# --------------------------------------------------
# 2. Read GSI susceptibility polygons
# --------------------------------------------------

gdf = gpd.read_file(SHP)

print("GSI CRS:", gdf.crs)
print("GSI features:", len(gdf))
print("GSI classes:", gdf["Susceptibi"].unique())

# Reproject polygons to reference CRS
gdf = gdf.to_crs(ref_crs)

# --------------------------------------------------
# 3. Rasterize onto reference grid
# --------------------------------------------------

class_values = {
    "Low": 1,
    "Moderate": 2,
    "High": 3
}

shapes = []

for geom, cls in zip(gdf.geometry, gdf["Susceptibi"]):

    if geom is None or geom.is_empty:
        continue

    value = class_values.get(str(cls).strip())

    if value is not None:
        shapes.append((geom, value))

susceptibility = rasterize(
    shapes,
    out_shape=(ref_height, ref_width),
    transform=ref_transform,
    fill=0,
    dtype="uint8"
)

# --------------------------------------------------
# 4. Save aligned raster
# --------------------------------------------------

with rasterio.open(
    OUTPUT,
    "w",
    driver="GTiff",
    height=ref_height,
    width=ref_width,
    count=1,
    dtype="uint8",
    crs=ref_crs,
    transform=ref_transform,
    nodata=0,
    compress="lzw"
) as dst:

    dst.write(susceptibility, 1)

print()
print("SUCCESS")
print("Output:", OUTPUT)
print("Low:", np.sum(susceptibility == 1))
print("Moderate:", np.sum(susceptibility == 2))
print("High:", np.sum(susceptibility == 3))
print("No GSI coverage:", np.sum(susceptibility == 0))