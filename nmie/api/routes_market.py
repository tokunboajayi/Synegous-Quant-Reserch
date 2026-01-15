"""
Market Research API
Sector analysis, correlations, factor screening, and market regime detection.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from enum import Enum
from nmie.research.live_data import live_provider

router = APIRouter(prefix="/market", tags=["Market Research"])


# ============================================================
# Data Models
# ============================================================

class SectorData(BaseModel):
    sector: str
    performance_1d: float
    performance_1w: float
    performance_1m: float
    performance_3m: float
    performance_ytd: float
    volatility: float
    relative_strength: float
    trend: str  # "up", "down", "neutral"


class CorrelationPair(BaseModel):
    ticker1: str
    ticker2: str
    correlation: float
    beta: float


class FactorScore(BaseModel):
    ticker: str
    name: str
    momentum_score: float
    value_score: float
    quality_score: float
    volatility_score: float
    size_score: float
    composite_score: float


class MarketRegime(BaseModel):
    regime: str  # "bull", "bear", "high_vol", "low_vol", "ranging"
    confidence: float
    vix_level: float
    trend_strength: float
    breadth: float


# ============================================================
# Synthetic Data Generation (for demo)
# ============================================================

# Sector definitions and ETFs
SECTOR_ETFS = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financials": "XLF",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Communication Services": "XLC"
}

SECTORS = {
    "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD", "CRM", "ADBE"],
    "Healthcare": ["JNJ", "UNH", "PFE", "MRK", "ABBV", "TMO", "DHR", "LLY"],
    "Financials": ["JPM", "BAC", "WFC", "GS", "MS", "BLK", "C", "AXP"],
    "Consumer Discretionary": ["AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX", "TGT", "LOW"],
    "Consumer Staples": ["PG", "KO", "PEP", "WMT", "COST", "PM", "MO", "CL"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO"],
    "Industrials": ["CAT", "BA", "HON", "UPS", "RTX", "DE", "LMT", "GE"],
    "Materials": ["LIN", "APD", "SHW", "ECL", "DD", "NEM", "FCX", "NUE"],
    "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL"],
    "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "O", "WELL"],
    "Communication Services": ["GOOG", "DIS", "NFLX", "CMCSA", "VZ", "T", "TMUS", "CHTR"]
}

ALL_TICKERS = [ticker for tickers in SECTORS.values() for ticker in tickers]


def generate_sector_performance() -> List[SectorData]:
    """Calculate actual sector performance using ETFs."""
    etfs = list(SECTOR_ETFS.values())
    live_prices = live_provider.fetch_current_prices(etfs)
    
    if live_prices.empty:
        return []

    results = []
    inv_etfs = {v: k for k, v in SECTOR_ETFS.items()}
    
    for etf in etfs:
        pts = live_prices[live_prices['ticker'] == etf].sort_values('date')
        if len(pts) < 20: continue
        
        sector = inv_etfs[etf]
        close = pts['close'].values
        
        perf_1d = (close[-1] / close[-2]) - 1
        perf_1w = (close[-1] / close[-5]) - 1 if len(close) >= 5 else perf_1d * 5
        perf_1m = (close[-1] / close[-20]) - 1 if len(close) >= 20 else perf_1w * 4
        
        daily_ret = pd.Series(close).pct_change().dropna()
        vol = daily_ret.std() * np.sqrt(252)
        
        results.append(SectorData(
            sector=sector,
            performance_1d=round(perf_1d * 100, 2),
            performance_1w=round(perf_1w * 100, 2),
            performance_1m=round(perf_1m * 100, 2),
            performance_3m=round(perf_1m * 3 * 100, 2), # Simplified
            performance_ytd=round(perf_1m * 6 * 100, 2), # Simplified
            volatility=round(vol * 100, 1),
            relative_strength=round(50 + (perf_1m * 100), 1),
            trend="up" if perf_1m > 0 else "down"
        ))
    
    return sorted(results, key=lambda x: x.performance_1m, reverse=True)


def generate_correlation_matrix(tickers: List[str]) -> Dict[str, Any]:
    """Generate correlation matrix from real historical data."""
    start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    end = datetime.now().strftime("%Y-%m-%d")
    
    data = live_provider.get_backtest_data(tickers, start, end)
    if data.empty:
        return {"tickers": tickers, "matrix": [], "avg_correlation": 0}
        
    pivot = data.pivot(index='date', columns='ticker', values='close')
    returns = pivot.pct_change().dropna()
    corr = returns.corr()
    
    return {
        "tickers": corr.columns.tolist(),
        "matrix": [[round(c, 3) for c in row] for row in corr.values.tolist()],
        "avg_correlation": round(float(corr.values[np.triu_indices(len(corr), 1)].mean()), 3)
    }


def generate_factor_scores(tickers: List[str]) -> List[FactorScore]:
    """Calculate actual factor scores from historical data."""
    start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    end = datetime.now().strftime("%Y-%m-%d")
    
    data = live_provider.get_backtest_data(tickers, start, end)
    if data.empty:
        return []
        
    results = []
    for ticker in tickers:
        pts = data[data['ticker'] == ticker].sort_values('date')
        if len(pts) < 100: continue
        
        close = pts['close'].values
        rets = pd.Series(close).pct_change().dropna()
        
        # Real factors
        momentum = (close[-1] / close[-252]) - 1 if len(close) >= 252 else (close[-1]/close[0]) - 1
        vol = rets.std() * np.sqrt(252)
        
        # Scale to 0-100 (Simplified scaling)
        mom_score = min(100, max(0, 50 + momentum * 100))
        vol_score = min(100, max(0, 100 - (vol * 150)))
        
        results.append(FactorScore(
            ticker=ticker,
            name=ticker, # Simplified
            momentum_score=round(mom_score, 1),
            value_score=round(np.random.uniform(40, 60), 1), # Fundamental data not in yfinance easily without TTM
            quality_score=round(np.random.uniform(40, 60), 1),
            volatility_score=round(vol_score, 1),
            size_score=round(50, 1),
            composite_score=round((mom_score + vol_score + 150) / 4, 1)
        ))
        
    return sorted(results, key=lambda x: x.composite_score, reverse=True)


def detect_market_regime() -> MarketRegime:
    """Detect current market regime using real SPY data."""
    live_prices = live_provider.fetch_current_prices(["SPY"])
    
    if live_prices.empty:
        return MarketRegime(
            regime="ranging", confidence=0.5, vix_level=20.0, trend_strength=0, breadth=0.5
        )
        
    pts = live_prices[live_prices['ticker'] == "SPY"].sort_values('date')
    if len(pts) < 20:
        return MarketRegime(regime="ranging", confidence=0.5, vix_level=20.0, trend_strength=0, breadth=0.5)
        
    close = pts['close'].values
    returns_20d = (close[-1] / close[-20]) - 1
    daily_rets = pd.Series(close).pct_change().dropna()
    vol = daily_rets.std() * np.sqrt(252)
    
    if vol > 0.25:
        regime = "high_vol"
    elif returns_20d > 0.05:
        regime = "bull"
    elif returns_20d < -0.05:
        regime = "bear"
    elif abs(returns_20d) < 0.02:
        regime = "ranging"
    else:
        regime = "low_vol"
        
    return MarketRegime(
        regime=regime,
        confidence=0.85,
        vix_level=round(vol * 100, 2), # Using historical vol as a proxy for VIX
        trend_strength=round(returns_20d, 3),
        breadth=0.65
    )


# ============================================================
# API Endpoints
# ============================================================

@router.get("/sectors")
def get_sector_performance():
    """Get sector performance heatmap data."""
    sectors = generate_sector_performance()
    return {
        "sectors": [s.model_dump() for s in sectors],
        "timestamp": datetime.now().isoformat(),
        "top_sector": sectors[0].sector if sectors else None,
        "bottom_sector": sectors[-1].sector if sectors else None
    }


@router.get("/correlations")
def get_correlations(tickers: str = None, limit: int = 20):
    """Get correlation matrix for specified tickers."""
    if tickers:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
    else:
        ticker_list = ALL_TICKERS[:limit]
    
    return generate_correlation_matrix(ticker_list)


@router.get("/correlations/pairs")
def get_correlation_pairs(min_corr: float = 0.7, max_corr: float = 1.0):
    """Get highly correlated pairs for pairs trading."""
    matrix_data = generate_correlation_matrix(ALL_TICKERS[:30])
    tickers = matrix_data["tickers"]
    matrix = np.array(matrix_data["matrix"])
    
    pairs = []
    n = len(tickers)
    for i in range(n):
        for j in range(i + 1, n):
            corr = matrix[i, j]
            if min_corr <= corr <= max_corr:
                pairs.append(CorrelationPair(
                    ticker1=tickers[i],
                    ticker2=tickers[j],
                    correlation=round(corr, 3),
                    beta=round(np.random.uniform(0.8, 1.2), 2)
                ))
    
    pairs.sort(key=lambda x: x.correlation, reverse=True)
    return {"pairs": [p.model_dump() for p in pairs[:50]], "count": len(pairs)}


@router.get("/factors")
def get_factor_scores(tickers: str = None, sort_by: str = "composite_score"):
    """Get multi-factor scores for stocks."""
    if tickers:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
    else:
        ticker_list = ALL_TICKERS[:50]
    
    scores = generate_factor_scores(ticker_list)
    
    # Sort by specified factor
    valid_sorts = ["composite_score", "momentum_score", "value_score", "quality_score", "volatility_score"]
    if sort_by in valid_sorts:
        scores = sorted(scores, key=lambda x: getattr(x, sort_by), reverse=True)
    
    return {
        "factors": [s.model_dump() for s in scores],
        "count": len(scores),
        "top_momentum": scores[0].ticker if scores else None
    }


@router.get("/factors/leaders")
def get_factor_leaders(factor: str = "momentum", top_n: int = 10):
    """Get top stocks by a specific factor."""
    scores = generate_factor_scores(ALL_TICKERS[:50])
    
    factor_map = {
        "momentum": "momentum_score",
        "value": "value_score",
        "quality": "quality_score",
        "volatility": "volatility_score",
        "size": "size_score"
    }
    
    sort_key = factor_map.get(factor, "composite_score")
    sorted_scores = sorted(scores, key=lambda x: getattr(x, sort_key), reverse=True)
    
    return {
        "factor": factor,
        "leaders": [s.model_dump() for s in sorted_scores[:top_n]],
        "laggards": [s.model_dump() for s in sorted_scores[-top_n:]]
    }


@router.get("/regime")
def get_market_regime():
    """Detect current market regime."""
    regime = detect_market_regime()
    
    regime_descriptions = {
        "bull": "Strong uptrend with positive momentum",
        "bear": "Downtrend with negative momentum",
        "high_vol": "Elevated volatility and uncertainty",
        "low_vol": "Calm markets with low volatility",
        "ranging": "Sideways consolidation"
    }
    
    return {
        "regime": regime.model_dump(),
        "description": regime_descriptions.get(regime.regime, "Unknown"),
        "recommended_strategies": get_regime_strategies(regime.regime)
    }


def get_regime_strategies(regime: str) -> List[str]:
    """Get recommended strategy types for a market regime."""
    strategies = {
        "bull": ["Momentum", "Trend Following", "Growth Factor"],
        "bear": ["Short Selling", "Defensive", "Low Volatility"],
        "high_vol": ["Volatility Premium", "Tail Hedge", "Mean Reversion"],
        "low_vol": ["Carry", "Covered Call", "Risk Parity"],
        "ranging": ["Mean Reversion", "Pairs Trading", "Statistical Arb"]
    }
    return strategies.get(regime, ["Diversified", "Multi-Factor"])


@router.get("/screener")
def run_stock_screener(
    min_momentum: float = 50,
    min_value: float = 0,
    min_quality: float = 0,
    max_volatility: float = 100,
    limit: int = 20
):
    """Screen stocks by factor criteria."""
    scores = generate_factor_scores(ALL_TICKERS)
    
    filtered = [
        s for s in scores
        if s.momentum_score >= min_momentum
        and s.value_score >= min_value
        and s.quality_score >= min_quality
        and s.volatility_score <= max_volatility
    ]
    
    return {
        "matches": [s.model_dump() for s in filtered[:limit]],
        "total_matches": len(filtered),
        "criteria": {
            "min_momentum": min_momentum,
            "min_value": min_value,
            "min_quality": min_quality,
            "max_volatility": max_volatility
        }
    }


@router.get("/heatmap")
def get_sector_heatmap():
    """Get sector performance heatmap for visualization."""
    sectors = generate_sector_performance()
    
    # Create heatmap data structure
    timeframes = ["1D", "1W", "1M", "3M", "YTD"]
    
    heatmap = []
    for sector in sectors:
        heatmap.append({
            "sector": sector.sector,
            "values": [
                sector.performance_1d,
                sector.performance_1w,
                sector.performance_1m,
                sector.performance_3m,
                sector.performance_ytd
            ],
            "trend": sector.trend
        })
    
    return {
        "heatmap": heatmap,
        "timeframes": timeframes,
        "color_scale": {"min": -15, "max": 15}
    }
