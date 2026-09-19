from pathlib import Path

import geopandas as gpd
import pandas as pd


INPUT = Path(
    "data/raw/boundaries/village/kerala_2011/geojson"
)

OUTPUT = Path(
    "data/processed/exposure/wayanad_village_boundary_qa.csv"
)


def find_vector_file():
    candidates = list(INPUT.rglob("*.geojson")) + list(INPUT.rglob("*.json"))

    if not candidates:
        raise FileNotFoundError(
            f"No GeoJSON found under {INPUT}"
        )

    if len(candidates) > 1:
        print("Multiple vector files found:")
        for p in candidates:
            print(" ", p)

    return candidates[0]


def main():
    path = find_vector_file()

    print("=" * 72)
    print("WAYANAD VILLAGE BOUNDARY QA")
    print("=" * 72)
    print(f"Input: {path}")

    gdf = gpd.read_file(path)

    required = [
        "village",
        "vlcode",
        "subdistric",
        "sdcode",
        "district",
        "dtcode",
        "total_households",
        "total_population_village",
        "geometry",
    ]

    missing = [c for c in required if c not in gdf.columns]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    print(f"\nFull dataset:")
    print(f"  Rows: {len(gdf):,}")
    print(f"  CRS:  {gdf.crs}")

    # ---------------------------------------------------------------
    # Filter Wayanad
    # ---------------------------------------------------------------

    wayanad = gdf[
        gdf["district"]
        .astype(str)
        .str.strip()
        .str.lower()
        == "wayanad"
    ].copy()

    if wayanad.empty:
        print("\nNo Wayanad records found using district name.")

        print("\nAvailable districts:")
        print(
            gdf["district"]
            .astype(str)
            .str.strip()
            .sort_values()
            .unique()
        )

        raise ValueError("Wayanad filtering failed.")

    print("\nWAYANAD")
    print("-" * 72)

    print(f"  Village polygons: {len(wayanad):,}")
    print(
        f"  Unique village codes: "
        f"{wayanad['vlcode'].nunique():,}"
    )

    print(
        f"  Population sum: "
        f"{wayanad['total_population_village'].sum():,.0f}"
    )

    print(
        f"  Households sum: "
        f"{wayanad['total_households'].sum():,.0f}"
    )

    # ---------------------------------------------------------------
    # Basic integrity checks
    # ---------------------------------------------------------------

    duplicate_codes = (
        wayanad[
            wayanad["vlcode"].duplicated(keep=False)
        ]
        .sort_values("vlcode")
    )

    print("\nCODE CHECK")
    print("-" * 72)

    if duplicate_codes.empty:
        print("  Duplicate village codes: NONE")
    else:
        print("  Duplicate village codes:")
        print(
            duplicate_codes[
                ["vlcode", "village", "district"]
            ].to_string(index=False)
        )
        raise ValueError(
            "Duplicate village codes found."
        )

    # ---------------------------------------------------------------
    # Geometry QA
    # ---------------------------------------------------------------

    invalid_geometry = ~wayanad.geometry.is_valid

    print("\nGEOMETRY CHECK")
    print("-" * 72)

    print(
        f"  Invalid geometries: "
        f"{invalid_geometry.sum():,}"
    )

    if invalid_geometry.any():
        print(
            wayanad.loc[
                invalid_geometry,
                ["vlcode", "village"]
            ].to_string(index=False)
        )
        raise ValueError(
            "Invalid village geometries found."
        )

    empty_geometry = wayanad.geometry.is_empty

    print(
        f"  Empty geometries: "
        f"{empty_geometry.sum():,}"
    )

    if empty_geometry.any():
        raise ValueError(
            "Empty village geometries found."
        )

    # ---------------------------------------------------------------
    # Population QA
    # ---------------------------------------------------------------

    population_missing = (
        wayanad["total_population_village"]
        .isna()
    )

    household_missing = (
        wayanad["total_households"]
        .isna()
    )

    print("\nPOPULATION CHECK")
    print("-" * 72)

    print(
        f"  Missing population: "
        f"{population_missing.sum():,}"
    )

    print(
        f"  Missing households: "
        f"{household_missing.sum():,}"
    )

    if population_missing.any():
        raise ValueError(
            "Missing village population values."
        )

    if household_missing.any():
        raise ValueError(
            "Missing village household values."
        )

    # ---------------------------------------------------------------
    # Save clean Wayanad layer
    # ---------------------------------------------------------------

    output_dir = OUTPUT.parent
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    columns = [
        "village",
        "vlcode",
        "subdistric",
        "sdcode",
        "district",
        "dtcode",
        "total_households",
        "total_population_village",
        "total_male_population_village",
        "total_female_population_village",
        "src_agency",
        "geometry",
    ]

    clean = wayanad[columns].copy()

    clean.to_file(
        output_dir / "wayanad_village_boundaries.geojson",
        driver="GeoJSON"
    )

    # QA CSV without geometry
    qa = clean.drop(columns="geometry").copy()

    qa.to_csv(
        OUTPUT,
        index=False
    )

    print("\n" + "=" * 72)
    print("QA COMPLETE")
    print("=" * 72)

    print(
        f"Wayanad villages: "
        f"{len(clean):,}"
    )

    print(
        f"Population: "
        f"{clean['total_population_village'].sum():,.0f}"
    )

    print(
        f"Households: "
        f"{clean['total_households'].sum():,.0f}"
    )

    print(
        f"\nGeoJSON written to:"
        f"\n  {output_dir / 'wayanad_village_boundaries.geojson'}"
    )

    print(
        f"\nQA CSV written to:"
        f"\n  {OUTPUT}"
    )


if __name__ == "__main__":
    main()