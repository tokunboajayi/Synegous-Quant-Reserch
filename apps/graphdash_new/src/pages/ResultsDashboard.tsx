import { useEffect, useState } from 'react';
import axios from 'axios';
import {
    Download, BarChart2, PieChart, TrendingUp, TrendingDown,
    CheckCircle, XCircle, AlertTriangle, FileText, Layers,
    RefreshCw, Calendar, Target, Activity, ArrowRight, LayoutDashboard
} from 'lucide-react';
import { Link } from 'react-router-dom';

// Types
interface FactorAttribution {
    factor: string;
    contribution: number;
    exposure: number;
    return_contribution: number;
}

interface SectorAttribution {
    sector: string;
    pnl: number;
    weight: number;
    return_pct: number;
    contribution: number;
}

interface TickerAttribution {
    ticker: string;
    pnl: number;
    trades: number;
    win_rate: number;
    avg_trade: number;
}

interface StatTest {
    test_name: string;
    statistic: number;
    p_value: number;
    significant: boolean;
    interpretation: string;
}

interface PeriodBreakdown {
    period: string;
    return_pct: number;
    alpha: number;
    sharpe: number;
    max_drawdown: number;
}

interface RunSummary {
    run_id: string;
    gate_decision?: string;
    n_days: number;
    n_tickers: number;
    n_orders: number;
}

type Tab = 'attribution' | 'statistics' | 'breakdown' | 'pipeline';

