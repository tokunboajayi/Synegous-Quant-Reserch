import polars as pl
from pathlib import Path

f = Path("data/labels/impact_labels_SPY_2025-12-02.parquet")
df = pl.read_parquet(f)
print(df)
print("\n--- Stats by Policy ---")
print(df.group_by("policy").agg([
    pl.col("is_bps").mean().alias("mean_is"),
    pl.col("is_bps").std().alias("std_is"),
    pl.col("adverse_selection_bps").mean().alias("mean_adverse")
]))
