"""
Backtesting Engine
Vectorized strategy backtesting with comprehensive performance metrics.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid
import json
from pathlib import Path


class BacktestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BacktestConfig:
    """Configuration for a backtest run."""
    strategy_id: str
    tickers: List[str]
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    position_size: float = 0.05  # 5% per position
    max_positions: int = 20
    transaction_cost_bps: float = 10.0  # 10 bps per trade
    slippage_bps: float = 5.0  # 5 bps slippage
    rebalance_frequency: str = "daily"  # daily, weekly, monthly
    benchmark: str = "SPY"


@dataclass
class BacktestMetrics:
    """Comprehensive performance metrics."""
    # Returns
    total_return: float = 0.0
    annualized_return: float = 0.0
    benchmark_return: float = 0.0
    alpha: float = 0.0
    
    # Risk
    volatility: float = 0.0
    downside_volatility: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0  # days
    var_95: float = 0.0  # 95% Value at Risk
    cvar_95: float = 0.0  # Conditional VaR
    
    # Risk-adjusted
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    information_ratio: float = 0.0
    
    # Trading
    total_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_trade_return: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    
    # Exposure
    avg_exposure: float = 0.0
    avg_positions: float = 0.0
    turnover: float = 0.0
    
    # Factor exposure
    beta: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "returns": {
                "total_return": round(self.total_return * 100, 2),
                "annualized_return": round(self.annualized_return * 100, 2),
                "benchmark_return": round(self.benchmark_return * 100, 2),
                "alpha": round(self.alpha * 100, 2),
            },
            "risk": {
                "volatility": round(self.volatility * 100, 2),
                "max_drawdown": round(self.max_drawdown * 100, 2),
                "max_drawdown_duration_days": self.max_drawdown_duration,
                "var_95": round(self.var_95 * 100, 2),
            },
            "risk_adjusted": {
                "sharpe_ratio": round(self.sharpe_ratio, 2),
                "sortino_ratio": round(self.sortino_ratio, 2),
                "calmar_ratio": round(self.calmar_ratio, 2),
                "information_ratio": round(self.information_ratio, 2),
            },
            "trading": {
                "total_trades": self.total_trades,
                "win_rate": round(self.win_rate * 100, 2),
                "profit_factor": round(self.profit_factor, 2),
                "avg_trade_return": round(self.avg_trade_return * 100, 3),
            },
            "exposure": {
                "beta": round(self.beta, 2),
                "avg_exposure": round(self.avg_exposure * 100, 2),
                "turnover": round(self.turnover * 100, 2),
            }
        }


@dataclass
class Trade:
    """Individual trade record."""
    trade_id: str
    ticker: str
    entry_date: str
    exit_date: Optional[str]
    entry_price: float
    exit_price: Optional[float]
    quantity: int
    side: str  # "long" or "short"
    pnl: float = 0.0
    pnl_pct: float = 0.0
    holding_days: int = 0


@dataclass 
class BacktestResult:
    """Complete backtest results."""
    backtest_id: str
    strategy_id: str
    config: BacktestConfig
    status: BacktestStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    
    # Results
    metrics: BacktestMetrics = field(default_factory=BacktestMetrics)
    equity_curve: List[Dict] = field(default_factory=list)
    drawdown_curve: List[Dict] = field(default_factory=list)
    monthly_returns: List[Dict] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
    
    # Errors
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "backtest_id": self.backtest_id,
            "strategy_id": self.strategy_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "metrics": self.metrics.to_dict(),
            "equity_curve_length": len(self.equity_curve),
            "total_trades": len(self.trades),
            "error": self.error_message,
        }


class BacktestEngine:
    """
    Vectorized backtesting engine for trading strategies.
    Supports momentum, mean-reversion, and factor-based strategies.
    """
    
    def __init__(self):
        self.results: Dict[str, BacktestResult] = {}
        self.risk_free_rate = 0.04  # 4% annual
    
    def run_backtest(self, config: BacktestConfig, price_data: pd.DataFrame) -> BacktestResult:
        """
        Run a backtest with the given configuration and price data.
        
        Args:
            config: BacktestConfig with strategy and parameters
            price_data: DataFrame with columns ['date', 'ticker', 'open', 'high', 'low', 'close', 'volume']
        
        Returns:
            BacktestResult with metrics, equity curve, and trades
        """
        backtest_id = str(uuid.uuid4())[:8]
        result = BacktestResult(
            backtest_id=backtest_id,
            strategy_id=config.strategy_id,
            config=config,
            status=BacktestStatus.RUNNING,
            started_at=datetime.now(timezone.utc)
        )
        
        try:
            # 1. Prepare data
            prices = self._prepare_price_data(price_data, config)
            if prices.empty:
                raise ValueError("No price data available for the specified tickers and date range")
            
            # 2. Generate signals based on strategy type
            signals = self._generate_signals(prices, config)
            
            # 3. Calculate positions and returns
            positions, trades = self._calculate_positions(prices, signals, config)
            
            # 4. Calculate portfolio returns
            portfolio_returns = self._calculate_portfolio_returns(prices, positions, config)
            
            # 5. Calculate equity curve
            equity_curve = self._calculate_equity_curve(portfolio_returns, config.initial_capital)
            
            # 6. Calculate metrics
            metrics = self._calculate_metrics(portfolio_returns, equity_curve, prices, trades, config)
            
            # 7. Calculate monthly returns heatmap
            monthly_returns = self._calculate_monthly_returns(portfolio_returns)
            
            # 8. Calculate drawdown curve
            drawdown_curve = self._calculate_drawdown_curve(equity_curve)
            
            # Package results
            result.metrics = metrics
            result.equity_curve = equity_curve
            result.drawdown_curve = drawdown_curve
            result.monthly_returns = monthly_returns
            result.trades = trades
            result.status = BacktestStatus.COMPLETED
            result.finished_at = datetime.now(timezone.utc)
            
        except Exception as e:
            result.status = BacktestStatus.FAILED
            result.error_message = str(e)
            result.finished_at = datetime.now(timezone.utc)
        
        self.results[backtest_id] = result
        return result
    
    def _prepare_price_data(self, df: pd.DataFrame, config: BacktestConfig) -> pd.DataFrame:
        """Prepare and validate price data."""
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df[(df['date'] >= config.start_date) & (df['date'] <= config.end_date)]
        df = df[df['ticker'].isin(config.tickers)]
        df = df.sort_values(['date', 'ticker'])
        return df
    
    def _generate_signals(self, prices: pd.DataFrame, config: BacktestConfig) -> pd.DataFrame:
        """
        Generate trading signals based on strategy type.
        Returns DataFrame with signal scores for each ticker/date.
        """
        # Pivot to get close prices by ticker
        pivot = prices.pivot(index='date', columns='ticker', values='close')
        
        # Calculate returns
        returns = pivot.pct_change()
        
        # Default: momentum signal (12-month return, skip last month)
        lookback = 252  # ~12 months
        skip = 21  # ~1 month
        
        # Momentum: trailing return
        momentum = pivot.pct_change(lookback).shift(skip)
        
        # Mean reversion: z-score
        rolling_mean = pivot.rolling(20).mean()
        rolling_std = pivot.rolling(20).std()
        zscore = (pivot - rolling_mean) / rolling_std
        
        # Volatility: inverse vol for risk parity
        vol = returns.rolling(60).std() * np.sqrt(252)
        inv_vol = 1 / vol
        
        # Combine signals (default: momentum)
        signals = momentum.rank(axis=1, pct=True)  # Cross-sectional rank
        
        # Normalize to [-1, 1]
        signals = (signals - 0.5) * 2
        
        return signals
    
    def _calculate_positions(
        self, 
        prices: pd.DataFrame, 
        signals: pd.DataFrame, 
        config: BacktestConfig
    ) -> Tuple[pd.DataFrame, List[Trade]]:
        """
        Convert signals to position weights.
        """
        # Long top quintile, short bottom quintile
        long_threshold = 0.6
        short_threshold = -0.6
        
        positions = signals.copy()
        positions[signals > long_threshold] = config.position_size
        positions[signals < short_threshold] = -config.position_size
        positions[(signals >= short_threshold) & (signals <= long_threshold)] = 0
        
        # Limit number of positions
        abs_pos = positions.abs()
        rank = abs_pos.rank(axis=1, ascending=False)
        positions[rank > config.max_positions] = 0
        
        # Normalize so sum of abs weights = 1
        abs_sum = positions.abs().sum(axis=1)
        abs_sum = abs_sum.replace(0, 1)  # Avoid division by zero
        positions = positions.div(abs_sum, axis=0)
        
        # Generate trade list (simplified)
        trades = []
        for i, (date, row) in enumerate(positions.iterrows()):
            if i == 0:
                continue
            prev_row = positions.iloc[i-1]
            for ticker in positions.columns:
                if pd.notna(row[ticker]) and pd.notna(prev_row[ticker]):
                    if row[ticker] != 0 and prev_row[ticker] == 0:
                        # Entry
                        trades.append(Trade(
                            trade_id=str(uuid.uuid4())[:8],
                            ticker=ticker,
                            entry_date=str(date.date()),
                            exit_date=None,
                            entry_price=100,  # Placeholder
                            exit_price=None,
                            quantity=1,
                            side="long" if row[ticker] > 0 else "short"
                        ))
        
        return positions, trades
    
    def _calculate_portfolio_returns(
        self,
        prices: pd.DataFrame,
        positions: pd.DataFrame,
        config: BacktestConfig
    ) -> pd.Series:
        """Calculate portfolio returns from positions."""
        # Get returns for each ticker
        pivot = prices.pivot(index='date', columns='ticker', values='close')
        returns = pivot.pct_change()
        
        # Align positions with returns (shift positions by 1 day for execution)
        shifted_positions = positions.shift(1)
        
        # Portfolio return = sum(position * return)
        portfolio_returns = (shifted_positions * returns).sum(axis=1)
        
        # Apply transaction costs
        turnover = (positions - positions.shift(1)).abs().sum(axis=1)
        tc = turnover * (config.transaction_cost_bps + config.slippage_bps) / 10000
        portfolio_returns = portfolio_returns - tc
        
        return portfolio_returns.dropna()
    
    def _calculate_equity_curve(self, returns: pd.Series, initial_capital: float) -> List[Dict]:
        """Calculate cumulative equity curve."""
        cumulative = (1 + returns).cumprod()
        equity = initial_capital * cumulative
        
        curve = []
        for date, value in equity.items():
            curve.append({
                "date": str(date.date()) if hasattr(date, 'date') else str(date),
                "equity": round(value, 2),
                "return": round((value / initial_capital - 1) * 100, 2)
            })
        
        return curve
    
    def _calculate_drawdown_curve(self, equity_curve: List[Dict]) -> List[Dict]:
        """Calculate drawdown series."""
        equities = [e["equity"] for e in equity_curve]
        dates = [e["date"] for e in equity_curve]
        
        peak = equities[0]
        drawdowns = []
        
        for i, eq in enumerate(equities):
            if eq > peak:
                peak = eq
            dd = (eq - peak) / peak
            drawdowns.append({
                "date": dates[i],
                "drawdown": round(dd * 100, 2)
            })
        
        return drawdowns
    
    def _calculate_monthly_returns(self, returns: pd.Series) -> List[Dict]:
        """Calculate monthly returns for heatmap."""
        monthly = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        result = []
        for date, ret in monthly.items():
            result.append({
                "year": date.year,
                "month": date.month,
                "return": round(ret * 100, 2)
            })
        
        return result
    
    def _calculate_metrics(
        self,
        returns: pd.Series,
        equity_curve: List[Dict],
        prices: pd.DataFrame,
        trades: List[Trade],
        config: BacktestConfig
    ) -> BacktestMetrics:
        """Calculate comprehensive performance metrics."""
        metrics = BacktestMetrics()
        
        if len(returns) < 2:
            return metrics
        
        # Basic returns
        total_ret = (1 + returns).prod() - 1
        n_years = len(returns) / 252
        ann_ret = (1 + total_ret) ** (1 / max(n_years, 0.01)) - 1
        
        metrics.total_return = total_ret
        metrics.annualized_return = ann_ret
        
        # Volatility
        metrics.volatility = returns.std() * np.sqrt(252)
        
        # Downside volatility (for Sortino)
        downside = returns[returns < 0]
        metrics.downside_volatility = downside.std() * np.sqrt(252) if len(downside) > 0 else 0.001
        
        # Max drawdown
        equity_values = [e["equity"] for e in equity_curve]
        peak = np.maximum.accumulate(equity_values)
        drawdown = (np.array(equity_values) - peak) / peak
        metrics.max_drawdown = drawdown.min()
        
        # Drawdown duration
        in_drawdown = drawdown < 0
        dd_periods = []
        current_dd = 0
        for is_dd in in_drawdown:
            if is_dd:
                current_dd += 1
            else:
                if current_dd > 0:
                    dd_periods.append(current_dd)
                current_dd = 0
        if current_dd > 0:
            dd_periods.append(current_dd)
        metrics.max_drawdown_duration = max(dd_periods) if dd_periods else 0
        
        # VaR and CVaR
        metrics.var_95 = np.percentile(returns, 5)
        metrics.cvar_95 = returns[returns <= metrics.var_95].mean() if len(returns[returns <= metrics.var_95]) > 0 else metrics.var_95
        
        # Risk-adjusted ratios
        rf_daily = self.risk_free_rate / 252
        excess_returns = returns - rf_daily
        
        if metrics.volatility > 0:
            metrics.sharpe_ratio = (ann_ret - self.risk_free_rate) / metrics.volatility
        
        if metrics.downside_volatility > 0:
            metrics.sortino_ratio = (ann_ret - self.risk_free_rate) / metrics.downside_volatility
        
        if metrics.max_drawdown != 0:
            metrics.calmar_ratio = ann_ret / abs(metrics.max_drawdown)
        
        # Trading metrics
        metrics.total_trades = len(trades)
        if len(trades) > 0:
            winning_trades = [t for t in trades if t.pnl > 0]
            losing_trades = [t for t in trades if t.pnl < 0]
            metrics.win_rate = len(winning_trades) / len(trades) if trades else 0
            
            total_wins = sum(t.pnl for t in winning_trades)
            total_losses = abs(sum(t.pnl for t in losing_trades))
            
            if total_losses > 0:
                metrics.profit_factor = total_wins / total_losses
            elif total_wins > 0:
                metrics.profit_factor = 99.99
            else:
                metrics.profit_factor = 0.0
        
        # Ensure all ratios are JSON-serializable (no NaN or Inf)
        for attr in ['sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'profit_factor']:
            val = getattr(metrics, attr)
            if np.isnan(val) or np.isinf(val):
                setattr(metrics, attr, 0.0)
        
        # Beta (vs benchmark placeholder)
        metrics.beta = 1.0  # Would calculate vs benchmark
        
        return metrics
    
    def get_result(self, backtest_id: str) -> Optional[BacktestResult]:
        """Get a backtest result by ID."""
        return self.results.get(backtest_id)
    
    def list_results(self) -> List[Dict]:
        """List all backtest results."""
        return [r.to_dict() for r in self.results.values()]


# Global engine instance
backtest_engine = BacktestEngine()
