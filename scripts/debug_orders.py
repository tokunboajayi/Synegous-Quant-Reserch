from nmie.labeling.parent_orders import ParentOrderGenerator
import polars as pl
from pathlib import Path

# Verify data exists
data_path = Path("data/raw/bars/data_2025-12-01.parquet")
print(f"Data exists: {data_path.exists()}")
if data_path.exists():
    print(pl.read_parquet(data_path).filter(pl.col("ticker")=="SPY"))

# Run Generator
gen = ParentOrderGenerator()
# asking for 2025-12-04, so it looks for < 2025-12-04. 
# We have 2025-12-01 in the system.
df = gen.generate_orders("SPY", "2025-12-04")
print(df)
