from nmie.config import POLYGON_API_KEY
import requests

def test():
    if not POLYGON_API_KEY:
        print("No API Key loaded!")
        return
        
    print(f"Key loaded: {POLYGON_API_KEY[:5]}...")
    
    ticker = "SPY"
    date = "2025-12-10"
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/minute/{date}/{date}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": 50000,
        "apiKey": POLYGON_API_KEY
    }
    
    resp = requests.get(url, params=params)
    print(f"Aggs Status: {resp.status_code}")
    print(f"Aggs Response: {resp.text[:200]}")
    
    # Try Reference Endpoint (usually less restricted)
    url_ref = "https://api.polygon.io/v3/reference/tickers"
    params_ref = {"apiKey": POLYGON_API_KEY, "limit": 1}
    resp2 = requests.get(url_ref, params=params_ref)
    print(f"Ref Status: {resp2.status_code}")
    print(f"Ref Response: {resp2.text[:200]}")

    # Try Daily Aggs
    url_daily = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{date}/{date}"
    params_daily = {
        "adjusted": "true",
        "apiKey": POLYGON_API_KEY
    }
    resp3 = requests.get(url_daily, params=params_daily)
    print(f"Daily Status: {resp3.status_code}")
    print(f"Daily Response: {resp3.text[:200]}")

if __name__ == "__main__":
    test()
