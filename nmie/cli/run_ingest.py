import argparse
import sys
from nmie.ingest.ingest_bars import ingest_range
from nmie.ingest.universe import get_universe
from nmie.config import START_DATE, END_DATE

def main():
    parser = argparse.ArgumentParser(description="Ingest market data for NMIE")
    parser.add_argument("--tickers", type=str, nargs="+", help="Specific tickers to ingest")
    parser.add_argument("--start", type=str, default=START_DATE, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", type=str, default=END_DATE, help="End date YYYY-MM-DD")
    parser.add_argument("--full-universe", action="store_true", help="Ingest full universe")
    
    args = parser.parse_args()
    
    if args.full_universe:
        tickers = get_universe()
        print(f"Ingesting full universe: {len(tickers)} tickers")
    elif args.tickers:
        tickers = args.tickers
    else:
        print("No tickers specified. Use --tickers or --full-universe")
        return
        
    print(f"Ingesting {tickers} from {args.start} to {args.end}")
    ingest_range(tickers, args.start, args.end)

if __name__ == "__main__":
    main()
