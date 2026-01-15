import numpy as np
import polars as pl
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class CorrelationGraph:
    """
    Dynamic correlation graph for cross-impact modeling.
    """
    tickers: List[str]
    adjacency: np.ndarray  # (n_nodes, n_nodes) correlation matrix
    edge_weights: np.ndarray  # Flattened edge weights
    
    @property
    def n_nodes(self) -> int:
        return len(self.tickers)
    
    def get_neighbors(self, ticker: str, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """Returns neighbors with correlation above threshold."""
        if ticker not in self.tickers:
            return []
        idx = self.tickers.index(ticker)
        neighbors = []
        for j, corr in enumerate(self.adjacency[idx]):
            if j != idx and abs(corr) >= threshold:
                neighbors.append((self.tickers[j], corr))
        return sorted(neighbors, key=lambda x: -abs(x[1]))

def build_correlation_graph(
    bars_dict: Dict[str, pl.DataFrame],
    lookback_days: int = 20
) -> CorrelationGraph:
    """
    Builds a correlation graph from multi-ticker bar data.
    
    Args:
        bars_dict: {ticker: DataFrame} with 1-minute bars
        lookback_days: Days of history for correlation calculation
        
    Returns:
        CorrelationGraph with adjacency matrix
    """
    tickers = sorted(bars_dict.keys())
    n = len(tickers)
    
    if n == 0:
        return CorrelationGraph(tickers=[], adjacency=np.array([]), edge_weights=np.array([]))
    
    # Compute daily returns for each ticker
    returns_dict = {}
    
    for ticker, bars in bars_dict.items():
        if bars.height == 0:
            continue
            
        # Resample to daily
        daily = bars.group_by(pl.col("timestamp").dt.date()).agg([
            pl.col("close").last().alias("close")
        ]).sort("timestamp")
        
        if daily.height < 2:
            continue
            
        # Compute returns
        closes = daily["close"].to_numpy()
        rets = np.diff(closes) / (closes[:-1] + 1e-9)
        returns_dict[ticker] = rets
    
    # Build correlation matrix
    valid_tickers = [t for t in tickers if t in returns_dict]
    n = len(valid_tickers)
    
    if n < 2:
        return CorrelationGraph(
            tickers=valid_tickers,
            adjacency=np.eye(max(n, 1)),
            edge_weights=np.array([])
        )
    
    # Align return series (truncate to min length)
    min_len = min(len(returns_dict[t]) for t in valid_tickers)
    aligned_rets = np.array([returns_dict[t][-min_len:] for t in valid_tickers])
    
    # Correlation matrix
    corr_matrix = np.corrcoef(aligned_rets)
    
    # Handle NaN
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    # Edge weights (upper triangle, flattened)
    edge_weights = []
    for i in range(n):
        for j in range(i+1, n):
            edge_weights.append(corr_matrix[i, j])
    
    return CorrelationGraph(
        tickers=valid_tickers,
        adjacency=corr_matrix,
        edge_weights=np.array(edge_weights)
    )

def compute_cross_impact_multiplier(
    graph: CorrelationGraph,
    target_ticker: str,
    active_orders: Dict[str, float] = None
) -> float:
    """
    Computes cross-impact multiplier for a target ticker.
    
    If correlated assets are also being traded, impact increases.
    
    Args:
        graph: Correlation graph
        target_ticker: Ticker to compute multiplier for
        active_orders: {ticker: order_size_fraction} of concurrent orders
        
    Returns:
        Multiplier in [1.0, 2.0]
    """
    if target_ticker not in graph.tickers:
        return 1.0
        
    if active_orders is None or len(active_orders) == 0:
        return 1.0
        
    idx = graph.tickers.index(target_ticker)
    
    # Sum correlation-weighted impact from concurrent orders
    cross_impact = 0.0
    
    for other_ticker, order_frac in active_orders.items():
        if other_ticker == target_ticker:
            continue
        if other_ticker not in graph.tickers:
            continue
            
        j = graph.tickers.index(other_ticker)
        corr = graph.adjacency[idx, j]
        
        # Impact scales with correlation and order size
        cross_impact += abs(corr) * order_frac
        
    # Multiplier = 1 + cross_impact (capped)
    multiplier = 1.0 + min(cross_impact, 1.0)
    
    return multiplier
