import pandas as pd
import numpy as np
import lightgbm as lgb
import json
from pathlib import Path

class LGBMRanker:
    """
    Production LightGBM Ranker.
    """
    def __init__(self, params_path: Path = None):
        self.model = None
        self.params = {
            "objective": "binary",
            "metric": "auc",
            "boosting_type": "gbdt",
            "verbosity": -1,
            "learning_rate": 0.05,
            "num_leaves": 31,
            "max_depth": -1
        }
        
        # Load tuned params if available
        if params_path and params_path.exists():
            try:
                with open(params_path, 'r') as f:
                    tuned = json.load(f)
                    self.params.update(tuned)
                print(f"[Model] Loaded tuned params: {tuned}")
            except Exception as e:
                print(f"[Model] Error loading tuned params: {e}")

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """
        Train the model on the provided features and target.
        """
        dtrain = lgb.Dataset(X, label=y)
        self.model = lgb.train(
            self.params, 
            dtrain, 
            num_boost_round=100
        )
        
    def predict(self, X: pd.DataFrame) -> np.array:
        """
        Generate predictions (scores).
        """
        if self.model is None:
            # Fallback for unconnected pipeline test, but ideally should fit first
            print("[Model] Warning: Predict called before fit. Returning zeros.")
            return np.zeros(len(X))
            
        return self.model.predict(X)
