import pandas as pd
from mnx.config import MNXConfig
from mnx.artifacts.schemas import MNXRebalanceRow
from mnx.portfolio.neutralize_cvx import neutralize_weights

def generate_rebalance_basket(scores: pd.Series, current_positions: pd.DataFrame = None) -> pd.DataFrame:
    """
    Given alpha scores, generate target weights and rebalance basket.
    """
    # 1. Neutralize
    target_weights = neutralize_weights(scores)
    
    # 2. Convert to Basket
    # Basket = Target - Current (Simplified: assume clean rebalance)
    
    # In real world, we would check current holdings.
    # For research, we often rebalance from zero or full turnover.
    
    rows = []
    for ticker, weight in target_weights.items():
        if abs(weight) < 1e-6:
            continue
            
        # Mock capital allocation: $10M AUM
        aum = 10_000_000
        notional = weight * aum
        # Mock price to get shares (assumed $100 for simplicity of mock)
        # In reality, pass `prices` argument.
        price = 100.0 
        qty = int(notional / price)
        
        if qty != 0:
            rows.append({
                "ticker": ticker,
                "weight": weight,
                "qty_delta": qty, 
                "urgency": "MEDIUM"
            })
            
    return pd.DataFrame(rows)
