"""
Live Executor - Connects ANEE schedules to Alpaca Paper Trading
"""
import time
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import threading

from nmie.providers.alpaca import AlpacaClient, OrderSide, OrderType, TimeInForce, OrderResult
from nmie.optimizer.types import Schedule

@dataclass
class ExecutionState:
    """Tracks live execution state."""
    parent_id: str
    symbol: str
    target_qty: float
    executed_qty: float = 0.0
    pending_orders: List[str] = field(default_factory=list)
    filled_orders: List[OrderResult] = field(default_factory=list)
    avg_fill_price: float = 0.0
    is_complete: bool = False
    is_cancelled: bool = False
    errors: List[str] = field(default_factory=list)

class LiveExecutor:
    """
    Executes ANEE schedules via Alpaca Paper Trading.
    
    This is a PAPER TRADING executor for testing purposes.
    """
    
    def __init__(self):
        self.client = AlpacaClient(paper=True)
        self.active_executions: Dict[str, ExecutionState] = {}
        self._stop_flag = False
        
    def is_ready(self) -> bool:
        """Check if executor is ready to trade."""
        return self.client.is_connected()
        
    def get_account_status(self) -> Dict:
        """Get current account info."""
        return self.client.get_account()
        
    def execute_schedule(
        self,
        schedule: Schedule,
        symbol: str,
        side: str = "BUY",
        interval_seconds: int = 60,
        dry_run: bool = True
    ) -> ExecutionState:
        """
        Execute a schedule via Alpaca.
        
        Args:
            schedule: ANEE schedule with quantities per interval
            symbol: Ticker symbol
            side: BUY or SELL
            interval_seconds: Seconds between order submissions
            dry_run: If True, log but don't submit orders
            
        Returns:
            ExecutionState with results
        """
        parent_id = f"{symbol}_{datetime.now().strftime('%H%M%S')}"
        total_qty = sum(schedule.quantities)
        
        state = ExecutionState(
            parent_id=parent_id,
            symbol=symbol,
            target_qty=total_qty
        )
        self.active_executions[parent_id] = state
        
        order_side = OrderSide.BUY if side == "BUY" else OrderSide.SELL
        
        print(f"\n[LiveExecutor] Starting execution: {parent_id}")
        print(f"  Symbol: {symbol}")
        print(f"  Side: {side}")
        print(f"  Total Qty: {total_qty}")
        print(f"  Intervals: {len(schedule.quantities)}")
        print(f"  Dry Run: {dry_run}")
        
        for i, qty in enumerate(schedule.quantities):
            if self._stop_flag or state.is_cancelled:
                print(f"  [!] Execution stopped at interval {i}")
                break
                
            if qty < 1:
                continue
                
            print(f"\n  [{i+1}/{len(schedule.quantities)}] Target: {int(qty)} shares")
            
            if dry_run:
                # Simulate fill
                print(f"    [DRY RUN] Would submit {int(qty)} shares")
                state.executed_qty += qty
            else:
                try:
                    result = self.client.submit_order(
                        symbol=symbol,
                        qty=int(qty),
                        side=order_side,
                        order_type=OrderType.MARKET,
                        time_in_force=TimeInForce.DAY
                    )
                    
                    print(f"    Order ID: {result.order_id}")
                    print(f"    Status: {result.status}")
                    
                    state.pending_orders.append(result.order_id)
                    
                    # Wait for fill (with timeout)
                    fill_wait = 0
                    while fill_wait < 10:
                        updated = self.client.get_order(result.order_id)
                        if updated.status in ['filled', 'partially_filled']:
                            state.executed_qty += updated.filled_qty
                            state.filled_orders.append(updated)
                            print(f"    Filled: {updated.filled_qty} @ ${updated.avg_fill_price}")
                            break
                        time.sleep(1)
                        fill_wait += 1
                        
                except Exception as e:
                    state.errors.append(str(e))
                    print(f"    [ERROR] {e}")
                    
            # Wait for next interval
            if i < len(schedule.quantities) - 1:
                time.sleep(interval_seconds)
                
        # Calculate avg price
        if state.filled_orders:
            total_value = sum(o.filled_qty * (o.avg_fill_price or 0) for o in state.filled_orders)
            if state.executed_qty > 0:
                state.avg_fill_price = total_value / state.executed_qty
                
        state.is_complete = state.executed_qty >= state.target_qty * 0.99
        
        print(f"\n[LiveExecutor] Execution complete")
        print(f"  Executed: {state.executed_qty}/{state.target_qty}")
        print(f"  Avg Price: ${state.avg_fill_price:.2f}" if state.avg_fill_price else "  Avg Price: N/A")
        print(f"  Errors: {len(state.errors)}")
        
        return state
        
    def cancel_execution(self, parent_id: str) -> bool:
        """Cancel an active execution."""
        if parent_id not in self.active_executions:
            return False
            
        state = self.active_executions[parent_id]
        state.is_cancelled = True
        
        # Cancel pending orders
        for order_id in state.pending_orders:
            self.client.cancel_order(order_id)
            
        return True
        
    def emergency_stop(self):
        """Stop all executions and cancel all orders."""
        self._stop_flag = True
        cancelled = self.client.cancel_all_orders()
        print(f"[EMERGENCY STOP] Cancelled {cancelled} orders")
        return cancelled
