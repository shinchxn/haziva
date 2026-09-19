import rasterio
from rasterio.merge import merge
from pathlib import Path
import numpy as np

dem_dir = Path("data/raw/dem")

files = [
    dem_dir / "Copernicus_DSM_10_N11_00_E075_00_DEM.tif",
    dem_dir / "Copernicus_DSM_10_N11_00_E076_00_DEM.tif",
]

srcs = [rasterio.open(f) for f in files]

try:
    mosaic, transform = merge(srcs)

    meta = srcs[0].meta.copy()
    meta.update({
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": transform,
        "compress": "deflate",
        "BIGTIFF": "IF_SAFER",
    })

    output = dem_dir / "wayanad_copernicus_glo30_merged.tif"

    with rasterio.open(output, "w", **meta) as dst:
        dst.write(mosaic)

    valid = np.isfinite(mosaic[0])

    print("Created:", output)
    print("Shape:", mosaic.shape)
    print("Bounds:", rasterio.transform.array_bounds(
        mosaic.shape[1],
        mosaic.shape[2],
        transform
    ))
    print("CRS:", meta["crs"])
    print("Resolution:", meta["transform"].a, abs(meta["transform"].e))
    print("NoData:", meta.get("nodata"))
    print("Valid pixels:", int(valid.sum()))
    print("Total pixels:", int(valid.size))

finally:
    for src in srcs:
        src.close()
