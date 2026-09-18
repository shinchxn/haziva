import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin


SHP = "data/raw/landslide/susceptibility/gsi_2022/Wayanad/Wayanad_GSI_LS.shp"
DEM = "data/raw/dem/wayanad_srtm_gl1_30m.tif"
OUTPUT = "data/processed/landslide/susceptibility/wayanad_gsi_susceptibility.tif"

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# Read GSI susceptibility polygons
gdf = gpd.read_file(SHP)

print("GSI CRS:", gdf.crs)
print("Features:", len(gdf))
print("Classes:", gdf["Susceptibi"].unique())

# Read DEM only to use its grid
with rasterio.open(DEM) as dem:
    dem_crs = dem.crs
    transform = dem.transform
    width = dem.width
    height = dem.height

print("DEM CRS:", dem_crs)
print("DEM size:", width, "x", height)

# Reproject GSI to DEM CRS if necessary
if gdf.crs != dem_crs:
    gdf = gdf.to_crs(dem_crs)

# Convert classes to numeric values
class_values = {
    "Low": 1,
    "Moderate": 2,
    "High": 3
}

shapes = [
    (geom, class_values[str(cls).strip()])
    for geom, cls in zip(gdf.geometry, gdf["Susceptibi"])
    if geom is not None and not geom.is_empty
]

# Rasterize onto DEM grid
susceptibility = rasterize(
    shapes,
    out_shape=(height, width),
    transform=transform,
    fill=0,
    dtype="uint8"
)

# Save raster
with rasterio.open(
    OUTPUT,
    "w",
    driver="GTiff",
    height=height,
    width=width,
    count=1,
    dtype="uint8",
    crs=dem_crs,
    transform=transform,
    nodata=0,
    compress="lzw"
) as dst:
    dst.write(susceptibility, 1)

print()
print("SUCCESS")
print("Output:", OUTPUT)
print("Values:")
print("  0 = No GSI coverage")
print("  1 = Low")
print("  2 = Moderate")
print("  3 = High")