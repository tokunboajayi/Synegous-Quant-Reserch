from enum import Enum
from pathlib import Path
import os

class MNXConfig:
    # Data Paths
    MNX_ROOT = Path("/app/data/mnx")
    ARTIFACTS_DIR = Path("/app/data/outputs")
    
    # Universe
    UNIVERSE_SIZE = 500  # Top 500 liquid
    MIN_PRICE = 5.0
    MIN_ADV = 1_000_000
    
    # Feature Params
    MOMENTUM_WINDOWS = [5, 20, 60]
    VOL_WINDOW = 20
    
    # Model Params
    TARGET_LOOKAHEAD = 1 # Next day return
    
    # Portfolio Params
    LONG_PERCENTILE = 0.90
    SHORT_PERCENTILE = 0.10
    MAX_POSITION_WEIGHT = 0.05
    TARGET_VOL = 0.15

    @staticmethod
    def get_run_dir(run_id: str) -> Path:
        return MNXConfig.ARTIFACTS_DIR / run_id / "mnx"
