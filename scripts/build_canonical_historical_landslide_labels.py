from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import xy


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

# Canonical 30 m grid
REFERENCE_RASTER = (
    ROOT
    / "data"
    / "processed"
    / "terrain"
    / "wayanad_copernicus_slope_degrees.tif"
)

# Historical landslide sources
BHUVAN_GEOJSON = (
    ROOT
    / "data"
    / "processed"
    / "landslide"
    / "inventory"
    / "wayanad_bhuvan_landslides_wms_derived.geojson"
)

GSI_EVENT_TABLE = (
    ROOT
    / "data"
    / "processed"
    / "landslide"
    / "inventory"
    / "wayanad_gsi_event_table.csv"
)

# Outputs
OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "landslide"
    / "inventory"
)

OUTPUT_RASTER = (
    OUTPUT_DIR
    / "wayanad_historical_landslide_presence_copernicus_30m.tif"
)

OUTPUT_PROVENANCE = (
    OUTPUT_DIR
    / "wayanad_historical_landslide_provenance_copernicus_30m.parquet"
)

OUTPUT_SUMMARY = (
    OUTPUT_DIR
    / "wayanad_historical_landslide_label_summary.csv"
)


# ============================================================
# CONSTANTS
# ============================================================

TARGET_CRS = "EPSG:32643"

BHUVAN_VALUE = 1
GSI_VALUE = 1

# Raster nodata.
# 0 = no historical inventory evidence.
# 1 = historical inventory evidence.
RASTER_NODATA = 0


# ============================================================
# HELPERS
# ============================================================

def validate_file(path: Path, description: str):
    if not path.exists():
        raise FileNotFoundError(
            f"{description} not found:\n{path}"
        )


def print_header(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


# ============================================================
# LOAD CANONICAL GRID
# ============================================================

def load_reference_grid():
    print_header("LOADING CANONICAL COPERNICUS 30 m GRID")

    validate_file(
        REFERENCE_RASTER,
        "Canonical Copernicus slope raster",
    )

    with rasterio.open(REFERENCE_RASTER) as src:
        profile = src.profile.copy()

        crs = src.crs
        transform = src.transform
        width = src.width
        height = src.height
        bounds = src.bounds

        slope = src.read(1, masked=True)

    print(f"Raster: {REFERENCE_RASTER}")
    print(f"CRS: {crs}")
    print(f"Width: {width}")
    print(f"Height: {height}")
    print(f"Resolution: {src.res}")
    print(f"Bounds: {bounds}")
    print(f"Valid slope cells: {slope.count():,}")

    if crs is None:
        raise ValueError("Reference raster has no CRS.")

    if str(crs) != TARGET_CRS:
        raise ValueError(
            f"Unexpected reference CRS: {crs}. "
            f"Expected {TARGET_CRS}."
        )

    return {
        "profile": profile,
        "crs": crs,
        "transform": transform,
        "width": width,
        "height": height,
        "bounds": bounds,
        "valid_mask": ~slope.mask,
    }


# ============================================================
# LOAD BHUVAN POLYGONS
# ============================================================

def load_bhuvan_polygons():
    print_header("LOADING BHUVAN LANDSLIDE POLYGONS")

    validate_file(
        BHUVAN_GEOJSON,
        "Bhuvan landslide GeoJSON",
    )

    gdf = gpd.read_file(BHUVAN_GEOJSON)

    print(f"Input features: {len(gdf):,}")
    print(f"Input CRS: {gdf.crs}")

    if gdf.empty:
        raise ValueError("Bhuvan GeoJSON contains no features.")

    if gdf.crs is None:
        raise ValueError(
            "Bhuvan GeoJSON has no CRS."
        )

    # Keep only valid geometries.
    before = len(gdf)

    gdf = gdf[
        gdf.geometry.notna()
        & ~gdf.geometry.is_empty
    ].copy()

    after = len(gdf)

    print(f"Non-empty geometries: {after:,}")

    if after == 0:
        raise ValueError(
            "No usable Bhuvan geometries remain."
        )

    if before != after:
        print(
            f"Removed {before - after:,} empty/null geometries."
        )

    # Reproject to canonical UTM CRS.
    gdf = gdf.to_crs(TARGET_CRS)

    # Attempt to repair invalid geometries.
    invalid_count = (~gdf.geometry.is_valid).sum()

    if invalid_count > 0:
        print(
            f"Invalid geometries before repair: "
            f"{invalid_count:,}"
        )

        gdf["geometry"] = gdf.geometry.buffer(0)

        invalid_after = (~gdf.geometry.is_valid).sum()

        print(
            f"Invalid geometries after repair: "
            f"{invalid_after:,}"
        )

        if invalid_after > 0:
            raise ValueError(
                "Some Bhuvan geometries remain invalid "
                "after repair."
            )

    print(f"Reprojected CRS: {gdf.crs}")

    return gdf


# ============================================================
# LOAD GSI EVENTS
# ============================================================

def load_gsi_events():
    print_header("LOADING GSI HISTORICAL LANDSLIDE EVENTS")

    validate_file(
        GSI_EVENT_TABLE,
        "GSI event table",
    )

    df = pd.read_csv(GSI_EVENT_TABLE)

    print(f"GSI records: {len(df):,}")
    print(f"Columns: {list(df.columns)}")

    required = [
        "Latitude",
        "Longitude",
        "Slide_No",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"GSI event table missing columns: {missing}"
        )

    # Coordinates must be numeric.
    df["Latitude"] = pd.to_numeric(
        df["Latitude"],
        errors="coerce",
    )

    df["Longitude"] = pd.to_numeric(
        df["Longitude"],
        errors="coerce",
    )

    before = len(df)

    df = df.dropna(
        subset=["Latitude", "Longitude"]
    ).copy()

    print(
        f"Records with valid coordinates: "
        f"{len(df):,}"
    )

    if len(df) == 0:
        raise ValueError(
            "No GSI records have valid coordinates."
        )

    # Basic geographic sanity check.
    if not (
        df["Latitude"].between(-90, 90).all()
        and df["Longitude"].between(-180, 180).all()
    ):
        raise ValueError(
            "GSI coordinates contain invalid latitude/longitude values."
        )

    # Convert to GeoDataFrame.
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df["Longitude"],
            df["Latitude"],
        ),
        crs="EPSG:4326",
    )

    gdf = gdf.to_crs(TARGET_CRS)

    print(f"Reprojected CRS: {gdf.crs}")

    if before != len(df):
        print(
            f"Dropped {before - len(df):,} "
            f"records without coordinates."
        )

    return gdf


