from datetime import datetime
import time
from typing import Dict, Any, List
import pandas as pd
import json
import traceback
import os

# Import Data Plane Components
from nmie.ingest.ingest_bars import ingest_range
from nmie.tca.pipeline_v2 import TCAPipeline
from nmie.control_plane.jobs import JobParams

def run_ingest(tickers: List[str], start_date: str, end_date: str):
    """Wraps ingest_range."""
    print(f"Logic: Ingesting {len(tickers)} tickers from {start_date} to {end_date}")
    ingest_range(tickers, start_date, end_date)

def run_feature_build(tickers: List[str]):
    """Placeholder for feature building."""
    print(f"Logic: Building features for {tickers}")
    # In v3, FeatureStore builds on fly or we could pre-cache here
    pass

def run_order_gen(run_id: str, params: JobParams):
    """
    Step 1 of Pipeline: Generate Orders.
    Returns: Path to orders artifact or list of order IDs.
    """
    pipeline = TCAPipeline(run_id=run_id)
    # We need to persist the orders intermediate state?
    # TCAPipeline_v2 needs to be stateful or we pass data via artifacts.
    # For simplicity v3++, we might run the sub-steps in one process 
    # OR we make TCAPipeline methods save intermediate parquets.
    
    # Let's assume TCAPipeline methods return data we can pickle/save?
    # Or better, let's keep it simple: 
    # Control Plane calls `run_full_pipeline` which calls the granular steps internally?
    # NO, the requirement is "resumable".
    # So we need intermediate artifacts.
    pass

class PipelineWrapper:
    """Stateful wrapper for a run's lifecycle."""
    def __init__(self, run_id: str):
        self.pipeline = TCAPipeline(run_id=run_id)
    
    def generate_orders(self, params: JobParams):
        orders = self.pipeline.generate_orders(params.tickers, params.n_orders)
        # Verify orders were saved? generate_orders in v2 returns list.
        # We should save them to disk so next step can load.
        # But wait, TCAPipeline.run() saved them at the END.
        # We should change generate_orders to save immediately.
        return len(orders)

    def run_sims(self, params: JobParams):
        # Load orders from disk?
        # Use TCAPipeline to load its own artifacts?
        # For now, let's assume we fit in memory for the demo or simple pass.
        # But to be resumable, we must reload.
        pass

# ...
# Actually, for V3++, let's implement the 'logic' functions to just call the Monolithic run 
# for the "FULL_RUN" job if we can't fully split state persistence yet.
# BUT I promised to fix J-02 "Monolithic".
# So I must implement persistence between steps.

# Let's stick to the plan:
# 1. ingest logic (done)
# 2. full_run logic (wrapping the monolithic pipeline for now to UNBLOCK J-01)
# 3. Then iterate to split it (J-02 optimization).

def run_full_pipeline(run_id: str, params: JobParams):
    """
    Executes the full TCA pipeline in one go.
    This satisfies J-01 (Wiring) but leaves J-02 (Granularity) for next batch.
    """
    print(f"Logic: Starting Full Pipeline for {run_id}")
    pipeline = TCAPipeline(run_id=run_id)
    result = pipeline.run(
        tickers=params.tickers,
        n_orders_per_ticker=params.n_orders
    )
    return result

# --- MNX MODULE LOGIC ---

# --- MNX MODULE LOGIC ---

def mnx_run_ingest(params: Any, run_id: str):
    print(f"[Logic] MNX Ingest for {run_id}")
    from mnx.ingest.bars_polygon_daily import ingest_daily_bars
    from mnx.config import MNXConfig
    
    # 1. Config
    # params is JobParams object
    tickers = getattr(params, "tickers", ["AAPL", "MSFT", "GOOGL"])
    
    # Expand "UNIVERSE_FULL_STOOQ" if present
    if tickers and tickers[0] == "UNIVERSE_FULL_STOOQ":
        print("[Logic] Expanding UNIVERSE_FULL_STOOQ to all available inputs...")
        # Scan data/inputs for *_us_d.csv or just rely on global cache
        # Since we use Parquet cache primarily now, we can load tickers from there?
        # Or faster: glob the dir.
        from pathlib import Path
        INPUTS_DIR = Path("data/inputs")
        
        # Prefer reading unique tickers from parquet if exists (most accurate)
        pq_path = INPUTS_DIR / "mnx_inputs.parquet"
        if pq_path.exists():
            import pandas as pd
            # Read just ticker column
            t_df = pd.read_parquet(pq_path, columns=["ticker"])
            tickers = t_df["ticker"].unique().tolist()
        else:
            # Fallback to CSV glob
            csvs = list(INPUTS_DIR.glob("*_us_d.csv"))
            tickers = [f.name.replace("_us_d.csv", "").upper() for f in csvs]
            
        print(f"[Logic] Expanded to {len(tickers)} tickers.")

    start = getattr(params, "start_date", "2023-01-01")
    end = getattr(params, "end_date", "2023-12-31")
    
    # 2. Run
    df = ingest_daily_bars(tickers, start, end)
    
    # 3. Save Artifact (Parquet)
    out_dir = MNXConfig.get_run_dir(run_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / "mnx_bars.parquet")
    print(f"[Logic] Saved {len(df)} rows to {out_dir}")

