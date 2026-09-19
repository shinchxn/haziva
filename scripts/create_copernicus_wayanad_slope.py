from pathlib import Path

import numpy as np
import rasterio
import geopandas as gpd

from rasterio.warp import (
    calculate_default_transform,
    reproject,
    Resampling,
)
from rasterio.features import geometry_mask


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

DEM = Path(
    "data/raw/dem/wayanad_copernicus_glo30_merged.tif"
)

BOUNDARY = Path(
    "data/raw/boundaries/wayanad_boundary.geojson"
)

OUTPUT = Path(
    "data/processed/terrain/wayanad_copernicus_slope_degrees.tif"
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Load Wayanad boundary
# ---------------------------------------------------------

gdf = gpd.read_file(BOUNDARY)

if gdf.crs is None:
    raise ValueError("Wayanad boundary has no CRS.")

print("Boundary CRS:", gdf.crs)

# UTM Zone 43N covers Wayanad
TARGET_CRS = "EPSG:32643"

gdf_utm = gdf.to_crs(TARGET_CRS)


# ---------------------------------------------------------
# Reproject DEM to UTM
# ---------------------------------------------------------

with rasterio.open(DEM) as src:

    transform, width, height = calculate_default_transform(
        src.crs,
        TARGET_CRS,
        src.width,
        src.height,
        *src.bounds,
        resolution=30,
    )

    profile = src.profile.copy()

    profile.update(
        crs=TARGET_CRS,
        transform=transform,
        width=width,
        height=height,
        dtype="float32",
        count=1,
        nodata=-9999.0,
        compress="deflate",
    )

    dem_utm = np.full(
        (height, width),
        np.nan,
        dtype=np.float32,
    )

    reproject(
        source=rasterio.band(src, 1),
        destination=dem_utm,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=transform,
        dst_crs=TARGET_CRS,
        resampling=Resampling.bilinear,
    )


# ---------------------------------------------------------
# Calculate slope
# ---------------------------------------------------------

valid_dem = np.isfinite(dem_utm)

if not valid_dem.any():
    raise ValueError("No valid DEM pixels after reprojection.")

# Pixel spacing in metres
pixel_x = transform.a
pixel_y = abs(transform.e)

print("UTM pixel size:", pixel_x, "x", pixel_y, "metres")

# Replace NaN temporarily for gradient calculation
dem_for_gradient = dem_utm.copy()

# Nearest valid value used only to prevent NaN propagation
# at the edges of the valid raster.
median_elevation = np.nanmedian(dem_for_gradient)

dem_for_gradient[~np.isfinite(dem_for_gradient)] = median_elevation

gradient_y, gradient_x = np.gradient(
    dem_for_gradient,
    pixel_y,
    pixel_x,
)

slope_radians = np.arctan(
    np.sqrt(
        gradient_x ** 2 +
        gradient_y ** 2
    )
)

slope_degrees = np.degrees(slope_radians).astype(
    np.float32
)

# Restore invalid DEM pixels
slope_degrees[~valid_dem] = np.nan


# ---------------------------------------------------------
# Mask outside Wayanad
# ---------------------------------------------------------

inside_wayanad = geometry_mask(
    gdf_utm.geometry,
    transform=transform,
    invert=True,
    out_shape=(height, width),
)

slope_degrees[~inside_wayanad] = np.nan


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

output = np.where(
    np.isfinite(slope_degrees),
    slope_degrees,
    -9999.0,
).astype(np.float32)

profile.update(
    dtype="float32",
    nodata=-9999.0,
)

with rasterio.open(OUTPUT, "w", **profile) as dst:
    dst.write(output, 1)


# ---------------------------------------------------------
# QA
# ---------------------------------------------------------

valid = output != -9999.0

print()
print("=" * 60)
print("SLOPE GENERATION COMPLETE")
print("=" * 60)

print("Output:", OUTPUT)
print("CRS:", TARGET_CRS)
print("Raster shape:", output.shape)
print("Pixel size:", pixel_x, "x", pixel_y, "m")

print("Valid Wayanad pixels:", int(valid.sum()))
print("NoData pixels:", int((~valid).sum()))

if valid.any():

    values = output[valid]

    print("Slope minimum:", float(values.min()), "degrees")
    print("Slope maximum:", float(values.max()), "degrees")
    print("Slope mean:", float(values.mean()), "degrees")

    print("Slope P01:", float(np.percentile(values, 1)))
    print("Slope P05:", float(np.percentile(values, 5)))
    print("Slope P25:", float(np.percentile(values, 25)))
    print("Slope P50:", float(np.percentile(values, 50)))
    print("Slope P75:", float(np.percentile(values, 75)))
    print("Slope P95:", float(np.percentile(values, 95)))
    print("Slope P99:", float(np.percentile(values, 99)))

    total = valid.sum()

    print()
    print("Slope distribution:")

    for name, low, high in [
        ("0-5°", 0, 5),
        ("5-15°", 5, 15),
        ("15-30°", 15, 30),
        ("30-45°", 30, 45),
        ("45°+", 45, np.inf),
    ]:

        count = np.sum(
            (values >= low) &
            (values < high)
        )

        print(
            f"{name}: "
            f"{count:,} pixels "
            f"({100 * count / total:.2f}%)"
        )

print("=" * 60)