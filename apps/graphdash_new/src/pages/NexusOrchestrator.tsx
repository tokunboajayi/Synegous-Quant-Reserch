import { useState, useEffect } from 'react';
import axios from 'axios';
import {
    Zap, Share2, Activity, Shield,
    Target, BarChart2, PieChart,
    ChevronRight, ArrowRight, Brain,
    Radar, Cpu, Rocket, CheckCircle2,
    Loader2, AlertCircle, RefreshCw,
    Network, Globe, Layers
} from 'lucide-react';

interface NexusStatus {
    status: 'IDLE' | 'RUNNING' | 'COMPLETED' | 'FAILED';
    current_stage: string;
    progress: number;
    has_last_run: boolean;
}

export const NexusOrchestrator = () => {
    const [status, setStatus] = useState<NexusStatus>({
        status: 'IDLE',
        current_stage: 'Nexus Idle',
        progress: 0,
        has_last_run: false
    });
    const [results, setResults] = useState<any>(null);
    const [polling, setPolling] = useState(false);
    const [strategies, setStrategies] = useState<any[]>([]);
    const [selectedStrategyId, setSelectedStrategyId] = useState<string | null>(null);

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        fetchStrategies();
        if (params.get('strategy_id')) {
            setSelectedStrategyId(params.get('strategy_id'));
        }

        fetchStatus();
        const interval = setInterval(fetchStatus, 2000);
        return () => clearInterval(interval);
    }, [window.location.search]);

    const fetchStrategies = async () => {
        try { const res = await axios.get('/strategies'); setStrategies(res.data); } catch (e) { }
    };

    const fetchStatus = async () => {
        try {
            const res = await axios.get('/nexus/status');
            setStatus(res.data);
            if (res.data.status === 'COMPLETED' && !results) {
                fetchResults();
            }
        } catch (e) {
            console.error(e);
        }
    };

    const fetchResults = async () => {
        try {
            const res = await axios.get('/nexus/results');
            setResults(res.data);
        } catch (e) {
            console.error(e);
        }
    };

    const launchNexus = async () => {
        try {
            await axios.post('/nexus/run', {
                strategy_override: selectedStrategyId
            });
            setResults(null);
            fetchStatus();
        } catch (e) {
            console.error(e);
        }
    };

    const stages = [
        { id: 1, name: 'Market Radar', icon: Radar, color: 'text-blue-400', threshold: 20 },
        { id: 2, name: 'Alpha Synthesis', icon: Cpu, color: 'text-purple-400', threshold: 40 },
        { id: 3, name: 'Stress Validation', icon: Shield, color: 'text-cyan-400', threshold: 60 },
        { id: 4, name: 'Intel Optimization', icon: Brain, color: 'text-indigo-400', threshold: 80 },
        { id: 5, name: 'Production Bridge', icon: Rocket, color: 'text-emerald-400', threshold: 100 },
    ];

    return (
        <div className="p-6 h-full flex flex-col bg-[#0f1419]">
            {/* Header Area */}
            <header className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-600 to-blue-600 flex items-center justify-center border border-cyan-400/30 shadow-[0_0_20px_rgba(6,182,212,0.2)]">
                        <Network size={32} className="text-white" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
                            SYNEGIOUS NEXUS
                            <span className="text-xs py-1 px-3 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-bold uppercase tracking-widest">
                                Autonomous Core
                            </span>
                        </h1>
                        <p className="text-slate-500 text-sm font-medium">DAMFRAPS Methodology: Dynamic Adaptive Multi-Factor Regime-Aligned Portfolio Synthesis</p>
                    </div>
                </div>

                {/* Strategy Selector */}
                <div className="flex items-center gap-3 bg-slate-800/50 p-2 rounded-lg border border-slate-700">
                    <span className="text-slate-400 text-sm font-medium">Execution Mode:</span>
                    <select
                        className="bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-cyan-500 min-w-[200px]"
                        value={selectedStrategyId || ''}
                        onChange={(e) => setSelectedStrategyId(e.target.value)}
                    >
                        <option value="">Global Alpha Synthesis (Auto)</option>
                        <optgroup label="Targeted Execution">
                            {strategies.map(s => (
                                <option key={s.strategy_id} value={s.strategy_id}>{s.name}</option>
                            ))}
                        </optgroup>
                    </select>
                </div>

                <div className="flex items-center gap-4">
                    <div className="text-right">
                        <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Nexus Status</div>
                        <div className={`flex items-center gap-2 font-bold ${status.status === 'RUNNING' ? 'text-cyan-400' :
                            status.status === 'COMPLETED' ? 'text-emerald-400' :
                                status.status === 'FAILED' ? 'text-red-400' : 'text-slate-400'
                            }`}>
                            {status.status === 'RUNNING' && <Loader2 size={14} className="animate-spin" />}
                            {status.status}
                        </div>
                    </div>

                    <button
                        onClick={launchNexus}
                        disabled={status.status === 'RUNNING'}
                        className={`px-8 py-3 rounded-xl font-black text-sm uppercase tracking-widest transition-all ${status.status === 'RUNNING'
                            ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                            : 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white hover:shadow-[0_0_30px_rgba(6,182,212,0.4)] active:scale-95 border border-cyan-400/20'
                            }`}
                    >
                        {status.status === 'RUNNING' ? 'Nexus Processing...' : 'Launch DAMFRAPS Loop'}
                    </button>
                </div>
            </header>

            {/* Loop Visualization */}
            <div className="bg-[#1a1f26] border border-slate-800 rounded-3xl p-10 mb-8 relative overflow-hidden group">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-500/20 to-transparent"></div>

                <div className="relative flex items-center justify-between">
                    {stages.map((stage, idx) => (
                        <div key={stage.id} className="flex items-center flex-1 last:flex-none">
                            <div className="flex flex-col items-center relative z-10">
                                <div className={`w-20 h-20 rounded-2xl flex items-center justify-center border-2 transition-all duration-500 ${status.progress >= stage.threshold
                                    ? `bg-slate-800 border-cyan-500 shadow-[0_0_30px_rgba(6,182,212,0.2)]`
                                    : `bg-slate-900 border-slate-800 opacity-40`
                                    }`}>
                                    <stage.icon size={32} className={status.progress >= stage.threshold ? stage.color : 'text-slate-600'} />

                                    {status.progress >= stage.threshold && status.status !== 'FAILED' && (
                                        <div className="absolute -top-2 -right-2 bg-emerald-500 rounded-full p-1 text-white shadow-lg animate-in zoom-in">
                                            <CheckCircle2 size={12} strokeWidth={4} />
                                        </div>
                                    )}
                                </div>
                                <span className={`mt-4 text-[10px] font-black uppercase tracking-tighter ${status.progress >= stage.threshold ? 'text-slate-200' : 'text-slate-600'
                                    }`}>
                                    {stage.name}
                                </span>
                            </div>

                            {idx < stages.length - 1 && (
                                <div className="flex-1 px-4 relative">
                                    <div className="h-1 bg-slate-800 rounded-full w-full"></div>
                                    <div
                                        className="absolute top-0 left-0 h-1 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all duration-1000 shadow-[0_0_10px_rgba(6,182,212,0.5)]"
                                        style={{ width: `${Math.max(0, Math.min(100, (status.progress - (idx * 20)) * 5))}%` }}
                                    ></div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                <div className="mt-12 flex flex-col items-center">
                    <div className="text-sm font-bold text-cyan-400 mb-2 uppercase tracking-widest animate-pulse">{status.current_stage}</div>
                    <div className="w-full max-w-2xl h-1.5 bg-slate-800 rounded-full overflow-hidden border border-slate-700/50">
                        <div
                            className="h-full bg-gradient-to-r from-cyan-500 via-blue-500 to-cyan-500 transition-all duration-500"
                            style={{ width: `${status.progress}%` }}
                        ></div>
                    </div>
                </div>
            </div>

            {/* Results Grid */}
            <div className="flex-1 grid grid-cols-12 gap-6 min-h-0">
                {/* Active Intelligence */}
                <div className="col-span-8 bg-[#1a1f26] border border-slate-800 rounded-3xl p-8 flex flex-col min-h-0">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            <Globe size={20} className="text-cyan-400" />
                            Loop Results Intelligence
                        </h3>
                        <div className="flex items-center gap-3">
                            <span className="flex items-center gap-1.5 text-[10px] py-1 px-2 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold uppercase tracking-wider">
                                <Activity size={10} className="animate-pulse" />
                                Live Market Feed
                            </span>
                            {results && (
                                <span className="text-[10px] font-mono text-slate-500 uppercase">{results.nexus_id}</span>
                            )}
                        </div>
                    </div>

                    {!results && status.status !== 'RUNNING' && (
                        <div className="flex-1 border-2 border-dashed border-slate-800 rounded-2xl flex flex-col items-center justify-center text-slate-600 text-center p-10">
                            <Zap size={48} className="mb-4 opacity-10" />
                            <p className="font-medium">No active synthesis found.</p>
                            <p className="text-xs max-w-xs mt-2 opacity-50">Launch the DAMFRAPS loop to begin autonomous market-strategy orchestration.</p>
                        </div>
                    )}

                    {status.status === 'RUNNING' && (
                        <div className="flex-1 flex flex-col items-center justify-center space-y-4">
                            <RefreshCw size={48} className="text-cyan-500 animate-spin opacity-40" />
                            <p className="text-sm font-bold text-slate-400 uppercase tracking-widest animate-pulse">Orchestrating Core Assets...</p>
                        </div>
                    )}

                    {results && (
                        <div className="flex-1 overflow-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div className="grid grid-cols-3 gap-6">
                                <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800">
                                    <label className="text-[10px] font-black text-slate-500 uppercase mb-2 block">Market Regime</label>
                                    <div className="text-2xl font-black text-white uppercase italic">{results.regime}</div>
                                </div>
                                <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800">
                                    <label className="text-[10px] font-black text-slate-500 uppercase mb-2 block">Portfolio Sizing</label>
                                    <div className="text-2xl font-black text-emerald-400">{(results.sizing_fraction * 100).toFixed(1)}% <span className="text-xs text-slate-600">Kelly</span></div>
                                </div>
                                <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800">
                                    <label className="text-[10px] font-black text-slate-500 uppercase mb-2 block">Exp. Returns</label>
                                    <div className="text-2xl font-black text-cyan-400">{(results.expected_metrics.expected_return * 100).toFixed(1)}% <span className="text-xs text-slate-600">MVO</span></div>
                                </div>
                            </div>

                            <div>
                                <h4 className="text-xs font-black text-slate-500 uppercase mb-4 tracking-widest">Regime-Aligned Strategy Candidates</h4>
                                <div className="flex flex-wrap gap-2">
                                    {results.strategy_candidates.map((s: string) => (
                                        <div key={s} className="px-4 py-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 text-xs font-bold">
                                            {s}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <h4 className="text-xs font-black text-slate-500 uppercase mb-4 tracking-widest">Optimized Portfolio Synthesis</h4>
                                <div className="space-y-3">
                                    {results.allocations.map((a: any) => (
                                        <div key={a.ticker} className="flex items-center gap-4">
                                            <div className="w-16 text-sm font-black text-slate-200">{a.ticker}</div>
                                            <div className="flex-1 h-3 bg-slate-900 rounded-full overflow-hidden p-0.5 border border-slate-800">
                                                <div
                                                    className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
                                                    style={{ width: `${a.weight * 100}%` }}
                                                />
                                            </div>
                                            <div className="w-16 text-right text-xs font-black text-cyan-500">{(a.weight * 100).toFixed(1)}%</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* System Logs */}
                <div className="col-span-4 bg-[#1a1f26] border border-slate-800 rounded-3xl p-8 flex flex-col min-h-0">
                    <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                        <Activity size={20} className="text-purple-400" />
                        System Analytics
                    </h3>

                    <div className="flex-1 bg-black/30 rounded-2xl border border-slate-800 p-4 font-mono text-[10px] space-y-2 overflow-auto scrollbar-hide">
                        <div className="text-slate-500">[NXS] Re-starting Autonomous Core...</div>
                        <div className="text-slate-500">[SYS] Syncing with Strategy API...</div>
                        <div className="text-slate-500">[SQL] Querying 115 strategy templates...</div>
                        <div className="text-cyan-400/70">[REG] Active Market Regime: {status.current_stage || 'Unknown'}</div>
                        <div className="text-purple-400/70">[OPT] Initializing Matrix MVO Solvers...</div>
                        <div className="text-emerald-400/70">[KEL] Applying 0.5f Kelly safety multiplier...</div>
                        <div className="text-blue-400/70 shadow-cyan-500/10">[NXS] Awaiting production bridge confirm...</div>
                    </div>

                    <div className="mt-6 pt-6 border-t border-slate-800 space-y-4">
                        <div className="flex justify-between items-center">
                            <span className="text-xs text-slate-500">Core Parallelism</span>
                            <span className="text-xs font-bold text-slate-100">8 Logical Cores</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-xs text-slate-500">Latency Target</span>
                            <span className="text-xs font-bold text-emerald-400">{'< 2.5ms'}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
