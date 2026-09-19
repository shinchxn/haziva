from pathlib import Path

import pandas as pd
import geopandas as gpd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

NWDP_GEOJSON = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "boundaries"
    / "village"
    / "kerala_2011"
    / "geojson"
    / "vb_soi_kl.GeoJSON"
)

CENSUS_XLSX = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "population"
    / "census_2011_kerala_village_population"
    / "DH_2011_DCHB_Village_Release_3200.xlsx"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "exposure"
    / "census_nwdp_reconciliation"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CONSTANTS
# ============================================================

EXPECTED_RURAL_WAYANAD_VILLAGES = 48
EXPECTED_RURAL_POPULATION_2011 = 785_840
EXPECTED_RURAL_HOUSEHOLDS_2011 = 183_375


# ============================================================
# HELPERS
# ============================================================

def normalize_code(series):
    """
    Normalize Census/NWDP village codes so that:

        627293
        627293.0
        "627293"

    all become:

        "627293"
    """

    numeric = pd.to_numeric(
        series,
        errors="coerce"
    )

    return (
        numeric
        .astype("Int64")
        .astype(str)
        .str.replace(
            "<NA>",
            "",
            regex=False
        )
        .str.strip()
    )


def normalize_column_names(df):
    """
    Normalize whitespace in Excel column names.

    Example:

        'Total   Households'

    becomes:

        'Total Households'
    """

    df.columns = (
        df.columns
        .astype(str)
        .str.replace(
            r"\s+",
            " ",
            regex=True
        )
        .str.strip()
    )

    return df


# ============================================================
# LOAD NWDP
# ============================================================

def load_nwdp():

    print("=" * 80)
    print("LOADING NWDP VILLAGE BOUNDARIES")
    print("=" * 80)

    if not NWDP_GEOJSON.exists():
        raise FileNotFoundError(
            f"NWDP GeoJSON not found:\n{NWDP_GEOJSON}"
        )

    gdf = gpd.read_file(
        NWDP_GEOJSON
    )

    print(
        f"Original NWDP spatial units: {len(gdf)}"
    )

    # --------------------------------------------------------
    # Validate required columns
    # --------------------------------------------------------

    required = [
        "district",
        "vlcode",
        "village",
    ]

    missing = [
        column
        for column in required
        if column not in gdf.columns
    ]

    if missing:
        raise ValueError(
            "NWDP file is missing required columns:\n"
            f"{missing}\n\n"
            f"Available columns:\n{list(gdf.columns)}"
        )

    # --------------------------------------------------------
    # Wayanad only
    # --------------------------------------------------------

    gdf["district"] = (
        gdf["district"]
        .astype(str)
        .str.strip()
    )

    gdf = gdf[
        gdf["district"]
        .str.lower()
        == "wayanad"
    ].copy()

    print(
        f"Total Wayanad spatial units: {len(gdf)}"
    )

    # --------------------------------------------------------
    # Normalize NWDP village code
    # --------------------------------------------------------

    gdf["village_code"] = normalize_code(
        gdf["vlcode"]
    )

    # --------------------------------------------------------
    # Validate codes
    # --------------------------------------------------------

    if gdf["village_code"].eq("").any():

        bad = gdf[
            gdf["village_code"].eq("")
        ]

        raise ValueError(
            "NWDP contains rows with missing "
            "village codes:\n"
            f"{bad[['village']].to_string(index=False)}"
        )

    duplicate_nwdp = gdf[
        gdf["village_code"].duplicated(
            keep=False
        )
    ]

    if not duplicate_nwdp.empty:

        print("\nDUPLICATE NWDP CODES:")
        print(
            duplicate_nwdp[
                [
                    "village_code",
                    "village",
                ]
            ].to_string(index=False)
        )

        raise ValueError(
            "Duplicate NWDP village codes found."
        )

    print(
        f"Unique NWDP village codes: "
        f"{gdf['village_code'].nunique()}"
    )

    # --------------------------------------------------------
    # CRS information
    # --------------------------------------------------------

    print(
        f"NWDP CRS: {gdf.crs}"
    )

    return gdf


# ============================================================
# LOAD CENSUS
# ============================================================

