import json
import pandas as pd
from pathlib import Path

input_file = Path(
    "data/raw/rainfall/observed/wayanad/wayanad_daily_rainfall_2015_2025.json"
)

output_file = Path(
    "data/raw/rainfall/accumulated/wayanad/wayanad_rainfall_accumulated_2015_2025.csv"
)

with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame({
    "date": data["daily"]["time"],
    "rainfall_mm": data["daily"]["precipitation_sum"]
})

df["date"] = pd.to_datetime(df["date"])

# Rolling rainfall accumulation
df["rainfall_24h_mm"] = df["rainfall_mm"].rolling(1).sum()
df["rainfall_72h_mm"] = df["rainfall_mm"].rolling(3).sum()
df["rainfall_7day_mm"] = df["rainfall_mm"].rolling(7).sum()

df.to_csv(output_file, index=False)

print("Accumulated rainfall created successfully.")
print(f"Rows: {len(df)}")
print(f"Output: {output_file}")
print()
print(df.head(10))