"""
LightGBM Impact Model
Quantile regression for Implementation Shortfall.
"""
try:
    import lightgbm as lgb
except ImportError:
    lgb = None

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import pickle
from pathlib import Path

class LGBMImpactModel:
    """
    Impact forecasting using Gradient Boosting Quantile Regression.
    
    Predicts the distribution of Execution Cost (IS bps) based on:
    - Volatility
    - Spread
    - Relative Size (% ADV)
    - Participation Rate
    """
    
    def __init__(self, model_dir: Optional[str] = None):
        self.models = {}  # quantile -> model
        self.quantiles = [0.5, 0.9]
        self.feature_names = [
            "volatility_bps",
            "spread_bps",
            "log_adv",
            "size_pct_adv",
            "participation_rate",
            "hour_of_day"
        ]
        self.model_dir = Path(model_dir) if model_dir else None
        
    def train(self, X: pd.DataFrame, y: pd.Series):
        """
        Train quantile regression models.
        X columns must match self.feature_names.
        """
        # Validation split
        mask = np.random.rand(len(X)) < 0.8
        X_train, X_val = X[mask], X[~mask]
        y_train, y_val = y[mask], y[~mask]
        
        if lgb is None:
            print("Warning: LightGBM not installed. Impact model training skipped.")
            return

        for q in self.quantiles:
            print(f"Training LightGBM for quantile {q}...")
            
            params = {
                'objective': 'quantile',
                'alpha': q,
                'metric': 'quantile',
                'learning_rate': 0.05,
                'num_leaves': 31,
                'min_data_in_leaf': 20,
                'verbose': -1
            }
            
            dtrain = lgb.Dataset(X_train, label=y_train)
            dval = lgb.Dataset(X_val, label=y_val, reference=dtrain)
            
            model = lgb.train(
                params,
                dtrain,
                num_boost_round=500,
                valid_sets=[dval],
                callbacks=[
                    lgb.early_stopping(stopping_rounds=20),
                    lgb.log_evaluation(period=0) # Suppress clutter
                ]
            )
            
            self.models[q] = model
            
    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Predict p50 and p90 IS bps.
        Returns DataFrame with 'pred_is_p50', 'pred_is_p90'.
        """
        if not self.models:
            raise ValueError("Models not trained")
            
        preds = pd.DataFrame(index=X.index)
        
        for q in self.quantiles:
            col = f"pred_is_p{int(q*100)}"
            preds[col] = self.models[q].predict(X)
            
        return preds
        
    def save(self, path: str):
        """Save models to pickle."""
        if not self.models:
            return
        
        # We can't pickle booster directly easily in all versions, 
        # but saving the whole class is standard for research code.
        with open(path, 'wb') as f:
            pickle.dump(self.models, f)
            
    def load(self, path: str):
        """Load models from pickle."""
        with open(path, 'rb') as f:
            self.models = pickle.load(f)

    def get_alpha_beta(self, volatility: float, spread: float) -> Tuple[float, float]:
        """
        Derive localized alpha/beta for CVX optimizer from model predictions.
        
        Cost ~ alpha * q + beta * q^2
        
        We approximate this by querying the model at two size points:
        1. Small size -> Linear impact dominates (alpha)
        2. Large size -> Quadratic impact dominates (beta)
        """
        # Default fallback if not trained
        if 0.5 not in self.models:
            # Default linear model: 0.5 * spread + small beta
            return spread * 0.5, 1e-4

        # Create dummy features for query
        # We assume 'size_pct_adv' is the 'q' variable
        
        base_features = {
            "volatility_bps": volatility,
            "spread_bps": spread,
            "log_adv": 15.0, # Dummy typical log ADV
            "participation_rate": 0.05, # Assumed avg
            "hour_of_day": 10 # Assumed avg
        }
        
        # Point A: Small trade (0.1% ADV)
        df_a = pd.DataFrame([base_features])
        df_a["size_pct_adv"] = 0.001
        
        # Point B: Large trade (5% ADV)
        df_b = pd.DataFrame([base_features])
        df_b["size_pct_adv"] = 0.05
        
        # Predict p50 cost
        cost_a = float(self.models[0.5].predict(df_a)[0])
        cost_b = float(self.models[0.5].predict(df_b)[0])
        
        # Cost_bps = (IS / Price) * 10000 ?? No, Model targets IS_bps directly.
        # Total Cost $ approx = IS_bps * Notional
        # But optimize minimizes total $ usually or normalized units.
        
        # Solve for alpha, beta:
        # Cost_bps(q) = alpha * 1 + beta * q  (if we normalize IS bps by q usually implies linear price impact)
        # Actually IS_bps = Slip_bps + Perm_bps
        # IS_bps(q) ~ Spread/2 + I * q^0.5 (Square root law)
        # or Linear: IS_bps(q) ~ Spread/2 + Beta * q
        
        # Let's fit linear approximation: IS_bps = alpha + beta * size_pct
        q_a = 0.001
        q_b = 0.05
        
        # Slope (beta)
        beta_est = (cost_b - cost_a) / (q_b - q_a)
        
        # Intercept (alpha - strictly spread/2 usually)
        alpha_est = cost_a - beta_est * q_a
        
        # Ensure positive
        alpha_est = max(0.0, alpha_est)
        beta_est = max(0.0, beta_est)
        
        return alpha_est, beta_est
