from pathlib import Path
import json
import csv

import pandas as pd
import rasterio


ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "gsi_event_table": ROOT / "data/processed/landslide/inventory/wayanad_gsi_event_table.csv",
    "gsi_inventory": ROOT / "data/processed/landslide/inventory/wayanad_gsi_landslide_inventory.csv",
    "historical_presence": ROOT / "data/processed/landslide/inventory/wayanad_historical_landslide_presence_30m.tif",
    "spatial_training": ROOT / "data/processed/features/wayanad_spatial_landslide_training.parquet",
    "bhuvan_geojson": ROOT / "data/processed/landslide/inventory/wayanad_bhuvan_landslides_wms_derived.geojson",
}


def inspect_csv(name, path):
    print("\n" + "=" * 90)
    print(f"CSV: {name}")
    print("=" * 90)
    print(f"Path: {path}")
    print(f"Size: {path.stat().st_size:,} bytes")

    df = pd.read_csv(path)

    print(f"\nShape: {df.shape}")
    print("\nColumns:")
    for col in df.columns:
        print(f"  - {col}: {df[col].dtype}")

    print("\nFirst 10 rows:")
    print(df.head(10).to_string(index=False))

    print("\nMissing values:")
    missing = df.isna().sum()
    for col, count in missing.items():
        if count > 0:
            print(f"  - {col}: {count}")

    print("\nUnique values for low-cardinality columns:")
    for col in df.columns:
        nunique = df[col].nunique(dropna=True)
        if nunique <= 20:
            values = df[col].dropna().unique()
            print(f"  - {col} ({nunique} unique): {values[:30]}")


def inspect_raster(name, path):
    print("\n" + "=" * 90)
    print(f"RASTER: {name}")
    print("=" * 90)
    print(f"Path: {path}")
    print(f"Size: {path.stat().st_size:,} bytes")

    with rasterio.open(path) as src:
        print(f"\nDriver: {src.driver}")
        print(f"CRS: {src.crs}")
        print(f"Width: {src.width}")
        print(f"Height: {src.height}")
        print(f"Count: {src.count}")
        print(f"Resolution: {src.res}")
        print(f"Bounds: {src.bounds}")
        print(f"Transform: {src.transform}")
        print(f"NoData: {src.nodata}")
        print(f"Dtype: {src.dtypes}")

        for band_idx in range(1, src.count + 1):
            data = src.read(band_idx, masked=True)

            print(f"\nBand {band_idx}:")
            print(f"  Valid pixels: {data.count():,}")
            print(f"  Masked pixels: {data.mask.sum():,}")

            if data.count() > 0:
                values = data.compressed()

                print(f"  Min: {values.min()}")
                print(f"  Max: {values.max()}")
                print(f"  Mean: {values.mean()}")

                unique, counts = __import__("numpy").unique(
                    values,
                    return_counts=True
                )

                print("  Unique values:")
                for value, count in zip(unique[:50], counts[:50]):
                    print(f"    {value}: {count:,}")

                if len(unique) > 50:
                    print(f"    ... {len(unique) - 50} more unique values")


def inspect_parquet(name, path):
    print("\n" + "=" * 90)
    print(f"PARQUET: {name}")
    print("=" * 90)
    print(f"Path: {path}")
    print(f"Size: {path.stat().st_size:,} bytes")

    df = pd.read_parquet(path)

    print(f"\nShape: {df.shape}")

    print("\nColumns:")
    for col in df.columns:
        print(f"  - {col}: {df[col].dtype}")

    print("\nFirst 10 rows:")
    print(df.head(10).to_string(index=False))

    print("\nMissing values:")
    missing = df.isna().sum()
    for col, count in missing.items():
        if count > 0:
            print(f"  - {col}: {count}")

    print("\nUnique values for low-cardinality columns:")
    for col in df.columns:
        nunique = df[col].nunique(dropna=True)
        if nunique <= 20:
            values = df[col].dropna().unique()
            print(f"  - {col} ({nunique} unique): {values[:30]}")


def inspect_geojson(name, path):
    print("\n" + "=" * 90)
    print(f"GEOJSON: {name}")
    print("=" * 90)
    print(f"Path: {path}")
    print(f"Size: {path.stat().st_size:,} bytes")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"\nTop-level keys: {list(data.keys())}")
    print(f"Type: {data.get('type')}")

    features = data.get("features", [])

    print(f"Feature count: {len(features)}")

    if features:
        first = features[0]

        print("\nFirst feature:")
        print(json.dumps(first, indent=2)[:8000])

        properties = first.get("properties", {})

        print("\nProperty schema from first feature:")
        for key, value in properties.items():
            print(f"  - {key}: {type(value).__name__} = {value}")


def main():
    print("=" * 90)
    print("WAYANAD HISTORICAL LANDSLIDE DATA INSPECTION")
    print("=" * 90)
    print(f"Project root: {ROOT}")

    for key, path in FILES.items():
        if not path.exists():
            print(f"\nMISSING: {path}")
            continue

        try:
            if path.suffix.lower() == ".csv":
                inspect_csv(key, path)

            elif path.suffix.lower() in [".tif", ".tiff"]:
                inspect_raster(key, path)

            elif path.suffix.lower() == ".parquet":
                inspect_parquet(key, path)

            elif path.suffix.lower() == ".geojson":
                inspect_geojson(key, path)

            else:
                print(f"\nUnsupported file type: {path}")

        except Exception as e:
            print(f"\nERROR inspecting {path}")
            print(f"{type(e).__name__}: {e}")

    print("\n" + "=" * 90)
    print("INSPECTION COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    main()