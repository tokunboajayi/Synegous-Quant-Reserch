import pandas as pd
from typing import Dict, Any

class RegimeDetector:
    """
    Detects market regime (Risk-On, Risk-Off, Crash).
    """
    def detect(self, market_data: pd.DataFrame) -> str:
        # Placeholder logic
        # 0 = Risk Off, 1 = Risk On
        return "RISK_ON"
