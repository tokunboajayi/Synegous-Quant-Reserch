import { useEffect, useState } from 'react';
import axios from 'axios';
import {
    Activity, BarChart2, Grid3X3,
    Target, Zap, RefreshCw, ArrowUp, ArrowDown, Minus,
    Layers
} from 'lucide-react';

// Types
interface SectorData {
    sector: string;
    performance_1d: number;
    performance_1w: number;
    performance_1m: number;
    performance_3m: number;
    performance_ytd: number;
    volatility: number;
    relative_strength: number;
    trend: string;
}

interface FactorScore {
    ticker: string;
    name: string;
    momentum_score: number;
    value_score: number;
    quality_score: number;
    volatility_score: number;
    size_score: number;
    composite_score: number;
}

interface MarketRegime {
    regime: string;
    confidence: number;
    vix_level: number;
    trend_strength: number;
    breadth: number;
}

interface CorrelationPair {
    ticker1: string;
    ticker2: string;
    correlation: number;
    beta: number;
}

// Tabs
type Tab = 'sectors' | 'factors' | 'correlations' | 'regime';

export const MarketResearch = () => {
    const [activeTab, setActiveTab] = useState<Tab>('sectors');
    const [loading, setLoading] = useState(false);

    // Data
    const [sectors, setSectors] = useState<SectorData[]>([]);
    const [factors, setFactors] = useState<FactorScore[]>([]);
    const [pairs, setPairs] = useState<CorrelationPair[]>([]);
    const [regime, setRegime] = useState<MarketRegime | null>(null);
    const [regimeStrategies, setRegimeStrategies] = useState<string[]>([]);

    // Load data based on active tab
    useEffect(() => {
        loadData();
    }, [activeTab]);

    const loadData = async () => {
        setLoading(true);
        try {
            switch (activeTab) {
                case 'sectors':
                    const sectorRes = await axios.get('/market/sectors');
                    setSectors(sectorRes.data.sectors);
                    break;
                case 'factors':
                    const factorRes = await axios.get('/market/factors');
                    setFactors(factorRes.data.factors);
                    break;
                case 'correlations':
                    const pairRes = await axios.get('/market/correlations/pairs?min_corr=0.6');
                    setPairs(pairRes.data.pairs);
                    break;
                case 'regime':
                    const regimeRes = await axios.get('/market/regime');
                    setRegime(regimeRes.data.regime);
                    setRegimeStrategies(regimeRes.data.recommended_strategies || []);
                    break;
            }
        } catch (e) {
            console.error('Failed to load data', e);
        }
        setLoading(false);
    };

    // Trend icon
    const TrendIcon = ({ trend }: { trend: string }) => {
        if (trend === 'up') return <ArrowUp size={14} className="text-green-400" />;
        if (trend === 'down') return <ArrowDown size={14} className="text-red-400" />;
        return <Minus size={14} className="text-slate-400" />;
    };

    // Performance cell color
    const getPerformanceColor = (value: number) => {
        if (value > 5) return 'bg-green-500/30 text-green-400';
        if (value > 2) return 'bg-green-500/20 text-green-400';
        if (value > 0) return 'bg-green-500/10 text-green-400';
        if (value > -2) return 'bg-red-500/10 text-red-400';
        if (value > -5) return 'bg-red-500/20 text-red-400';
        return 'bg-red-500/30 text-red-400';
    };

    // Score bar
    const ScoreBar = ({ value, color }: { value: number; color: string }) => (
        <div className="w-full bg-slate-800 rounded-full h-1.5">
            <div
                className={`h-1.5 rounded-full ${color}`}
                style={{ width: `${Math.min(100, value)}%` }}
            />
        </div>
    );

    // Regime badge
    const RegimeBadge = ({ regime }: { regime: string }) => {
        const styles: Record<string, string> = {
            bull: 'bg-green-500/20 text-green-400 border-green-500/30',
            bear: 'bg-red-500/20 text-red-400 border-red-500/30',
            high_vol: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
            low_vol: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
            ranging: 'bg-slate-500/20 text-slate-400 border-slate-500/30'
        };
        return (
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${styles[regime] || styles.ranging}`}>
                {regime.replace('_', ' ').toUpperCase()}
            </span>
        );
    };

    return (
        <div className="p-6 h-full flex flex-col">
            {/* Header */}
            <header className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500/30 to-blue-500/30 flex items-center justify-center border border-cyan-500/30">
                        <Activity size={24} className="text-cyan-400" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-slate-100">Market Research</h1>
                        <p className="text-slate-500 text-sm">Sector analysis, factors, correlations, and market regime</p>
                    </div>
                </div>

                <button
                    onClick={loadData}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                >
                    <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                    Refresh
                </button>
            </header>

            {/* Tabs */}
            <div className="flex gap-2 mb-6 border-b border-slate-800 pb-4">
                {[
                    { id: 'sectors', label: 'Sector Heatmap', icon: Grid3X3 },
                    { id: 'factors', label: 'Factor Zoo', icon: BarChart2 },
                    { id: 'correlations', label: 'Correlations', icon: Layers },
                    { id: 'regime', label: 'Market Regime', icon: Zap },
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as Tab)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === tab.id
                            ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                            : 'text-slate-400 hover:bg-slate-800'
                            }`}
                    >
                        <tab.icon size={16} />
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto">
                {loading ? (
                    <div className="text-center py-12 text-slate-500">Loading...</div>
                ) : (
                    <>
                        {/* Sector Heatmap */}
                        {activeTab === 'sectors' && (
                            <div className="space-y-4">
                                <div className="grid grid-cols-6 gap-2 text-xs text-slate-500 font-medium px-4">
                                    <div>Sector</div>
                                    <div className="text-center">1D</div>
                                    <div className="text-center">1W</div>
                                    <div className="text-center">1M</div>
                                    <div className="text-center">3M</div>
                                    <div className="text-center">YTD</div>
                                </div>
                                {sectors.map(sector => (
                                    <div key={sector.sector} className="grid grid-cols-6 gap-2 items-center p-3 bg-[#1a1f26] rounded-lg border border-slate-700/50">
                                        <div className="flex items-center gap-2">
                                            <TrendIcon trend={sector.trend} />
                                            <span className="font-medium text-slate-200 text-sm">{sector.sector}</span>
                                        </div>
                                        {[sector.performance_1d, sector.performance_1w, sector.performance_1m, sector.performance_3m, sector.performance_ytd].map((val, i) => (
                                            <div key={i} className={`text-center py-1.5 rounded text-sm font-medium ${getPerformanceColor(val)}`}>
                                                {val > 0 ? '+' : ''}{val.toFixed(1)}%
                                            </div>
                                        ))}
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Factor Zoo */}
                        {activeTab === 'factors' && (
                            <div className="space-y-3">
                                <div className="grid grid-cols-7 gap-4 text-xs text-slate-500 font-medium px-4 pb-2">
                                    <div>Ticker</div>
                                    <div>Momentum</div>
                                    <div>Value</div>
                                    <div>Quality</div>
                                    <div>Low Vol</div>
                                    <div>Size</div>
                                    <div>Composite</div>
                                </div>
                                {factors.slice(0, 30).map(stock => (
                                    <div key={stock.ticker} className="grid grid-cols-7 gap-4 items-center p-3 bg-[#1a1f26] rounded-lg border border-slate-700/50">
                                        <div>
                                            <div className="font-medium text-slate-200">{stock.ticker}</div>
                                            <div className="text-xs text-slate-500 truncate">{stock.name}</div>
                                        </div>
                                        {[
                                            { val: stock.momentum_score, color: 'bg-green-500' },
                                            { val: stock.value_score, color: 'bg-blue-500' },
                                            { val: stock.quality_score, color: 'bg-purple-500' },
                                            { val: stock.volatility_score, color: 'bg-yellow-500' },
                                            { val: stock.size_score, color: 'bg-cyan-500' },
                                        ].map((factor, i) => (
                                            <div key={i} className="space-y-1">
                                                <div className="text-xs text-slate-400 text-right">{factor.val.toFixed(0)}</div>
                                                <ScoreBar value={factor.val} color={factor.color} />
                                            </div>
                                        ))}
                                        <div className="text-center">
                                            <span className={`px-2 py-1 rounded text-sm font-bold ${stock.composite_score >= 60 ? 'bg-green-500/20 text-green-400' :
                                                stock.composite_score >= 40 ? 'bg-yellow-500/20 text-yellow-400' :
                                                    'bg-red-500/20 text-red-400'
                                                }`}>
                                                {stock.composite_score.toFixed(0)}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Correlations / Pairs */}
                        {activeTab === 'correlations' && (
                            <div className="space-y-4">
                                <div className="bg-[#1a1f26] rounded-lg border border-slate-700 p-4 mb-4">
                                    <h3 className="text-sm font-medium text-slate-300 mb-2">Pairs Trading Candidates</h3>
                                    <p className="text-xs text-slate-500">Highly correlated pairs suitable for statistical arbitrage</p>
                                </div>
                                <div className="grid grid-cols-3 gap-4">
                                    {pairs.slice(0, 30).map((pair, i) => (
                                        <div key={i} className="p-4 bg-[#1a1f26] rounded-lg border border-slate-700/50">
                                            <div className="flex items-center justify-between mb-2">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-medium text-cyan-400">{pair.ticker1}</span>
                                                    <span className="text-slate-600">/</span>
                                                    <span className="font-medium text-purple-400">{pair.ticker2}</span>
                                                </div>
                                            </div>
                                            <div className="flex items-center justify-between text-xs">
                                                <span className="text-slate-500">Correlation</span>
                                                <span className={`font-medium ${pair.correlation > 0.8 ? 'text-green-400' : 'text-yellow-400'}`}>
                                                    {(pair.correlation * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                            <div className="mt-1">
                                                <div className="w-full bg-slate-800 rounded-full h-1">
                                                    <div
                                                        className="h-1 rounded-full bg-gradient-to-r from-cyan-500 to-purple-500"
                                                        style={{ width: `${pair.correlation * 100}%` }}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Market Regime */}
                        {activeTab === 'regime' && regime && (
                            <div className="space-y-6">
                                {/* Main Regime Card */}
                                <div className="bg-[#1a1f26] rounded-xl border border-slate-700 p-6">
                                    <div className="flex items-center justify-between mb-6">
                                        <div>
                                            <div className="text-sm text-slate-500 mb-1">Current Market Regime</div>
                                            <RegimeBadge regime={regime.regime} />
                                        </div>
                                        <div className="text-right">
                                            <div className="text-sm text-slate-500 mb-1">Confidence</div>
                                            <div className="text-2xl font-bold text-slate-200">{(regime.confidence * 100).toFixed(0)}%</div>
                                        </div>
                                    </div>

                                    {/* Metrics Grid */}
                                    <div className="grid grid-cols-3 gap-6">
                                        <div className="bg-slate-800/50 rounded-lg p-4">
                                            <div className="text-xs text-slate-500 mb-1">VIX Level</div>
                                            <div className={`text-xl font-bold ${regime.vix_level > 25 ? 'text-orange-400' : regime.vix_level > 18 ? 'text-yellow-400' : 'text-green-400'}`}>
                                                {regime.vix_level.toFixed(1)}
                                            </div>
                                            <div className="text-xs text-slate-600">
                                                {regime.vix_level > 25 ? 'High Fear' : regime.vix_level > 18 ? 'Moderate' : 'Low Fear'}
                                            </div>
                                        </div>
                                        <div className="bg-slate-800/50 rounded-lg p-4">
                                            <div className="text-xs text-slate-500 mb-1">Trend Strength</div>
                                            <div className="text-xl font-bold text-cyan-400">{(regime.trend_strength * 100).toFixed(0)}%</div>
                                            <div className="text-xs text-slate-600">
                                                {regime.trend_strength > 0.3 ? 'Strong' : regime.trend_strength > 0.15 ? 'Moderate' : 'Weak'}
                                            </div>
                                        </div>
                                        <div className="bg-slate-800/50 rounded-lg p-4">
                                            <div className="text-xs text-slate-500 mb-1">Market Breadth</div>
                                            <div className="text-xl font-bold text-purple-400">{(regime.breadth * 100).toFixed(0)}%</div>
                                            <div className="text-xs text-slate-600">
                                                {regime.breadth > 0.6 ? 'Healthy' : regime.breadth > 0.4 ? 'Mixed' : 'Narrow'}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Recommended Strategies */}
                                <div className="bg-[#1a1f26] rounded-xl border border-slate-700 p-6">
                                    <h3 className="text-sm font-medium text-slate-300 mb-4 flex items-center gap-2">
                                        <Target size={16} className="text-cyan-400" />
                                        Recommended Strategies for This Regime
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        {regimeStrategies.map((strategy, i) => (
                                            <span key={i} className="px-3 py-1.5 bg-cyan-500/10 text-cyan-400 rounded-lg text-sm border border-cyan-500/20">
                                                {strategy}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};