# ============================================================
# RASTERIZE BHUVAN
# ============================================================

def rasterize_bhuvan(
    gdf,
    reference,
):
    print_header("RASTERIZING BHUVAN POLYGONS")

    shapes = [
        (geometry, BHUVAN_VALUE)
        for geometry in gdf.geometry
        if geometry is not None
        and not geometry.is_empty
    ]

    print(f"Polygon geometries: {len(shapes):,}")

    mask = rasterize(
        shapes=shapes,
        out_shape=(
            reference["height"],
            reference["width"],
        ),
        transform=reference["transform"],
        fill=0,
        default_value=BHUVAN_VALUE,
        dtype="uint8",
        all_touched=False,
    )

    # Enforce reference valid-data mask.
    mask[~reference["valid_mask"]] = 0

    positive = int((mask == 1).sum())

    print(
        f"Bhuvan-positive cells: {positive:,}"
    )

    return mask


# ============================================================
# RASTERIZE GSI POINTS
# ============================================================

def rasterize_gsi(
    gdf,
    reference,
):
    print_header("RASTERIZING GSI POINTS")

    shapes = [
        (geometry, GSI_VALUE)
        for geometry in gdf.geometry
        if geometry is not None
        and not geometry.is_empty
    ]

    print(f"GSI point geometries: {len(shapes):,}")

    mask = rasterize(
        shapes=shapes,
        out_shape=(
            reference["height"],
            reference["width"],
        ),
        transform=reference["transform"],
        fill=0,
        default_value=GSI_VALUE,
        dtype="uint8",
        all_touched=False,
    )

    mask[~reference["valid_mask"]] = 0

    positive = int((mask == 1).sum())

    print(
        f"GSI-positive cells: {positive:,}"
    )

    return mask


# ============================================================
# BUILD COMBINED LABEL
# ============================================================

def build_combined_label(
    bhuvan_mask,
    gsi_mask,
    valid_mask,
):
    print_header("BUILDING COMBINED HISTORICAL LABEL")

    combined = (
        (bhuvan_mask == 1)
        | (gsi_mask == 1)
    ).astype(np.uint8)

    combined[~valid_mask] = 0

    bhuvan_only = (
        (bhuvan_mask == 1)
        & (gsi_mask == 0)
    )

    gsi_only = (
        (gsi_mask == 1)
        & (bhuvan_mask == 0)
    )

    both = (
        (gsi_mask == 1)
        & (bhuvan_mask == 1)
    )

    print(
        f"Bhuvan only cells: {bhuvan_only.sum():,}"
    )

    print(
        f"GSI only cells: {gsi_only.sum():,}"
    )

    print(
        f"Both sources cells: {both.sum():,}"
    )

    print(
        f"Combined positive cells: "
        f"{(combined == 1).sum():,}"
    )

    print(
        f"Combined negative/background cells: "
        f"{(combined == 0).sum():,}"
    )

    return combined


