import json
import pandas as pd
from pathlib import Path


# ============================================================
# FILES
# ============================================================

OBSERVED = Path(
    "data/raw/rainfall/observed/wayanad/"
    "wayanad_daily_rainfall_2015_2025.json"
)

ACCUMULATED = Path(
    "data/raw/rainfall/accumulated/wayanad/"
    "wayanad_rainfall_accumulated_2015_2025.csv"
)

FORECAST = Path(
    "data/raw/rainfall/forecast/wayanad/"
    "wayanad_rainfall_forecast_7day.json"
)


# ============================================================
# CHECK FILES
# ============================================================

print("\n=== FILE CHECK ===")

for path in [OBSERVED, ACCUMULATED, FORECAST]:

    print(
        path,
        "->",
        "FOUND" if path.exists() else "MISSING"
    )


# ============================================================
# OBSERVED RAINFALL
# ============================================================

print("\n=== OBSERVED RAINFALL ===")

if not OBSERVED.exists():

    raise FileNotFoundError(
        f"Missing observed rainfall file: {OBSERVED}"
    )

with open(
    OBSERVED,
    "r",
    encoding="utf-8"
) as f:

    observed = json.load(f)

print(
    "Python type:",
    type(observed)
)

if isinstance(observed, dict):

    print(
        "Top-level keys:"
    )

    for key in observed.keys():

        print(
            "-",
            key
        )

elif isinstance(observed, list):

    print(
        "Number of records:",
        len(observed)
    )

    if len(observed) > 0:

        print(
            "First record:"
        )

        print(
            observed[0]
        )


# ============================================================
# ACCUMULATED RAINFALL
# ============================================================

print("\n=== ACCUMULATED RAINFALL ===")

if not ACCUMULATED.exists():

    raise FileNotFoundError(
        f"Missing accumulated rainfall file: {ACCUMULATED}"
    )

accumulated = pd.read_csv(
    ACCUMULATED
)

print(
    "Rows:",
    len(accumulated)
)

print(
    "Columns:"
)

for column in accumulated.columns:

    print(
        "-",
        column
    )

print(
    "\nFirst 5 rows:"
)

print(
    accumulated.head()
)

print(
    "\nData types:"
)

print(
    accumulated.dtypes
)

print(
    "\nMissing values:"
)

print(
    accumulated.isna().sum()
)


# ============================================================
# FORECAST RAINFALL
# ============================================================

print("\n=== FORECAST RAINFALL ===")

if not FORECAST.exists():

    raise FileNotFoundError(
        f"Missing forecast rainfall file: {FORECAST}"
    )

with open(
    FORECAST,
    "r",
    encoding="utf-8"
) as f:

    forecast = json.load(f)

print(
    "Python type:",
    type(forecast)
)

if isinstance(forecast, dict):

    print(
        "Top-level keys:"
    )

    for key in forecast.keys():

        print(
            "-",
            key
        )

    print(
        "\nForecast structure:"
    )

    for key, value in forecast.items():

        if isinstance(value, list):

            print(
                key,
                "-> list with",
                len(value),
                "records"
            )

            if len(value) > 0:

                print(
                    "First record:",
                    value[0]
                )

        else:

            print(
                key,
                "->",
                type(value)
            )

elif isinstance(forecast, list):

    print(
        "Number of records:",
        len(forecast)
    )

    if len(forecast) > 0:

        print(
            "First record:"
        )

        print(
            forecast[0]
        )


# ============================================================
# RAINFALL STATISTICS
# ============================================================

print(
    "\n=== ACCUMULATED RAINFALL STATISTICS ==="
)

numeric_columns = accumulated.select_dtypes(
    include="number"
).columns

for column in numeric_columns:

    print(
        f"\n{column}"
    )

    print(
        "min:",
        accumulated[column].min()
    )

    print(
        "max:",
        accumulated[column].max()
    )

    print(
        "mean:",
        accumulated[column].mean()
    )

    print(
        "median:",
        accumulated[column].median()
    )


print(
    "\n=== INSPECTION COMPLETE ==="
)