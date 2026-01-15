"""
Backtest API Routes
Endpoints for running and viewing backtests.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
import pandas as pd
from pathlib import Path

from nmie.research.backtest_engine import (
    backtest_engine, BacktestConfig, BacktestResult, BacktestStatus
)
from nmie.research.live_data import live_provider

router = APIRouter(prefix="/backtest", tags=["Backtesting"])


# ============================================================
# Request/Response Models
# ============================================================

class BacktestRequest(BaseModel):
    """Request to start a new backtest."""
    strategy_id: str
    tickers: List[str] = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "WMT"]
    start_date: str = "2023-01-01"
    end_date: str = "2024-12-31"
    initial_capital: float = 100000.0
    position_size: float = 0.05
    max_positions: int = 20
    transaction_cost_bps: float = 10.0
    slippage_bps: float = 5.0


class BacktestSummary(BaseModel):
    """Summary of a backtest for listing."""
    backtest_id: str
    strategy_id: str
    status: str
    total_return: Optional[float]
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    started_at: str


# ============================================================
# Helper Functions  
# ============================================================

def load_price_data(tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
    """
    Load price data for backtesting.
    First tries to load from local parquet files, then generates synthetic data.
    """
    data_dir = Path("/app/data/outputs") if Path("/app").exists() else Path("data/outputs")
    
    all_data = []
    
    for ticker in tickers:
        # Try to load real data
        ticker_path = data_dir / f"{ticker}_daily.parquet"
        if ticker_path.exists():
            df = pd.read_parquet(ticker_path)
            df['ticker'] = ticker
            all_data.append(df)
        else:
            # Try to fetch live data instead of generating synthetic
            print(f"Loading live data for {ticker}...")
            df = live_provider.get_backtest_data([ticker], start_date, end_date)
            
            if not df.empty:
                all_data.append(df)
            else:
                # Last resort: Generate synthetic data for demo
                dates = pd.date_range(start=start_date, end=end_date, freq='B')
                n = len(dates)
                
                # Random walk with drift
                np.random.seed(hash(ticker) % 2**32)
                returns = np.random.normal(0.0005, 0.02, n)  # ~12% annual return, 20% vol
                prices = 100 * np.exp(np.cumsum(returns))
                
                df = pd.DataFrame({
                    'date': dates,
                    'ticker': ticker,
                    'open': prices * np.random.uniform(0.99, 1.01, n),
                    'high': prices * np.random.uniform(1.00, 1.03, n),
                    'low': prices * np.random.uniform(0.97, 1.00, n),
                    'close': prices,
                    'volume': np.random.randint(1000000, 10000000, n)
                })
                all_data.append(df)
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


import numpy as np  # Add this import


# ============================================================
# API Endpoints
# ============================================================

@router.post("/run")
def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """Start a new backtest."""
    config = BacktestConfig(
        strategy_id=request.strategy_id,
        tickers=request.tickers,
        start_date=request.start_date,
        end_date=request.end_date,
        initial_capital=request.initial_capital,
        position_size=request.position_size,
        max_positions=request.max_positions,
        transaction_cost_bps=request.transaction_cost_bps,
        slippage_bps=request.slippage_bps,
    )
    
    # Load price data
    price_data = load_price_data(config.tickers, config.start_date, config.end_date)
    
    # Run backtest
    result = backtest_engine.run_backtest(config, price_data)
    
    return {
        "backtest_id": result.backtest_id,
        "status": result.status.value,
        "message": "Backtest completed" if result.status == BacktestStatus.COMPLETED else f"Failed: {result.error_message}"
    }


@router.get("/results")
def list_backtests():
    """List all backtest results."""
    results = backtest_engine.list_results()
    return {"backtests": results, "count": len(results)}


@router.get("/results/{backtest_id}")
def get_backtest(backtest_id: str):
    """Get full backtest results."""
    result = backtest_engine.get_result(backtest_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Backtest {backtest_id} not found")
    
    return {
        "backtest_id": result.backtest_id,
        "strategy_id": result.strategy_id,
        "status": result.status.value,
        "started_at": result.started_at.isoformat(),
        "finished_at": result.finished_at.isoformat() if result.finished_at else None,
        "metrics": result.metrics.to_dict(),
        "config": {
            "tickers": result.config.tickers,
            "start_date": result.config.start_date,
            "end_date": result.config.end_date,
            "initial_capital": result.config.initial_capital,
        },
        "error": result.error_message,
    }


@router.get("/results/{backtest_id}/equity")
def get_equity_curve(backtest_id: str):
    """Get equity curve for charting."""
    result = backtest_engine.get_result(backtest_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Backtest {backtest_id} not found")
    
    return {
        "backtest_id": backtest_id,
        "equity_curve": result.equity_curve,
        "drawdown_curve": result.drawdown_curve,
    }


@router.get("/results/{backtest_id}/monthly")
def get_monthly_returns(backtest_id: str):
    """Get monthly returns for heatmap."""
    result = backtest_engine.get_result(backtest_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Backtest {backtest_id} not found")
    
    return {
        "backtest_id": backtest_id,
        "monthly_returns": result.monthly_returns,
    }


@router.get("/results/{backtest_id}/trades")
def get_trades(backtest_id: str, limit: int = 100):
    """Get trade history."""
    result = backtest_engine.get_result(backtest_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Backtest {backtest_id} not found")
    
    trades = [
        {
            "trade_id": t.trade_id,
            "ticker": t.ticker,
            "entry_date": t.entry_date,
            "exit_date": t.exit_date,
            "side": t.side,
            "pnl": t.pnl,
            "pnl_pct": t.pnl_pct,
        }
        for t in result.trades[:limit]
    ]
    
    return {
        "backtest_id": backtest_id,
        "trades": trades,
        "total_trades": len(result.trades),
    }


@router.post("/quick-test/{strategy_id}")
def quick_test_strategy(strategy_id: str):
    """
    Quick test a strategy with default parameters.
    Uses 2 years of data on top 10 US stocks.
    """
    config = BacktestConfig(
        strategy_id=strategy_id,
        tickers=["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "WMT"],
        start_date="2023-01-01",
        end_date="2024-12-31",
        initial_capital=100000.0,
    )
    
    price_data = load_price_data(config.tickers, config.start_date, config.end_date)
    result = backtest_engine.run_backtest(config, price_data)
    
    return {
        "backtest_id": result.backtest_id,
        "strategy_id": strategy_id,
        "status": result.status.value,
        "quick_metrics": {
            "total_return": f"{result.metrics.total_return * 100:.1f}%",
            "sharpe_ratio": f"{result.metrics.sharpe_ratio:.2f}",
            "max_drawdown": f"{result.metrics.max_drawdown * 100:.1f}%",
            "win_rate": f"{result.metrics.win_rate * 100:.0f}%",
        } if result.status == BacktestStatus.COMPLETED else None,
        "error": result.error_message,
    }
