from pathlib import Path

import numpy as np
import pandas as pd


INPUT = Path(
    "data/processed/features/wayanad_spatial_landslide_training.parquet"
)

TRAIN_OUTPUT = Path(
    "data/processed/features/wayanad_spatial_train.parquet"
)

TEST_OUTPUT = Path(
    "data/processed/features/wayanad_spatial_test.parquet"
)

BLOCK_SIZE_M = 3000
TEST_FRACTION = 0.20
RANDOM_SEED = 42


print("=" * 80)
print("CREATING SPATIAL TRAIN / TEST SPLIT")
print("=" * 80)

df = pd.read_parquet(INPUT)

print(f"\nInput rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")


# -------------------------------------------------------------------------
# CREATE SPATIAL BLOCKS
# -------------------------------------------------------------------------

print("\n" + "-" * 80)
print("SPATIAL BLOCKING")
print("-" * 80)

df["block_x"] = np.floor(df["x"] / BLOCK_SIZE_M).astype(np.int64)
df["block_y"] = np.floor(df["y"] / BLOCK_SIZE_M).astype(np.int64)

df["spatial_block"] = (
    df["block_x"].astype(str)
    + "_"
    + df["block_y"].astype(str)
)

blocks = df["spatial_block"].unique()

print(f"Block size: {BLOCK_SIZE_M:,} m")
print(f"Total spatial blocks: {len(blocks):,}")


# -------------------------------------------------------------------------
# RANDOMLY SELECT WHOLE BLOCKS FOR TEST
# -------------------------------------------------------------------------

rng = np.random.default_rng(RANDOM_SEED)

blocks = np.array(blocks)
rng.shuffle(blocks)

n_test_blocks = max(
    1,
    int(len(blocks) * TEST_FRACTION)
)

test_blocks = set(blocks[:n_test_blocks])

print(f"Test blocks: {len(test_blocks):,}")
print(f"Test block fraction: {len(test_blocks) / len(blocks):.2%}")


# -------------------------------------------------------------------------
# ASSIGN ROWS
# -------------------------------------------------------------------------

df["is_test"] = df["spatial_block"].isin(test_blocks)

train_df = df[~df["is_test"]].copy()
test_df = df[df["is_test"]].copy()


# -------------------------------------------------------------------------
# REMOVE SPLIT HELPER COLUMNS
# -------------------------------------------------------------------------

for data in [train_df, test_df]:
    data.drop(
        columns=[
            "block_x",
            "block_y",
            "spatial_block",
            "is_test",
        ],
        inplace=True,
    )


# -------------------------------------------------------------------------
# REPORT
# -------------------------------------------------------------------------

print("\n" + "-" * 80)
print("SPLIT RESULTS")
print("-" * 80)

print(f"Train rows: {len(train_df):,}")
print(f"Test rows:  {len(test_df):,}")

train_pos = int(train_df["historical_landslide"].sum())
test_pos = int(test_df["historical_landslide"].sum())

train_neg = len(train_df) - train_pos
test_neg = len(test_df) - test_pos

print("\nTRAIN")
print(f"Positive: {train_pos:,}")
print(f"Negative: {train_neg:,}")
print(f"Positive %: {train_pos / len(train_df) * 100:.4f}%")

print("\nTEST")
print(f"Positive: {test_pos:,}")
print(f"Negative: {test_neg:,}")
print(f"Positive %: {test_pos / len(test_df) * 100:.4f}%")


# -------------------------------------------------------------------------
# SAVE
# -------------------------------------------------------------------------

TRAIN_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

train_df.to_parquet(TRAIN_OUTPUT, index=False)
test_df.to_parquet(TEST_OUTPUT, index=False)

print("\n" + "=" * 80)
print("SPATIAL SPLIT CREATED")
print("=" * 80)

print(f"\nTrain:")
print(TRAIN_OUTPUT)

print("\nTest:")
print(TEST_OUTPUT)

print("\nIMPORTANT:")
print("Train and test contain different geographic blocks.")
print("This reduces spatial leakage during evaluation.")