def load_census():

    print()
    print("=" * 80)
    print("LOADING CENSUS DCHB")
    print("=" * 80)

    if not CENSUS_XLSX.exists():
        raise FileNotFoundError(
            f"Census workbook not found:\n{CENSUS_XLSX}"
        )

    # --------------------------------------------------------
    # Inspect workbook
    # --------------------------------------------------------

    xl = pd.ExcelFile(
        CENSUS_XLSX,
        engine="openpyxl"
    )

    print("Sheets:")
    print(xl.sheet_names)

    required_sheet = "Village_Data_3200"

    if required_sheet not in xl.sheet_names:
        raise ValueError(
            f"Required sheet '{required_sheet}' "
            f"not found.\n"
            f"Available sheets: {xl.sheet_names}"
        )

    # --------------------------------------------------------
    # Read village data
    # --------------------------------------------------------

    census = pd.read_excel(
        CENSUS_XLSX,
        sheet_name=required_sheet,
        engine="openpyxl"
    )

    print(
        f"\nTotal Census rows: {len(census)}"
    )

    # --------------------------------------------------------
    # Normalize messy Excel column names
    # --------------------------------------------------------

    census = normalize_column_names(
        census
    )

    print(
        "\nNormalized Census columns:"
    )

    for column in census.columns:
        print(
            f"  {column}"
        )

    # --------------------------------------------------------
    # Required Census columns
    # --------------------------------------------------------

    required = [
        "District Name",
        "Village Code",
        "Village Name",
        "Total Households",
        "Total Population of Village",
        "Total Male Population of Village",
        "Total Female Population of Village",
        "Sub District Code",
    ]

    missing = [
        column
        for column in required
        if column not in census.columns
    ]

    if missing:
        raise ValueError(
            "\nMissing required Census columns:\n"
            f"{missing}\n\n"
            "This means the workbook schema has changed. "
            "Inspect the normalized column list above."
        )

    # --------------------------------------------------------
    # Filter Wayanad
    # --------------------------------------------------------

    census["District Name"] = (
        census["District Name"]
        .astype(str)
        .str.strip()
    )

    census = census[
        census["District Name"]
        .str.lower()
        == "wayanad"
    ].copy()

    print(
        f"\nWayanad Census records: "
        f"{len(census)}"
    )

    # --------------------------------------------------------
    # Normalize village codes
    # --------------------------------------------------------

    census["village_code"] = normalize_code(
        census["Village Code"]
    )

    # --------------------------------------------------------
    # Validate village codes
    # --------------------------------------------------------

    if census["village_code"].eq("").any():

        bad = census[
            census["village_code"].eq("")
        ]

        raise ValueError(
            "Census contains rows with missing "
            "village codes:\n"
            f"{bad[['Village Name']].to_string(index=False)}"
        )

    # --------------------------------------------------------
    # Rename fields
    # --------------------------------------------------------

    census = census.rename(
        columns={
            "Village Name":
                "village_name",

            "Total Households":
                "households_2011",

            "Total Population of Village":
                "population_2011",

            "Total Male Population of Village":
                "male_population_2011",

            "Total Female Population of Village":
                "female_population_2011",

            "Sub District Code":
                "subdistrict_code",
        }
    )

    # --------------------------------------------------------
    # Convert population fields
    # --------------------------------------------------------

    numeric_columns = [
        "households_2011",
        "population_2011",
        "male_population_2011",
        "female_population_2011",
    ]

    for column in numeric_columns:

        census[column] = pd.to_numeric(
            census[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Missing-value QA
    # --------------------------------------------------------

    for column in numeric_columns:

        missing_count = int(
            census[column].isna().sum()
        )

        if missing_count > 0:

            raise ValueError(
                f"Census field '{column}' "
                f"contains {missing_count} missing values."
            )

    # --------------------------------------------------------
    # Duplicate Census codes
    # --------------------------------------------------------

    duplicate_census = census[
        census["village_code"].duplicated(
            keep=False
        )
    ]

    if not duplicate_census.empty:

        print(
            "\nDUPLICATE CENSUS CODES:"
        )

        print(
            duplicate_census[
                [
                    "village_code",
                    "village_name",
                ]
            ].to_string(index=False)
        )

        raise ValueError(
            "Duplicate Census village codes found."
        )

    # --------------------------------------------------------
    # Print Census totals before reconciliation
    # --------------------------------------------------------

    print()
    print(
        "WAYANAD CENSUS TOTALS"
    )
    print(
        "-" * 80
    )

    print(
        f"Village records : {len(census)}"
    )

    print(
        f"Population      : "
        f"{census['population_2011'].sum():,.0f}"
    )

    print(
        f"Households      : "
        f"{census['households_2011'].sum():,.0f}"
    )

    print(
        f"Male population : "
        f"{census['male_population_2011'].sum():,.0f}"
    )

    print(
        f"Female population: "
        f"{census['female_population_2011'].sum():,.0f}"
    )

    return census


# ============================================================
# RECONCILIATION
# ============================================================

def reconcile(
    nwdp,
    census
):

    print()
    print("=" * 80)
    print("CENSUS ↔ NWDP RECONCILIATION")
    print("=" * 80)

    print(
        f"NWDP spatial units : {len(nwdp)}"
    )

    print(
        f"Census villages    : {len(census)}"
    )

    # --------------------------------------------------------
    # Expected Census record count
    # --------------------------------------------------------

    if len(census) != EXPECTED_RURAL_WAYANAD_VILLAGES:

        raise ValueError(
            "\nUnexpected Wayanad Census village count.\n"
            f"Expected: "
            f"{EXPECTED_RURAL_WAYANAD_VILLAGES}\n"
            f"Actual: {len(census)}\n"
        )

    print(
        f"\nPASS: Census contains "
        f"{EXPECTED_RURAL_WAYANAD_VILLAGES} "
        "rural Wayanad village records."
    )

    # --------------------------------------------------------
    # Code sets
    # --------------------------------------------------------

    nwdp_codes = set(
        nwdp["village_code"]
    )

    census_codes = set(
        census["village_code"]
    )

    matched_codes = (
        nwdp_codes
        & census_codes
    )

    census_only_codes = (
        census_codes
        - nwdp_codes
    )

    nwdp_only_codes = (
        nwdp_codes
        - census_codes
    )

    # --------------------------------------------------------
    # Print code reconciliation
    # --------------------------------------------------------

    print()
    print(
        "-" * 80
    )
    print(
        "VILLAGE CODE RECONCILIATION"
    )
    print(
        "-" * 80
    )

    print(
        f"NWDP codes       : {len(nwdp_codes)}"
    )

    print(
        f"Census codes     : {len(census_codes)}"
    )

    print(
        f"Exact matches    : {len(matched_codes)}"
    )

    print(
        f"Census-only      : {len(census_only_codes)}"
    )

    print(
        f"NWDP-only        : {len(nwdp_only_codes)}"
    )

    # --------------------------------------------------------
    # Census-only details
    # --------------------------------------------------------

    print()
    print(
        "CENSUS-ONLY CODES"
    )

    census_only = census[
        census["village_code"]
        .isin(census_only_codes)
    ].copy()

    if census_only.empty:

        print(
            "  NONE"
        )

    else:

        print(
            census_only[
                [
                    "village_code",
                    "village_name",
                ]
            ].to_string(index=False)
        )

    # --------------------------------------------------------
    # NWDP-only details
    # --------------------------------------------------------

    print()
    print(
        "NWDP-ONLY CODES"
    )

    nwdp_only = nwdp[
        nwdp["village_code"]
        .isin(nwdp_only_codes)
    ].copy()

    if nwdp_only.empty:

        print(
            "  NONE"
        )

    else:

        print(
            nwdp_only[
                [
                    "village_code",
                    "village",
                ]
            ].to_string(index=False)
        )

    # --------------------------------------------------------
    # Exact join
    # --------------------------------------------------------

    census_attributes = census[
        [
            "village_code",
            "village_name",
            "subdistrict_code",
            "households_2011",
            "population_2011",
            "male_population_2011",
            "female_population_2011",
        ]
    ].copy()

    matched = nwdp.merge(
        census_attributes,
        on="village_code",
        how="inner",
        validate="one_to_one",
    )

    print()
    print(
        f"Exact village-code matches: "
        f"{len(matched)}"
    )

    # --------------------------------------------------------
    # Exact-match QA
    # --------------------------------------------------------

    if len(matched) != EXPECTED_RURAL_WAYANAD_VILLAGES:

        raise ValueError(
            "\nExact village-code reconciliation failed.\n"
            f"Expected matches: "
            f"{EXPECTED_RURAL_WAYANAD_VILLAGES}\n"
            f"Actual matches: {len(matched)}\n"
        )

    print(
        f"PASS: all "
        f"{EXPECTED_RURAL_WAYANAD_VILLAGES} "
        "Census villages have exact NWDP geometry matches."
    )

    # --------------------------------------------------------
    # Population QA
    # --------------------------------------------------------

    population_total = (
        matched[
            "population_2011"
        ].sum()
    )

    household_total = (
        matched[
            "households_2011"
        ].sum()
    )

    male_total = (
        matched[
            "male_population_2011"
        ].sum()
    )

    female_total = (
        matched[
            "female_population_2011"
        ].sum()
    )

    print()
    print(
        "-" * 80
    )
    print(
        "MATCHED CENSUS TOTALS"
    )
    print(
        "-" * 80
    )

    print(
        f"Population 2011       : "
        f"{population_total:,.0f}"
    )

    print(
        f"Households 2011       : "
        f"{household_total:,.0f}"
    )

    print(
        f"Male population       : "
        f"{male_total:,.0f}"
    )

    print(
        f"Female population     : "
        f"{female_total:,.0f}"
    )

    # --------------------------------------------------------
    # Population QA
    # --------------------------------------------------------

    if population_total != EXPECTED_RURAL_POPULATION_2011:

        raise ValueError(
            "\nPopulation QA FAILED.\n"
            f"Expected: "
            f"{EXPECTED_RURAL_POPULATION_2011:,}\n"
            f"Actual:   {population_total:,.0f}"
        )

    print()
    print(
        f"PASS: population total matches "
        f"{EXPECTED_RURAL_POPULATION_2011:,}"
    )

    # --------------------------------------------------------
    # Household QA
    # --------------------------------------------------------

    if household_total != EXPECTED_RURAL_HOUSEHOLDS_2011:

        raise ValueError(
            "\nHousehold QA FAILED.\n"
            f"Expected: "
            f"{EXPECTED_RURAL_HOUSEHOLDS_2011:,}\n"
            f"Actual:   {household_total:,.0f}"
        )

    print(
        f"PASS: household total matches "
        f"{EXPECTED_RURAL_HOUSEHOLDS_2011:,}"
    )

    # --------------------------------------------------------
    # Sex population QA
    # --------------------------------------------------------

    sex_total = (
        male_total
        + female_total
    )

    if sex_total != population_total:

        raise ValueError(
            "\nSex population QA FAILED.\n"
            f"Male + Female: {sex_total:,.0f}\n"
            f"Population:    {population_total:,.0f}"
        )

    print(
        "PASS: male + female population "
        "equals total population."
    )

    # --------------------------------------------------------
    # Geometry QA
    # --------------------------------------------------------

    if matched.geometry.is_empty.any():

        empty_count = int(
            matched.geometry.is_empty.sum()
        )

        raise ValueError(
            f"\nGeometry QA FAILED: "
            f"{empty_count} matched records "
            "have empty geometry."
        )

    if matched.geometry.isna().any():

        null_count = int(
            matched.geometry.isna().sum()
        )

        raise ValueError(
            f"\nGeometry QA FAILED: "
            f"{null_count} matched records "
            "have null geometry."
        )

    print(
        "PASS: all matched villages have valid geometry."
    )

    # --------------------------------------------------------
    # Save clean output
    # --------------------------------------------------------

    output_file = (
        OUTPUT_DIR
        / "wayanad_census_nwdp_village_population_2011.gpkg"
    )

    # Keep the output focused instead of carrying hundreds
    # of unrelated NWDP attribute columns forward.
    output_columns = [
        "village_code",
        "village",
        "village_name",
        "district",
        "subdistrict_code",
        "households_2011",
        "population_2011",
        "male_population_2011",
        "female_population_2011",
        "geometry",
    ]

    output_columns = [
        column
        for column in output_columns
        if column in matched.columns
    ]

    output = matched[
        output_columns
    ].copy()

    # --------------------------------------------------------
    # Save GeoPackage
    # --------------------------------------------------------

    if output_file.exists():
        output_file.unlink()

    output.to_file(
        output_file,
        layer="village_population",
        driver="GPKG",
    )

    print()
    print(
        "OUTPUT CREATED:"
    )

    print(
        output_file
    )

    print()
    print(
        f"Output village features: "
        f"{len(output)}"
    )

    return output


# ============================================================
# MAIN
# ============================================================

def main():

    nwdp = load_nwdp()

    census = load_census()

    matched = reconcile(
        nwdp,
        census
    )

    print()
    print("=" * 80)
    print("RECONCILIATION COMPLETE")
    print("=" * 80)

    print()
    print(
        "Final dataset:"
    )

    print(
        f"  Features : {len(matched)}"
    )

    print(
        f"  Population: "
        f"{matched['population_2011'].sum():,.0f}"
    )

    print(
        f"  Households: "
        f"{matched['households_2011'].sum():,.0f}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()