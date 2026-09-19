import rasterio
import geopandas as gpd
import numpy as np
from rasterio.mask import mask
from pathlib import Path

dem = Path("data/raw/dem/wayanad_copernicus_glo30_merged.tif")
boundary = "data/raw/boundaries/wayanad_boundary.geojson"

gdf = gpd.read_file(boundary).to_crs("EPSG:4326")

with rasterio.open(dem) as src:
    clipped, transform = mask(
        src,
        gdf.geometry,
        crop=True,
        filled=False
    )

    data = clipped[0]

    total = data.size
    valid = np.count_nonzero(~data.mask)
    invalid = total - valid

    print("DEM:", dem)
    print("CRS:", src.crs)
    print("Resolution:", src.res)
    print("Wayanad clipped shape:", data.shape)
    print("Wayanad pixels:", total)
    print("Valid DEM pixels:", valid)
    print("Invalid/NoData pixels:", invalid)
    print("Valid coverage: {:.4f}%".format(100 * valid / total))
    print("Elevation min:", float(data.min()))
    print("Elevation max:", float(data.max()))
    print("Elevation mean:", float(data.mean()))
