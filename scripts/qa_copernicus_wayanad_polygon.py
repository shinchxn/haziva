import rasterio
import geopandas as gpd
import numpy as np
from rasterio.features import geometry_mask
from pathlib import Path

dem = Path("data/raw/dem/wayanad_copernicus_glo30_merged.tif")
boundary = "data/raw/boundaries/wayanad_boundary.geojson"

gdf = gpd.read_file(boundary).to_crs("EPSG:4326")

with rasterio.open(dem) as src:
    inside = geometry_mask(
        gdf.geometry,
        transform=src.transform,
        invert=True,
        out_shape=(src.height, src.width)
    )

    data = src.read(1)

    inside_pixels = data[inside]

    valid = np.isfinite(inside_pixels)

    print("DEM:", dem)
    print("Raster shape:", data.shape)
    print("CRS:", src.crs)
    print("Resolution:", src.res)

    print("Wayanad polygon pixels:", inside_pixels.size)
    print("Valid pixels inside Wayanad:", int(valid.sum()))
    print("Invalid pixels inside Wayanad:", int((~valid).sum()))
    print(
        "Valid coverage inside polygon: {:.4f}%".format(
            100 * valid.sum() / inside_pixels.size
        )
    )

    if valid.any():
        print("Elevation min:", float(inside_pixels[valid].min()))
        print("Elevation max:", float(inside_pixels[valid].max()))
        print("Elevation mean:", float(inside_pixels[valid].mean()))
