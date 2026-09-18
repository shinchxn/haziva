import rasterio
import numpy as np
from pathlib import Path

INPUT = Path(
    "data/processed/terrain/wayanad_slope_degrees.tif"
)

with rasterio.open(INPUT) as src:

    data = src.read(1)

    print("\n=== RAW SLOPE INSPECTION ===")
    print("CRS:", src.crs)
    print("Size:", src.width, src.height)
    print("NoData:", src.nodata)
    print("dtype:", data.dtype)

    print("\nRaw statistics:")
    print("Min:", np.min(data))
    print("Max:", np.max(data))
    print("Mean:", np.mean(data))

    print("\nPercentiles:")
    for p in [0, 1, 5, 25, 50, 75, 95, 99, 100]:
        print(
            f"{p}%:",
            np.percentile(data, p)
        )

    print("\nSuspicious values:")
    print("Negative pixels:", np.sum(data < 0))
    print("Below -100:", np.sum(data < -100))
    print("Above 90:", np.sum(data > 90))