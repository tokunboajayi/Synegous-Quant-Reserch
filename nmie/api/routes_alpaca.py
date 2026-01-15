from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from nmie.providers.alpaca import AlpacaClient
from nmie.optimizer.live_executor import LiveExecutor
from nmie.optimizer.types import Schedule

router = APIRouter(prefix="/alpaca", tags=["Alpaca Paper Trading"])

# Global executor instance
executor = LiveExecutor()

class ScheduleExecuteRequest(BaseModel):
    symbol: str
    quantities: list  # List of quantities per interval
    side: str = "BUY"
    interval_seconds: int = 60
    dry_run: bool = True

class AccountResponse(BaseModel):
    connected: bool
    buying_power: Optional[float] = None
    cash: Optional[float] = None
    equity: Optional[float] = None
    pnl_day: Optional[float] = None
    pnl_day_pct: Optional[float] = None
    status: Optional[str] = None

@router.get("/status", response_model=AccountResponse)
def get_status():
    """Check Alpaca connection and account status."""
    connected = executor.is_ready()
    
    if not connected:
        return AccountResponse(connected=False)
        
    account = executor.get_account_status()
    
    if "error" in account:
        return AccountResponse(connected=False)
        
    return AccountResponse(
        connected=True,
        buying_power=account.get("buying_power"),
        cash=account.get("cash"),
        equity=account.get("equity"),
        pnl_day=account.get("pnl_day"),
        pnl_day_pct=account.get("pnl_day_pct"),
        status=account.get("status")
    )

@router.post("/execute")
def execute_schedule(req: ScheduleExecuteRequest):
    """
    Execute a schedule via Alpaca paper trading.
    
    Set dry_run=True to test without submitting orders.
    """
    if not executor.is_ready() and not req.dry_run:
        return {"error": "Alpaca not connected. Check API keys."}
    
    import numpy as np
    
    # Create a simple list-based schedule to avoid numpy issues
    quantities_list = [float(q) for q in req.quantities]
    
    # Execute directly without Schedule dataclass
    parent_id = f"{req.symbol}_{len(quantities_list)}"
    total_qty = sum(quantities_list)
    executed_qty = 0.0
    errors = []
    
    print(f"\n[ExecuteRoute] Dry run={req.dry_run}, Symbol={req.symbol}, Qty={quantities_list}")
    
    if req.dry_run:
        # Simulate execution
        executed_qty = total_qty
        print(f"[ExecuteRoute] Simulated execution: {executed_qty} shares")
    else:
        # Real execution via Alpaca
        from nmie.providers.alpaca import OrderSide, OrderType, TimeInForce
        order_side = OrderSide.BUY if req.side == "BUY" else OrderSide.SELL
        
        for i, qty in enumerate(quantities_list):
            if qty < 1:
                continue
            try:
                result = executor.client.submit_order(
                    symbol=req.symbol,
                    qty=int(qty),
                    side=order_side,
                    order_type=OrderType.MARKET,
                    time_in_force=TimeInForce.DAY
                )
                print(f"  Order {i}: {result.order_id} - {result.status}")
                executed_qty += qty
            except Exception as e:
                errors.append(str(e))
                print(f"  Order {i} failed: {e}")
    
    return {
        "parent_id": parent_id,
        "symbol": req.symbol,
        "target_qty": total_qty,
        "executed_qty": executed_qty,
        "avg_fill_price": 0.0,
        "is_complete": executed_qty >= total_qty * 0.99,
        "errors": errors,
        "dry_run": req.dry_run
    }

@router.post("/cancel/{parent_id}")
def cancel_execution(parent_id: str):
    """Cancel an active execution."""
    success = executor.cancel_execution(parent_id)
    return {"cancelled": success}

@router.post("/emergency-stop")
def emergency_stop():
    """EMERGENCY: Cancel all orders and stop all executions."""
    cancelled = executor.emergency_stop()
    return {"cancelled_orders": cancelled, "status": "stopped"}
