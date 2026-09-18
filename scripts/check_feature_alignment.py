import rasterio
from pathlib import Path

REFERENCE = Path(
    "data/processed/terrain/wayanad_slope_degrees.tif"
)

GSI = Path(
    "data/processed/landslide/susceptibility/"
    "wayanad_gsi_susceptibility_aligned.tif"
)

WORLD_COVER_DIR = Path(
    "data/processed/exposure/worldcover"
)

FEATURES = sorted(
    WORLD_COVER_DIR.glob(
        "wayanad_*_fraction_30m.tif"
    )
)

with rasterio.open(REFERENCE) as ref:

    print("\n=== REFERENCE GRID ===")
    print("CRS:", ref.crs)
    print("Size:", ref.width, ref.height)
    print("Transform:", ref.transform)
    print("Bounds:", ref.bounds)

    reference = {
        "crs": ref.crs,
        "width": ref.width,
        "height": ref.height,
        "transform": ref.transform,
        "bounds": ref.bounds,
    }


def check_raster(path, reference):

    with rasterio.open(path) as src:

        same_crs = src.crs == reference["crs"]
        same_size = (
            src.width == reference["width"]
            and src.height == reference["height"]
        )
        same_transform = (
            src.transform == reference["transform"]
        )
        same_bounds = (
            src.bounds == reference["bounds"]
        )

        print("\n", path.name)
        print("CRS:", src.crs)
        print("Size:", src.width, src.height)
        print("Same CRS:", same_crs)
        print("Same size:", same_size)
        print("Same transform:", same_transform)
        print("Same bounds:", same_bounds)

        if not all([
            same_crs,
            same_size,
            same_transform,
            same_bounds,
        ]):
            print("WARNING: GRID MISMATCH")

        else:
            print("STATUS: ALIGNED")


print("\n=== GSI ===")
check_raster(GSI, reference)

print("\n=== WORLDCOVER FEATURES ===")

for feature in FEATURES:
    check_raster(feature, reference)

print("\n=== CHECK COMPLETE ===")