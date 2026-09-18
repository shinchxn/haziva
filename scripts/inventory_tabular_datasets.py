from pathlib import Path

import pandas as pd


ROOT = Path("data")


print("=" * 100)
print("HAZIVA — TABULAR DATASET INVENTORY")
print("=" * 100)


files = sorted(
    list(ROOT.rglob("*.csv"))
    + list(ROOT.rglob("*.parquet"))
    + list(ROOT.rglob("*.json"))
)


for path in files:

    print("\n" + "=" * 100)
    print(f"FILE: {path}")
    print("=" * 100)

    try:

        size_mb = path.stat().st_size / (1024 * 1024)

        print(f"Size: {size_mb:.2f} MB")

        # -------------------------------------------------------------
        # CSV
        # -------------------------------------------------------------

        if path.suffix.lower() == ".csv":

            df = pd.read_csv(path, nrows=5)

            print("Type: CSV")
            print("Columns:")
            print(df.columns.tolist())

            print("\nSample:")
            print(df.head(2).to_string(index=False))

        # -------------------------------------------------------------
        # PARQUET
        # -------------------------------------------------------------

        elif path.suffix.lower() == ".parquet":

            df = pd.read_parquet(path)

            print("Type: Parquet")
            print(f"Rows: {len(df):,}")
            print(f"Columns: {len(df.columns)}")

            print("\nColumns:")
            for column in df.columns:
                print(
                    f"  {column:30s}"
                    f" dtype={str(df[column].dtype):15s}"
                )

            print("\nSample:")
            print(df.head(2).to_string(index=False))

            print("\nMissing values:")
            missing = df.isna().sum()

            for column, count in missing.items():

                if count > 0:
                    print(
                        f"  {column:30s}"
                        f" {count:,}"
                        f" ({count / len(df) * 100:.2f}%)"
                    )

        # -------------------------------------------------------------
        # JSON
        # -------------------------------------------------------------

        elif path.suffix.lower() == ".json":

            try:

                df = pd.read_json(path)

                print("Type: JSON")
                print(f"Rows: {len(df):,}")
                print("Columns:")
                print(df.columns.tolist())

            except Exception as e:

                print("JSON could not be interpreted as a table.")
                print(f"Reason: {e}")

    except Exception as e:

        print(f"ERROR: {e}")


print("\n")
print("=" * 100)
print("INVENTORY COMPLETE")
print("=" * 100)