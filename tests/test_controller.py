from nmie.optimizer.trust_region import TrustRegion, TrustRegionConfig
from nmie.optimizer.neural_controller import LocalController, MarketState

def test_controller():
    # Setup
    tr = TrustRegion(TrustRegionConfig(max_deviation_pct=0.10, step_limit_pct=0.50))
    ctrl = LocalController()
    
    # 1. Normal State
    state = MarketState(
        vol_ratio=1.0, spread_ratio=1.0, imbalance=0.0,
        progress_frac=0.5, time_frac=0.5, deviation_pct=0.0
    )
    alpha = ctrl.get_action(state)
    print(f"Normal Action: {alpha} (Expected ~1.0)")
    
    # 2. Good Liquidity (High Vol, Tight Spread)
    state_liq = MarketState(
        vol_ratio=1.5, spread_ratio=0.8, imbalance=0.2,
        progress_frac=0.5, time_frac=0.5, deviation_pct=0.0
    )
    alpha_liq = ctrl.get_action(state_liq)
    print(f"Liquidity Action: {alpha_liq} (Expected > 1.0)")
    
    # 3. Bad Spread
    state_bad = MarketState(
        vol_ratio=1.0, spread_ratio=1.5, imbalance=0.0,
        progress_frac=0.5, time_frac=0.5, deviation_pct=0.0
    )
    alpha_bad = ctrl.get_action(state_bad)
    print(f"Bad Spread Action: {alpha_bad} (Expected < 1.0)")
    
    # 4. Behind Schedule
    state_behind = MarketState(
        vol_ratio=1.0, spread_ratio=1.0, imbalance=0.0,
        progress_frac=0.4, time_frac=0.4, deviation_pct=-0.05
    )
    alpha_catchup = ctrl.get_action(state_behind)
    print(f"Behind Action: {alpha_catchup} (Expected > 1.0 due to catchup)")
    
    # 5. Trust Region Clip
    # Suppose Controller goes CRAZY (alpha=3.0)
    # But step limit is 50% (max 1.5)
    planned_q = 1000
    total_shares = 100000
    cum_exec = 50000
    cum_plan = 50000
    
    safe_q = tr.clip_quantity(planned_q, 3.0, cum_exec, cum_plan, total_shares)
    print(f"Trust Region Clip: Proposed(3.0 -> 3000), Safe({safe_q})")
    assert safe_q <= 1500 # max 1.5x

if __name__ == "__main__":
    test_controller()
