import os
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling


INPUT = "data/raw/dem/wayanad_srtm_gl1_30m.tif"
OUTPUT = "data/processed/terrain/wayanad_slope_degrees.tif"

# Wayanad is approximately in UTM Zone 43N
TARGET_CRS = "EPSG:32643"


os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)


# --------------------------------------------------
# 1. Read DEM
# --------------------------------------------------

with rasterio.open(INPUT) as src:

    print("Input CRS:", src.crs)
    print("Input size:", src.width, "x", src.height)
    print("Input bounds:", src.bounds)

    transform, width, height = calculate_default_transform(
        src.crs,
        TARGET_CRS,
        src.width,
        src.height,
        *src.bounds
    )

    dem = np.empty((height, width), dtype=np.float32)

    reproject(
        source=rasterio.band(src, 1),
        destination=dem,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=transform,
        dst_crs=TARGET_CRS,
        resampling=Resampling.bilinear
    )

    nodata = src.nodata


# --------------------------------------------------
# 2. Handle invalid DEM values
# --------------------------------------------------

if nodata is not None:
    invalid = dem == nodata
else:
    invalid = ~np.isfinite(dem)

dem[invalid] = np.nan


# --------------------------------------------------
# 3. Calculate terrain slope
# --------------------------------------------------

# Pixel dimensions in metres
pixel_size_x = transform.a
pixel_size_y = abs(transform.e)

print("Pixel size X:", pixel_size_x, "metres")
print("Pixel size Y:", pixel_size_y, "metres")

# Elevation gradients
dz_dy, dz_dx = np.gradient(
    dem,
    pixel_size_y,
    pixel_size_x
)

# Slope in radians
slope_radians = np.arctan(
    np.sqrt(
        dz_dx ** 2 +
        dz_dy ** 2
    )
)

# Convert to degrees
slope_degrees = np.degrees(slope_radians)

# Restore nodata
slope_degrees[np.isnan(slope_degrees)] = -9999


# --------------------------------------------------
# 4. Save slope raster
# --------------------------------------------------

profile = {
    "driver": "GTiff",
    "height": height,
    "width": width,
    "count": 1,
    "dtype": "float32",
    "crs": TARGET_CRS,
    "transform": transform,
    "nodata": -9999,
    "compress": "lzw"
}

with rasterio.open(OUTPUT, "w", **profile) as dst:
    dst.write(slope_degrees.astype(np.float32), 1)


print("\nSlope calculation completed.")
print("Output:", OUTPUT)