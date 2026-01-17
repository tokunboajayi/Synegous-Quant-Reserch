import { useState, useEffect } from 'react';

const RocketIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-400"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" /><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z" /><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" /><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" /></svg>
);
import axios from 'axios';
import {
    Zap, Brain, Target, Activity, Share2,
    TrendingUp, Shield, BarChart2, PieChart,
    ChevronRight, ArrowRight, Info, AlertTriangle, Play
} from 'lucide-react';

type IntelTab = 'kelly' | 'optimizer' | 'montecarlo';

interface KellyResult {
    kelly_fraction: number;
    fraction_recommended: number;
    interpretation: string;
}

interface WeightResult {
    ticker: string;
    weight: number;
    expected_return: number;
}

interface OptimizationResult {
    weights: WeightResult[];
    portfolio_metrics: {
        expected_return: number;
        volatility: number;
        sharpe_ratio: number;
    };
}

interface MonteCarloResult {
    simulations: number[][];
    summary: {
        mean: number;
        median: number;
        std: number;
        p5: number;
        p95: number;
        prob_loss: number;
    };
}

export const PortfolioIntelligence = () => {
    const [activeTab, setActiveTab] = useState<IntelTab>('kelly');
    const [loading, setLoading] = useState(false);
    const [statusParams, setStatusParams] = useState<URLSearchParams | null>(null);
    const [deployed, setDeployed] = useState(false);
    const [strategies, setStrategies] = useState<any[]>([]);
    const [selectedStrategyId, setSelectedStrategyId] = useState<string | null>(null);

    // Kelly States
    const [winRate, setWinRate] = useState(0.55);
    const [winLoss, setWinLoss] = useState(1.5);
    const [kellyResult, setKellyResult] = useState<KellyResult | null>(null);

    // Optimizer States
    const [tickers, setTickers] = useState('AAPL,MSFT,GOOGL,AMZN,META,NVDA');
    const [objective, setObjective] = useState('sharpe');
    const [optResult, setOptResult] = useState<OptimizationResult | null>(null);

    // Monte Carlo States
    const [initialCap, setInitialCap] = useState(100000);
    const [expRet, setExpRet] = useState(0.12);
    const [vol, setVol] = useState(0.18);
    const [mcResult, setMcResult] = useState<MonteCarloResult | null>(null);

    // Auto-load Strategy
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        setStatusParams(params);
        fetchStrategies();
        const sId = params.get('strategy_id');
        if (sId) {
            setSelectedStrategyId(sId);
            runStrategyLogic(sId);
        }
    }, [window.location.search]);

    const fetchStrategies = async () => {
        try { const res = await axios.get('/strategies'); setStrategies(res.data); } catch (e) { }
    };

    const runStrategyLogic = (sId: string) => {
        // Auto-switch to optimizer
        setActiveTab('optimizer');
        // Mock fetching strategy details
        // In prod this would come from /strategies/{id}
        if (sId.includes('TECH')) setTickers('AAPL,MSFT,NVDA,AMD,INTC,QCOM');
        else if (sId.includes('MOM')) setTickers('NVDA,META,LLY,AVGO,ANET');
        else if (sId.includes('VAL')) setTickers('JPM,XOM,CVX,BRK.B,UNH');
        else setTickers('SPY,QQQ,IWM,GLD,TLT');
    };

    const launchNexusTargeted = async () => {
        if (!optResult || !statusParams?.get('strategy_id')) return;

        try {
            await axios.post('/nexus/run', {
                strategy_id: statusParams.get('strategy_id'),
                weights: optResult.weights,
                metrics: optResult.portfolio_metrics
            });
            setDeployed(true);
        } catch (e) {
            console.error("Deployment failed", e);
            alert("Failed to deploy to Nexus");
        }
    };

    // Calculations
    const calculateKelly = async () => {
        setLoading(true);
        try {
            const res = await axios.post('/intelligence/kelly', {
                win_rate: winRate,
                win_loss_ratio: winLoss
            });
            setKellyResult(res.data);
        } catch (e) {
            console.error(e);
        }
        setLoading(false);
    };

    const runOptimizer = async () => {
        setLoading(true);
        try {
            const res = await axios.post('/intelligence/optimize', {
                tickers: tickers.split(',').map(t => t.trim().toUpperCase()),
                objective
            });
            setOptResult(res.data);
        } catch (e) {
            console.error(e);
        }
        setLoading(false);
    };

    const runMonteCarlo = async () => {
        setLoading(true);
        try {
            const res = await axios.post('/intelligence/monte-carlo', {
                initial_capital: initialCap,
                expected_return: expRet,
                volatility: vol,
                n_simulations: 1000,
                n_days: 252
            });
            setMcResult(res.data);
        } catch (e) {
            console.error(e);
        }
        setLoading(false);
    };

    return (
        <div className="p-6 h-full flex flex-col">
            <header className="flex items-center gap-3 mb-8">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/30 to-blue-500/30 flex items-center justify-center border border-purple-500/30">
                    <Brain size={24} className="text-purple-400" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-blue-400">
                        Deep Portfolio Intelligence
                    </h1>
                    <p className="text-slate-400 mt-1">Deep learning optimization and Kelly Criterion sizing</p>
                </div>
                {activeTab === 'optimizer' && (
                    <div className="flex items-center gap-3">
                        <span className="text-slate-400 text-sm">Target Strategy:</span>
                        <select
                            className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-cyan-500"
                            value={selectedStrategyId || ''}
                            onChange={(e) => {
                                setSelectedStrategyId(e.target.value);
                                runStrategyLogic(e.target.value);
                            }}
                        >
                            <option value="">Manual Input</option>
                            {strategies.map(s => (
                                <option key={s.strategy_id} value={s.strategy_id}>{s.name}</option>
                            ))}
                        </select>
                    </div>
                )}
            </header>

            {/* Sub Tabs */}
            <div className="flex gap-4 mb-8">
                {[
                    { id: 'kelly', label: 'Kelly Criterion', icon: Target, desc: 'Optimal Sizing' },
                    { id: 'optimizer', label: 'Markowitz Optimizer', icon: PieChart, desc: 'Efficient Frontier' },
                    { id: 'montecarlo', label: 'Monte Carlo', icon: Activity, desc: 'Stress Testing' },
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as IntelTab)}
                        className={`flex-1 p-4 rounded-xl border text-left transition-all ${activeTab === tab.id
                            ? 'bg-purple-500/10 border-purple-500/50 ring-1 ring-purple-500/30'
                            : 'bg-[#1a1f26] border-slate-700 hover:border-slate-600'
                            }`}
                    >
                        <div className="flex items-center gap-2 mb-1">
                            <tab.icon size={18} className={activeTab === tab.id ? 'text-purple-400' : 'text-slate-400'} />
                            <span className={`font-bold ${activeTab === tab.id ? 'text-slate-100' : 'text-slate-400'}`}>{tab.label}</span>
                        </div>
                        <p className="text-xs text-slate-500">{tab.desc}</p>
                    </button>
                ))}
            </div>

            <div className="flex-1 grid grid-cols-12 gap-6 overflow-hidden">
                {/* Inputs Area */}
                <div className="col-span-4 space-y-6 overflow-auto pr-2">
                    {activeTab === 'kelly' && (
                        <div className="bg-[#1a1f26] rounded-xl border border-slate-700 p-6 space-y-6">
                            <h3 className="text-sm font-medium text-slate-300">Kelly Configuration</h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs text-slate-500 mb-2 uppercase">Strategy Win Rate ({Math.round(winRate * 100)}%)</label>
                                    <input
                                        type="range" min="0.3" max="0.9" step="0.01"
                                        value={winRate} onChange={(e) => setWinRate(parseFloat(e.target.value))}
                                        className="w-full accent-purple-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-500 mb-2 uppercase">Win/Loss Ratio ({winLoss}:1)</label>
                                    <input
                                        type="range" min="0.5" max="5.0" step="0.1"
                                        value={winLoss} onChange={(e) => setWinLoss(parseFloat(e.target.value))}
                                        className="w-full accent-blue-500"
                                    />
                                </div>
                                <button
                                    onClick={calculateKelly}
                                    disabled={loading}
                                    className="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-bold hover:shadow-[0_0_20px_rgba(147,51,234,0.3)] transition-all flex items-center justify-center gap-2"
                                >
                                    {loading ? <Zap size={18} className="animate-spin" /> : <Brain size={18} />}
                                    Calculate Optimum size
                                </button>
                            </div>
                        </div>
                    )}

                    {activeTab === 'optimizer' && (
                        <div className="bg-[#1a1f26] rounded-xl border border-slate-700 p-6 space-y-6">
                            <h3 className="text-sm font-medium text-slate-300">Optimizer Parameters</h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs text-slate-500 mb-1 uppercase">Assets (Tickers)</label>
                                    <textarea
                                        value={tickers} onChange={(e) => setTickers(e.target.value)}
                                        className="w-full bg-[#11161d] border border-slate-700 rounded p-2 text-sm text-cyan-400 font-mono"
                                        rows={3}
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-500 mb-1 uppercase">Objective</label>
                                    <select
                                        value={objective} onChange={(e) => setObjective(e.target.value)}
                                        className="w-full bg-[#11161d] border border-slate-700 rounded p-2 text-sm text-slate-100"
                                    >
                                        <option value="sharpe">Maximize Sharpe Ratio</option>
                                        <option value="min_vol">Minimize Volatility</option>
                                    </select>
                                </div>
                                <button
                                    onClick={runOptimizer}
                                    disabled={loading}
                                    className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg font-bold transition-all flex items-center justify-center gap-2"
                                >
                                    {loading ? <Zap size={18} className="animate-spin" /> : <PieChart size={18} />}
                                    Solve Efficient Frontier
                                </button>
                            </div>
                        </div>
                    )}

                    {activeTab === 'montecarlo' && (
                        <div className="bg-[#1a1f26] rounded-xl border border-slate-700 p-6 space-y-6">
                            <h3 className="text-sm font-medium text-slate-300">Simulation Variables</h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs text-slate-500 mb-1 uppercase">Initial Capital ($)</label>
                                    <input
                                        type="number" value={initialCap} onChange={(e) => setInitialCap(parseInt(e.target.value))}
                                        className="w-full bg-[#11161d] border border-slate-700 rounded p-2 text-sm text-slate-100 font-mono"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-500 mb-1 uppercase">Exp. Annual Return (%)</label>
                                    <input
                                        type="number" step="0.01" value={expRet} onChange={(e) => setExpRet(parseFloat(e.target.value))}
                                        className="w-full bg-[#11161d] border border-slate-700 rounded p-2 text-sm text-green-400 font-mono"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-500 mb-1 uppercase">Annual Volatility (%)</label>
                                    <input
                                        type="number" step="0.01" value={vol} onChange={(e) => setVol(parseFloat(e.target.value))}
                                        className="w-full bg-[#11161d] border border-slate-700 rounded p-2 text-sm text-red-400 font-mono"
                                    />
                                </div>
                                <button
                                    onClick={runMonteCarlo}
                                    disabled={loading}
                                    className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-bold transition-all flex items-center justify-center gap-2"
                                >
                                    {loading ? <Zap size={18} className="animate-spin" /> : <Activity size={18} />}
                                    Launch 1,000 Sim Path
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Results Display Area */}
                <div className="col-span-8 overflow-auto">
                    {!loading && !kellyResult && !optResult && !mcResult && (
                        <div className="h-full flex flex-col items-center justify-center text-slate-600 border-2 border-dashed border-slate-800 rounded-2xl">
                            <Brain size={48} className="mb-4 opacity-20" />
                            <p>Select a model and configure variables to begin analysis.</p>
                        </div>
                    )}

                    {loading && (
                        <div className="h-full flex flex-col items-center justify-center text-slate-500">
                            <div className="relative w-16 h-16 mb-4">
                                <div className="absolute inset-0 border-4 border-purple-500/20 rounded-full" />
                                <div className="absolute inset-0 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
                            </div>
                            <p className="animate-pulse">Solving mathematical model...</p>
                        </div>
                    )}

                    {/* Kelly Results View */}
                    {activeTab === 'kelly' && kellyResult && !loading && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                            <div className="grid grid-cols-2 gap-6">
                                <div className="bg-[#1a1f26] rounded-xl border border-slate-700 p-6 flex flex-col items-center text-center">
                                    <div className="text-xs text-slate-500 mb-2 uppercase">Full Kelly Fraction</div>
                                    <div className="text-5xl font-black text-purple-400">{(kellyResult.kelly_fraction * 100).toFixed(1)}%</div>
                                    <p className="text-xs text-slate-500 mt-2">Theoretical maximum sizing for growth.</p>
                                </div>
                                <div className="bg-[#1a1f26] rounded-xl border border-purple-500/30 p-6 flex flex-col items-center text-center ring-2 ring-purple-500/20">
                                    <div className="text-xs text-slate-500 mb-2 uppercase">Half Kelly (Recommended)</div>
                                    <div className="text-5xl font-black text-green-400">{(kellyResult.fraction_recommended * 100).toFixed(1)}%</div>
                                    <p className="text-xs text-slate-500 mt-2">Optimized for risk-adjusted CAGR.</p>
                                </div>
                            </div>
                            <div className="bg-slate-800/30 rounded-xl p-6 border border-slate-700">
                                <div className="flex items-center gap-2 text-cyan-400 mb-2">
                                    <Info size={16} />
                                    <span className="text-sm font-bold">Model Interpretation</span>
                                </div>
                                <p className="text-slate-300 text-sm italic">{kellyResult.interpretation}</p>
                                <div className="mt-4 flex gap-4">
                                    <div className={`flex-1 p-3 rounded bg-slate-800 border ${winRate > 0.5 ? 'border-green-500/20' : 'border-red-500/20'}`}>
                                        <div className="text-[10px] text-slate-500 uppercase">Probability of edge</div>
                                        <div className="text-sm font-bold text-slate-200">{(winRate * 100).toFixed(0)}% Mean Win Rate</div>
                                    </div>
                                    <div className="flex-1 p-3 rounded bg-slate-800 border border-blue-500/20">
                                        <div className="text-[10px] text-slate-500 uppercase">Magnitude of edge</div>
                                        <div className="text-sm font-bold text-slate-200">{winLoss}x Reward/Risk</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Optimizer Results View */}
                    {activeTab === 'optimizer' && optResult && !loading && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                            <div className="grid grid-cols-3 gap-4">
                                <div className="bg-[#1a1f26] p-4 rounded-xl border border-slate-700">
                                    <div className="text-[10px] text-slate-500 uppercase">Exp. Return</div>
                                    <div className="text-xl font-bold text-green-400">{(optResult.portfolio_metrics.expected_return * 100).toFixed(2)}%</div>
                                </div>
                                <div className="bg-[#1a1f26] p-4 rounded-xl border border-slate-700">
                                    <div className="text-[10px] text-slate-500 uppercase">Portfolio Vol</div>
                                    <div className="text-xl font-bold text-red-400">{(optResult.portfolio_metrics.volatility * 100).toFixed(2)}%</div>
                                </div>
                                <div className="bg-[#1a1f26] p-4 rounded-xl border border-slate-700">
                                    <div className="text-[10px] text-slate-500 uppercase">Sharpe Ratio</div>
                                    <div className="text-xl font-bold text-cyan-400">{optResult.portfolio_metrics.sharpe_ratio.toFixed(2)}</div>
                                </div>
                            </div>

                            <div className="bg-[#1a1f26] rounded-xl border border-slate-700 overflow-hidden">
                                <header className="p-4 bg-slate-800/30 border-b border-slate-700 flex justify-between items-center">
                                    <span className="text-xs font-bold uppercase text-slate-400">Allocations</span>
                                    <span className="text-[10px] py-0.5 px-2 bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30">Optimized</span>
                                </header>
                                <div className="divide-y divide-slate-800">
                                    {optResult.weights.map(w => (
                                        <div key={w.ticker} className="p-4 flex items-center gap-4">
                                            <div className="w-12 font-mono font-bold text-slate-200">{w.ticker}</div>
                                            <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-emerald-500 to-teal-500"
                                                    style={{ width: `${w.weight * 100}%` }}
                                                />
                                            </div>
                                            <div className="w-16 text-right font-mono text-cyan-400 text-sm">{(w.weight * 100).toFixed(2)}%</div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Targeted Deployment CTA */}
                            {statusParams?.get('strategy_id') && (
                                <div className="mt-6 p-6 bg-gradient-to-r from-cyan-900/40 to-blue-900/40 border border-cyan-500/30 rounded-xl relative overflow-hidden">
                                    <div className="absolute top-0 right-0 p-4 opacity-10">
                                        <Share2 size={120} />
                                    </div>
                                    <div className="relative z-10">
                                        <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                                            <RocketIcon />
                                            Deploy Targeted Alpha
                                        </h3>
                                        <p className="text-slate-300 text-sm mb-4 max-w-lg">
                                            You have optimized the <strong>{statusParams.get('strategy_id')}</strong> strategy.
                                            Deploy these exact weights to the Nexus Orchestrator for automated execution.
                                        </p>

                                        {deployed ? (
                                            <div className="flex items-center gap-2 text-green-400 font-bold bg-green-500/10 p-3 rounded border border-green-500/20 w-fit">
                                                <Zap size={20} className="fill-current" />
                                                Strategy Deployed to Nexus Logic Engine.
                                            </div>
                                        ) : (
                                            <button
                                                onClick={launchNexusTargeted}
                                                className="px-6 py-3 bg-cyan-500 hover:bg-cyan-400 text-black font-bold rounded shadow-lg shadow-cyan-500/20 transition-all flex items-center gap-2"
                                            >
                                                <Play size={20} className="fill-current" />
                                                DEPLOY TO NEXUS
                                            </button>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Monte Carlo Results View */}
                    {activeTab === 'montecarlo' && mcResult && !loading && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                            <div className="bg-[#1a1f26] border border-slate-700 rounded-xl p-6">
                                <h3 className="text-sm font-medium text-slate-300 mb-6 flex items-center justify-between">
                                    <span>Outcome Distribution (1 Year Horizon)</span>
                                    <span className={`text-xs px-2 py-1 rounded bg-slate-800 border ${mcResult.summary.prob_loss > 40 ? 'text-red-400 border-red-500/30' : 'text-green-400 border-green-500/30'}`}>
                                        Prob. of Loss: {mcResult.summary.prob_loss}%
                                    </span>
                                </h3>

                                <div className="grid grid-cols-5 gap-4">
                                    <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700">
                                        <div className="text-[10px] text-slate-500 mb-1">BEST (P95)</div>
                                        <div className="text-sm font-bold text-green-400">${mcResult.summary.p95.toLocaleString()}</div>
                                    </div>
                                    <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700">
                                        <div className="text-[10px] text-slate-500 mb-1">AVERAGE</div>
                                        <div className="text-sm font-bold text-slate-200">${mcResult.summary.mean.toLocaleString()}</div>
                                    </div>
                                    <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700">
                                        <div className="text-[10px] text-slate-500 mb-1">MEDIAN</div>
                                        <div className="text-sm font-bold text-slate-200">${mcResult.summary.median.toLocaleString()}</div>
                                    </div>
                                    <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700">
                                        <div className="text-[10px] text-slate-500 mb-1">WORST (P5)</div>
                                        <div className="text-sm font-bold text-red-400">${mcResult.summary.p5.toLocaleString()}</div>
                                    </div>
                                    <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700">
                                        <div className="text-[10px] text-slate-500 mb-1">VOLATILITY ($)</div>
                                        <div className="text-sm font-bold text-cyan-400">${mcResult.summary.std.toLocaleString()}</div>
                                    </div>
                                </div>

                                <div className="mt-8 flex gap-3 text-xs text-slate-500 italic">
                                    <AlertTriangle size={14} className="text-amber-500 shrink-0" />
                                    <span>Note: Results are based on 1,000 geometric brownian motion simulations. Actual market fat-tails may increase probability of extreme loss.</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
