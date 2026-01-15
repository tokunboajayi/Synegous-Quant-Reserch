"""
Deep Portfolio Intelligence API
Advanced mathematical tools for portfolio optimization and risk management.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import scipy.optimize as sco
from nmie.research.live_data import live_provider

router = APIRouter(prefix="/intelligence", tags=["Deep Intelligence"])

# ============================================================
# Data Models
# ============================================================

class KellyInput(BaseModel):
    win_rate: float
    win_loss_ratio: float
    risk_per_trade: float = 0.01

class OptimalWeightsInput(BaseModel):
    tickers: List[str]
    objective: str = "sharpe"  # sharpe, min_vol, risk_parity

class MonteCarloInput(BaseModel):
    initial_capital: float = 100000
    n_simulations: int = 1000
    n_days: int = 252
    expected_return: float = 0.12
    volatility: float = 0.15

# ============================================================
# Intelligence Logic
# ============================================================

@router.post("/kelly")
def calculate_kelly(input_data: KellyInput):
    """Calculate Kelly Criterion for optimal position sizing."""
    p = input_data.win_rate
    q = 1 - p
    b = input_data.win_loss_ratio
    
    # Kelly Formula: f* = (bp - q) / b
    if b == 0:
        return {"kelly_fraction": 0, "fraction_recommended": 0}
        
    kelly_f = (b * p - q) / b
    
    # Adjusted Kelly (Half-Kelly or Fractional Kelly is safer)
    fractional_kelly = max(0, kelly_f * 0.5)
    
    return {
        "kelly_fraction": round(kelly_f, 4),
        "fraction_recommended": round(fractional_kelly, 4),
        "interpretation": f"Recommended sizing: {fractional_kelly*100:.1f}% of capital per trade."
    }

@router.post("/optimize")
def optimize_portfolio(input_data: OptimalWeightsInput):
    """Calculate optimal weights using Mean-Variance Optimization on REAL data."""
    n = len(input_data.tickers)
    
    # Fetch real historical data for the last year
    start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    end = datetime.now().strftime("%Y-%m-%d")
    
    data = live_provider.get_backtest_data(input_data.tickers, start, end)
    if data.empty:
        raise HTTPException(status_code=400, detail="No historical data found for optimization.")
        
    pivot = data.pivot(index='date', columns='ticker', values='close')
    rets_df = pivot.pct_change().dropna()
    
    # Annualized mean returns and covariance matrix
    returns = rets_df.mean() * 252
    cov = rets_df.cov() * 252
    
    # Objective functions
    def get_ret_vol_sharpe(weights):
        weights = np.array(weights)
        ret = np.sum(returns * weights)
        vol = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
        sharpe = ret / max(vol, 0.001)
        return np.array([ret, vol, sharpe])

    def neg_sharpe(weights):
        return -get_ret_vol_sharpe(weights)[2]

    def min_vol(weights):
        return get_ret_vol_sharpe(weights)[1]

    # Constraints: sum(weights) = 1
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    # Bounds: weights between 0 and 0.4 (max 40% per asset)
    bounds = tuple((0, 0.4) for _ in range(n))
    # Initial guess
    init_guess = n * [1. / n]
    
    if input_data.objective == "sharpe":
        opt = sco.minimize(neg_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    else:
        opt = sco.minimize(min_vol, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    
    weights = opt['x']
    metrics = get_ret_vol_sharpe(weights)
    
    results = []
    for i, ticker in enumerate(input_data.tickers):
        results.append({
            "ticker": ticker,
            "weight": round(float(weights[i]), 4),
            "expected_return": round(float(returns[ticker]), 4)
        })
    
    return {
        "weights": results,
        "portfolio_metrics": {
            "expected_return": round(float(metrics[0]), 4),
            "volatility": round(float(metrics[1]), 4),
            "sharpe_ratio": round(float(metrics[2]), 4)
        }
    }

@router.post("/monte-carlo")
def run_monte_carlo(input_data: MonteCarloInput):
    """Run Monte Carlo simulation for portfolio outcomes."""
    np.random.seed(42)
    
    mu = input_data.expected_return / 252
    sigma = input_data.volatility / np.sqrt(252)
    
    simulations = np.zeros((input_data.n_simulations, input_data.n_days))
    
    for i in range(input_data.n_simulations):
        prices = [input_data.initial_capital]
        for t in range(1, input_data.n_days):
            price = prices[-1] * (1 + np.random.normal(mu, sigma))
            prices.append(price)
        simulations[i] = prices
    
    final_values = simulations[:, -1]
    
    return {
        "simulations": simulations[:10].tolist(),  # Return first 10 for plotting
        "summary": {
            "mean": round(float(np.mean(final_values)), 2),
            "median": round(float(np.median(final_values)), 2),
            "std": round(float(np.std(final_values)), 2),
            "p5": round(float(np.percentile(final_values, 5)), 2),
            "p95": round(float(np.percentile(final_values, 95)), 2),
            "prob_loss": round(float(np.sum(final_values < input_data.initial_capital) / input_data.n_simulations * 100), 2)
        }
    }