# ============================================================
# WRITE RASTER
# ============================================================

def write_raster(
    combined,
    reference,
):
    print_header("WRITING CANONICAL HISTORICAL LABEL RASTER")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    profile = reference["profile"].copy()

    profile.update(
        driver="GTiff",
        dtype="uint8",
        count=1,
        nodata=0,
        compress="deflate",
        predictor=2,
    )

    with rasterio.open(
        OUTPUT_RASTER,
        "w",
        **profile,
    ) as dst:

        dst.write(
            combined,
            1,
        )

        dst.set_band_description(
            1,
            "historical_landslide_presence",
        )

        dst.update_tags(
            source_bhuvan=(
                "wayanad_bhuvan_landslides_wms_derived.geojson"
            ),
            source_gsi=(
                "wayanad_gsi_event_table.csv"
            ),
            label_definition=(
                "1 = historical inventory evidence; "
                "0 = no inventory evidence"
            ),
            target_grid=(
                "Copernicus GLO-30 derived 30m UTM EPSG:32643"
            ),
        )

    print(f"Output: {OUTPUT_RASTER}")
    print(
        f"Size: {OUTPUT_RASTER.stat().st_size:,} bytes"
    )


# ============================================================
# BUILD PROVENANCE TABLE
# ============================================================

def build_provenance_table(
    bhuvan_mask,
    gsi_mask,
    combined,
    reference,
):
    print_header("BUILDING PROVENANCE TABLE")

    valid = reference["valid_mask"]

    rows, cols = np.where(valid)

    xs, ys = rasterio.transform.xy(
        reference["transform"],
        rows,
        cols,
        offset="center",
    )

    bhuvan_values = bhuvan_mask[
        rows,
        cols,
    ]

    gsi_values = gsi_mask[
        rows,
        cols,
    ]

    combined_values = combined[
        rows,
        cols,
    ]

    bhuvan_bool = bhuvan_values == 1
    gsi_bool = gsi_values == 1

    source = np.full(
        len(rows),
        "NONE",
        dtype=object,
    )

    source[bhuvan_bool & ~gsi_bool] = "BHUVAN"
    source[~bhuvan_bool & gsi_bool] = "GSI"
    source[bhuvan_bool & gsi_bool] = "BOTH"

    df = pd.DataFrame(
        {
            "row": rows.astype(np.int32),
            "col": cols.astype(np.int32),
            "x": np.asarray(xs, dtype=np.float64),
            "y": np.asarray(ys, dtype=np.float64),
            "bhuvan_evidence": bhuvan_values.astype(
                np.uint8
            ),
            "gsi_evidence": gsi_values.astype(
                np.uint8
            ),
            "historical_landslide": combined_values.astype(
                np.uint8
            ),
            "evidence_source": source,
        }
    )

    print(f"Provenance rows: {len(df):,}")

    print("\nEvidence source counts:")
    print(
        df["evidence_source"]
        .value_counts()
        .to_string()
    )

    df.to_parquet(
        OUTPUT_PROVENANCE,
        index=False,
    )

    print(
        f"\nOutput: {OUTPUT_PROVENANCE}"
    )

    return df


# ============================================================
# SUMMARY
# ============================================================

def write_summary(
    bhuvan_gdf,
    gsi_gdf,
    bhuvan_mask,
    gsi_mask,
    combined,
    reference,
):
    print_header("WRITING QA SUMMARY")

    valid_cells = int(
        reference["valid_mask"].sum()
    )

    bhuvan_cells = int(
        (bhuvan_mask == 1).sum()
    )

    gsi_cells = int(
        (gsi_mask == 1).sum()
    )

    combined_cells = int(
        (combined == 1).sum()
    )

    both_cells = int(
        (
            (bhuvan_mask == 1)
            & (gsi_mask == 1)
        ).sum()
    )

    bhuvan_only = int(
        (
            (bhuvan_mask == 1)
            & (gsi_mask == 0)
        ).sum()
    )

    gsi_only = int(
        (
            (gsi_mask == 1)
            & (bhuvan_mask == 0)
        ).sum()
    )

    summary = pd.DataFrame(
        [
            {
                "metric": "reference_valid_cells",
                "value": valid_cells,
            },
            {
                "metric": "bhuvan_polygon_features",
                "value": len(bhuvan_gdf),
            },
            {
                "metric": "gsi_event_records",
                "value": len(gsi_gdf),
            },
            {
                "metric": "bhuvan_positive_cells",
                "value": bhuvan_cells,
            },
            {
                "metric": "gsi_positive_cells",
                "value": gsi_cells,
            },
            {
                "metric": "combined_positive_cells",
                "value": combined_cells,
            },
            {
                "metric": "bhuvan_only_cells",
                "value": bhuvan_only,
            },
            {
                "metric": "gsi_only_cells",
                "value": gsi_only,
            },
            {
                "metric": "both_source_cells",
                "value": both_cells,
            },
        ]
    )

    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
    )

    print(
        summary.to_string(index=False)
    )

    print(
        f"\nOutput: {OUTPUT_SUMMARY}"
    )


