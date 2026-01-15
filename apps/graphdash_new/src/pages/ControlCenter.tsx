import { useState } from 'react';
import axios from 'axios';
import { Play } from 'lucide-react';
import type { JobParams } from '../types';

export const ControlCenter = () => {
    const [params, setParams] = useState<JobParams & { mnx_enabled: boolean, mode: 'EXECUTE' | 'TUNE' }>({
        tickers: ['SPY', 'AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA', 'JPM', 'V'],
        start_date: '2024-01-01',
        end_date: '2024-12-31',
        bar_size: '1m',
        strategies: ['TWAP', 'VWAP', 'POV', 'CVX'],
        participation_cap: 0.10,
        n_orders: 1000,
        mnx_enabled: true,
        mode: 'EXECUTE'
    });
    const [submitting, setSubmitting] = useState(false);
    const [message, setMessage] = useState('');

    const toggleUniverse = (useFull: boolean) => {
        if (useFull) {
            setParams({ ...params, tickers: ['UNIVERSE_FULL_STOOQ'] });
        } else {
            setParams({ ...params, tickers: ['SPY', 'AAPL', 'MSFT'] });
        }
    };

    const launchRun = async () => {
        setSubmitting(true);
        setMessage('');
        try {
            // Determine Job Type
            let jobType = 'FULL_RUN';
            if (params.mnx_enabled) {
                jobType = params.mode === 'TUNE' ? 'MNX_TUNE_MODEL' : 'FULL_RUN_MNX_NMIE';
            }

            const payload = { ...params, job_type: jobType };
            const res = await axios.post('/control/runs/create', payload);
            setMessage(`🚀 Run Created! ID: ${res.data.run_id}`);
        } catch (e: any) {
            setMessage(`Error: ${e.response?.data?.detail || e.message}`);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold mb-6 text-cyan-400 flex items-center gap-2">
                <Play className="fill-current" size={24} />
                Research Platform <span className="text-xs ml-2 px-2 py-0.5 rounded bg-cyan-900 text-cyan-200">Execution-Aware v3++</span>
            </h2>

            <div className="bg-[#1a1f26] border border-slate-700 rounded-xl p-6 shadow-2xl">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-semibold text-slate-200">Simulation Configuration</h3>

                    {/* Mode Switcher */}
                    <div className="flex bg-slate-900 rounded-lg p-1 border border-slate-700">
                        <button
                            onClick={() => setParams({ ...params, mode: 'EXECUTE' })}
                            className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${params.mode === 'EXECUTE'
                                ? 'bg-cyan-600 text-white shadow'
                                : 'text-slate-400 hover:text-slate-200'
                                }`}
                        >
                            Execute Strategy
                        </button>
                        <button
                            onClick={() => setParams({ ...params, mode: 'TUNE' })}
                            className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${params.mode === 'TUNE'
                                ? 'bg-purple-600 text-white shadow'
                                : 'text-slate-400 hover:text-slate-200'
                                }`}
                        >
                            Auto-Tune AI
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-6 mb-6">
                    <div>
                        <div className="flex justify-between items-center mb-2">
                            <label className="text-sm text-slate-400">Universe</label>
                            <div className="flex items-center gap-2 text-xs">
                                <label className="flex items-center gap-1 cursor-pointer text-cyan-400 hover:text-cyan-300">
                                    <input type="checkbox"
                                        checked={params.tickers[0] === 'UNIVERSE_FULL_STOOQ'}
                                        onChange={e => toggleUniverse(e.target.checked)}
                                        className="rounded bg-slate-800 border-slate-600 focus:ring-cyan-500"
                                    />
                                    Use Full Stooq (400+)
                                </label>
                            </div>
                        </div>
                        <textarea
                            className="w-full h-32 bg-[#0f1419] border border-slate-700 rounded p-3 text-sm font-mono text-slate-200 focus:border-cyan-500 outline-none"
                            value={params.tickers.join(', ')}
                            onChange={e => setParams({ ...params, tickers: e.target.value.split(',').map(s => s.trim()).filter(Boolean) })}
                            disabled={params.tickers[0] === 'UNIVERSE_FULL_STOOQ'}
                        />
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm text-slate-400 mb-2">Start Date</label>
                                <input type="date"
                                    className="w-full bg-[#0f1419] border border-slate-700 rounded p-2 text-sm text-slate-200"
                                    value={params.start_date}
                                    onChange={e => setParams({ ...params, start_date: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-2">End Date</label>
                                <input type="date"
                                    className="w-full bg-[#0f1419] border border-slate-700 rounded p-2 text-sm text-slate-200"
                                    value={params.end_date}
                                    onChange={e => setParams({ ...params, end_date: e.target.value })}
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm text-slate-400 mb-2">Simulated Orders</label>
                            <input type="number"
                                className="w-full bg-[#0f1419] border border-slate-700 rounded p-2 text-sm text-slate-200"
                                value={params.n_orders}
                                onChange={e => setParams({ ...params, n_orders: parseInt(e.target.value) })}
                            />
                        </div>
                    </div>
                </div>

                <div className="flex justify-between items-center gap-4 border-t border-slate-700 pt-6">
                    <div className="text-xs text-slate-500">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" checked={params.mnx_enabled}
                                onChange={e => setParams({ ...params, mnx_enabled: e.target.checked })}
                                className="rounded bg-slate-800 border-slate-600 text-cyan-600 focus:ring-cyan-500" />
                            <span>Enable MNX Alpha Module (Market-Neutral)</span>
                        </label>
                    </div>

                    <div className="flex items-center gap-4">
                        {message && <span className={`text-sm ${message.startsWith('Error') ? "text-red-400" : "text-green-400 font-bold"}`}>{message}</span>}
                        <button
                            onClick={launchRun}
                            disabled={submitting}
                            className={`px-6 py-2 bg-gradient-to-r text-white font-semibold rounded-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all
                                ${params.mode === 'TUNE' ? 'from-purple-600 to-indigo-600 hover:from-purple-500' : 'from-cyan-600 to-blue-600 hover:from-cyan-500'}
                            `}
                        >
                            {submitting ? 'Launching...' : (params.mode === 'TUNE' ? 'START AUTO-TUNING' : 'EXECUTE STRATEGY')}
                        </button>
                    </div>
                </div>
            </div>

            <div className="mt-8 p-4 bg-emerald-500/5 border border-emerald-500/20 rounded-lg text-emerald-400/80 text-sm flex gap-3">
                <div className="text-2xl">⚡</div>
                <div>
                    <strong>System Status:</strong> Execution-Aware Research Mode (Real Stooq Data).
                    <ul className="list-disc ml-5 mt-1 text-xs opacity-75">
                        <li><strong>Alpha Engine:</strong> Cross-Sectional Rank (LightGBM)</li>
                        <li><strong>Portfolio Guardrails:</strong> Dollar Neutral | 5% Cap | Cost-Gating (&gt;10bps)</li>
                        <li><strong>Execution Bridge:</strong> Connected (External Basket → Sim)</li>
                    </ul>
                </div>
            </div>
        </div>
    );
};

