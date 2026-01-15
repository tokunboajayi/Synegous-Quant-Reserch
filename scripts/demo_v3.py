"""
NMIE v3 Demo Script
2-minute walkthrough for non-quants.
"""

def run_demo():
    """
    NMIE v3 Demo - TCA-First Execution Research
    
    This demo shows:
    1. How we compare execution strategies
    2. Why our results are trustworthy
    3. What the system recommends
    """
    print("""
╔══════════════════════════════════════════════════════════════════╗
║              NMIE v3 - TCA-First Execution Research              ║
║                     2-Minute Demo for Non-Quants                 ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    print("📌 WHAT IS THIS SYSTEM?")
    print("-" * 60)
    print("""
NMIE v3 is a research platform that helps answer one question:

    "When we need to buy or sell a large block of shares,
     what's the BEST way to do it?"

We compare different strategies (like TWAP, VWAP, CVX) and measure
which one costs less. Then we tell you if we're confident in that answer.
    """)
    
    print("\n📊 RUNNING THE ANALYSIS...")
    print("-" * 60)
    
    # Run the pipeline
    from nmie.tca.pipeline import TCAPipeline
    
    pipeline = TCAPipeline()
    result = pipeline.run(tickers=["SPY"], n_orders_per_ticker=5)
    
    print("\n📈 WHAT WE FOUND")
    print("-" * 60)
    
    summary = result.get("summary", {})
    
    if summary:
        # Find best strategy
        best = min(summary.keys(), key=lambda s: summary[s].get("mean_is_bps", float('inf')))
        twap_is = summary.get("TWAP", {}).get("mean_is_bps", 0)
        best_is = summary[best]["mean_is_bps"]
        savings = twap_is - best_is
        
        print(f"""
We tested {result.get('n_orders', 0)} orders and found:

    📍 Best Strategy: {best}
    💰 Average Cost: {best_is:.2f} basis points
    📉 Savings vs TWAP: {savings:.2f} bps
    
What does this mean?
    - On a $1,000,000 order, we'd save about ${savings * 10:.0f}
    - At 100 orders/day, that's ${savings * 10 * 100:.0f}/day potential savings
        """)
    
    print("\n🔍 WHY SHOULD YOU TRUST THIS?")
    print("-" * 60)
    print(f"""
Gate Decision: {result.get('gate_decision', 'UNKNOWN')}

Our system checks:
    ✓ Did we test enough data? ({result.get('n_days', 0)} days)
    ✓ Did multiple simulators agree? (Yes/No)
    ✓ Was the improvement statistically significant?
    ✓ Did it work in different market conditions?

If ANY check fails, we label the run as "VALIDATION ONLY" -
meaning the results are interesting but not production-ready.
    """)
    
    print("\n🖥️ EXPLORE THE DASHBOARD")
    print("-" * 60)
    print("""
To see interactive charts and dig deeper:

    1. Start the API:
       python -m uvicorn nmie.api.server:app --reload
       
    2. Open the dashboard:
       apps/graphdash/index.html
       
    3. Toggle between:
       - Layman Mode: Simple explanations
       - Quant Mode: Advanced analytics
    """)
    
    print("\n" + "=" * 60)
    print("Demo complete! Questions? Toggle to Quant Mode for deep dives.")
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    run_demo()