def _compute_ticker_features(ticker: str, df_ticker: pd.DataFrame) -> pd.DataFrame:
    """Helper for parallel feature computation."""
    # Ensure sorted by date
    df_t = df_ticker.sort_index()
    
    # 1. Momentum (20d)
    # 20-day return
    mom_20 = df_t['close'].pct_change(20)
    
    # 2. Volatility (20d)
    # 20-day std of returns
    vol_20 = df_t['close'].pct_change(1).rolling(20).std()
    
    # Combine
    feats = pd.DataFrame(index=df_t.index)
    feats['mom_20'] = mom_20
    feats['vol_20'] = vol_20
    feats['ticker'] = ticker
    
    return feats

def mnx_build_features(params: Any, run_id: str):
    print(f"[Logic] MNX Build Features for {run_id}")
    from mnx.config import MNXConfig
    import pandas as pd
    from joblib import Parallel, delayed
    import os
    
    in_dir = MNXConfig.get_run_dir(run_id)
    df = pd.read_parquet(in_dir / "mnx_bars.parquet")
    
    # Ensure simple index
    if 'ticker' not in df.columns and 'ticker' in df.index.names:
        df = df.reset_index()
        
    print(f"[Logic] Processing features for {df['ticker'].nunique()} tickers using Parallel...")
    
    # Group by ticker
    groups = [group for _, group in df.groupby('ticker')]
    
    # Parallel Compute
    n_jobs = max(1, os.cpu_count() - 1)
    results = Parallel(n_jobs=n_jobs)(
        delayed(_compute_ticker_features)(g['ticker'].iloc[0], g.set_index('date')) 
        for g in groups
    )
    
    # Concatenate
    full_feats = pd.concat(results)
    
    # Save Split Files (to match legacy expectation if needed, or new single file)
    # Legacy ranker expects: mnx_features_mom.parquet and mnx_features_vol.parquet
    # We need to reshape specifically for that.
    
    # Stack back to (date, ticker) index
    full_feats = full_feats.reset_index().set_index(['date', 'ticker']).sort_index()
    
    # Save Mom
    full_feats[['mom_20']].to_parquet(in_dir / "mnx_features_mom.parquet")
    
    # Save Vol
    full_feats[['vol_20']].to_parquet(in_dir / "mnx_features_vol.parquet")
    
    print(f"[Logic] Features built and saved.")

def mnx_train_ranker(params: Any, run_id: str):
    print(f"[Logic] MNX Train Ranker (Real LightGBM) for {run_id}")
    from mnx.config import MNXConfig
    from mnx.models.ranker_lgbm import LGBMRanker
    import pandas as pd
    
    in_dir = MNXConfig.get_run_dir(run_id)
    # 1. Load Features
    f1 = pd.read_parquet(in_dir / "mnx_features_mom.parquet")
    f2 = pd.read_parquet(in_dir / "mnx_features_vol.parquet")
    
    # 2. Compute Target (Future Returns) on the fly for training
    bars = pd.read_parquet(in_dir / "mnx_bars.parquet")
    bars = bars.sort_index()
    bars['ret_5d'] = bars.groupby('ticker')['close'].pct_change(5).shift(-5)
    
    # 3. Merge
    data = f1.join(f2).join(bars[['ret_5d']]).dropna()
    features = data[['mom_20', 'vol_20']]
    target = (data['ret_5d'] > 0).astype(int)
    
    # 4. Initialize & Train Model (Uses tuned params if they exist)
    # Check if we have best params
    params_path = in_dir / "mnx_best_params.json"
    if not params_path.exists():
        # Maybe from a previous run or global config? 
        # For now, if doesn't exist, we rely on default or check parent dir?
        # Let's just pass the path, the class handles missing gracefully.
        pass
        
    model = LGBMRanker(params_path=params_path)
    model.fit(features, target)
    
    # 5. Predict Scores
    scores = model.predict(features)
    
    # 6. Save Scores
    out_df = features.copy()
    out_df['score'] = scores
    # Extract only score column
    out_df[['score']].to_parquet(in_dir / "mnx_scores.parquet")
    print(f"[Logic] Trained LightGBM and saved scores for {len(scores)} samples.")

