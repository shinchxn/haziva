import rasterio
import numpy as np
from pathlib import Path
from collections import Counter

INPUT = Path(
    "data/processed/exposure/wayanad_worldcover_10m.tif"
)

with rasterio.open(INPUT) as src:
    data = src.read(1)
    nodata = src.nodata

    print("\n=== WORLD COVER INSPECTION ===")
    print("File:", INPUT)
    print("CRS:", src.crs)
    print("Size:", src.width, src.height)
    print("Resolution:", src.res)
    print("Bounds:", src.bounds)
    print("NoData:", nodata)

    total_pixels = data.size

    if nodata is not None:
        valid = data[data != nodata]
    else:
        valid = data

    print("\nTotal pixels:", total_pixels)
    print("Valid pixels:", len(valid))
    print(
        "NoData pixels:",
        total_pixels - len(valid)
    )

    if total_pixels > 0:
        print(
            "NoData percentage:",
            round(
                100 * (total_pixels - len(valid))
                / total_pixels,
                2
            ),
            "%"
        )

    print("\n=== CLASS DISTRIBUTION ===")

    counts = Counter(valid.tolist())

    for class_id, count in sorted(counts.items()):
        percentage = 100 * count / len(valid)

        print(
            f"Class {class_id}: "
            f"{count:,} pixels "
            f"({percentage:.2f}%)"
        )