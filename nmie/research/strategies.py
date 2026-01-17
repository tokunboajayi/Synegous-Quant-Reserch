"""
Strategy Models & Storage
Data models for user-defined trading strategies.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Literal
from datetime import datetime, timezone
import uuid
import sqlite3
import json
from pathlib import Path

# Database path
STRATEGIES_DB = Path("/app/data/strategies.db") if Path("/app").exists() else Path("data/strategies.db")


# ============================================================
# Data Models
# ============================================================

class Signal(BaseModel):
    """A trading signal component."""
    signal_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    type: Literal["momentum", "mean_reversion", "volatility", "volume", "factor", "custom"]
    parameters: Dict[str, Any] = {}
    weight: float = 1.0


class Rule(BaseModel):
    """Entry or exit rule."""
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    condition: str  # e.g., "signal > 0.5", "position_age > 5"
    action: Literal["buy", "sell", "hold", "close", "short_spread", "long_spread"]
    size: Optional[float] = None  # Position size as fraction of portfolio


class Strategy(BaseModel):
    """Complete trading strategy definition."""
    strategy_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    type: Literal["momentum", "mean_reversion", "factor", "pairs", "statistical_arb", "custom"] = "custom"
    status: Literal["idea", "refine", "backtest", "deployed"] = "idea"
    
    # Strategy components
    signals: List[Signal] = []
    entry_rules: List[Rule] = []
    exit_rules: List[Rule] = []
    
    # Parameters
    parameters: Dict[str, Any] = {
        "lookback_window": 20,
        "rebalance_frequency": "daily",
        "max_position_size": 0.05,
        "stop_loss": 0.02,
        "take_profit": 0.05,
    }
    
    # For advanced users - custom Python-like code
    code: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_template: bool = False
    author: str = "user"
    version: str = "1.0"
    
    # Performance metrics (populated after backtest)
    last_backtest_id: Optional[str] = None
    last_sharpe: Optional[float] = None
    last_return: Optional[float] = None


# ============================================================
# SQLite Strategy Storage
# ============================================================

class StrategyStore:
    """Persistent storage for strategies using SQLite."""
    
    def __init__(self, db_path: Path = STRATEGIES_DB):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS strategies (
                    strategy_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT,
                    updated_at TEXT,
                    is_template INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_strategies_type ON strategies(type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_strategies_template ON strategies(is_template)
            """)
            conn.commit()
            
            # Insert library templates if empty
            count = conn.execute("SELECT COUNT(*) FROM strategies WHERE is_template=1").fetchone()[0]
            if count == 0:
                self._insert_library_templates(conn)
    
    def _insert_library_templates(self, conn):
        """Insert strategy library templates."""
        from nmie.research.strategy_library import STRATEGY_LIBRARY
        
        for strategy in STRATEGY_LIBRARY:
            strategy.is_template = True
            conn.execute(
                "INSERT OR IGNORE INTO strategies (strategy_id, name, type, data, created_at, updated_at, is_template) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (strategy.strategy_id, strategy.name, strategy.type, strategy.model_dump_json(), strategy.created_at.isoformat(), strategy.updated_at.isoformat(), 1)
            )
        conn.commit()
        print(f"[StrategyStore] Loaded {len(STRATEGY_LIBRARY)} strategy templates")
    
    def save(self, strategy: Strategy) -> Strategy:
        """Save or update a strategy."""
        strategy.updated_at = datetime.now(timezone.utc)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO strategies (strategy_id, name, type, data, created_at, updated_at, is_template)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                strategy.strategy_id,
                strategy.name,
                strategy.type,
                strategy.model_dump_json(),
                strategy.created_at.isoformat(),
                strategy.updated_at.isoformat(),
                1 if strategy.is_template else 0
            ))
            conn.commit()
        return strategy
    
    def get(self, strategy_id: str) -> Optional[Strategy]:
        """Get a strategy by ID."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT data FROM strategies WHERE strategy_id = ?",
                (strategy_id,)
            ).fetchone()
            if row:
                return Strategy.model_validate_json(row[0])
        return None
    
    def list_all(self, include_templates: bool = True) -> List[Strategy]:
        """List all strategies."""
        with sqlite3.connect(self.db_path) as conn:
            if include_templates:
                rows = conn.execute("SELECT data FROM strategies ORDER BY updated_at DESC").fetchall()
            else:
                rows = conn.execute("SELECT data FROM strategies WHERE is_template=0 ORDER BY updated_at DESC").fetchall()
            return [Strategy.model_validate_json(row[0]) for row in rows]
    
    def list_templates(self) -> List[Strategy]:
        """List only template strategies."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT data FROM strategies WHERE is_template=1 ORDER BY name").fetchall()
            return [Strategy.model_validate_json(row[0]) for row in rows]
    
    def delete(self, strategy_id: str) -> bool:
        """Delete a strategy."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM strategies WHERE strategy_id = ? AND is_template = 0", (strategy_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def duplicate(self, strategy_id: str, new_name: str) -> Optional[Strategy]:
        """Create a copy of an existing strategy."""
        original = self.get(strategy_id)
        if original:
            new_strategy = original.model_copy(deep=True)
            new_strategy.strategy_id = str(uuid.uuid4())
            new_strategy.name = new_name
            new_strategy.is_template = False
            new_strategy.created_at = datetime.now(timezone.utc)
            new_strategy.updated_at = datetime.now(timezone.utc)
            return self.save(new_strategy)
        return None


# Global store instance
strategy_store = StrategyStore()
