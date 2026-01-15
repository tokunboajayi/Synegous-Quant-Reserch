"""
Leaderboard
Compare policies and models across runs.
"""
import numpy as np
from typing import List, Dict
from dataclasses import dataclass

from nmie.research.types import LeaderboardEntry

def compute_leaderboard(
    results: Dict[str, List[float]],
    twap_key: str = "TWAP"
) -> List[LeaderboardEntry]:
    """
    Create leaderboard from policy results.
    
    results: {policy_name: [is_values]}
    """
    entries = []
    
    twap_values = np.array(results.get(twap_key, []))
    
    for policy, is_values in results.items():
        arr = np.array(is_values)
        
        if len(arr) == 0:
            continue
            
        # Win rate vs TWAP
        if len(twap_values) == len(arr):
            wins = np.sum(arr < twap_values)
            win_rate = wins / len(arr)
        else:
            win_rate = 0.0
            
        entries.append(LeaderboardEntry(
            policy=policy,
            mean_is=float(np.mean(arr)),
            median_is=float(np.median(arr)),
            p95_is=float(np.percentile(arr, 95)),
            win_rate_vs_twap=float(win_rate),
            rank=0  # Will be set below
        ))
    
    # Rank by mean IS (lower is better)
    entries.sort(key=lambda x: x.mean_is)
    for i, entry in enumerate(entries):
        entry.rank = i + 1
        
    return entries

def leaderboard_to_dict(entries: List[LeaderboardEntry]) -> List[Dict]:
    """Convert leaderboard to dict format."""
    return [
        {
            "rank": e.rank,
            "policy": e.policy,
            "mean_is": e.mean_is,
            "median_is": e.median_is,
            "p95_is": e.p95_is,
            "win_rate_vs_twap": e.win_rate_vs_twap
        }
        for e in entries
    ]

def compare_model_versions(
    version_results: Dict[str, Dict[str, List[float]]]
) -> Dict[str, List[LeaderboardEntry]]:
    """
    Compare across model versions.
    
    version_results: {version_id: {policy: [is_values]}}
    """
    version_leaderboards = {}
    
    for version_id, results in version_results.items():
        version_leaderboards[version_id] = compute_leaderboard(results)
        
    return version_leaderboards

def get_best_policy(entries: List[LeaderboardEntry]) -> str:
    """Get name of best policy."""
    if not entries:
        return "unknown"
    return entries[0].policy

def format_leaderboard_table(entries: List[LeaderboardEntry]) -> str:
    """Format leaderboard as ASCII table."""
    lines = [
        "| Rank | Policy | Mean IS | Median IS | p95 IS | Win Rate |",
        "|------|--------|---------|-----------|--------|----------|"
    ]
    
    for e in entries:
        lines.append(
            f"| {e.rank:4d} | {e.policy:6s} | {e.mean_is:7.2f} | "
            f"{e.median_is:9.2f} | {e.p95_is:6.2f} | {e.win_rate_vs_twap:7.1%} |"
        )
        
    return "\n".join(lines)
