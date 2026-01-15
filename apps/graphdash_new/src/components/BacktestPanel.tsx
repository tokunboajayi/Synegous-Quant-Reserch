import { useEffect, useState } from 'react';
import axios from 'axios';
import {
    Play, TrendingUp, TrendingDown, AlertTriangle, BarChart2,
    Calendar, DollarSign, Target, Percent, Clock, RefreshCw,
    ArrowUpRight, ArrowDownRight, Activity, Loader2
} from 'lucide-react';

interface BacktestMetrics {
    returns: {
        total_return: number;
        annualized_return: number;
        benchmark_return: number;
        alpha: number;
    };
    risk: {
        volatility: number;
        max_drawdown: number;
        max_drawdown_duration_days: number;
        var_95: number;
    };
    risk_adjusted: {
        sharpe_ratio: number;
        sortino_ratio: number;
        calmar_ratio: number;
        information_ratio: number;
    };
    trading: {
        total_trades: number;
        win_rate: number;
        profit_factor: number;
        avg_trade_return: number;
    };
    exposure: {
        beta: number;
        avg_exposure: number;
        turnover: number;
    };
}

interface BacktestResult {
    backtest_id: string;
    strategy_id: string;
    status: string;
    metrics?: BacktestMetrics;
    quick_metrics?: {
        total_return: string;
        sharpe_ratio: string;
        max_drawdown: string;
        win_rate: string;
    };
    error?: string;
}

interface EquityPoint {
    date: string;
    equity: number;
    return: number;
}

interface DrawdownPoint {
    date: string;
    drawdown: number;
}

interface BacktestPanelProps {
    strategyId?: string;
    strategyName?: string;
}

// Default tickers
const DEFAULT_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "WMT"];

