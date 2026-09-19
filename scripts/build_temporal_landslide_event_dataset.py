from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

EVENT_TABLE = (
    ROOT
    / "data"
    / "processed"
    / "landslide"
    / "inventory"
    / "wayanad_gsi_event_table.csv"
)

RAINFALL_TABLE = (
    ROOT
    / "data"
    / "raw"
    / "rainfall"
    / "accumulated"
    / "wayanad"
    / "wayanad_rainfall_accumulated_2015_2025.csv"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "features"
)

OUTPUT_DATASET = (
    OUTPUT_DIR
    / "wayanad_temporal_landslide_events.parquet"
)

OUTPUT_DATE_SUMMARY = (
    OUTPUT_DIR
    / "wayanad_temporal_landslide_event_dates.parquet"
)

OUTPUT_SUMMARY = (
    OUTPUT_DIR
    / "wayanad_temporal_landslide_events_summary.csv"
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

EVENT_COLUMNS = [
    "Slide_No",
    "District",
    "Slide_Name",
    "Latitude",
    "Longitude",
    "Material Involved",
    "Movement Type",
    "History",
    "event_date",
    "event_date_end",
    "event_year",
    "date_precision",
    "temporal_confidence",
    "event_date_source",
]

RAINFALL_COLUMNS = [
    "date",
    "rainfall_mm",
    "rainfall_24h_mm",
    "rainfall_72h_mm",
    "rainfall_7day_mm",
]


# ============================================================
# HELPERS
# ============================================================

def header(title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def validate_file(path, description):
    if not path.exists():
        raise FileNotFoundError(
            f"{description} not found:\n{path}"
        )


def validate_columns(df, expected, name):
    missing = [
        column
        for column in expected
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{name} is missing columns: {missing}"
        )


# ============================================================
# LOAD EVENTS
# ============================================================

def load_events():

    header("LOADING HISTORICAL LANDSLIDE EVENTS")

    validate_file(
        EVENT_TABLE,
        "GSI event table",
    )

    df = pd.read_csv(
        EVENT_TABLE
    )

    print(
        f"Path: {EVENT_TABLE}"
    )

    print(
        f"Shape: {df.shape}"
    )

    validate_columns(
        df,
        EVENT_COLUMNS,
        "GSI event table",
    )

    # --------------------------------------------------------
    # Parse dates
    # --------------------------------------------------------

    df["event_date"] = pd.to_datetime(
        df["event_date"],
        errors="coerce",
    )

    df["event_date_end"] = pd.to_datetime(
        df["event_date_end"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Coordinates
    # --------------------------------------------------------

    df["Latitude"] = pd.to_numeric(
        df["Latitude"],
        errors="coerce",
    )

    df["Longitude"] = pd.to_numeric(
        df["Longitude"],
        errors="coerce",
    )

    if df["Latitude"].isna().any():
        raise ValueError(
            "Invalid latitude values found."
        )

    if df["Longitude"].isna().any():
        raise ValueError(
            "Invalid longitude values found."
        )

    if (
        (df["Latitude"] < -90)
        |
        (df["Latitude"] > 90)
    ).any():
        raise ValueError(
            "Latitude outside valid range."
        )

    if (
        (df["Longitude"] < -180)
        |
        (df["Longitude"] > 180)
    ).any():
        raise ValueError(
            "Longitude outside valid range."
        )

    print(
        f"Total GSI records: {len(df):,}"
    )

    print(
        f"Records with usable event_date: "
        f"{df['event_date'].notna().sum():,}"
    )

    print(
        f"Records without event_date: "
        f"{df['event_date'].isna().sum():,}"
    )

    return df


# ============================================================
# LOAD RAINFALL
# ============================================================

def load_rainfall():

    header("LOADING ACCUMULATED RAINFALL")

    validate_file(
        RAINFALL_TABLE,
        "Accumulated rainfall table",
    )

    rainfall = pd.read_csv(
        RAINFALL_TABLE
    )

    print(
        f"Path: {RAINFALL_TABLE}"
    )

    print(
        f"Shape: {rainfall.shape}"
    )

    validate_columns(
        rainfall,
        RAINFALL_COLUMNS,
        "Rainfall table",
    )

    # --------------------------------------------------------
    # Parse date
    # --------------------------------------------------------

    rainfall["date"] = pd.to_datetime(
        rainfall["date"],
        errors="coerce",
    )

    if rainfall["date"].isna().any():
        raise ValueError(
            "Rainfall table contains invalid dates."
        )

    # --------------------------------------------------------
    # Convert rainfall columns
    # --------------------------------------------------------

    rainfall_columns = [
        "rainfall_mm",
        "rainfall_24h_mm",
        "rainfall_72h_mm",
        "rainfall_7day_mm",
    ]

    for column in rainfall_columns:

        rainfall[column] = pd.to_numeric(
            rainfall[column],
            errors="coerce",
        )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Missing 72h/7day values at the beginning of the
    # rainfall series are expected.
    #
    # Do NOT replace them with zero.
    # --------------------------------------------------------

    print("\nRainfall missing-value counts:")

    print(
        rainfall[
            rainfall_columns
        ]
        .isna()
        .sum()
        .to_string()
    )

    # 24h rainfall should be complete because it requires
    # only the current day's rainfall.
    if rainfall["rainfall_24h_mm"].isna().any():
        raise ValueError(
            "Unexpected missing rainfall_24h_mm values."
        )

    # Negative rainfall is invalid.
    for column in rainfall_columns:

        if (
            rainfall[column]
            .dropna()
            .lt(0)
            .any()
        ):
            raise ValueError(
                f"Negative rainfall found in {column}."
            )

    # --------------------------------------------------------
    # Duplicate dates
    # --------------------------------------------------------

    duplicate_dates = int(
        rainfall["date"]
        .duplicated()
        .sum()
    )

    print(
        f"\nDuplicate rainfall dates: "
        f"{duplicate_dates:,}"
    )

    if duplicate_dates != 0:
        raise ValueError(
            "Rainfall table contains duplicate dates."
        )

    print(
        f"Rainfall period: "
        f"{rainfall['date'].min().date()} "
        f"to "
        f"{rainfall['date'].max().date()}"
    )

    print(
        "\nRainfall table validation: PASSED"
    )

    return rainfall


# ============================================================
# INSPECT EVENT DATES
# ============================================================

def inspect_event_dates(events):

    header("INSPECTING EVENT DATE QUALITY")

    dated = events[
        events["event_date"].notna()
    ].copy()

    dated["event_date"] = (
        dated["event_date"]
        .dt.normalize()
    )

    unique_dates = (
        dated["event_date"]
        .drop_duplicates()
        .sort_values()
    )

    print(
        f"Unique exact event dates: "
        f"{len(unique_dates):,}"
    )

    print(
        "\nExact event dates:"
    )

    for date in unique_dates:

        count = int(
            (
                dated["event_date"]
                == date
            ).sum()
        )

        print(
            f"  {date.date()} : "
            f"{count} event record(s)"
        )

    print(
        "\nDate precision distribution:"
    )

    print(
        events["date_precision"]
        .fillna("MISSING")
        .value_counts()
        .to_string()
    )

    print(
        "\nTemporal confidence distribution:"
    )

    print(
        events["temporal_confidence"]
        .fillna("MISSING")
        .value_counts()
        .to_string()
    )

    return dated


# ============================================================
# JOIN EVENTS WITH RAINFALL
# ============================================================

def join_events_and_rainfall(
    events,
    rainfall,
):

    header("JOINING EVENTS WITH RAINFALL")

    dated = events[
        events["event_date"].notna()
    ].copy()

    dated["event_date"] = (
        dated["event_date"]
        .dt.normalize()
    )

    rainfall = rainfall.copy()

    rainfall["date"] = (
        rainfall["date"]
        .dt.normalize()
    )

    merged = dated.merge(
        rainfall,
        left_on="event_date",
        right_on="date",
        how="left",
        validate="many_to_one",
    )

    merged = merged.drop(
        columns=["date"]
    )

    # --------------------------------------------------------
    # Rainfall availability
    # --------------------------------------------------------

    rainfall_columns = [
        "rainfall_mm",
        "rainfall_24h_mm",
        "rainfall_72h_mm",
        "rainfall_7day_mm",
    ]

    merged["rainfall_24h_available"] = (
        merged["rainfall_24h_mm"]
        .notna()
        .astype(np.uint8)
    )

    merged["rainfall_72h_available"] = (
        merged["rainfall_72h_mm"]
        .notna()
        .astype(np.uint8)
    )

    merged["rainfall_7day_available"] = (
        merged["rainfall_7day_mm"]
        .notna()
        .astype(np.uint8)
    )

    merged["rainfall_available"] = (
        merged[
            rainfall_columns
        ]
        .notna()
        .all(axis=1)
        .astype(np.uint8)
    )

    print(
        f"Dated event records: "
        f"{len(merged):,}"
    )

    print(
        f"Records with 24h rainfall: "
        f"{merged['rainfall_24h_available'].sum():,}"
    )

    print(
        f"Records with 72h rainfall: "
        f"{merged['rainfall_72h_available'].sum():,}"
    )

    print(
        f"Records with 7-day rainfall: "
        f"{merged['rainfall_7day_available'].sum():,}"
    )

    print(
        f"Records with complete rainfall set: "
        f"{merged['rainfall_available'].sum():,}"
    )

    return merged


# ============================================================
# UNIQUE EVENT-DATE DATASET
# ============================================================

def build_event_date_dataset(event_level):

    header("BUILDING UNIQUE EVENT-DATE DATASET")

    # --------------------------------------------------------
    # Each exact event date corresponds to one district-level
    # rainfall condition.
    # --------------------------------------------------------

    date_level = (
        event_level
        .groupby(
            "event_date",
            as_index=False,
        )
        .agg(
            landslide_record_count=(
                "Slide_No",
                "count",
            ),

            rainfall_mm=(
                "rainfall_mm",
                "first",
            ),

            rainfall_24h_mm=(
                "rainfall_24h_mm",
                "first",
            ),

            rainfall_72h_mm=(
                "rainfall_72h_mm",
                "first",
            ),

            rainfall_7day_mm=(
                "rainfall_7day_mm",
                "first",
            ),

            rainfall_24h_available=(
                "rainfall_24h_available",
                "first",
            ),

            rainfall_72h_available=(
                "rainfall_72h_available",
                "first",
            ),

            rainfall_7day_available=(
                "rainfall_7day_available",
                "first",
            ),

            rainfall_available=(
                "rainfall_available",
                "first",
            ),
        )
    )

    date_level = date_level.sort_values(
        "event_date"
    )

    print(
        f"Unique event dates: "
        f"{len(date_level):,}"
    )

    print(
        "\nUnique event-date dataset:"
    )

    print(
        date_level.to_string(
            index=False
        )
    )

    return date_level


# ============================================================
# FINAL QA
# ============================================================

def final_qa(
    all_events,
    event_level,
    date_level,
):

    header("FINAL TEMPORAL DATASET QA")

    total_events = len(
        all_events
    )

    dated_events = int(
        all_events[
            "event_date"
        ].notna().sum()
    )

    undated_events = (
        total_events
        - dated_events
    )

    print(
        f"Total GSI records: "
        f"{total_events:,}"
    )

    print(
        f"Dated records: "
        f"{dated_events:,}"
    )

    print(
        f"Undated records: "
        f"{undated_events:,}"
    )

    if len(event_level) != dated_events:
        raise ValueError(
            "Event-level row count does not match "
            "number of dated GSI records."
        )

    # --------------------------------------------------------
    # Slide_No uniqueness
    # --------------------------------------------------------

    duplicate_slide_numbers = int(
        event_level[
            "Slide_No"
        ].duplicated()
        .sum()
    )

    print(
        f"Duplicate Slide_No values: "
        f"{duplicate_slide_numbers:,}"
    )

    if duplicate_slide_numbers != 0:
        raise ValueError(
            "Duplicate Slide_No values detected."
        )

    # --------------------------------------------------------
    # Same-date rainfall consistency
    # --------------------------------------------------------

    rainfall_columns = [
        "rainfall_mm",
        "rainfall_24h_mm",
        "rainfall_72h_mm",
        "rainfall_7day_mm",
    ]

    consistency = (
        event_level
        .groupby("event_date")[
            rainfall_columns
        ]
        .nunique(
            dropna=False
        )
    )

    inconsistent = (
        consistency
        .gt(1)
        .any(axis=1)
    )

    inconsistent_count = int(
        inconsistent.sum()
    )

    print(
        f"Event dates with inconsistent rainfall: "
        f"{inconsistent_count:,}"
    )

    if inconsistent_count != 0:
        raise ValueError(
            "Rainfall differs between records sharing "
            "the same event date."
        )

    # --------------------------------------------------------
    # Event-date aggregation
    # --------------------------------------------------------

    if (
        date_level[
            "landslide_record_count"
        ].sum()
        != len(event_level)
    ):
        raise ValueError(
            "Unique event-date aggregation does not "
            "account for every event record."
        )

    # --------------------------------------------------------
    # Rainfall ordering sanity
    # --------------------------------------------------------

    valid_72h = event_level[
        event_level[
            "rainfall_72h_mm"
        ].notna()
    ]

    valid_7day = event_level[
        event_level[
            "rainfall_7day_mm"
        ].notna()
    ]

    # A cumulative 72h amount should not be lower than
    # the current 24h amount.
    invalid_72h = (
        valid_72h[
            "rainfall_72h_mm"
        ]
        <
        valid_72h[
            "rainfall_24h_mm"
        ]
    )

    print(
        f"Invalid 72h < 24h cases: "
        f"{invalid_72h.sum():,}"
    )

    if invalid_72h.any():
        raise ValueError(
            "Some 72h rainfall values are smaller "
            "than 24h rainfall."
        )

    # A cumulative 7-day amount should not be lower than
    # the 72h amount.
    valid_7day = valid_7day[
        valid_7day[
            "rainfall_72h_mm"
        ].notna()
    ]

    invalid_7day = (
        valid_7day[
            "rainfall_7day_mm"
        ]
        <
        valid_7day[
            "rainfall_72h_mm"
        ]
    )

    print(
        f"Invalid 7day < 72h cases: "
        f"{invalid_7day.sum():,}"
    )

    if invalid_7day.any():
        raise ValueError(
            "Some 7-day rainfall values are smaller "
            "than 72h rainfall."
        )

    # --------------------------------------------------------
    # Date range
    # --------------------------------------------------------

    print(
        f"\nEvent date range: "
        f"{event_level['event_date'].min().date()} "
        f"to "
        f"{event_level['event_date'].max().date()}"
    )

    print(
        f"Unique event dates: "
        f"{event_level['event_date'].nunique():,}"
    )

    print(
        "\nALL TEMPORAL QA CHECKS PASSED"
    )


# ============================================================
# WRITE OUTPUTS
# ============================================================

def write_outputs(
    event_level,
    date_level,
    all_events,
):

    header("WRITING TEMPORAL DATASETS")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Event date identifier
    # --------------------------------------------------------

    event_level = event_level.copy()

    date_level = date_level.copy()

    event_level["event_date_id"] = (
        event_level[
            "event_date"
        ]
        .dt.strftime("%Y%m%d")
    )

    date_level["event_date_id"] = (
        date_level[
            "event_date"
        ]
        .dt.strftime("%Y%m%d")
    )

    # --------------------------------------------------------
    # Event-level output
    # --------------------------------------------------------

    event_level.to_parquet(
        OUTPUT_DATASET,
        index=False,
    )

    print(
        f"Event-level output:"
        f"\n{OUTPUT_DATASET}"
    )

    # --------------------------------------------------------
    # Unique-date output
    # --------------------------------------------------------

    date_level.to_parquet(
        OUTPUT_DATE_SUMMARY,
        index=False,
    )

    print(
        f"\nEvent-date output:"
        f"\n{OUTPUT_DATE_SUMMARY}"
    )

    # --------------------------------------------------------
    # Summary CSV
    # --------------------------------------------------------

    summary = pd.DataFrame(
        [
            {
                "metric": "total_gsi_records",
                "value": len(all_events),
            },
            {
                "metric": "dated_gsi_records",
                "value": int(
                    all_events[
                        "event_date"
                    ].notna().sum()
                ),
            },
            {
                "metric": "undated_gsi_records",
                "value": int(
                    all_events[
                        "event_date"
                    ].isna().sum()
                ),
            },
            {
                "metric": "unique_event_dates",
                "value": event_level[
                    "event_date"
                ].nunique(),
            },
            {
                "metric": "records_with_24h_rainfall",
                "value": int(
                    event_level[
                        "rainfall_24h_available"
                    ].sum()
                ),
            },
            {
                "metric": "records_with_72h_rainfall",
                "value": int(
                    event_level[
                        "rainfall_72h_available"
                    ].sum()
                ),
            },
            {
                "metric": "records_with_7day_rainfall",
                "value": int(
                    event_level[
                        "rainfall_7day_available"
                    ].sum()
                ),
            },
            {
                "metric": "records_with_complete_rainfall",
                "value": int(
                    event_level[
                        "rainfall_available"
                    ].sum()
                ),
            },
        ]
    )

    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
    )

    print(
        f"\nSummary output:"
        f"\n{OUTPUT_SUMMARY}"
    )

    print(
        "\nSummary:"
    )

    print(
        summary.to_string(
            index=False
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    header(
        "WAYANAD TEMPORAL LANDSLIDE EVENT DATASET BUILDER"
    )

    print(
        "Purpose:"
    )

    print(
        "Connect dated GSI landslide records with "
        "district-level accumulated rainfall."
    )

    print(
        "\nImportant:"
    )

    print(
        "Missing early 72h/7day rainfall values are "
        "expected and are NOT replaced with zero."
    )

    print(
        "This dataset does NOT create a spatial rainfall grid."
    )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    events = load_events()

    rainfall = load_rainfall()

    # --------------------------------------------------------
    # Inspect
    # --------------------------------------------------------

    inspect_event_dates(
        events
    )

    # --------------------------------------------------------
    # Join
    # --------------------------------------------------------

    event_level = join_events_and_rainfall(
        events,
        rainfall,
    )

    # --------------------------------------------------------
    # Unique-date representation
    # --------------------------------------------------------

    date_level = build_event_date_dataset(
        event_level
    )

    # --------------------------------------------------------
    # QA
    # --------------------------------------------------------

    final_qa(
        events,
        event_level,
        date_level,
    )

    # --------------------------------------------------------
    # Write
    # --------------------------------------------------------

    write_outputs(
        event_level,
        date_level,
        events,
    )

    header(
        "COMPLETE"
    )

    print(
        "Temporal rainfall/event datasets created successfully."
    )

    print(
        "\nNext stage:"
    )

    print(
        "Use the validated spatial base and temporal "
        "event dataset to design susceptibility and "
        "future-risk modeling."
    )


if __name__ == "__main__":
    main()