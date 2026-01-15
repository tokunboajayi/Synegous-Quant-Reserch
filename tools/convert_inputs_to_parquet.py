import pandas as pd
from pathlib import Path
import os
import time

INPUTS_DIR = Path("data/inputs")
OUTPUT_FILE = INPUTS_DIR / "mnx_inputs.parquet"

def convert_all():
    print(f"Scanning {INPUTS_DIR} for CSVs...")
    files = list(INPUTS_DIR.glob("*_us_d.csv"))
    
    if not files:
        print("No CSV files found.")
        return

    print(f"Found {len(files)} CSVs. Starting conversion...")
    start_time = time.time()
    
    dfs = []
    for i, f in enumerate(files):
        try:
            # Parse Polish format: Data, Otwarcie, Najwyzszy, Najnizszy, Zamkniecie, Wolumen
            df = pd.read_csv(f)
            
            # Map columns
            df = df.rename(columns={
                "Data": "date",
                "Zamkniecie": "close",
                "Wolumen": "volume",
                "Date": "date",      
                "Close": "close",
                "Volume": "volume"
            })
            
            # Keep only essential columns
            cols = ["date", "close", "volume"]
            df = df[[c for c in cols if c in df.columns]]
            
            if "date" not in df.columns or "close" not in df.columns:
                print(f"Skipping {f.name} (missing columns)")
                continue

            df["date"] = pd.to_datetime(df["date"])
            
            # Add ticker column
            ticker = f.name.replace("_us_d.csv", "").upper()
            df["ticker"] = ticker
            
            dfs.append(df)
            
            if (i+1) % 50 == 0:
                print(f"Processed {i+1}/{len(files)}")
                
        except Exception as e:
            print(f"Error reading {f}: {e}")

    if not dfs:
        print("No valid data loaded.")
        return

    print("Concatenating...")
    full_df = pd.concat(dfs, ignore_index=True)
    
    print("Saving to Parquet...")
    # Sort for efficiency
    full_df = full_df.sort_values(["ticker", "date"])
    
    # Save optimized parquet (snappy compression is default and fast)
    full_df.to_parquet(OUTPUT_FILE, index=False)
    
    elapsed = time.time() - start_time
    print(f"SUCCESS! Created {OUTPUT_FILE}")
    print(f"Rows: {len(full_df)}")
    print(f"Time: {elapsed:.2f}s")

if __name__ == "__main__":
    convert_all()
