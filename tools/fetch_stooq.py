import requests
import time
import pandas as pd
from pathlib import Path
import random

# Configuration
DATA_DIR = Path("data/inputs")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Expanded Universe: Major US Constituents (S&P 100 + Tech + Finance + Energy)
DEFAULT_TICKERS = [
    # Indices/ETFs
    "SPY", "QQQ", "IWM", "DIA", "IVV", "VOO", "VTI", "GLD", "SLV", "TLT",
    # Tech / Mag 7
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AMD", "NFLX", "INTC",
    # Finance
    "JPM", "BAC", "GS", "MS", "C", "WFC", "BLK", "AXP", "V", "MA",
    # Healthcare
    "JNJ", "PFE", "UNH", "LLY", "ABBV", "MRK", "TMO", "DHR",
    # Consumer
    "KO", "PEP", "PG", "WMT", "COST", "MCD", "NKE", "SBUX", "DIS",
    # Energy / Industrial
    "XOM", "CVX", "COP", "SLB", "GE", "CAT", "BA", "LMT", "RTX", "HON"
]

def fetch_ticker(ticker: str):
    """Download daily CSV for a ticker from Stooq."""
    # Stooq format: s=ticker.country & i=interval (d=daily)
    # US stocks: .US
    # Indices: ^SPX (usually differ, but let's stick to ETFs for now as they are tradable)
    
    symbol = ticker.upper()
    if not symbol.startswith("^"):
        query_symbol = f"{symbol}.US"
    else:
        query_symbol = symbol

    url = f"https://stooq.pl/q/d/l/?s={query_symbol}&i=d"
    
    print(f"Downloading {symbol} from {url}...")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            if "Exceeded the limit" in content:
                print("Rate limit exceeded. Waiting 5 seconds...")
                time.sleep(5)
                return fetch_ticker(ticker)
            
            if "No data" in content or len(content) < 50:
                 print(f"No data found for {symbol}")
                 return

            # Save
            filename = DATA_DIR / f"{symbol}_us_d.csv"
            with open(filename, "w", encoding='utf-8') as f:
                f.write(content)
            print(f"Saved to {filename}")
            
        else:
            print(f"Failed to download {symbol}: Status {response.status_code}")
            
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")

def main():
    print("Starting Stooq Scraper...")
    
    # Try to load full S&P 500 from a local file if it exists, otherwise use default
    universe_path = Path("universe.txt")
    if universe_path.exists():
        print(f"Loading custom universe from {universe_path}...")
        with open(universe_path) as f:
            tickers = [line.strip().split(',')[0] for line in f if line.strip()]
    else:
        print("Using default expanded universe (Major US Assets)...")
        tickers = DEFAULT_TICKERS

    print(f"Target Directory: {DATA_DIR.absolute()}")
    print(f"Total Tickers to Download: {len(tickers)}")
    
    for i, ticker in enumerate(tickers):
        print(f"[{i+1}/{len(tickers)}] Processing {ticker}...")
        fetch_ticker(ticker)
        
        # Rate limit kindness
        sleep_time = random.uniform(1.0, 3.0)
        time.sleep(sleep_time)

    print("Download complete.")

if __name__ == "__main__":
    main()
