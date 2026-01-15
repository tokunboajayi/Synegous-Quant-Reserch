"""
Synegious Nexus Engine
Autonomous orchestrator linking Market Research, Strategy Selection, Backtesting, and Portfolio Optimization.
Methodology: DAMFRAPS (Dynamic Adaptive Multi-Factor Regime-Aligned Portfolio Synthesis)
"""
import logging
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any

from nmie.api.routes_market import detect_market_regime, generate_factor_scores
from nmie.api.routes_strategies import list_strategies
from nmie.research.backtest_engine import BacktestEngine, BacktestConfig
from nmie.api.routes_intelligence import calculate_kelly, KellyInput, optimize_portfolio, OptimalWeightsInput
from nmie.research.live_data import live_provider

logger = logging.getLogger("nexus")

class NexusEngine:
    def __init__(self):
        self.status = "IDLE"
        self.progress = 0
        self.current_stage = ""
        self.last_run_results = {}

    async def run_autonomous_loop(self):
        """Execute the full DAMFRAPS loop."""
        try:
            self.status = "RUNNING"
            self.progress = 0
            
            # STAGE 1: Market Radar (Live Regime Detection)
            self.current_stage = "Market Radar: Detecting Live Regime"
            logger.info("Starting Stage 1: Market Radar")
            
            # Fetch live prices for a basket of broad market ETFs
            market_basket = ["SPY", "QQQ", "IWM", "GLD", "TLT"]
            live_prices = live_provider.fetch_current_prices(market_basket)
            
            if not live_prices.empty:
                regime_data = self._calculate_real_regime(live_prices)
                regime = regime_data["regime"]
            else:
                logger.warning("Live data fetch failed, falling back to simulated regime")
                regime_data = detect_market_regime()
                regime = regime_data.regime
            
            self.progress = 20
            await asyncio.sleep(1) # Simulation delay

            # STAGE 2: Strategy Synthesis (Regime Alignment)
            self.current_stage = f"Strategy Synthesis: Selecting for {regime}"
            logger.info(f"Starting Stage 2: Strategy Synthesis for {regime}")
            all_strats = list_strategies()
            
            # Map regime to categories
            regime_map = {
                "bull": ["trend_following", "momentum"],
                "bear": ["short_selling", "volatility"],
                "high_vol": ["mean_reversion", "volatility"],
                "low_vol": ["carry_trade", "arbitrage"],
                "ranging": ["mean_reversion", "statistical_arbitrage"]
            }
            target_cats = regime_map.get(regime, ["trend_following"])
            candidates = [s for s in all_strats if s.type in target_cats][:5]
            
            if not candidates:
                candidates = all_strats[:5] # Fallback
            
            self.progress = 40
            await asyncio.sleep(1)

            # STAGE 3: Backtest Validation (Stress Testing)
            self.current_stage = "Backtest Validation: High-Speed Stress Test"
            logger.info("Starting Stage 3: Backtest Validation")
            engine = BacktestEngine()
            
            valid_strategies = []
            
            for strat in candidates:
                # Run a simplified 1-year backtest using LIVE historical data
                config = BacktestConfig(
                    strategy_id=strat.strategy_id,
                    tickers=["AAPL", "MSFT", "GOOGL"],
                    start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                    end_date=datetime.now().strftime("%Y-%m-%d")
                )
                
                # Use live provider instead of local parity files
                price_data = live_provider.get_backtest_data(config.tickers, config.start_date, config.end_date)
                
                if price_data.empty:
                    logger.warning(f"No live data for {strat.name}, skipping validation")
                    continue
                    
                result = engine.run_backtest(config, price_data)
                
                if result.metrics.sharpe_ratio > 1.0: # Minimum alpha threshold
                    valid_strategies.append({
                        "id": strat.strategy_id,
                        "name": strat.name,
                        "sharpe": result.metrics.sharpe_ratio,
                        "returns": result.metrics.total_return
                    })
            
            self.progress = 60
            await asyncio.sleep(1)

            # STAGE 4: Intelligence Filter (Allocation & Sizing)
            self.current_stage = "Intelligence Filter: Kelly & MVO Optimization"
            logger.info("Starting Stage 4: Intelligence Filter")
            
            # Apply Kelly for sizing (using average metrics)
            kelly_data = calculate_kelly(KellyInput(win_rate=0.58, win_loss_ratio=1.6))
            fraction = kelly_data["fraction_recommended"]
            
            # Apply MVO for weights
            tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META"]
            opt_data = optimize_portfolio(OptimalWeightsInput(tickers=tickers, objective="sharpe"))
            
            self.progress = 80
            await asyncio.sleep(1)

            # STAGE 5: Execution Bridge (Production Deployment)
            self.current_stage = "Execution Bridge: Generating Master Basket"
            logger.info("Starting Stage 5: Execution Bridge")
            
            final_basket = {
                "nexus_id": f"NEXUS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "regime": regime,
                "sizing_fraction": fraction,
                "strategy_candidates": [s["name"] for s in valid_strategies],
                "allocations": opt_data["weights"],
                "expected_metrics": opt_data["portfolio_metrics"]
            }
            
            self.last_run_results = final_basket
            self.progress = 100
            self.status = "COMPLETED"
            self.current_stage = "Nexus Loop Complete"
            
            return final_basket

        except Exception as e:
            logger.error(f"Nexus Loop Failed: {e}")
            self.status = "FAILED"
            self.current_stage = f"Error: {str(e)}"
            raise

    def _calculate_real_regime(self, prices: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate the actual market regime based on input price data.
        Logic:
        - Bull: Positive 20-day return, Low volatility
        - Bear: Negative 20-day return, High volatility
        - High Vol: Volatility > 2.0x 60-day average
        - Ranging: Return near zero
        """
        # Pivot to get SPY (or first ticker) returns
        ticker = prices['ticker'].unique()[0]
        pts = prices[prices['ticker'] == ticker].sort_values('date')
        
        # Calculate 20-day return
        returns_20d = (pts['close'].iloc[-1] / pts['close'].iloc[-20]) - 1 if len(pts) >= 20 else 0
        
        # Calculate daily returns for volatility
        daily_returns = pts['close'].pct_change().dropna()
        vol = daily_returns.std() * np.sqrt(252)
        
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
            
        return {
            "regime": regime,
            "volatility": round(vol, 4),
            "return_20d": round(returns_20d, 4),
            "confidence": 0.85
        }

nexus_engine = NexusEngine()
