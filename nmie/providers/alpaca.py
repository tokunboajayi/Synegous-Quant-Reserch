"""
Alpaca Trading Client for ANEE
Paper Trading Mode Only
"""
import os
from typing import Optional, List, Dict
from dataclasses import dataclass
from enum import Enum
import alpaca_trade_api as tradeapi

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"

class TimeInForce(Enum):
    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"

@dataclass
class OrderResult:
    order_id: str
    symbol: str
    side: str
    qty: float
    filled_qty: float
    avg_fill_price: Optional[float]
    status: str
    submitted_at: str

class AlpacaClient:
    """
    Alpaca Paper Trading Client.
    Connects ANEE execution schedules to Alpaca's paper trading API.
    """
    
    def __init__(self, api_key: str = None, secret_key: str = None, paper: bool = True):
        """
        Initialize Alpaca client.
        
        Args:
            api_key: Alpaca API Key ID (or set APCA_API_KEY_ID env var)
            secret_key: Alpaca Secret Key (or set APCA_API_SECRET_KEY env var)
            paper: If True, use paper trading endpoint (REQUIRED for safety)
        """
        self.api_key = api_key or os.getenv("APCA_API_KEY_ID", "")
        self.secret_key = secret_key or os.getenv("APCA_API_SECRET_KEY", "")
        
        if not paper:
            raise ValueError("Live trading disabled. Only paper trading is supported.")
        
        # Paper trading endpoint
        self.base_url = "https://paper-api.alpaca.markets"
        
        if not self.api_key or not self.secret_key:
            print("WARNING: Alpaca API keys not configured. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY")
            self.api = None
        else:
            self.api = tradeapi.REST(
                self.api_key,
                self.secret_key,
                self.base_url,
                api_version='v2'
            )
            
    def is_connected(self) -> bool:
        """Check if API is connected and authenticated."""
        if not self.api:
            return False
        try:
            account = self.api.get_account()
            return account.status == 'ACTIVE'
        except Exception as e:
            print(f"Connection check failed: {e}")
            return False
            
    def get_account(self) -> Dict:
        """Get account info with real P&L metrics."""
        if not self.api:
            return {"error": "API not configured"}
        try:
            account = self.api.get_account()
            equity = float(account.equity)
            last_equity = float(account.last_equity)
            pnl_day = equity - last_equity
            
            return {
                "buying_power": float(account.buying_power),
                "cash": float(account.cash),
                "equity": equity,
                "pnl_day": round(pnl_day, 2),
                "pnl_day_pct": round((pnl_day / last_equity) * 100, 2) if last_equity > 0 else 0.0,
                "status": account.status
            }
        except Exception as e:
            return {"error": str(e)}
            
    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        order_type: OrderType = OrderType.MARKET,
        time_in_force: TimeInForce = TimeInForce.DAY,
        limit_price: float = None
    ) -> OrderResult:
        """
        Submit a single order to Alpaca.
        """
        if not self.api:
            raise RuntimeError("Alpaca API not configured")
            
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=int(qty),
                side=side.value,
                type=order_type.value,
                time_in_force=time_in_force.value,
                limit_price=limit_price if order_type == OrderType.LIMIT else None
            )
            
            return OrderResult(
                order_id=order.id,
                symbol=order.symbol,
                side=order.side,
                qty=float(order.qty),
                filled_qty=float(order.filled_qty or 0),
                avg_fill_price=float(order.filled_avg_price) if order.filled_avg_price else None,
                status=order.status,
                submitted_at=str(order.submitted_at)
            )
        except Exception as e:
            raise RuntimeError(f"Order submission failed: {e}")
            
    def get_order(self, order_id: str) -> OrderResult:
        """Get order status by ID."""
        if not self.api:
            raise RuntimeError("Alpaca API not configured")
            
        order = self.api.get_order(order_id)
        return OrderResult(
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            qty=float(order.qty),
            filled_qty=float(order.filled_qty or 0),
            avg_fill_price=float(order.filled_avg_price) if order.filled_avg_price else None,
            status=order.status,
            submitted_at=str(order.submitted_at)
        )
        
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        if not self.api:
            return False
        try:
            self.api.cancel_order(order_id)
            return True
        except:
            return False
            
    def cancel_all_orders(self) -> int:
        """Cancel all open orders. Returns count cancelled."""
        if not self.api:
            return 0
        try:
            cancelled = self.api.cancel_all_orders()
            return len(cancelled)
        except:
            return 0
            
    def get_position(self, symbol: str) -> Dict:
        """Get current position for a symbol."""
        if not self.api:
            return {}
        try:
            pos = self.api.get_position(symbol)
            return {
                "symbol": pos.symbol,
                "qty": float(pos.qty),
                "avg_entry_price": float(pos.avg_entry_price),
                "market_value": float(pos.market_value),
                "unrealized_pl": float(pos.unrealized_pl)
            }
        except:
            return {}