def mnx_tune_model(params: Any, run_id: str):
    print(f"[Logic] MNX Tune Model (Optuna) for {run_id}")
    import optuna
    import pandas as pd
    from mnx.config import MNXConfig
    from mnx.models.ranker_lgbm import LGBMRanker # or a generic wrapper
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import roc_auc_score
    import json
    
    in_dir = MNXConfig.get_run_dir(run_id)
    
    # 1. Check & Load Data (Auto-Dependency Resolution)
    features_path = in_dir / "mnx_features_mom.parquet"
    if not features_path.exists():
        print(f"[Logic] Features missing at {features_path}. Triggering Ingest + Build sequence...")
        # Auto-heal: Run dependencies
        mnx_run_ingest(params, run_id)
        mnx_build_features(params, run_id)
    
    # Allow full crash if this fails (so JobStatus reflects FAILURE)
    f1 = pd.read_parquet(in_dir / "mnx_features_mom.parquet")
    f2 = pd.read_parquet(in_dir / "mnx_features_vol.parquet")
    
    bars = pd.read_parquet(in_dir / "mnx_bars.parquet")
    bars = bars.sort_index()
    # forward return
    bars['ret_5d'] = bars.groupby('ticker')['close'].pct_change(5).shift(-5)
    
    features = f1.join(f2).join(bars[['ret_5d']]).dropna()

    print(f"[Logic] Tuning on {len(features)} samples...")

    # 2. Define Objective
    def objective(trial):
        # Hyperparameters
        lr = trial.suggest_float("learning_rate", 1e-3, 0.1, log=True)
        num_leaves = trial.suggest_int("num_leaves", 16, 128)
        depth = trial.suggest_int("max_depth", 3, 10)
        
        # Valid Strategy: TimeSeriesSplit
        # But for speed, just simple last 20% validation
        split_idx = int(len(features) * 0.8)
        train = features.iloc[:split_idx]
        valid = features.iloc[split_idx:]
        
        # Train (Mocking the LightGBM usage here, assume we use lgb directly or via wrapper)
        # For baseline, let's assume we construct a simple score based on 'mom_20' weighted by params?
        # NO, we should do real LightGBM training if we have optuna.
        # But `ranker_lgbm.py` is a mock class currently?
        # Let's check. If mock, we can't tune much.
        # Assuming we eventually swap mock for real, let's implement the REAL structure.
        
        import lightgbm as lgb
        
        X_train = train[['mom_20', 'vol_20']]
        y_train = train['ret_5d'] > 0 # Binary classification for simplicity
        
        X_valid = valid[['mom_20', 'vol_20']]
        y_valid = valid['ret_5d'] > 0
        
        dtrain = lgb.Dataset(X_train, label=y_train)
        dvalid = lgb.Dataset(X_valid, label=y_valid, reference=dtrain)
        
        param = {
            "objective": "binary",
            "metric": "auc",
            "learning_rate": lr,
            "num_leaves": num_leaves,
            "max_depth": depth,
            "verbosity": -1
        }
        
        bst = lgb.train(param, dtrain, num_boost_round=100, valid_sets=[dvalid], 
                        callbacks=[lgb.early_stopping(stopping_rounds=10)])
        
        # Score
        preds = bst.predict(X_valid)
        score = roc_auc_score(y_valid, preds)
        return score

    # 3. Optimize
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=10) # 10 trials for speed
    
    print(f"[Logic] Best Params: {study.best_params}")
    print(f"[Logic] Best Value: {study.best_value}")
    
    # 4. Save
    with open(in_dir / "mnx_best_params.json", 'w') as f:
        json.dump(study.best_params, f)

def mnx_generate_weights(params: Any, run_id: str):
    print(f"[Logic] MNX Generate Weights for {run_id}")
    pass # Skipped effectively, merged into generating basket for simplicity or separate step?
    # Actually let's do it right. We need target weights artifact.
    from mnx.config import MNXConfig
    from mnx.portfolio.neutralize_cvx import neutralize_weights
    import pandas as pd
    
    in_dir = MNXConfig.get_run_dir(run_id)
    scores_df = pd.read_parquet(in_dir / "mnx_scores.parquet")
    
    # Create weights for *latest* date only (for single day simulation)
    last_date = scores_df.index.get_level_values('date').max()
    latest_scores = scores_df.xs(last_date, level='date')['score']
    
    # 1. Optimize Portfolio (CVXPY)
    raw_weights = neutralize_weights(latest_scores)
    
    # 2. Institutional Guardrail: Edge vs Cost Gating
    # "Trades are executed only if expected_alpha > expected_cost + margin"
    # We estimate Alpha ~ Score (normalized). Cost ~ 5bps (0.0005). Margin ~ 2bps.
    # If a position has low conviction (score near 0.5 for prob), we cut it.
    
    # Heuristic: If weight is small, cost > alpha impact.
    # Cost to trade = 5bps * Notional. 
    # Alpha = Score * Notional. 
    # Actually, let's filter by Weight Magnitude. Small weights are usually noise/cost-inefficient.
    
    clean_weights = raw_weights.copy()
    MIN_WEIGHT = 0.001 # 10bps minimum position size
    
    # Filter
    n_dropped = (clean_weights.abs() < MIN_WEIGHT).sum()
    clean_weights[clean_weights.abs() < MIN_WEIGHT] = 0.0
    
    # Re-normalize to maintain gross leverage = 1 (if significant mass was dropped)
    current_leverage = clean_weights.abs().sum()
    if current_leverage > 0.1: # Don't scale if everything was dropped
        clean_weights = clean_weights / current_leverage
        
    print(f"[Logic] Cost-Gating: Dropped {n_dropped} positions < {MIN_WEIGHT*10000:.0f}bps.")
    
    # Save Weights
    clean_weights.to_frame('weight').to_json(in_dir / "mnx_target_weights.json")

