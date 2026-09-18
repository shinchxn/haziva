import rasterio
import numpy as np
from pathlib import Path
from rasterio.warp import reproject, Resampling
from rasterio.transform import Affine

WORLDCOVER = Path(
    "data/processed/exposure/wayanad_worldcover_10m.tif"
)

REFERENCE = Path(
    "data/processed/terrain/wayanad_slope_degrees.tif"
)

OUTPUT_DIR = Path(
    "data/processed/exposure/worldcover"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ESA WorldCover classes
CLASSES = {
    10: "tree_cover",
    30: "grassland",
    40: "cropland",
    50: "builtup",
    60: "bare",
    80: "water",
    90: "wetland",
}

with rasterio.open(WORLDCOVER) as src:
    wc = src.read(1)
    wc_transform = src.transform
    wc_crs = src.crs

with rasterio.open(REFERENCE) as ref:
    ref_crs = ref.crs
    ref_transform = ref.transform
    ref_width = ref.width
    ref_height = ref.height

    profile = ref.profile.copy()

print("WorldCover CRS:", wc_crs)
print("Reference CRS:", ref_crs)
print("Reference size:", ref_width, ref_height)

# Create fraction rasters
features = {}

for class_id, name in CLASSES.items():

    source = (
        wc == class_id
    ).astype(np.float32)

    destination = np.zeros(
        (ref_height, ref_width),
        dtype=np.float32
    )

    reproject(
        source,
        destination,
        src_transform=wc_transform,
        src_crs=wc_crs,
        dst_transform=ref_transform,
        dst_crs=ref_crs,
        resampling=Resampling.average
    )

    features[name] = destination

    output = OUTPUT_DIR / f"wayanad_{name}_fraction_30m.tif"

    out_profile = profile.copy()
    out_profile.update(
        dtype="float32",
        count=1,
        nodata=0.0,
        compress="lzw"
    )

    with rasterio.open(output, "w", **out_profile) as dst:
        dst.write(destination, 1)

    print(
        f"Created: {output}"
    )

print("\n=== SUMMARY ===")

for name, data in features.items():

    print(
        f"{name:15s} "
        f"min={data.min():.3f} "
        f"max={data.max():.3f} "
        f"mean={data.mean():.3f}"
    )

print("\nWorldCover feature generation complete.")