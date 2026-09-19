import rasterio
from pathlib import Path


TILES = [
    Path(
        "data/raw/landuse/worldcover/"
        "ESA_WorldCover_10m_2021_v200_N11E075_Map.tif"
    ),
    Path(
        "data/raw/landuse/worldcover/"
        "ESA_WorldCover_10m_2021_v200_N11E076_Map.tif"
    ),
]


for path in TILES:

    print()
    print("=" * 70)
    print(path)
    print("=" * 70)

    if not path.exists():
        print("MISSING")
        continue

    with rasterio.open(path) as src:

        print("CRS:", src.crs)
        print("Shape:", (src.height, src.width))
        print("Resolution:", src.res)
        print("Bounds:", src.bounds)
        print("Dtype:", src.dtypes[0])
        print("NoData:", src.nodata)

        print("Width:", src.width)
        print("Height:", src.height)