# ============================================================
# FINAL QA
# ============================================================

def run_final_qa(
    combined,
    bhuvan_mask,
    gsi_mask,
    reference,
):
    print_header("FINAL QA")

    valid = reference["valid_mask"]

    # Shape
    expected_shape = (
        reference["height"],
        reference["width"],
    )

    assert combined.shape == expected_shape
    assert bhuvan_mask.shape == expected_shape
    assert gsi_mask.shape == expected_shape

    # Valid cells only.
    valid_combined = combined[valid]
    valid_bhuvan = bhuvan_mask[valid]
    valid_gsi = gsi_mask[valid]

    # Binary validation.
    assert set(
        np.unique(valid_combined)
    ).issubset({0, 1})

    assert set(
        np.unique(valid_bhuvan)
    ).issubset({0, 1})

    assert set(
        np.unique(valid_gsi)
    ).issubset({0, 1})

    # Combined must be logical OR.
    expected = (
        (valid_bhuvan == 1)
        | (valid_gsi == 1)
    ).astype(np.uint8)

    assert np.array_equal(
        valid_combined,
        expected,
    )

    # No labels outside valid Copernicus cells.
    assert np.all(
        combined[~valid] == 0
    )

    print("Shape validation: PASSED")
    print("Binary label validation: PASSED")
    print("OR-combination validation: PASSED")
    print("Reference-grid mask validation: PASSED")

    print("\nFinal label counts:")
    print(
        f"  Positive: {(valid_combined == 1).sum():,}"
    )
    print(
        f"  Background: {(valid_combined == 0).sum():,}"
    )

    print("\nALL QA CHECKS PASSED")


# ============================================================
# MAIN
# ============================================================

def main():
    print_header(
        "WAYANAD CANONICAL HISTORICAL LANDSLIDE LABEL BUILDER"
    )

    print(
        "Purpose:"
    )
    print(
        "Create historical landslide evidence labels on the "
        "canonical Copernicus 30 m grid."
    )

    print(
        "\nIMPORTANT:"
    )
    print(
        "0 means no inventory evidence, not confirmed absence "
        "of landslides."
    )

    # 1. Canonical grid
    reference = load_reference_grid()

    # 2. Historical sources
    bhuvan_gdf = load_bhuvan_polygons()
    gsi_gdf = load_gsi_events()

    # 3. Rasterize
    bhuvan_mask = rasterize_bhuvan(
        bhuvan_gdf,
        reference,
    )

    gsi_mask = rasterize_gsi(
        gsi_gdf,
        reference,
    )

    # 4. Combine
    combined = build_combined_label(
        bhuvan_mask,
        gsi_mask,
        reference["valid_mask"],
    )

    # 5. QA before writing
    run_final_qa(
        combined,
        bhuvan_mask,
        gsi_mask,
        reference,
    )

    # 6. Write canonical raster
    write_raster(
        combined,
        reference,
    )

    # 7. Provenance
    build_provenance_table(
        bhuvan_mask,
        gsi_mask,
        combined,
        reference,
    )

    # 8. Summary
    write_summary(
        bhuvan_gdf,
        gsi_gdf,
        bhuvan_mask,
        gsi_mask,
        combined,
        reference,
    )

    print_header("COMPLETE")

    print(
        "Canonical historical landslide label generation "
        "completed successfully."
    )

    print("\nCreated:")
    print(
        f"  {OUTPUT_RASTER}"
    )
    print(
        f"  {OUTPUT_PROVENANCE}"
    )
    print(
        f"  {OUTPUT_SUMMARY}"
    )

    print(
        "\nLegacy files were not modified."
    )


if __name__ == "__main__":
    main()