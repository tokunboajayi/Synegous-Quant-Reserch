import pandas as pd
from typing import List, Dict

def bridge_mnx_basket_to_nmie_orders(basket_path: str) -> pd.DataFrame:
    """
    Reads MNX rebalance basket and converts to NMIE Parent Orders DataFrame.
    """
    # 1. Load Basket
    basket = pd.read_parquet(basket_path)
    
    # 2. Map to NMIE Format
    # NMIE expects: [ticker, side, qty, type, limit_price, arrival_time, urgency]
    # For research, we simplify:
    
    orders = []
    for _, row in basket.iterrows():
        # Logic to determine qty from weight * capital would go here
        # For now, assuming basket has 'target_qty_delta'
        qty = abs(row['qty_delta'])
        side = 'BUY' if row['qty_delta'] > 0 else 'SELL'
        
        if qty > 0:
            orders.append({
                'ticker': row['ticker'],
                'side': side,
                'qty': int(qty),
                'type': 'MARKET', # Research default
                'urgency': row.get('urgency', 'MEDIUM')
            })
            
    return pd.DataFrame(orders)
