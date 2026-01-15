"""
Walk-Forward Split Generator
Strict time-based splits with no leakage.
"""
from datetime import date, timedelta
from typing import List, Tuple
import polars as pl

from nmie.research.types import WalkForwardFold

def generate_walkforward_splits(
    start_date: date,
    end_date: date,
    train_days: int = 90,
    test_days: int = 20,
    step_days: int = None
) -> List[WalkForwardFold]:
    """
    Generate walk-forward folds.
    
    Args:
        start_date: First available data date
        end_date: Last available data date
        train_days: Training window size
        test_days: Test window size
        step_days: Step forward amount (defaults to test_days)
        
    Returns:
        List of WalkForwardFold objects
    """
    if step_days is None:
        step_days = test_days
        
    folds = []
    fold_id = 0
    
    current_train_start = start_date
    
    while True:
        train_end = current_train_start + timedelta(days=train_days - 1)
        test_start = train_end + timedelta(days=1)
        test_end = test_start + timedelta(days=test_days - 1)
        
        # Check if we have enough data
        if test_end > end_date:
            break
            
        folds.append(WalkForwardFold(
            fold_id=fold_id,
            train_start=current_train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end
        ))
        
        fold_id += 1
        current_train_start += timedelta(days=step_days)
        
    return folds

def get_available_dates(bars_dir: str, ticker: str = "SPY") -> Tuple[date, date]:
    """
    Get date range from available data.
    """
    from pathlib import Path
    
    path = Path(bars_dir)
    files = list(path.glob(f"{ticker}_*.parquet"))
    
    if not files:
        return None, None
        
    dates = []
    for f in files:
        parts = f.stem.split("_")
        if len(parts) >= 2:
            try:
                d = date.fromisoformat(parts[-1])
                dates.append(d)
            except:
                pass
                
    if not dates:
        return None, None
        
    return min(dates), max(dates)

def validate_no_leakage(folds: List[WalkForwardFold]) -> bool:
    """
    Validate that folds have no temporal leakage.
    Train must end before test starts.
    """
    for fold in folds:
        if fold.train_end >= fold.test_start:
            return False
        if fold.train_start > fold.train_end:
            return False
        if fold.test_start > fold.test_end:
            return False
    return True

def validate_no_overlap(folds: List[WalkForwardFold]) -> bool:
    """
    Validate that test periods don't overlap with prior train periods.
    """
    for i, fold in enumerate(folds):
        for j in range(i):
            prior = folds[j]
            # Test should not overlap with prior train
            if fold.test_start <= prior.train_end:
                return False
    return True

def get_fold_data_filter(
    fold: WalkForwardFold,
    is_train: bool = True
) -> Tuple[date, date]:
    """
    Get date filter for a fold.
    """
    if is_train:
        return fold.train_start, fold.train_end
    else:
        return fold.test_start, fold.test_end

def print_folds_summary(folds: List[WalkForwardFold]):
    """Print fold summary."""
    print(f"\nWalk-Forward Splits: {len(folds)} folds")
    print("-" * 60)
    for f in folds:
        print(f"  Fold {f.fold_id}: Train {f.train_start} to {f.train_end} | "
              f"Test {f.test_start} to {f.test_end}")
    print("-" * 60)
