"""
TCA - Layman Explanations
Plain English explanations for non-quants.
"""
from typing import Dict, List
from dataclasses import dataclass

@dataclass  
class Explanation:
    """Explanation for laypeople."""
    headline: str
    summary: str
    details: List[str]
    recommendation: str

# Glossary for tooltips
GLOSSARY = {
    "IS": "Implementation Shortfall - How much extra we paid compared to when we decided to trade",
    "bps": "Basis Points - 1/100th of a percent (1 bps = 0.01%)",
    "VWAP": "Volume Weighted Average Price - Average price weighted by volume traded",
    "TWAP": "Time Weighted Average Price - Simple average price over time",
    "Spread": "The gap between buy and sell prices - we pay half when we trade",
    "Impact": "How our trading moved the market against us",
    "Slippage": "The difference between expected and actual price",
    "Participation Rate": "What fraction of market volume our order represents",
    "Regime": "Market conditions (e.g., volatile, calm, liquid, illiquid)",
}

def explain_is(is_bps: float, side: str = "BUY") -> Explanation:
    """Explain Implementation Shortfall."""
    if is_bps < 0:
        headline = "We did BETTER than expected"
        quality = "saved money"
    elif is_bps < 5:
        headline = "Execution was GOOD"
        quality = "reasonable cost"
    elif is_bps < 10:
        headline = "Execution was ACCEPTABLE"
        quality = "moderate cost"
    else:
        headline = "Execution was EXPENSIVE"
        quality = "high cost"
    
    side_verb = "bought" if side.upper() == "BUY" else "sold"
    direction = "higher" if side.upper() == "BUY" else "lower"
    
    return Explanation(
        headline=headline,
        summary=f"We {side_verb} the shares at a price that was {abs(is_bps):.1f} basis points {direction} than when we decided to trade. This represents {quality}.",
        details=[
            f"Implementation Shortfall: {is_bps:.2f} bps",
            "1 basis point = 0.01% = $1 per $10,000 traded",
            f"On a $1M order, this is approximately ${abs(is_bps) * 10:.0f}"
        ],
        recommendation="Lower IS is better. Compare against VWAP and TWAP benchmarks."
    )

def explain_cost_decomposition(
    spread_bps: float,
    timing_bps: float,
    impact_bps: float,
    total_bps: float
) -> Explanation:
    """Explain cost decomposition."""
    largest = max(
        ("spread", spread_bps),
        ("timing", timing_bps),
        ("impact", impact_bps),
        key=lambda x: abs(x[1])
    )
    
    return Explanation(
        headline=f"Biggest cost driver: {largest[0].upper()}",
        summary=f"Your total cost of {total_bps:.1f} bps came from three sources. The largest was {largest[0]} at {largest[1]:.1f} bps.",
        details=[
            f"Spread cost: {spread_bps:.2f} bps - Cost of crossing bid-ask",
            f"Timing cost: {timing_bps:.2f} bps - Market moved during execution",
            f"Impact cost: {impact_bps:.2f} bps - Our trading moved the price"
        ],
        recommendation=_get_decomposition_recommendation(largest[0], largest[1])
    )

def _get_decomposition_recommendation(component: str, value: float) -> str:
    if component == "spread":
        return "Consider trading during tighter spread periods or using limit orders"
    elif component == "timing":
        if value > 0:
            return "Market moved against us - consider faster execution next time"
        else:
            return "Market moved in our favor - timing helped"
    else:
        return "Our order size impacted the market - consider smaller slices or longer horizon"

def explain_strategy_comparison(
    strategy_results: Dict[str, float]
) -> Explanation:
    """Explain which strategy won and why."""
    best = min(strategy_results.items(), key=lambda x: x[1])
    worst = max(strategy_results.items(), key=lambda x: x[1])
    
    savings = worst[1] - best[1]
    
    return Explanation(
        headline=f"{best[0]} was the best strategy",
        summary=f"Compared to {worst[0]}, using {best[0]} would have saved {savings:.1f} basis points.",
        details=[
            f"{k}: {v:.2f} bps" for k, v in sorted(strategy_results.items(), key=lambda x: x[1])
        ],
        recommendation=f"The {best[0]} strategy worked best for this order's characteristics."
    )

def explain_regime_impact(
    regime: str,
    is_bps: float,
    normal_is_bps: float
) -> Explanation:
    """Explain how market regime affected execution."""
    delta = is_bps - normal_is_bps
    
    regime_descriptions = {
        "high_volatility": "The market was moving a lot during execution",
        "low_volatility": "The market was calm during execution",
        "wide_spread": "The gap between buy and sell prices was larger than normal",
        "tight_spread": "The gap between buy and sell prices was small",
        "low_liquidity": "There was less trading volume available",
        "high_liquidity": "There was plenty of trading volume",
        "open_hour": "This was during the first hour of trading",
        "close_hour": "This was near market close"
    }
    
    desc = regime_descriptions.get(regime, "Market conditions were unusual")
    
    if delta > 2:
        impact = "This made execution MORE expensive"
    elif delta < -2:
        impact = "This made execution LESS expensive"
    else:
        impact = "This had minimal impact on cost"
    
    return Explanation(
        headline=f"Regime: {regime.replace('_', ' ').title()}",
        summary=f"{desc}. {impact}",
        details=[
            f"Cost in this regime: {is_bps:.2f} bps",
            f"Normal conditions cost: {normal_is_bps:.2f} bps",
            f"Regime impact: {delta:+.2f} bps"
        ],
        recommendation="Consider adjusting strategy based on market conditions"
    )

def generate_order_story(
    order_id: str,
    symbol: str,
    side: str,
    total_shares: float,
    strategies: Dict[str, float],
    selected_strategy: str
) -> str:
    """Generate a simple story about the order for laypeople."""
    best = min(strategies.items(), key=lambda x: x[1])
    selected_cost = strategies.get(selected_strategy, 0)
    
    side_verb = "buy" if side.upper() == "BUY" else "sell"
    
    story = f"""
## Order Story: {order_id}

**What we wanted to do:**
We needed to {side_verb} {total_shares:,.0f} shares of {symbol}.

**How we could have done it:**
We compared {len(strategies)} different strategies:
"""
    
    for name, cost in sorted(strategies.items(), key=lambda x: x[1]):
        if name == best[0]:
            story += f"- **{name}: {cost:.1f} bps** (BEST)\n"
        else:
            story += f"- {name}: {cost:.1f} bps\n"
    
    story += f"""
**What we actually did:**
We used {selected_strategy}, which cost {selected_cost:.1f} bps.

**The bottom line:**
"""
    
    if selected_strategy == best[0]:
        story += "We chose the best strategy!"
    else:
        savings = selected_cost - best[1]
        story += f"If we had used {best[0]}, we could have saved {savings:.1f} bps."
    
    return story
