from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling


# ============================================================
# INPUT / OUTPUT PATHS
# ============================================================

GSI_INPUT = Path(
    "data/processed/landslide/susceptibility/"
    "wayanad_gsi_susceptibility_aligned.tif"
)

TARGET_RASTER = Path(
    "data/processed/terrain/"
    "wayanad_copernicus_slope_degrees.tif"
)

OUTPUT = Path(
    "data/processed/landslide/susceptibility/"
    "wayanad_gsi_susceptibility_copernicus_30m.tif"
)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("ALIGN GSI SUSCEPTIBILITY TO COPERNICUS 30m GRID")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Read GSI source raster
    # --------------------------------------------------------

    print("\n[1/5] Reading GSI susceptibility raster...")

    with rasterio.open(GSI_INPUT) as src:

        gsi = src.read(1)

        src_transform = src.transform
        src_crs = src.crs
        src_nodata = src.nodata

        src_height = src.height
        src_width = src.width

        src_bounds = src.bounds
        src_res = src.res

    print(f"Source CRS:        {src_crs}")
    print(f"Source shape:      {src_height} x {src_width}")
    print(f"Source resolution: {src_res}")
    print(f"Source bounds:     {src_bounds}")
    print(f"Source nodata:     {src_nodata}")

    print("\nSource class counts:")

    source_values, source_counts = np.unique(
        gsi,
        return_counts=True
    )

    for value, count in zip(source_values, source_counts):
        print(f"  {int(value)}: {int(count):,}")


    # --------------------------------------------------------
    # 2. Read canonical Copernicus target grid
    # --------------------------------------------------------

    print("\n[2/5] Reading Copernicus target grid...")

    with rasterio.open(TARGET_RASTER) as target:

        target_transform = target.transform
        target_crs = target.crs

        target_height = target.height
        target_width = target.width

        target_bounds = target.bounds
        target_res = target.res

        target_profile = target.profile.copy()

    print(f"Target CRS:        {target_crs}")
    print(f"Target shape:      {target_height} x {target_width}")
    print(f"Target resolution: {target_res}")
    print(f"Target bounds:     {target_bounds}")


    # --------------------------------------------------------
    # 3. Validate target grid
    # --------------------------------------------------------

    print("\n[3/5] Validating target grid...")

    if target_crs is None:
        raise ValueError("Target raster has no CRS.")

    if target_transform is None:
        raise ValueError("Target raster has no transform.")

    if target_height <= 0 or target_width <= 0:
        raise ValueError("Invalid target raster dimensions.")

    print("Target grid validation: PASSED")


    # --------------------------------------------------------
    # 4. Reproject / align categorical GSI classes
    # --------------------------------------------------------

    print("\n[4/5] Reprojecting GSI to Copernicus grid...")

    # GSI classes:
    #
    # 0 = No GSI coverage
    # 1 = Low
    # 2 = Moderate
    # 3 = High
    #
    # Since this is categorical data, nearest-neighbour
    # resampling MUST be used.
    #
    # We initialize the target with 0, which preserves
    # "no GSI coverage" semantics.

    aligned_gsi = np.zeros(
        (target_height, target_width),
        dtype=np.uint8
    )

    reproject(
        source=gsi,
        destination=aligned_gsi,

        src_transform=src_transform,
        src_crs=src_crs,
        src_nodata=0,

        dst_transform=target_transform,
        dst_crs=target_crs,
        dst_nodata=0,

        resampling=Resampling.nearest,
    )

    print("Reprojection: PASSED")


    # --------------------------------------------------------
    # 5. Write output
    # --------------------------------------------------------

    print("\n[5/5] Writing aligned GSI raster...")

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_profile = target_profile.copy()

    output_profile.update(
        driver="GTiff",
        dtype="uint8",
        count=1,
        nodata=0,
        height=target_height,
        width=target_width,
        crs=target_crs,
        transform=target_transform,
        compress="deflate",
        predictor=2,
    )

    with rasterio.open(
        OUTPUT,
        "w",
        **output_profile
    ) as dst:

        dst.write(aligned_gsi, 1)

        dst.set_band_description(
            1,
            "GSI landslide susceptibility "
            "(0=no coverage, 1=Low, 2=Moderate, 3=High)"
        )

    print(f"\nCreated:")
    print(OUTPUT)


    # --------------------------------------------------------
    # Final QA
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("FINAL QA")
    print("=" * 70)

    output_values, output_counts = np.unique(
        aligned_gsi,
        return_counts=True
    )

    print(f"Output shape:      {aligned_gsi.shape}")
    print(f"Output CRS:        {target_crs}")
    print(f"Output resolution: {target_res}")
    print(f"Output bounds:     {target_bounds}")
    print(f"Output nodata:     0")

    print("\nOutput class counts:")

    for value, count in zip(output_values, output_counts):
        labels = {
            0: "No GSI coverage",
            1: "Low",
            2: "Moderate",
            3: "High",
        }

        label = labels.get(
            int(value),
            "UNKNOWN"
        )

        print(
            f"  {int(value)} = {label:<18} "
            f"{int(count):,}"
        )


    # --------------------------------------------------------
    # Validate allowed class values
    # --------------------------------------------------------

    allowed_values = {0, 1, 2, 3}

    actual_values = set(
        int(v) for v in np.unique(aligned_gsi)
    )

    unexpected = actual_values - allowed_values

    if unexpected:
        raise ValueError(
            f"Unexpected GSI class values found: {unexpected}"
        )

    print("\nClass-value validation: PASSED")


    # --------------------------------------------------------
    # Validate dimensions against target
    # --------------------------------------------------------

    if aligned_gsi.shape != (
        target_height,
        target_width
    ):
        raise ValueError(
            "Output dimensions do not match target grid."
        )

    print("Grid-dimension validation: PASSED")


    print("\n" + "=" * 70)
    print("SUCCESS")
    print("=" * 70)

    print(
        "\nThe GSI susceptibility layer is now aligned "
        "to the canonical Copernicus 30 m grid."
    )

    print(
        "\nIMPORTANT:"
        "\n0 = No GSI coverage"
        "\n1 = Low"
        "\n2 = Moderate"
        "\n3 = High"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()