export const ResultsDashboard = () => {
    const [activeTab, setActiveTab] = useState<Tab>('attribution');
    const [loading, setLoading] = useState(false);

    // Data states
    const [factorAttr, setFactorAttr] = useState<FactorAttribution[]>([]);
    const [sectorAttr, setSectorAttr] = useState<SectorAttribution[]>([]);
    const [tickerAttr, setTickerAttr] = useState<TickerAttribution[]>([]);
    const [tests, setTests] = useState<StatTest[]>([]);
    const [breakdown, setBreakdown] = useState<PeriodBreakdown[]>([]);
    const [summary, setSummary] = useState<any>(null);
    const [runs, setRuns] = useState<RunSummary[]>([]);

    // Load data
    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [factorRes, sectorRes, tickerRes, testRes, breakdownRes, summaryRes, runsRes] = await Promise.all([
                axios.get('/analytics/attribution/factor'),
                axios.get('/analytics/attribution/sector'),
                axios.get('/analytics/attribution/ticker'),
                axios.get('/analytics/statistics'),
                axios.get('/analytics/breakdown'),
                axios.get('/analytics/summary'),
                axios.get('/graphdash/runs')
            ]);

            setFactorAttr(factorRes.data.attribution);
            setSectorAttr(sectorRes.data.sectors);
            setTickerAttr(tickerRes.data.tickers);
            setTests(testRes.data.tests);
            setBreakdown(breakdownRes.data.periods);
            setSummary(summaryRes.data);
            setRuns(runsRes.data.runs || []);
        } catch (e) {
            console.error('Failed to load analytics', e);
        }
        setLoading(false);
    };

    // Export functions
    const exportCSV = async (type: string) => {
        window.open(`/analytics/export/${type}/csv`, '_blank');
    };

    const exportJSON = async () => {
        window.open('/analytics/export/full/json', '_blank');
    };

    // P&L color
    const getPnLColor = (value: number) => value >= 0 ? 'text-green-400' : 'text-red-400';
    const getPnLBg = (value: number) => value >= 0 ? 'bg-green-500/20' : 'bg-red-500/20';

    return (
        <div className="p-6 h-full flex flex-col">
            {/* Header */}
            <header className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500/30 to-emerald-500/30 flex items-center justify-center border border-green-500/30">
                        <BarChart2 size={24} className="text-green-400" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-slate-100">Results Dashboard</h1>
                        <p className="text-slate-500 text-sm">P&L attribution, statistical tests, and performance analysis</p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={loadData}
                        className="flex items-center gap-2 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-300 hover:bg-slate-700"
                    >
                        <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                        Refresh
                    </button>
                    <button
                        onClick={() => exportCSV('attribution')}
                        className="flex items-center gap-2 px-3 py-2 bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded-lg text-sm hover:bg-cyan-500/30"
                    >
                        <Download size={14} />
                        Export CSV
                    </button>
                    <button
                        onClick={exportJSON}
                        className="flex items-center gap-2 px-3 py-2 bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded-lg text-sm hover:bg-purple-500/30"
                    >
                        <FileText size={14} />
                        Full Report
                    </button>
                </div>
            </header>

            {/* Summary Cards */}
            {summary && (
                <div className="grid grid-cols-5 gap-4 mb-6">
                    <div className="bg-[#1a1f26] rounded-xl border border-slate-700 p-4">
                        <div className="text-xs text-slate-500 mb-1">Total P&L</div>
                        <div className={`text-2xl font-bold ${getPnLColor(summary.key_insights.total_pnl)}`}>
                            ${summary.key_insights.total_pnl.toLocaleString()}
                        </div>
                    </div>
                    <div className="bg-[#1a1f26] rounded-xl border border-slate-700 p-4">
                        <div className="text-xs text-slate-500 mb-1">YTD Return</div>
                        <div className={`text-2xl font-bold ${getPnLColor(summary.quick_stats.ytd_return)}`}>
                            {summary.quick_stats.ytd_return > 0 ? '+' : ''}{summary.quick_stats.ytd_return}%
                        </div>
                    </div>
                    <div className="bg-[#1a1f26] rounded-xl border border-slate-700 p-4">
                        <div className="text-xs text-slate-500 mb-1">Sharpe Ratio</div>
                        <div className="text-2xl font-bold text-cyan-400">{summary.quick_stats.sharpe}</div>
                    </div>
                    <div className="bg-[#1a1f26] rounded-xl border border-slate-700 p-4">
                        <div className="text-xs text-slate-500 mb-1">Alpha</div>
                        <div className={`text-2xl font-bold ${getPnLColor(summary.quick_stats.alpha)}`}>
                            {summary.quick_stats.alpha > 0 ? '+' : ''}{summary.quick_stats.alpha}%
                        </div>
                    </div>
                    <div className="bg-[#1a1f26] rounded-xl border border-slate-700 p-4">
                        <div className="text-xs text-slate-500 mb-1">Max Drawdown</div>
                        <div className="text-2xl font-bold text-red-400">{summary.quick_stats.max_drawdown}%</div>
                    </div>
                </div>
            )}

            {/* Tabs */}
            <div className="flex gap-2 mb-6 border-b border-slate-800 pb-4">
                {[
                    { id: 'attribution', label: 'P&L Attribution', icon: PieChart },
                    { id: 'statistics', label: 'Statistical Tests', icon: Activity },
                    { id: 'breakdown', label: 'Period Breakdown', icon: Calendar },
                    { id: 'pipeline', label: 'Pipeline History', icon: LayoutDashboard },
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as Tab)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === tab.id
                            ? 'bg-green-500/20 text-green-400 border border-green-500/30'
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
                    <div className="text-center py-12 text-slate-500">Loading analytics...</div>
                ) : (
                    <>
                        {/* Attribution Tab */}
                        {activeTab === 'attribution' && (
                            <div className="grid grid-cols-2 gap-6">
                                {/* Factor Attribution */}
                                <div className="bg-[#1a1f26] rounded-xl border border-slate-700 p-4">
                                    <h3 className="text-sm font-medium text-slate-300 mb-4 flex items-center gap-2">
                                        <Layers size={16} className="text-purple-400" />
                                        Factor Attribution
                                    </h3>
                                    <div className="space-y-3">
                                        {factorAttr.map(f => (
                                            <div key={f.factor} className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <div className={`w-2 h-2 rounded-full ${f.return_contribution >= 0 ? 'bg-green-500' : 'bg-red-500'}`} />
                                                    <span className="text-sm text-slate-300">{f.factor}</span>
                                                </div>
                                                <div className="flex items-center gap-4 text-sm">
                                                    <span className="text-slate-500">β: {f.exposure.toFixed(2)}</span>
                                                    <span className={getPnLColor(f.return_contribution)}>
                                                        {f.return_contribution > 0 ? '+' : ''}{f.return_contribution}%
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Sector Attribution */}
                                <div className="bg-[#1a1f26] rounded-xl border border-slate-700 p-4">
                                    <h3 className="text-sm font-medium text-slate-300 mb-4 flex items-center gap-2">
                                        <PieChart size={16} className="text-cyan-400" />
                                        Sector P&L
                                    </h3>
                                    <div className="space-y-2 max-h-64 overflow-auto">
                                        {sectorAttr.slice(0, 8).map(s => (
                                            <div key={s.sector} className="flex items-center justify-between p-2 rounded bg-slate-800/30">
                                                <span className="text-sm text-slate-300">{s.sector}</span>
                                                <div className="flex items-center gap-3">
                                                    <span className="text-xs text-slate-500">{s.contribution.toFixed(1)}%</span>
                                                    <span className={`text-sm font-medium ${getPnLColor(s.pnl)}`}>
                                                        ${s.pnl.toLocaleString()}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Ticker Attribution */}
                                <div className="col-span-2 bg-[#1a1f26] rounded-xl border border-slate-700 p-4">
                                    <h3 className="text-sm font-medium text-slate-300 mb-4 flex items-center gap-2">
                                        <Target size={16} className="text-green-400" />
                                        Top/Bottom Performers
                                    </h3>
                                    <div className="grid grid-cols-2 gap-4">
                                        {/* Winners */}
                                        <div>
                                            <div className="text-xs text-green-400 mb-2 uppercase">Winners</div>
                                            <div className="space-y-1">
                                                {tickerAttr.filter(t => t.pnl > 0).slice(0, 5).map(t => (
                                                    <div key={t.ticker} className="flex items-center justify-between p-2 rounded bg-green-500/10 border border-green-500/20">
                                                        <div className="flex items-center gap-2">
                                                            <TrendingUp size={14} className="text-green-400" />
                                                            <span className="font-medium text-slate-200">{t.ticker}</span>
                                                        </div>
                                                        <span className="text-green-400 font-medium">+${t.pnl.toLocaleString()}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                        {/* Losers */}
                                        <div>
                                            <div className="text-xs text-red-400 mb-2 uppercase">Losers</div>
                                            <div className="space-y-1">
                                                {tickerAttr.filter(t => t.pnl < 0).slice(-5).reverse().map(t => (
                                                    <div key={t.ticker} className="flex items-center justify-between p-2 rounded bg-red-500/10 border border-red-500/20">
                                                        <div className="flex items-center gap-2">
                                                            <TrendingDown size={14} className="text-red-400" />
                                                            <span className="font-medium text-slate-200">{t.ticker}</span>
                                                        </div>
                                                        <span className="text-red-400 font-medium">${t.pnl.toLocaleString()}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Statistics Tab */}
                        {activeTab === 'statistics' && (
                            <div className="space-y-4">
                                <div className="bg-[#1a1f26] rounded-xl border border-slate-700 p-4">
                                    <h3 className="text-sm font-medium text-slate-300 mb-4">Statistical Significance Tests</h3>
                                    <div className="space-y-3">
                                        {tests.map((test, i) => (
                                            <div key={i} className={`p-4 rounded-lg border ${test.significant ? 'bg-green-500/10 border-green-500/30' : 'bg-slate-800/30 border-slate-700'}`}>
                                                <div className="flex items-center justify-between mb-2">
                                                    <div className="flex items-center gap-2">
                                                        {test.significant ? (
                                                            <CheckCircle size={16} className="text-green-400" />
                                                        ) : (
                                                            <XCircle size={16} className="text-slate-500" />
                                                        )}
                                                        <span className="font-medium text-slate-200">{test.test_name}</span>
                                                    </div>
                                                    <div className="flex items-center gap-4 text-sm">
                                                        <span className="text-slate-400">Stat: {test.statistic}</span>
                                                        <span className={test.p_value < 0.05 ? 'text-green-400' : 'text-slate-500'}>
                                                            p = {test.p_value}
                                                        </span>
                                                    </div>
                                                </div>
                                                <p className="text-xs text-slate-500">{test.interpretation}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Breakdown Tab */}
                        {activeTab === 'breakdown' && (
                            <div className="bg-[#1a1f26] rounded-xl border border-slate-700 p-4">
                                <h3 className="text-sm font-medium text-slate-300 mb-4">Performance by Period</h3>
                                <table className="w-full">
                                    <thead>
                                        <tr className="text-xs text-slate-500 uppercase border-b border-slate-700">
                                            <th className="text-left py-2">Period</th>
                                            <th className="text-right py-2">Return</th>
                                            <th className="text-right py-2">Alpha</th>
                                            <th className="text-right py-2">Sharpe</th>
                                            <th className="text-right py-2">Max DD</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {breakdown.map(p => (
                                            <tr key={p.period} className="border-b border-slate-800">
                                                <td className="py-3 text-slate-300">{p.period}</td>
                                                <td className={`py-3 text-right font-medium ${getPnLColor(p.return_pct)}`}>
                                                    {p.return_pct > 0 ? '+' : ''}{p.return_pct}%
                                                </td>
                                                <td className={`py-3 text-right ${getPnLColor(p.alpha)}`}>
                                                    {p.alpha > 0 ? '+' : ''}{p.alpha}%
                                                </td>
                                                <td className="py-3 text-right text-cyan-400">{p.sharpe}</td>
                                                <td className="py-3 text-right text-red-400">{p.max_drawdown}%</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}

                        {/* Pipeline History Tab */}
                        {activeTab === 'pipeline' && (
                            <div className="bg-[#1a1f26] border border-slate-700 rounded-xl overflow-hidden">
                                <div className="p-4 border-b border-slate-700 bg-slate-800/30">
                                    <h3 className="text-sm font-medium text-slate-200">Production Pipeline Runs</h3>
                                    <p className="text-xs text-slate-500">History of automated research and model training jobs.</p>
                                </div>
                                <table className="w-full text-left">
                                    <thead className="bg-[#0f1419] border-b border-slate-700 text-xs uppercase text-slate-500 font-medium">
                                        <tr>
                                            <th className="p-4">Run ID</th>
                                            <th className="p-4">Decision</th>
                                            <th className="p-4 text-right">Horizon</th>
                                            <th className="p-4 text-right">Universe</th>
                                            <th className="p-4 text-right">Orders</th>
                                            <th className="p-4"></th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-800">
                                        {runs.length === 0 ? (
                                            <tr>
                                                <td colSpan={6} className="p-8 text-center text-slate-500 text-sm">No pipeline runs available.</td>
                                            </tr>
                                        ) : (
                                            runs.map(run => (
                                                <tr key={run.run_id} className="hover:bg-slate-800/50 transition-colors">
                                                    <td className="p-4 font-mono text-cyan-400 font-bold">{run.run_id}</td>
                                                    <td className="p-4">
                                                        <span className={`px-2 py-1 rounded text-[10px] font-bold ${run.gate_decision === 'PROMOTED' ? 'bg-green-500/20 text-green-400' :
                                                            run.gate_decision === 'REJECTED' ? 'bg-red-500/20 text-red-400' :
                                                                'bg-slate-700 text-slate-300'
                                                            }`}>
                                                            {run.gate_decision || 'PENDING'}
                                                        </span>
                                                    </td>
                                                    <td className="p-4 text-right text-sm">{run.n_days}d</td>
                                                    <td className="p-4 text-right text-sm">{run.n_tickers}</td>
                                                    <td className="p-4 text-right text-sm">{run.n_orders.toLocaleString()}</td>
                                                    <td className="p-4 text-right">
                                                        <Link to={`/runs/${run.run_id}`} className="text-slate-400 hover:text-cyan-400 inline-block p-1 hover:bg-slate-700 rounded transition-colors">
                                                            <ArrowRight size={16} />
                                                        </Link>
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};
