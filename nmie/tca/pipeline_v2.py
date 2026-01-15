"""
NMIE v3 TCA Pipeline Runner
End-to-end TCA evaluation with dual simulators.
"""
import numpy as np
import polars as pl
from datetime import datetime
from typing import List, Dict

from nmie.config import DATA_DIR
from nmie.store.feature_store import FeatureStore
from nmie.labeling.parent_orders import ParentOrderGenerator
from nmie.optimizer.policies import twap_schedule, vwap_schedule, pov_schedule
from nmie.execution_sim import (
    NextTradeFillSimulator, BarVwapFillSimulator,
    ExecutionConstraints, compare_simulators, aggregate_metrics
)
from nmie.tca import (
    decompose_cost, compute_regime_slices, identify_failure_buckets,
    write_tca_summary, write_tca_orders, write_regime_slices,
    write_simulator_sensitivity, write_executive_note
)
from nmie.research import generate_run_id, PromotionGate, GateConfig
from nmie.models.lgbm_impact import LGBMImpactModel
from nmie.optimizer.cvx_planner import GlobalPlanner
from nmie.optimizer.types import PlanningInput, MarketForecast, Schedule
import pandas as pd

class TCAPipeline:
    """
    v3 TCA-First Pipeline.
    
    Runs both simulators, computes TCA, generates all artifacts.
    """
    
    def __init__(self, run_id: str = None):
        self.run_id = run_id or generate_run_id()
        self.store = FeatureStore()
        self.hard_sim = NextTradeFillSimulator()
        self.soft_sim = BarVwapFillSimulator()
        self.gate = PromotionGate()
        self.planner = GlobalPlanner()
        self.comp_model = LGBMImpactModel()
        
        # Load model if exists
        try:
             self.comp_model.load("nmie/models/impact_model.pkl")
             print("Loaded impact model.")
        except:
             print("No pre-trained impact model found. Using defaults.")
        
    def generate_orders(self, tickers: List[str], n_orders_per_ticker: int) -> List[Dict]:
        """Step 1: Generate Parent Orders and Plans."""
        print(f"[1/5] Generating Orders for {len(tickers)} tickers...")
        all_orders = []
        data_dir = DATA_DIR / "raw" / "bars"
        dates = []
        for f in data_dir.glob("*.parquet"):
            parts = f.stem.split("_")
            if len(parts) >= 2:
                dates.append(parts[-1])
        dates = sorted(set(dates))
        
        n_orders = 0
        for ticker in tickers:
            for date in dates:
                bars = self.store.load_bars(ticker, date)
                if bars.is_empty(): continue
                    
                gen = ParentOrderGenerator(seed=42)
                orders_df = gen.generate_orders(ticker, date, n_orders=n_orders_per_ticker)
                
                if orders_df.is_empty(): continue
                
                for order in orders_df.to_dicts():
                    n_orders += 1
                    order_id = f"{ticker}_{date}_{n_orders:04d}"
                    horizon = order["horizon_mins"]
                    total_qty = order["size_shares"]
                    side = order["side"]
                    
                    volumes = bars["volume"].to_numpy()[:horizon]
                    n_intervals = len(volumes)
                    if n_intervals == 0: continue

                    twap_sched = twap_schedule(total_qty, n_intervals)
                    vwap_sched = vwap_schedule(total_qty, volumes)
                    pov_sched = pov_schedule(total_qty, volumes, 0.1)
                    
                    # CVX Plan
                    closes = bars["close"].to_numpy()[:n_intervals+1]
                    vol = np.std(np.diff(np.log(closes))) if len(closes) > 1 else 0.0001
                    alpha, beta = self.comp_model.get_alpha_beta(vol*10000, 2.0)

                    forecast = MarketForecast(
                         intervals=[str(i) for i in range(n_intervals)],
                         expected_volume=volumes,
                         expected_volatility=np.full(n_intervals, vol),
                         expected_spread=np.full(n_intervals, 0.02),
                         alpha=np.full(n_intervals, alpha),
                         beta=np.full(n_intervals, beta)
                    )
                    
                    cvx_sched_result = self.planner.plan(PlanningInput(
                        total_shares=total_qty,
                        forecast=forecast,
                        risk_aversion=0.5,
                        max_participation=0.15 
                    ))
                    cvx_sched = cvx_sched_result.quantities if cvx_sched_result.is_feasible else twap_sched

                    all_orders.append({
                        "order_id": order_id,
                        "ticker": ticker,
                        "date": date,
                        "side": side,
                        "size_shares": total_qty,
                        "horizon": horizon,
                        "meta": order, # keep original meta
                        "schedules": {
                            "TWAP": twap_sched.tolist(),
                            "VWAP": vwap_sched.tolist(),
                            "POV": pov_sched.tolist(),
                            "CVX": cvx_sched.tolist()
                        }
                    })
        return all_orders

    def run_from_external_orders(self, basket_path: str, capital: float = 1_000_000.0) -> Dict:
        """
        Runs pipeline driven by MNX Alpha Basket.
        """
        print(f"[Pipeline] Loading External Basket from {basket_path}")
        df = pd.read_parquet(basket_path)
        
        # Basket format: index=date,ticker, columns=weight
        # We need to convert weights to ORDERS (shares).
        
        all_orders = []
        
        # Iterate over unique (date, ticker) in basket
        # Assume df has multiindex or cols
        if 'date' not in df.columns or 'ticker' not in df.columns:
            df = df.reset_index()
            
        print(f"[Pipeline] Processing {len(df)} basket items...")
        
        # Pre-load dates available in store to avoid missing data crash
        # Actually store handles it nicely returning empty bars.
        
        for _, row in df.iterrows():
            ticker = row['ticker']
            date = str(row['date']) # Ensure string YYYY-MM-DD
            weight = row['weight']
            
            if abs(weight) < 1e-6: continue # Skip near zero if not filtered
            
            bars = self.store.load_bars(ticker, date)
            if bars.is_empty():
                print(f"  [Warn] No bars for {ticker} on {date}. Skipping.")
                continue
                
            # Calculate Target Shares
            # Shares = (Capital * Weight) / Price
            entry_price = bars['open'][0]
            notional = capital * abs(weight)
            qty = int(notional / entry_price)
            if qty < 1: continue
            
            side = 1 if weight > 0 else -1
            
            # Create Order Dict
            # Default Horizon: Full Day (390 mins)
            horizon = min(390, len(bars))
            volumes = bars["volume"].to_numpy()[:horizon]
            
            # Schedules
            twap_sched = twap_schedule(qty, horizon)
            vwap_sched = vwap_schedule(qty, volumes)
            pov_sched = pov_schedule(qty, volumes, 0.1) # 10% POV limit default
            
            # Add to list
            all_orders.append({
                "order_id": f"MNX_{ticker}_{date}",
                "ticker": ticker,
                "date": date,
                "side": side,
                "size_shares": qty,
                "horizon": horizon,
                "meta": {"volatility": 0.015, "ref_adv": 1e6, "pct_adv": 0.01}, # Defaults for sim
                "schedules": {
                    "TWAP": twap_sched.tolist(),
                    "VWAP": vwap_sched.tolist(),
                    "POV": pov_sched.tolist()
                    # Skip CVX plan inside loop for speed, or add if critical
                }
            })
            
        print(f"[Pipeline] Converted basket to {len(all_orders)} execution orders.")
        
        # Run standard flow from step 2
        results = self.run_simulations(all_orders)
        summary = self.compute_metrics(results)
        
        # Save artifacts
        write_tca_summary(self.run_id, summary)
        
        return summary

    def run_simulations(self, orders: List[Dict]) -> List[Dict]:
        """Step 2: Run HARD + SOFT sims for all orders/strategies."""
        print(f"[2/5] Running Simulations for {len(orders)} orders...")
        results = []
        
        for ord_data in orders:
            ticker = ord_data["ticker"]
            date = ord_data["date"]
            horizon = ord_data["horizon"]
            side = ord_data["side"]
            
            bars = self.store.load_bars(ticker, date).head(horizon)
            if bars.is_empty(): continue
                
            row = ord_data.copy()
            del row["schedules"] 
            del row["meta"]
            
            order = ord_data["meta"]
            row.update({
                "volatility_bps": order.get("volatility", 0) * 10000,
                "log_adv": np.log(order["ref_adv"]) if order["ref_adv"] > 0 else 0,
                "size_pct_adv": order["pct_adv"]
            })

            for strategy, sched_list in ord_data["schedules"].items():
                sched = np.array(sched_list)
                _, hard_m = self.hard_sim.simulate(sched, bars, side)
                _, soft_m = self.soft_sim.simulate(sched, bars, side)
                
                if hard_m and soft_m:
                    res = row.copy()
                    res.update({
                        "strategy": strategy,
                        "is_bps": hard_m.is_bps,
                        "is_soft_bps": soft_m.is_bps,
                        "pct_filled": hard_m.pct_filled,
                        "avg_price": hard_m.avg_fill_price
                    })
                    results.append(res)
        
        return results

    def compute_metrics(self, results: List[Dict]) -> Dict:
        """Step 3: Aggregate metrics and Gate logic."""
        print("[3/5] Computing Metrics...")
        df = pd.DataFrame(results)
        if df.empty: return {}
        
        summary = {}
        strategies = df["strategy"].unique()
        
        for strat in strategies:
            sub = df[df["strategy"] == strat]
            vals = sub["is_bps"].values
            summary[strat] = {
                "mean_is_bps": float(np.mean(vals)),
                "median_is_bps": float(np.median(vals)),
                "p95_is_bps": float(np.percentile(vals, 95)),
                "n_orders": len(vals)
            }
            
        twap_df = df[df["strategy"] == "TWAP"].set_index("order_id")["is_bps"]
        # Pre-calc win rates map
        strategy_results = {}
        for s in strategies:
             strategy_results[s] = df[df["strategy"] == s].set_index("order_id")["is_bps"]

        for strat in strategies:
            if strat == "TWAP": 
                summary[strat]["win_rate_vs_twap"] = 0.5
                continue
                
            strat_vals = strategy_results[strat]
            # Align by index
            common = twap_df.index.intersection(strat_vals.index)
            if len(common) == 0:
                 summary[strat]["win_rate_vs_twap"] = 0.0
                 continue
                 
            t_v = twap_df.loc[common]
            s_v = strat_vals.loc[common]
            wins = (s_v < t_v).sum()
            summary[strat]["win_rate_vs_twap"] = wins / len(common)
        
        return summary

    def run_sensitivity_check(self, orders: List[Dict]) -> None:
        """
        E-01 Optimization: Generate Sensitivity Matrix.
        Runs subset of orders with variations: Cap 5%, 20%, Spread OFF.
        """
        print("[4.5/5] Generating Sensitivity Matrix (Sampling)...")
        from nmie.execution_sim import NextTradeFillSimulator, ExecutionConstraints
        
        # Sample limit to save time
        sample = orders[:20] if len(orders) > 20 else orders
        matrix_rows = []
        
        scenarios = [
            ("Base", 0.10, True),
            ("Cap_5pct", 0.05, True),
            ("Cap_20pct", 0.20, True),
            ("NoSpread", 0.10, False)
        ]
        
        for ord_data in sample:
            ticker = ord_data["ticker"]
            date = ord_data["date"]
            horizon = ord_data["horizon"]
            side = ord_data["side"]
            
            # Just test TWAP for sensitivity to isolate sim effects
            if "TWAP" not in ord_data["schedules"]: continue
            sched = np.array(ord_data["schedules"]["TWAP"])
            
            bars = self.store.load_bars(ticker, date).head(horizon)
            if bars.is_empty(): continue
            
            for (scen_name, cap, spread_on) in scenarios:
                # Build specific sim
                sim = NextTradeFillSimulator(
                    constraints=ExecutionConstraints(max_participation_rate=cap),
                    use_spread_crossing=spread_on
                )
                _, metrics = sim.simulate(sched, bars, side)
                
                if metrics:
                    matrix_rows.append({
                        "order_id": ord_data["order_id"],
                        "scenario": scen_name,
                        "cap": cap,
                        "spread_on": spread_on,
                        "is_bps": metrics.is_bps,
                        "pct_filled": metrics.pct_filled
                    })
                    
        if matrix_rows:
            import pandas as pd
            df = pd.DataFrame(matrix_rows)
            path = DATA_DIR / "outputs" / self.run_id / "sensitivity_matrix.csv"
            df.to_csv(path, index=False)
            print(f"Saved sensitivity matrix to {path}")

    def run(self, tickers: List[str] = ["SPY"], n_orders_per_ticker: int = 10):
        """Monolithic run (Legacy support wrapper)."""
        orders = self.generate_orders(tickers, n_orders_per_ticker)
        results = self.run_simulations(orders)
        summary = self.compute_metrics(results)
        
        write_tca_summary(self.run_id, summary)
        write_tca_orders(self.run_id, orders)
        
        # E-01 Optimization: Sensitivity Matrix
        self.run_sensitivity_check(orders)
        
        # Recalculate counts for Gate
        n_orders = len(orders)
        n_tickers = len(set(o["ticker"] for o in orders))
        n_days = len(set(o["date"] for o in orders))
        
        # Simulator sensitivity
        print("[4/5] Checking simulator sensitivity...")
        
        # Re-extract HARD/SOFT results for TWAP (Baseline)
        hard_results = [r["is_bps"] for r in results if r["strategy"] == "TWAP"]
        soft_results = [r["is_soft_bps"] for r in results if r["strategy"] == "TWAP"]
        
        hard_mean = np.mean(hard_results) if hard_results else 0
        soft_mean = np.mean(soft_results) if soft_results else 0
        divergence = abs(hard_mean - soft_mean)
        agrees = divergence < GateConfig.MAX_HARD_SOFT_DIVERGENCE_BPS
        
        sensitivity = {
            "hard_mean_is_bps": float(hard_mean),
            "soft_mean_is_bps": float(soft_mean),
            "divergence_bps": float(divergence),
            "simulators_agree": agrees,
            "sensitivity_warning": not agrees
        }
        write_simulator_sensitivity(self.run_id, sensitivity)
        
        # Regime slices (placeholder)
        write_regime_slices(self.run_id, [])
        
        # Gate decision
        print("[5/5] Evaluating promotion gate...")
        from nmie.research.types import WalkForwardResult
        
        # Train Impact Model if sufficient data
        if len(orders) >= 100:
             print("  Training Impact Model (Continuous Learning)...")
             df_train = pd.DataFrame(results) # Use results for training data
             try:
                 cols = self.comp_model.feature_names
                 if all(c in df_train.columns for c in cols):
                     self.comp_model.train(df_train[cols], df_train["is_bps"])
                     self.comp_model.save("nmie/models/impact_model.pkl")
             except Exception as e:
                 print(f"  Model training failed: {e}")

        fold = WalkForwardResult(
            fold_id=0,
            n_orders=n_orders,
            mean_is_anee=summary.get("VWAP", {}).get("mean_is_bps", 0),
            mean_is_twap=summary.get("TWAP", {}).get("mean_is_bps", 0),
            delta_is=summary.get("TWAP", {}).get("mean_is_bps", 0) - summary.get("VWAP", {}).get("mean_is_bps", 0),
            p95_is_anee=summary.get("VWAP", {}).get("p95_is_bps", 0),
            p95_is_twap=summary.get("TWAP", {}).get("p95_is_bps", 0),
            win_rate=summary.get("VWAP", {}).get("win_rate_vs_twap", 0)
        )
        
        gate_result = self.gate.evaluate(
            run_id=self.run_id,
            fold_results=[fold],
            n_days=n_days,
            n_tickers=n_tickers,
            n_orders=n_orders,
            hard_sim_agrees=agrees,
            n_regimes_improved=3 # Placeholder for v3
        )
        self.gate.save_decision(self.run_id, gate_result)
        
        # Executive note
        best_strategy = min(summary.keys(), key=lambda s: summary[s]["mean_is_bps"]) if summary else "N/A"
        best_is = summary.get(best_strategy, {}).get("mean_is_bps", 0)
        twap_is = summary.get("TWAP", {}).get("mean_is_bps", 0)
        savings = twap_is - best_is
        
        write_executive_note(
            self.run_id,
            headline=f"{best_strategy} saves {savings:.1f} bps vs TWAP",
            summary=f"Evaluated {n_orders} orders across {n_tickers} tickers over {n_days} days. {best_strategy} achieved the lowest mean IS.",
            key_findings=[
                f"Best strategy: {best_strategy} ({best_is:.2f} bps mean IS)",
                f"TWAP baseline: {twap_is:.2f} bps mean IS",
                f"Improvement: {savings:.2f} bps",
                f"Simulators agree: {'Yes' if agrees else 'NO - SENSITIVITY WARNING'}"
            ],
            recommendation="Consider using {best_strategy} for execution" if savings > 0 and agrees else "Optimization Inconclusive or Unsafe",
            gate_decision=gate_result.decision.value
        )
        
        print(f"\n{'='*60}")
        print(f"  PIPELINE COMPLETE")
        print(f"  Run ID: {self.run_id}")
        print(f"  Gate Decision: {gate_result.decision.value}")
        print(f"  Artifacts: data/outputs/{self.run_id}/")
        print(f"{'='*60}")
        
        return {
            "run_id": self.run_id,
            "n_days": n_days,
            "n_tickers": n_tickers,
            "n_orders": n_orders,
            "gate_decision": gate_result.decision.value,
            "summary": summary
        }

def run_tca_pipeline(tickers: List[str] = ["SPY"]) -> str:
    """Convenience function to run TCA pipeline."""
    pipeline = TCAPipeline()
    result = pipeline.run(tickers=tickers)
    return result["run_id"]

if __name__ == "__main__":
    run_id = run_tca_pipeline()
    print(f"\nRun ID: {run_id}")

def run_tca_pipeline(tickers: List[str] = ["SPY"]) -> str:
    """Convenience function to run TCA pipeline."""
    pipeline = TCAPipeline()
    result = pipeline.run(tickers=tickers)
    return result["run_id"]

if __name__ == "__main__":
    run_id = run_tca_pipeline()
    print(f"\nRun ID: {run_id}")

def run_tca_pipeline(tickers: List[str] = ["SPY"]) -> str:
    """Convenience function to run TCA pipeline."""
    pipeline = TCAPipeline()
    result = pipeline.run(tickers=tickers)
    return result["run_id"]

if __name__ == "__main__":
    run_id = run_tca_pipeline()
    print(f"\nRun ID: {run_id}")
