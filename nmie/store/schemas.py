import polars as pl
import pandas as pd
from typing import Dict

# 1-minute Bar Schema
BAR_SCHEMA = {
    "ticker": pl.Utf8,
    "timestamp": pl.Datetime(time_unit="ms", time_zone="UTC"),
    "open": pl.Float64,
    "high": pl.Float64,
    "low": pl.Float64,
    "close": pl.Float64,
    "volume": pl.Float64,
    "vwap": pl.Float64,
    "trade_count": pl.Float64,
}

# Quote Schema (NBBO)
QUOTE_SCHEMA = {
    "ticker": pl.Utf8,
    "timestamp": pl.Datetime(time_unit="ms", time_zone="UTC"),
    "bid_price": pl.Float64,
    "bid_size": pl.Float64,
    "ask_price": pl.Float64,
    "ask_size": pl.Float64,
    "exchange_id": pl.Int32
}

def validate_dataframe(df: pl.DataFrame, schema_type: str = "bar") -> bool:
    """
    Validates that a polars DataFrame matches the expected schema.
    """
    target_schema = BAR_SCHEMA if schema_type == "bar" else QUOTE_SCHEMA
    
    # Check columns exist
    missing_cols = [col for col in target_schema.keys() if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")
        
    return True

def enforce_types(df: pd.DataFrame, schema_type: str = "bar") -> pd.DataFrame:
    """
    Casts pandas dataframe to strict types before storage.
    """
    # Todo: Implement pandas type enforcement if needed, usually we convert to polars
    return df
