from typing import List

def get_universe() -> List[str]:
    """
    Returns the target universe for the NMIE system.
    
    Includes:
    - SPY (Market Proxy)
    - Sector ETFs (XLF, XLK, XLE, XLV, XLI, XLY, XLP, XLU, XLB)
    - Top Liquid Stocks (Examples: AAPL, MSFT, NVDA, TSLA, AMD, AMZN, GOOGL, META)
    
    In a real production system, this would query a reference database for
    the top N stocks by ADTV (Average Daily Trading Volume).
    """
    etfs = [
        "SPY",  # S&P 500
        "QQQ",  # Nasdaq 100
        "IWM",  # Russell 2000
        "XLF",  # Financials
        "XLK",  # Technology
        "XLE",  # Energy
        "XLV",  # Healthcare
        "XLI",  # Industrials
        "XLY",  # Consumer Discretionary
        "XLP",  # Consumer Staples
        "XLU",  # Utilities
        "XLB",  # Materials
    ]
    
    # Selection of highly liquid single names across sectors for diverse microstructure
    stocks = [
        "AAPL", "MSFT", "NVDA", "TSLA", "AMD", "AMZN", "GOOGL", "META",
        "JPM", "BAC", "GS", "MS", "C",
        "XOM", "CVX",
        "JNJ", "PFE", "UNH",
        "V", "MA",
        "WMT", "COST",
        "HD", "LOW",
        "BA", "CAT",
        "DIS", "NFLX"
    ]
    
    return sorted(list(set(etfs + stocks)))

def get_market_calendar(start_date: str, end_date: str):
    """
    Returns valid trading days between start and end.
    Placeholder: returns simple date range. 
    In prod, check against NYSE calendar (pandas_market_calendars).
    """
    import pandas as pd
    return pd.bdate_range(start=start_date, end=end_date).strftime('%Y-%m-%d').tolist()
