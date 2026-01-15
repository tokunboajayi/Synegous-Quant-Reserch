"""
Strategy Library - 100+ Trading Strategies
Comprehensive collection of testing methods across market conditions.
"""
from typing import List
from nmie.research.strategies import Strategy, Signal, Rule


def get_strategy_library() -> List[Strategy]:
    """
    Returns 100+ pre-built strategy templates organized by category:
    - Momentum Strategies (1-15)
    - Mean Reversion Strategies (16-30)
    - Factor Strategies (31-50)
    - Statistical Arbitrage (51-65)
    - Volatility Strategies (66-80)
    - Market Regime Strategies (81-90)
    - Execution Strategies (91-100)
    - Advanced/Hybrid Strategies (101-110)
    """
    
    strategies = []
    
    # ================================================================
    # CATEGORY 1: MOMENTUM STRATEGIES (1-15)
    # ================================================================
    
    momentum_strategies = [
        Strategy(
            strategy_id="lib_mom_01",
            name="Price Momentum (12M-1M)",
            description="Classic momentum: rank by 12-month return excluding last month. Go long top decile, short bottom decile.",
            type="momentum",
            signals=[Signal(name="mom_12_1", type="momentum", parameters={"lookback": 252, "skip": 21})],
            entry_rules=[Rule(condition="rank > 0.9", action="buy"), Rule(condition="rank < 0.1", action="sell")],
            exit_rules=[Rule(condition="rank_change > 0.3", action="close")],
            parameters={"lookback_window": 252, "skip_days": 21, "rebalance": "monthly"},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_mom_02",
            name="Short-Term Momentum (1M)",
            description="Short-term momentum using 1-month returns. Higher turnover but captures quick trends.",
            type="momentum",
            signals=[Signal(name="mom_1m", type="momentum", parameters={"lookback": 21})],
            parameters={"lookback_window": 21, "rebalance": "weekly"},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_mom_03",
            name="Dual Momentum (Absolute + Relative)",
            description="Combine absolute momentum (vs cash) and relative momentum (vs peers). Only long when both are positive.",
            type="momentum",
            signals=[
                Signal(name="abs_mom", type="momentum", parameters={"benchmark": "cash"}),
                Signal(name="rel_mom", type="momentum", parameters={"benchmark": "universe"})
            ],
            entry_rules=[Rule(condition="abs_mom > 0 AND rel_mom > 0", action="buy")],
            parameters={"lookback_window": 126},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_mom_04",
            name="Sector Momentum Rotation",
            description="Rotate into top 3 momentum sectors each month. Avoid weakest sectors.",
            type="momentum",
            signals=[Signal(name="sector_mom", type="momentum", parameters={"level": "sector"})],
            parameters={"n_sectors": 3, "rebalance": "monthly"},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_mom_05",
            name="52-Week High Momentum",
            description="Buy stocks making new 52-week highs. Anchoring bias creates underreaction.",
            type="momentum",
            signals=[Signal(name="high_52w", type="momentum", parameters={"metric": "proximity_to_high"})],
            entry_rules=[Rule(condition="price > 0.95 * high_52w", action="buy")],
            parameters={"proximity_threshold": 0.95},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_mom_06",
            name="Earnings Momentum (SUE)",
            description="Trade on Standardized Unexpected Earnings. Long positive surprises, short negative.",
            type="factor",
            signals=[Signal(name="sue", type="factor", parameters={"metric": "earnings_surprise_std"})],
            parameters={"holding_period": 60},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_mom_07",
            name="Revenue Momentum",
            description="Rank by quarter-over-quarter revenue growth. Revenue trends are persistent.",
            type="momentum",
            signals=[Signal(name="rev_growth", type="factor", parameters={"metric": "revenue_qoq"})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_mom_08",
            name="Analyst Revision Momentum",
            description="Buy stocks with upward EPS revisions, sell downward revisions.",
            type="momentum",
            signals=[Signal(name="revision", type="factor", parameters={"metric": "eps_revision_3m"})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_mom_09",
            name="Time-Series Momentum (TSMOM)",
            description="Go long if 12-month return is positive, otherwise go to cash.",
            type="momentum",
            signals=[Signal(name="tsmom", type="momentum", parameters={"lookback": 252, "absolute": True})],
            entry_rules=[Rule(condition="return_12m > 0", action="buy")],
            exit_rules=[Rule(condition="return_12m < 0", action="close")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_mom_10",
            name="Momentum Crash Protection",
            description="Standard momentum with volatility scaling. Reduce exposure when VIX is high.",
            type="momentum",
            signals=[Signal(name="mom", type="momentum"), Signal(name="vix_scale", type="volatility")],
            parameters={"vix_threshold": 25, "scale_factor": 0.5},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_mom_11",
            name="Cross-Asset Momentum",
            description="Apply momentum across stocks, bonds, commodities, currencies.",
            type="momentum",
            signals=[Signal(name="xasset_mom", type="momentum", parameters={"assets": ["equity", "bond", "commodity", "fx"]})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_mom_12",
            name="Industry Momentum",
            description="Rank industries by 6-month momentum. Long top 5, short bottom 5.",
            type="momentum",
            signals=[Signal(name="industry_mom", type="momentum", parameters={"level": "industry", "lookback": 126})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_mom_13",
            name="Residual Momentum",
            description="Momentum after removing market/factor exposure. Captures firm-specific momentum.",
            type="momentum",
            signals=[Signal(name="residual_mom", type="momentum", parameters={"adjusted": True})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_mom_14",
            name="Momentum + Quality",
            description="Combine momentum with quality factor. Avoid low-quality momentum stocks.",
            type="momentum",
            signals=[
                Signal(name="momentum", type="momentum", weight=0.6),
                Signal(name="quality", type="factor", parameters={"metric": "roe"}, weight=0.4)
            ],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_mom_15",
            name="Momentum Decile Spread",
            description="Long top decile, short bottom decile of 12-month momentum.",
            type="momentum",
            signals=[Signal(name="mom_decile", type="momentum")],
            entry_rules=[Rule(condition="decile == 10", action="buy"), Rule(condition="decile == 1", action="sell")],
            is_template=True, author="library"
        ),
    ]
    strategies.extend(momentum_strategies)
    
    # ================================================================
    # CATEGORY 2: MEAN REVERSION STRATEGIES (16-30)
    # ================================================================
    
    mean_reversion_strategies = [
        Strategy(
            strategy_id="lib_rev_16",
            name="Bollinger Band Reversion",
            description="Buy below lower band, sell above upper band. 2 standard deviations.",
            type="mean_reversion",
            signals=[Signal(name="bb_zscore", type="mean_reversion", parameters={"std_dev": 2, "lookback": 20})],
            entry_rules=[Rule(condition="price < lower_band", action="buy"), Rule(condition="price > upper_band", action="sell")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_rev_17",
            name="RSI Mean Reversion",
            description="Buy when RSI < 30 (oversold), sell when RSI > 70 (overbought).",
            type="mean_reversion",
            signals=[Signal(name="rsi", type="mean_reversion", parameters={"period": 14})],
            entry_rules=[Rule(condition="rsi < 30", action="buy"), Rule(condition="rsi > 70", action="sell")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_rev_18",
            name="Short-Term Reversal (1-Week)",
            description="Buy last week's losers, sell last week's winners. Liquidity-driven reversal.",
            type="mean_reversion",
            signals=[Signal(name="reversal_1w", type="mean_reversion", parameters={"lookback": 5})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_rev_19",
            name="Long-Term Reversal (5-Year)",
            description="Buy 5-year losers (value-like), sell 5-year winners. Contrarian.",
            type="mean_reversion",
            signals=[Signal(name="reversal_5y", type="mean_reversion", parameters={"lookback": 1260})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_rev_20",
            name="Pairs Trading - Cointegration",
            description="Trade mean-reversion of cointegrated stock pairs. Statistical arbitrage.",
            type="statistical_arb",
            signals=[Signal(name="spread_zscore", type="mean_reversion", parameters={"pair_method": "cointegration"})],
            entry_rules=[Rule(condition="zscore > 2", action="short_spread"), Rule(condition="zscore < -2", action="long_spread")],
            exit_rules=[Rule(condition="abs(zscore) < 0.5", action="close")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_rev_21",
            name="ETF Arbitrage",
            description="Trade spreads between ETF and its underlying basket.",
            type="statistical_arb",
            signals=[Signal(name="etf_nav_spread", type="mean_reversion")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_rev_22",
            name="Intraday Mean Reversion",
            description="Fade intraday moves. Buy morning losers, sell afternoon if recovered.",
            type="mean_reversion",
            signals=[Signal(name="intraday_return", type="mean_reversion", parameters={"period": "morning"})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_rev_23",
            name="Event-Driven Reversion",
            description="Buy oversold after negative events (earnings miss), fade overreaction.",
            type="mean_reversion",
            signals=[Signal(name="event_reaction", type="mean_reversion")],
            parameters={"event_type": "earnings", "threshold": -0.05},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_rev_24",
            name="Sector Relative Reversion",
            description="Buy stock underperforming sector, sell outperformers. Sector-neutral.",
            type="mean_reversion",
            signals=[Signal(name="sector_relative", type="mean_reversion", parameters={"benchmark": "sector"})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_rev_25",
            name="Gap Fade Strategy",
            description="Fade overnight gaps. Buy gap-downs, sell gap-ups.",
            type="mean_reversion",
            signals=[Signal(name="gap_pct", type="mean_reversion")],
            entry_rules=[Rule(condition="gap < -0.02", action="buy"), Rule(condition="gap > 0.02", action="sell")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_rev_26",
            name="VIX Mean Reversion",
            description="Buy VIX puts when VIX > 25, sell when VIX < 15.",
            type="mean_reversion",
            signals=[Signal(name="vix_zscore", type="volatility")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_rev_27",
            name="Calendar Spread Mean Reversion",
            description="Trade term structure of futures/options.",
            type="statistical_arb",
            signals=[Signal(name="term_spread", type="mean_reversion")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_rev_28",
            name="Dividend Capture + Reversion",
            description="Buy before ex-div, hold through, fade any overreaction.",
            type="mean_reversion",
            signals=[Signal(name="div_yield", type="factor"), Signal(name="exdiv_gap", type="mean_reversion")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_rev_29",
            name="Extreme Value Reversion",
            description="Buy stocks at 52-week lows, sell at 52-week highs. Contrarian.",
            type="mean_reversion",
            signals=[Signal(name="extremes", type="mean_reversion", parameters={"metric": "52w_range_pct"})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_rev_30",
            name="Ornstein-Uhlenbeck Reversion",
            description="Model price as OU process. Trade based on mean-reversion speed.",
            type="statistical_arb",
            signals=[Signal(name="ou_params", type="mean_reversion", parameters={"model": "ornstein_uhlenbeck"})],
            is_template=True, author="library"
        ),
    ]
    strategies.extend(mean_reversion_strategies)
    
    # ================================================================
    # CATEGORY 3: FACTOR STRATEGIES (31-50)
    # ================================================================
    
    factor_strategies = [
        Strategy(
            strategy_id="lib_fac_31",
            name="Value (Book-to-Market)",
            description="Classic value factor. Buy high B/M, sell low B/M.",
            type="factor",
            signals=[Signal(name="btm", type="factor", parameters={"metric": "book_to_market"})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_32",
            name="Value (Earnings Yield)",
            description="Rank by E/P ratio. Alternative value measure.",
            type="factor",
            signals=[Signal(name="ep", type="factor", parameters={"metric": "earnings_yield"})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_33",
            name="Value (Free Cash Flow Yield)",
            description="Rank by FCF/EV. Focuses on cash generation.",
            type="factor",
            signals=[Signal(name="fcfy", type="factor", parameters={"metric": "fcf_yield"})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_34",
            name="Size (Small-Cap Premium)",
            description="Long small caps, short large caps. SMB factor.",
            type="factor",
            signals=[Signal(name="size", type="factor", parameters={"metric": "market_cap", "inverse": True})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_35",
            name="Quality (ROE)",
            description="Buy high ROE stocks. Warren Buffett approach.",
            type="factor",
            signals=[Signal(name="roe", type="factor", parameters={"metric": "return_on_equity"})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_36",
            name="Quality (Gross Profitability)",
            description="Rank by GP/Assets. Novy-Marx profitability factor.",
            type="factor",
            signals=[Signal(name="gpa", type="factor", parameters={"metric": "gross_profit_assets"})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_37",
            name="Quality (Low Accruals)",
            description="Short high accruals (earnings manipulation). Sloan accruals anomaly.",
            type="factor",
            signals=[Signal(name="accruals", type="factor", parameters={"metric": "accruals", "inverse": True})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_38",
            name="Low Volatility",
            description="Buy low-vol stocks. Betting against beta.",
            type="factor",
            signals=[Signal(name="vol", type="volatility", parameters={"inverse": True})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_39",
            name="Low Beta",
            description="Long low beta, short high beta. BAB factor.",
            type="factor",
            signals=[Signal(name="beta", type="factor", parameters={"metric": "beta", "inverse": True})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_40",
            name="Dividend Yield",
            description="Buy high dividend stocks. Income strategy.",
            type="factor",
            signals=[Signal(name="div_yield", type="factor", parameters={"metric": "dividend_yield"})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_41",
            name="Investment (Conservative)",
            description="Buy low asset growth stocks. Avoid aggressive investment.",
            type="factor",
            signals=[Signal(name="asset_growth", type="factor", parameters={"metric": "asset_growth", "inverse": True})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_42",
            name="Shareholder Yield",
            description="Combine dividends + buybacks. Full capital return.",
            type="factor",
            signals=[Signal(name="shareholder_yield", type="factor", parameters={"metric": "shareholder_yield"})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_43",
            name="Fama-French 3-Factor",
            description="Market + SMB + HML. Classic 3-factor model.",
            type="factor",
            signals=[
                Signal(name="mkt", type="factor", weight=0.34),
                Signal(name="smb", type="factor", parameters={"metric": "size"}, weight=0.33),
                Signal(name="hml", type="factor", parameters={"metric": "book_to_market"}, weight=0.33)
            ],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_44",
            name="Fama-French 5-Factor",
            description="Add RMW (profitability) + CMA (investment) to 3-factor.",
            type="factor",
            signals=[
                Signal(name="mkt", type="factor", weight=0.2),
                Signal(name="smb", type="factor", weight=0.2),
                Signal(name="hml", type="factor", weight=0.2),
                Signal(name="rmw", type="factor", weight=0.2),
                Signal(name="cma", type="factor", weight=0.2)
            ],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_45",
            name="Momentum + Value",
            description="Combine momentum and value. Avoid value traps.",
            type="factor",
            signals=[
                Signal(name="momentum", type="momentum", weight=0.5),
                Signal(name="value", type="factor", parameters={"metric": "btm"}, weight=0.5)
            ],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_46",
            name="GARP (Growth at Reasonable Price)",
            description="Buy growth stocks that aren't overvalued. PEG-like.",
            type="factor",
            signals=[
                Signal(name="growth", type="factor", parameters={"metric": "earnings_growth"}, weight=0.5),
                Signal(name="value", type="factor", parameters={"metric": "pe_ratio", "inverse": True}, weight=0.5)
            ],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_47",
            name="Magic Formula",
            description="Joel Greenblatt: High earnings yield + high ROIC.",
            type="factor",
            signals=[
                Signal(name="ey", type="factor", parameters={"metric": "earnings_yield"}, weight=0.5),
                Signal(name="roic", type="factor", parameters={"metric": "roic"}, weight=0.5)
            ],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_48",
            name="Piotroski F-Score",
            description="Score stocks 0-9 on fundamental strength. Buy 8-9.",
            type="factor",
            signals=[Signal(name="f_score", type="factor", parameters={"metric": "piotroski_score"})],
            entry_rules=[Rule(condition="f_score >= 8", action="buy")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_49",
            name="Altman Z-Score",
            description="Avoid bankruptcy risk. Short low Z-score stocks.",
            type="factor",
            signals=[Signal(name="z_score", type="factor", parameters={"metric": "altman_z"})],
            entry_rules=[Rule(condition="z_score < 1.8", action="sell")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_fac_50",
            name="ESG Tilt",
            description="Overweight high ESG, underweight low ESG.",
            type="factor",
            signals=[Signal(name="esg", type="factor", parameters={"metric": "esg_score"})],
            is_template=True, author="library"
        ),
    ]
    strategies.extend(factor_strategies)
    
    # ================================================================
    # CATEGORY 4: STATISTICAL ARBITRAGE (51-65)
    # ================================================================
    
    stat_arb_strategies = [
        Strategy(
            strategy_id="lib_stat_51",
            name="PCA Statistical Arbitrage",
            description="Trade residuals from PCA decomposition of returns. Pure alpha.",
            type="statistical_arb",
            signals=[Signal(name="pca_residual", type="mean_reversion", parameters={"n_components": 5})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_stat_52",
            name="Sector Neutralization",
            description="Remove sector exposure, trade pure stock selection.",
            type="statistical_arb",
            signals=[Signal(name="sector_neutral_alpha", type="factor")],
            parameters={"neutralize": ["sector", "beta"]},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_stat_53",
            name="Dollar Neutral Long/Short",
            description="Equal dollar long and short. Market neutral.",
            type="statistical_arb",
            parameters={"dollar_neutral": True, "gross_leverage": 2.0},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_stat_54",
            name="Beta Neutral",
            description="Hedge beta exposure. Pure alpha extraction.",
            type="statistical_arb",
            parameters={"beta_neutral": True},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_stat_55",
            name="Correlation Arbitrage",
            description="Trade implied vs realized correlation. Dispersion trades.",
            type="statistical_arb",
            signals=[Signal(name="corr_spread", type="volatility")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_stat_56",
            name="Index Rebalance Arb",
            description="Front-run index additions/deletions.",
            type="statistical_arb",
            signals=[Signal(name="index_effect", type="custom")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_stat_57",
            name="Merger Arbitrage",
            description="Long target, short acquirer. Capture spread.",
            type="statistical_arb",
            signals=[Signal(name="merger_spread", type="custom")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_stat_58",
            name="Convertible Arbitrage",
            description="Long convertible bond, hedge equity risk.",
            type="statistical_arb",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_stat_59",
            name="Cross-Exchange Arbitrage",
            description="Exploit price differences across exchanges.",
            type="statistical_arb",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_stat_60",
            name="ADR Arbitrage",
            description="Trade ADR vs underlying. Currency + price arb.",
            type="statistical_arb",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_stat_61",
            name="Basis Trading",
            description="Futures vs spot arbitrage. Carry trades.",
            type="statistical_arb",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_stat_62",
            name="Box Spread Arbitrage",
            description="Risk-free options arbitrage. Synthetic lending.",
            type="statistical_arb",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_stat_63",
            name="Triangular Arbitrage",
            description="Currency triangle inefficiencies.",
            type="statistical_arb",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_stat_64",
            name="Stub Trading",
            description="Trade holding company discount to subsidiaries.",
            type="statistical_arb",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_stat_65",
            name="Capital Structure Arbitrage",
            description="Trade equity vs debt of same company.",
            type="statistical_arb",
            is_template=True, author="library"
        ),
    ]
    strategies.extend(stat_arb_strategies)
    
    # ================================================================
    # CATEGORY 5: VOLATILITY STRATEGIES (66-80)
    # ================================================================
    
    volatility_strategies = [
        Strategy(
            strategy_id="lib_vol_66",
            name="Volatility Risk Premium",
            description="Sell volatility to harvest premium. Short straddles.",
            type="custom",
            signals=[Signal(name="vrp", type="volatility", parameters={"metric": "iv_minus_rv"})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_vol_67",
            name="VIX Carry",
            description="Short VIX futures, roll down term structure.",
            type="custom",
            signals=[Signal(name="vix_term", type="volatility")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_vol_68",
            name="Variance Swap",
            description="Trade realized vs implied variance.",
            type="custom",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_vol_69",
            name="Gamma Scalping",
            description="Delta-hedge long gamma position. Profit from moves.",
            type="custom",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_vol_70",
            name="Vol Surface Arbitrage",
            description="Trade kinks in implied vol surface.",
            type="custom",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_vol_71",
            name="Skew Trading",
            description="Trade put-call vol skew.",
            type="custom",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_vol_72",
            name="Iron Condor",
            description="Sell OTM puts and calls. Range-bound market.",
            type="custom",
            parameters={"strike_width": 0.1},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_vol_73",
            name="Butterfly Spread",
            description="Long wings, short body. Low-cost range bet.",
            type="custom",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_vol_74",
            name="Calendar Spread",
            description="Long back-month, short front-month. Vol term structure.",
            type="custom",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_vol_75",
            name="Tail Hedge",
            description="Buy deep OTM puts for crash protection.",
            type="custom",
            parameters={"delta": 0.05, "allocation": 0.02},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_vol_76",
            name="Covered Call",
            description="Long stock, sell covered calls. Enhanced yield.",
            type="custom",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_vol_77",
            name="Protective Put",
            description="Long stock + put. Downside protection.",
            type="custom",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_vol_78",
            name="Collar Strategy",
            description="Long stock, sell call, buy put. Bounded payoff.",
            type="custom",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_vol_79",
            name="Risk Reversal",
            description="Sell put, buy call. Bullish vol position.",
            type="custom",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_vol_80",
            name="Straddle Strangle",
            description="Buy straddle/strangle before events. Long gamma.",
            type="custom",
            parameters={"event_type": "earnings"},
            is_template=True, author="library"
        ),
    ]
    strategies.extend(volatility_strategies)
    
    # ================================================================
    # CATEGORY 6: MARKET REGIME STRATEGIES (81-90)
    # ================================================================
    
    regime_strategies = [
        Strategy(
            strategy_id="lib_reg_81",
            name="Trend Following (SMA)",
            description="Long when price > 200-day SMA, else cash.",
            type="momentum",
            signals=[Signal(name="sma_trend", type="momentum", parameters={"sma_period": 200})],
            entry_rules=[Rule(condition="price > sma_200", action="buy")],
            exit_rules=[Rule(condition="price < sma_200", action="close")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_reg_82",
            name="Dual Moving Average",
            description="Long when 50-day > 200-day (golden cross).",
            type="momentum",
            signals=[Signal(name="ma_cross", type="momentum", parameters={"fast": 50, "slow": 200})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_reg_83",
            name="Regime Detection (HMM)",
            description="Hidden Markov Model for bull/bear regimes.",
            type="custom",
            signals=[Signal(name="hmm_state", type="custom", parameters={"model": "hmm", "n_states": 2})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_reg_84",
            name="Volatility Regime Switch",
            description="Full exposure in low-vol, reduce in high-vol.",
            type="custom",
            signals=[Signal(name="vol_regime", type="volatility")],
            parameters={"vol_threshold": 20},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_reg_85",
            name="Risk Parity",
            description="Allocate inversely to volatility. Equal risk contribution.",
            type="custom",
            parameters={"method": "inverse_vol"},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_reg_86",
            name="Momentum Regime",
            description="Use momentum in uptrends, mean reversion in downtrends.",
            type="custom",
            signals=[
                Signal(name="trend_indicator", type="momentum"),
                Signal(name="momentum_signal", type="momentum"),
                Signal(name="reversion_signal", type="mean_reversion")
            ],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_reg_87",
            name="Seasonal Strategy",
            description="Sell in May and go away. November to April long.",
            type="custom",
            parameters={"long_months": [11, 12, 1, 2, 3, 4]},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_reg_88",
            name="Economic Regime",
            description="Rotate based on growth/inflation quadrant.",
            type="custom",
            signals=[Signal(name="econ_regime", type="custom", parameters={"indicators": ["gdp", "cpi"]})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_reg_89",
            name="Drawdown Control",
            description="De-risk when portfolio drawdown > 10%.",
            type="custom",
            parameters={"max_drawdown": 0.10, "recovery_threshold": 0.05},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_reg_90",
            name="Adaptive Allocation",
            description="Dynamically weight strategies based on recent performance.",
            type="custom",
            parameters={"lookback": 63, "method": "sharpe_weighted"},
            is_template=True, author="library"
        ),
    ]
    strategies.extend(regime_strategies)
    
    # ================================================================
    # CATEGORY 7: EXECUTION STRATEGIES (91-100)
    # ================================================================
    
    execution_strategies = [
        Strategy(
            strategy_id="lib_exec_91",
            name="TWAP (Time-Weighted)",
            description="Split order evenly over time. Minimize timing risk.",
            type="custom",
            parameters={"duration_hours": 4, "n_slices": 48},
            code="# TWAP: Split order into equal slices over time",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_exec_92",
            name="VWAP (Volume-Weighted)",
            description="Follow historical volume profile. Minimize market impact.",
            type="custom",
            parameters={"participation_rate": 0.05},
            code="# VWAP: Match historical volume pattern",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_exec_93",
            name="Implementation Shortfall",
            description="Minimize slippage vs decision price. Balance urgency vs impact.",
            type="custom",
            parameters={"urgency": 0.5},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_exec_94",
            name="POV (Percentage of Volume)",
            description="Participate at fixed % of market volume.",
            type="custom",
            parameters={"pov_rate": 0.10},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_exec_95",
            name="Iceberg Order",
            description="Show small size, hide full order. Reduce information leakage.",
            type="custom",
            parameters={"visible_size": 100},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_exec_96",
            name="Sniper",
            description="Wait for liquidity, execute in dark pools.",
            type="custom",
            parameters={"min_block_size": 10000},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_exec_97",
            name="Arrival Price",
            description="Target price at order arrival. Aggressive start.",
            type="custom",
            parameters={"aggression": 0.7},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_exec_98",
            name="Close Price",
            description="Target closing price. Execute near market close.",
            type="custom",
            parameters={"close_window_minutes": 30},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_exec_99",
            name="Liquidity Seeking",
            description="Route to venues with best liquidity. Smart order routing.",
            type="custom",
            parameters={"venues": ["NYSE", "NASDAQ", "BATS", "IEX"]},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_exec_100",
            name="Pairs Execution",
            description="Execute legs simultaneously. Minimize spread risk.",
            type="custom",
            parameters={"sync_tolerance": 0.01},
            is_template=True, author="library"
        ),
    ]
    strategies.extend(execution_strategies)
    
    # ================================================================
    # CATEGORY 8: ADVANCED/HYBRID STRATEGIES (101-115)
    # ================================================================
    
    advanced_strategies = [
        Strategy(
            strategy_id="lib_adv_101",
            name="Machine Learning Alpha",
            description="XGBoost/Random Forest for signal generation.",
            type="custom",
            parameters={"model": "xgboost", "features": ["momentum", "value", "vol", "size"]},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_adv_102",
            name="Deep Learning Factor",
            description="Neural network for non-linear factor combinations.",
            type="custom",
            parameters={"model": "mlp", "hidden_layers": [64, 32]},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_adv_103",
            name="Reinforcement Learning Trading",
            description="RL agent learns optimal trading policy. PPO/DQN.",
            type="custom",
            parameters={"algorithm": "ppo"},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_adv_104",
            name="NLP Sentiment",
            description="Trade on news/social media sentiment.",
            type="custom",
            signals=[Signal(name="sentiment", type="custom", parameters={"source": "news"})],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_adv_105",
            name="Alternative Data",
            description="Satellite imagery, web traffic, credit card data.",
            type="custom",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_adv_106",
            name="Options Flow",
            description="Follow unusual options activity. Smart money tracking.",
            type="custom",
            signals=[Signal(name="options_flow", type="custom")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_adv_107",
            name="Order Flow Imbalance",
            description="Trade on buy/sell pressure from order book.",
            type="custom",
            signals=[Signal(name="ofi", type="custom")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_adv_108",
            name="High-Frequency Market Making",
            description="Provide liquidity, capture spread.",
            type="custom",
            parameters={"min_edge": 0.0001},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_adv_109",
            name="Carry + Momentum",
            description="Combine carry (yield) with momentum across assets.",
            type="custom",
            signals=[
                Signal(name="carry", type="factor", weight=0.5),
                Signal(name="momentum", type="momentum", weight=0.5)
            ],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_adv_110",
            name="Global Macro",
            description="Trade macro themes across asset classes.",
            type="custom",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_adv_111",
            name="Crypto Momentum",
            description="Momentum strategies for cryptocurrency markets.",
            type="momentum",
            parameters={"universe": "crypto"},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_adv_112",
            name="Multi-Strategy Portfolio",
            description="Combine uncorrelated strategies. Kelly optimal sizing.",
            type="custom",
            parameters={"strategies": ["momentum", "value", "stat_arb"], "method": "kelly"},
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_adv_113",
            name="Factor Timing",
            description="Time exposure to factors based on macro/sentiment.",
            type="custom",
            signals=[Signal(name="factor_timing", type="custom")],
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_adv_114",
            name="Tail Risk Harvesting",
            description="Systematically sell tail risk premium.",
            type="custom",
            is_template=True, author="library"
        ),
        Strategy(
            strategy_id="lib_adv_115",
            name="Market Microstructure",
            description="Exploit microstructure patterns. Quote stuffing detection.",
            type="custom",
            is_template=True, author="library"
        ),
    ]
    strategies.extend(advanced_strategies)
    
    return strategies


# Pre-compute the library
STRATEGY_LIBRARY = get_strategy_library()
