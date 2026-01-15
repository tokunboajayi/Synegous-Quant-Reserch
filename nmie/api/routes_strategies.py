"""
Strategy API Routes
CRUD operations for user-defined trading strategies.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from nmie.research.strategies import Strategy, Signal, Rule, strategy_store

router = APIRouter(prefix="/strategies", tags=["Strategy Builder"])


# ============================================================
# Request/Response Models
# ============================================================

class StrategyCreateRequest(BaseModel):
    """Request body for creating a new strategy."""
    name: str
    description: str = ""
    type: str = "custom"
    parameters: dict = {}
    signals: List[Signal] = []
    entry_rules: List[Rule] = []
    exit_rules: List[Rule] = []
    code: Optional[str] = None


class StrategyUpdateRequest(BaseModel):
    """Request body for updating a strategy."""
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    parameters: Optional[dict] = None
    signals: Optional[List[Signal]] = None
    entry_rules: Optional[List[Rule]] = None
    exit_rules: Optional[List[Rule]] = None
    code: Optional[str] = None


class DuplicateRequest(BaseModel):
    """Request to duplicate a strategy."""
    new_name: str


class ValidateResponse(BaseModel):
    """Response from strategy validation."""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []


# ============================================================
# API Endpoints
# ============================================================

@router.get("", response_model=List[Strategy])
def list_strategies(include_templates: bool = True):
    """List all saved strategies."""
    return strategy_store.list_all(include_templates=include_templates)


@router.get("/templates", response_model=List[Strategy])
def list_templates():
    """List pre-built strategy templates."""
    return strategy_store.list_templates()


@router.get("/{strategy_id}", response_model=Strategy)
def get_strategy(strategy_id: str):
    """Get a specific strategy by ID."""
    strategy = strategy_store.get(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    return strategy


@router.post("", response_model=Strategy)
def create_strategy(request: StrategyCreateRequest):
    """Create a new strategy."""
    strategy = Strategy(
        name=request.name,
        description=request.description,
        type=request.type,
        parameters=request.parameters,
        signals=request.signals,
        entry_rules=request.entry_rules,
        exit_rules=request.exit_rules,
        code=request.code
    )
    return strategy_store.save(strategy)


@router.put("/{strategy_id}", response_model=Strategy)
def update_strategy(strategy_id: str, request: StrategyUpdateRequest):
    """Update an existing strategy."""
    strategy = strategy_store.get(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    if strategy.is_template:
        raise HTTPException(status_code=400, detail="Cannot modify template strategies. Duplicate first.")
    
    # Update fields if provided
    if request.name is not None:
        strategy.name = request.name
    if request.description is not None:
        strategy.description = request.description
    if request.type is not None:
        strategy.type = request.type
    if request.parameters is not None:
        strategy.parameters = request.parameters
    if request.signals is not None:
        strategy.signals = request.signals
    if request.entry_rules is not None:
        strategy.entry_rules = request.entry_rules
    if request.exit_rules is not None:
        strategy.exit_rules = request.exit_rules
    if request.code is not None:
        strategy.code = request.code
    
    return strategy_store.save(strategy)


@router.delete("/{strategy_id}")
def delete_strategy(strategy_id: str):
    """Delete a strategy (templates cannot be deleted)."""
    strategy = strategy_store.get(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    if strategy.is_template:
        raise HTTPException(status_code=400, detail="Cannot delete template strategies")
    
    success = strategy_store.delete(strategy_id)
    return {"deleted": success, "strategy_id": strategy_id}


@router.post("/{strategy_id}/duplicate", response_model=Strategy)
def duplicate_strategy(strategy_id: str, request: DuplicateRequest):
    """Create a copy of an existing strategy or template."""
    new_strategy = strategy_store.duplicate(strategy_id, request.new_name)
    if not new_strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    return new_strategy


@router.post("/{strategy_id}/validate", response_model=ValidateResponse)
def validate_strategy(strategy_id: str):
    """Validate strategy logic and parameters."""
    strategy = strategy_store.get(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    errors = []
    warnings = []
    
    # Validate signals
    if not strategy.signals and not strategy.code:
        errors.append("Strategy must have at least one signal or custom code")
    
    # Validate entry rules
    if not strategy.entry_rules and not strategy.code:
        warnings.append("No entry rules defined - strategy may not generate trades")
    
    # Validate exit rules
    if not strategy.exit_rules and not strategy.code:
        warnings.append("No exit rules defined - positions may not be closed automatically")
    
    # Validate parameters
    if strategy.parameters.get("max_position_size", 0) > 0.5:
        warnings.append("Max position size > 50% is high risk")
    
    if strategy.parameters.get("stop_loss", 0) == 0:
        warnings.append("No stop loss defined - unlimited downside risk")
    
    # Validate custom code (basic check)
    if strategy.code:
        if "def execute" not in strategy.code and "def generate_signals" not in strategy.code:
            warnings.append("Custom code should define 'execute' or 'generate_signals' function")
    
    return ValidateResponse(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


@router.get("/{strategy_id}/summary")
def get_strategy_summary(strategy_id: str):
    """Get a human-readable summary of the strategy."""
    strategy = strategy_store.get(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    signal_names = [s.name for s in strategy.signals]
    entry_conditions = [r.condition for r in strategy.entry_rules]
    exit_conditions = [r.condition for r in strategy.exit_rules]
    
    return {
        "name": strategy.name,
        "type": strategy.type,
        "description": strategy.description,
        "signals": signal_names,
        "entry_conditions": entry_conditions,
        "exit_conditions": exit_conditions,
        "key_parameters": {
            k: v for k, v in strategy.parameters.items()
            if k in ["lookback_window", "max_position_size", "stop_loss", "take_profit"]
        },
        "has_custom_code": strategy.code is not None,
        "last_sharpe": strategy.last_sharpe,
        "last_return": strategy.last_return
    }
