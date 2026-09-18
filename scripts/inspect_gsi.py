import rasterio
import numpy as np
from pathlib import Path
from collections import Counter

INPUT = Path(
    "data/processed/landslide/susceptibility/"
    "wayanad_gsi_susceptibility_aligned.tif"
)

with rasterio.open(INPUT) as src:

    data = src.read(1)

    print("\n=== GSI SUSCEPTIBILITY INSPECTION ===")
    print("File:", INPUT)
    print("CRS:", src.crs)
    print("Size:", src.width, src.height)
    print("Resolution:", src.res)
    print("Bounds:", src.bounds)
    print("NoData:", src.nodata)

    print("\nUnique values:")

    values, counts = np.unique(
        data,
        return_counts=True
    )

    for value, count in zip(values, counts):

        percentage = (
            100 * count / data.size
        )

        print(
            f"Value {value}: "
            f"{count:,} pixels "
            f"({percentage:.2f}%)"
        )