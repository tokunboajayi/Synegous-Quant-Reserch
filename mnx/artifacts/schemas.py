from pydantic import BaseModel
from typing import List, Dict, Optional

class MNXRebalanceRow(BaseModel):
    ticker: str
    weight: float
    action: str # BUY, SELL, HOLD
    
class MNXArtifacts:
    RUN_PARAMS = "mnx_run_params.json"
    UNIVERSE = "mnx_universe.csv"
    SCORES = "mnx_scores.parquet"
    TARGET_WEIGHTS = "mnx_target_weights.json"
    BASKET = "mnx_rebalance_basket.parquet"