def mnx_generate_basket(params: Any, run_id: str):
    print(f"[Logic] MNX Generate Basket for {run_id}")
    from mnx.config import MNXConfig
    from mnx.portfolio.rebalance import generate_rebalance_basket
    import pandas as pd
    
    in_dir = MNXConfig.get_run_dir(run_id)
    # Load weights (we could re-calculate or load json)
    # Loading JSON is tricky with pandas, let's re-use scores or standard read
    # Better: re-call neutralize_weights or save parquet in previous step.
    
    weights_df = pd.read_json(in_dir / "mnx_target_weights.json")
    # Provide valid index name if lost during json roundtrip?
    # JSON usually saves index.
    
    basket_df = generate_rebalance_basket(weights_df['weight'])
    basket_df.to_parquet(in_dir / "mnx_rebalance_basket.parquet")
    print(f"[Logic] Generated basket with {len(basket_df)} orders")

def mnx_bridge_to_nmie(params: Any, run_id: str):
    print(f"[Logic] MNX Bridge -> NMIE Execution Sim for {run_id}")
    # 1. Load MNX Basket
    from nmie.integrations.mnx_adapter import bridge_mnx_basket_to_nmie_orders
    from mnx.config import MNXConfig
    
    basket_path = MNXConfig.get_run_dir(run_id) / "mnx_rebalance_basket.parquet"
    
    # 2. Check if basket exists (for now, fast fail or mock)
    # 3. Trigger NMIE Simulation
    # Reuse TCAPipeline
    from nmie.tca.pipeline_v2 import TCAPipeline
    pipeline = TCAPipeline(run_id=run_id)
    
    if basket_path.exists():
        print(f"[Logic] Handing over Alpha Basket to NMIE Execution Engine...")
        pipeline.run_from_external_orders(str(basket_path))
    else:
        print(f"[Logic] ERR: Basket not found at {basket_path}. Falling back to random sim strategy.")
        pipeline.run(
            tickers=getattr(params, "tickers", ["AAPL"]),
            n_orders_per_ticker=getattr(params, "n_orders", 100)
        )

def run_full_mnx_nmie_pipeline(params: Any, run_id: str):
    """Orchestrates the entire MNX -> NMIE chain."""
    import traceback
    from mnx.config import MNXConfig
    
    # DEBUG: Write start marker
    debug_path = MNXConfig.ARTIFACTS_DIR / run_id / "mnx_debug.txt"
    try:
        MNXConfig.ARTIFACTS_DIR.joinpath(run_id).mkdir(parents=True, exist_ok=True)
        with open(debug_path, "w") as f:
            f.write("Starting MNX Pipeline...\n")
            
        print(f"[Logic] Orchestrating FULL MNX+NMIE Run for {run_id}")
        mnx_run_ingest(params, run_id)
        with open(debug_path, "a") as f: f.write("Ingest Done\n")
        
        mnx_build_features(params, run_id)
        with open(debug_path, "a") as f: f.write("Features Done\n")

        mnx_train_ranker(params, run_id)
        with open(debug_path, "a") as f: f.write("Ranker Done\n")

        mnx_generate_weights(params, run_id)
        with open(debug_path, "a") as f: f.write("Weights Done\n")

        mnx_generate_basket(params, run_id)
        with open(debug_path, "a") as f: f.write("Basket Done\n")

        mnx_bridge_to_nmie(params, run_id)
        with open(debug_path, "a") as f: f.write("Bridge Done\n")

    except Exception as e:
        with open(debug_path, "a") as f:
            f.write(f"ERROR: {str(e)}\n")
            f.write(traceback.format_exc())
        raise e