export const BacktestPanel = ({ strategyId, strategyName }: BacktestPanelProps) => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<BacktestResult | null>(null);
    const [equityCurve, setEquityCurve] = useState<EquityPoint[]>([]);
    const [drawdownCurve, setDrawdownCurve] = useState<DrawdownPoint[]>([]);

    // Config
    const [config, setConfig] = useState({
        tickers: DEFAULT_TICKERS.join(', '),
        start_date: '2023-01-01',
        end_date: '2024-12-31',
        initial_capital: 100000,
        position_size: 5,
        max_positions: 20,
        transaction_cost_bps: 10,
    });

    const runBacktest = async () => {
        if (!strategyId) return;

        setLoading(true);
        setResult(null);
        setEquityCurve([]);
        setDrawdownCurve([]);

        try {
            // Run backtest
            const res = await axios.post('/backtest/run', {
                strategy_id: strategyId,
                tickers: config.tickers.split(',').map(t => t.trim()),
                start_date: config.start_date,
                end_date: config.end_date,
                initial_capital: config.initial_capital,
                position_size: config.position_size / 100,
                max_positions: config.max_positions,
                transaction_cost_bps: config.transaction_cost_bps,
            });

            if (res.data.status === 'completed') {
                // Fetch full results
                const fullRes = await axios.get(`/backtest/results/${res.data.backtest_id}`);
                setResult(fullRes.data);

                // Fetch equity curve
                const eqRes = await axios.get(`/backtest/results/${res.data.backtest_id}/equity`);
                setEquityCurve(eqRes.data.equity_curve || []);
                setDrawdownCurve(eqRes.data.drawdown_curve || []);
            } else {
                setResult(res.data);
            }
        } catch (e) {
            console.error('Backtest failed', e);
            setResult({ backtest_id: '', strategy_id: strategyId, status: 'failed', error: 'Network error' });
        }

        setLoading(false);
    };

    const runQuickTest = async () => {
        if (!strategyId) return;

        setLoading(true);
        try {
            const res = await axios.post(`/backtest/quick-test/${strategyId}`);
            setResult(res.data);

            if (res.data.status === 'completed') {
                const eqRes = await axios.get(`/backtest/results/${res.data.backtest_id}/equity`);
                setEquityCurve(eqRes.data.equity_curve || []);
                setDrawdownCurve(eqRes.data.drawdown_curve || []);
            }
        } catch (e) {
            console.error('Quick test failed', e);
        }
        setLoading(false);
    };

    // Mini chart component
    const MiniChart = ({ data, dataKey, color }: { data: any[]; dataKey: string; color: string }) => {
        if (data.length === 0) return <div className="h-24 flex items-center justify-center text-slate-600">No data</div>;

        const values = data.map(d => d[dataKey]);
        const min = Math.min(...values);
        const max = Math.max(...values);
        const range = max - min || 1;

        const points = data.map((d, i) => {
            const x = (i / (data.length - 1)) * 100;
            const y = 100 - ((d[dataKey] - min) / range) * 100;
            return `${x},${y}`;
        }).join(' ');

        return (
            <svg viewBox="0 0 100 100" className="w-full h-24" preserveAspectRatio="none">
                <polyline
                    fill="none"
                    stroke={color}
                    strokeWidth="1.5"
                    points={points}
                />
            </svg>
        );
    };

    // Metric card component
    const MetricCard = ({ label, value, subValue, icon: Icon, color, trend }: any) => (
        <div className="bg-slate-800/30 rounded-lg p-3 border border-slate-700/50">
            <div className="flex items-center gap-2 mb-1">
                <Icon size={14} className={color} />
                <span className="text-xs text-slate-500 uppercase">{label}</span>
            </div>
            <div className="flex items-baseline gap-2">
                <span className={`text-xl font-bold ${color}`}>{value}</span>
                {subValue && <span className="text-xs text-slate-500">{subValue}</span>}
            </div>
            {trend !== undefined && (
                <div className={`flex items-center gap-1 text-xs mt-1 ${trend >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {trend >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                    {Math.abs(trend).toFixed(1)}%
                </div>
            )}
        </div>
    );

    return (
        <div className="bg-[#1a1f26] border border-slate-700 rounded-xl overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-slate-700 flex items-center justify-between bg-slate-800/30">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                        <BarChart2 size={20} className="text-green-400" />
                    </div>
                    <div>
                        <h2 className="font-semibold text-slate-200">Backtest</h2>
                        <p className="text-xs text-slate-500">{strategyName || strategyId || 'Select a strategy'}</p>
                    </div>
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={runQuickTest}
                        disabled={!strategyId || loading}
                        className="px-3 py-1.5 bg-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-600 transition-colors disabled:opacity-50 flex items-center gap-1"
                    >
                        <RefreshCw size={14} />
                        Quick Test
                    </button>
                    <button
                        onClick={runBacktest}
                        disabled={!strategyId || loading}
                        className="px-4 py-1.5 bg-green-500/20 text-green-400 rounded-lg text-sm hover:bg-green-500/30 transition-colors disabled:opacity-50 flex items-center gap-2"
                    >
                        {loading ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
                        {loading ? 'Running...' : 'Run Backtest'}
                    </button>
                </div>
            </div>

            <div className="p-4">
                {/* Config Section */}
                <div className="grid grid-cols-4 gap-3 mb-4">
                    <div>
                        <label className="text-xs text-slate-500 mb-1 block">Start Date</label>
                        <input
                            type="date"
                            value={config.start_date}
                            onChange={e => setConfig({ ...config, start_date: e.target.value })}
                            className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-sm"
                        />
                    </div>
                    <div>
                        <label className="text-xs text-slate-500 mb-1 block">End Date</label>
                        <input
                            type="date"
                            value={config.end_date}
                            onChange={e => setConfig({ ...config, end_date: e.target.value })}
                            className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-sm"
                        />
                    </div>
                    <div>
                        <label className="text-xs text-slate-500 mb-1 block">Initial Capital</label>
                        <input
                            type="number"
                            value={config.initial_capital}
                            onChange={e => setConfig({ ...config, initial_capital: Number(e.target.value) })}
                            className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-sm"
                        />
                    </div>
                    <div>
                        <label className="text-xs text-slate-500 mb-1 block">Position Size (%)</label>
                        <input
                            type="number"
                            value={config.position_size}
                            onChange={e => setConfig({ ...config, position_size: Number(e.target.value) })}
                            className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-sm"
                        />
                    </div>
                </div>

                {/* Results */}
                {result && result.status === 'completed' && result.metrics && (
                    <>
                        {/* Key Metrics Grid */}
                        <div className="grid grid-cols-5 gap-3 mb-4">
                            <MetricCard
                                label="Total Return"
                                value={`${result.metrics.returns.total_return.toFixed(1)}%`}
                                icon={TrendingUp}
                                color={result.metrics.returns.total_return >= 0 ? 'text-green-400' : 'text-red-400'}
                            />
                            <MetricCard
                                label="Sharpe Ratio"
                                value={result.metrics.risk_adjusted.sharpe_ratio.toFixed(2)}
                                icon={Target}
                                color={result.metrics.risk_adjusted.sharpe_ratio >= 1 ? 'text-green-400' : 'text-yellow-400'}
                            />
                            <MetricCard
                                label="Max Drawdown"
                                value={`${result.metrics.risk.max_drawdown.toFixed(1)}%`}
                                icon={TrendingDown}
                                color="text-red-400"
                            />
                            <MetricCard
                                label="Win Rate"
                                value={`${result.metrics.trading.win_rate.toFixed(0)}%`}
                                icon={Percent}
                                color={result.metrics.trading.win_rate >= 50 ? 'text-green-400' : 'text-yellow-400'}
                            />
                            <MetricCard
                                label="Volatility"
                                value={`${result.metrics.risk.volatility.toFixed(1)}%`}
                                icon={Activity}
                                color="text-cyan-400"
                            />
                        </div>

                        {/* Charts */}
                        <div className="grid grid-cols-2 gap-4">
                            {/* Equity Curve */}
                            <div className="bg-slate-800/30 rounded-lg p-3 border border-slate-700/50">
                                <h3 className="text-xs text-slate-500 uppercase mb-2">Equity Curve</h3>
                                <MiniChart data={equityCurve} dataKey="equity" color="#22c55e" />
                                <div className="flex justify-between text-xs text-slate-600 mt-1">
                                    <span>{equityCurve[0]?.date}</span>
                                    <span>{equityCurve[equityCurve.length - 1]?.date}</span>
                                </div>
                            </div>

                            {/* Drawdown */}
                            <div className="bg-slate-800/30 rounded-lg p-3 border border-slate-700/50">
                                <h3 className="text-xs text-slate-500 uppercase mb-2">Drawdown</h3>
                                <MiniChart data={drawdownCurve} dataKey="drawdown" color="#ef4444" />
                                <div className="flex justify-between text-xs text-slate-600 mt-1">
                                    <span>0%</span>
                                    <span>{result.metrics.risk.max_drawdown.toFixed(1)}%</span>
                                </div>
                            </div>
                        </div>

                        {/* Additional Metrics */}
                        <div className="mt-4 grid grid-cols-4 gap-3 text-xs">
                            <div className="bg-slate-800/30 p-2 rounded">
                                <span className="text-slate-500">Sortino</span>
                                <span className="float-right text-slate-300">{result.metrics.risk_adjusted.sortino_ratio.toFixed(2)}</span>
                            </div>
                            <div className="bg-slate-800/30 p-2 rounded">
                                <span className="text-slate-500">Calmar</span>
                                <span className="float-right text-slate-300">{result.metrics.risk_adjusted.calmar_ratio.toFixed(2)}</span>
                            </div>
                            <div className="bg-slate-800/30 p-2 rounded">
                                <span className="text-slate-500">Profit Factor</span>
                                <span className="float-right text-slate-300">{result.metrics.trading.profit_factor.toFixed(2)}</span>
                            </div>
                            <div className="bg-slate-800/30 p-2 rounded">
                                <span className="text-slate-500">Total Trades</span>
                                <span className="float-right text-slate-300">{result.metrics.trading.total_trades}</span>
                            </div>
                        </div>
                    </>
                )}

                {/* Quick test results */}
                {result && result.quick_metrics && (
                    <div className="grid grid-cols-4 gap-3">
                        <MetricCard label="Return" value={result.quick_metrics.total_return} icon={TrendingUp} color="text-green-400" />
                        <MetricCard label="Sharpe" value={result.quick_metrics.sharpe_ratio} icon={Target} color="text-cyan-400" />
                        <MetricCard label="Max DD" value={result.quick_metrics.max_drawdown} icon={TrendingDown} color="text-red-400" />
                        <MetricCard label="Win Rate" value={result.quick_metrics.win_rate} icon={Percent} color="text-purple-400" />
                    </div>
                )}

                {/* Error state */}
                {result && result.status === 'failed' && (
                    <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
                        <AlertTriangle size={16} />
                        <span>{result.error || 'Backtest failed'}</span>
                    </div>
                )}

                {/* Empty state */}
                {!result && !loading && (
                    <div className="text-center py-8 text-slate-500">
                        <BarChart2 size={32} className="mx-auto mb-2 opacity-30" />
                        <p>Configure and run a backtest to see results</p>
                    </div>
                )}

                {/* Loading state */}
                {loading && (
                    <div className="text-center py-8 text-slate-500">
                        <Loader2 size={32} className="mx-auto mb-2 animate-spin" />
                        <p>Running backtest...</p>
                    </div>
                )}
            </div>
        </div>
    );
};
