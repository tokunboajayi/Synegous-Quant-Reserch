from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd

from nmie.counterfactual.evaluate_anee import compare_strategies, run_counterfactual_suite
from nmie.store.feature_store import FeatureStore
from nmie.optimizer.anee_engine import ANEEEngine

router = APIRouter(prefix="/execution", tags=["Execution"])

class RunRequest(BaseModel):
    ticker: str
    size_shares: float
    start_time: str  # ISO format
    end_time: str
    date: str  # YYYY-MM-DD for data lookup

class RunResponse(BaseModel):
    order_id: str
    strategy: str
    implementation_shortfall_bps: float
    avg_exec_price: float
    benchmark_price: float
    is_feasible: bool

@router.post("/run", response_model=RunResponse)
def run_anee(req: RunRequest):
    """
    Run ANEE simulation for a single order.
    """
    store = FeatureStore()
    df = store.load_bars(req.ticker, req.date)
    
    if df.is_empty():
        return RunResponse(
            order_id="error",
            strategy="ANEE",
            implementation_shortfall_bps=0,
            avg_exec_price=0,
            benchmark_price=0,
            is_feasible=False
        )
    
    parent_order = {
        "order_id": f"{req.ticker}_{req.start_time}",
        "ticker": req.ticker,
        "size_shares": req.size_shares,
        "start_time": pd.to_datetime(req.start_time),
        "end_time": pd.to_datetime(req.end_time)
    }
    
    engine = ANEEEngine()
    result = engine.run_simulation(parent_order, df)
    
    if result is None:
        return RunResponse(
            order_id="error",
            strategy="ANEE",
            implementation_shortfall_bps=0,
            avg_exec_price=0,
            benchmark_price=0,
            is_feasible=False
        )
    
    return RunResponse(
        order_id=result.parent_id,
        strategy=result.strategy,
        implementation_shortfall_bps=result.implementation_shortfall_bps,
        avg_exec_price=result.avg_exec_price,
        benchmark_price=result.benchmark_price,
        is_feasible=True
    )

class CompareRequest(BaseModel):
    ticker: str
    size_shares: float
    start_time: str
    end_time: str
    date: str

class CompareResponse(BaseModel):
    is_anee: float
    is_twap: float
    is_vwap: float
    is_pov: float
    anee_vs_twap: float

@router.post("/compare", response_model=CompareResponse)
def compare_execution(req: CompareRequest):
    """
    Compare ANEE vs baselines for a single order.
    """
    store = FeatureStore()
    df = store.load_bars(req.ticker, req.date)
    
    if df.is_empty():
        return CompareResponse(is_anee=0, is_twap=0, is_vwap=0, is_pov=0, anee_vs_twap=0)
    
    parent_order = {
        "order_id": f"{req.ticker}_{req.start_time}",
        "ticker": req.ticker,
        "size_shares": req.size_shares,
        "start_time": pd.to_datetime(req.start_time),
        "end_time": pd.to_datetime(req.end_time)
    }
    
    result = compare_strategies(parent_order, df)
    
    return CompareResponse(
        is_anee=result.is_anee,
        is_twap=result.is_twap,
        is_vwap=result.is_vwap,
        is_pov=result.is_pov,
        anee_vs_twap=result.anee_vs_twap_bps
    )
