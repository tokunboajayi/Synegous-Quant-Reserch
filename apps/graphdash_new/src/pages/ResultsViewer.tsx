import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import axios from 'axios';

interface RunSummary {
    run_id: string;
    gate_decision?: string;
    n_days: number;
    n_tickers: number;
    n_orders: number;
}

export const ResultsViewer = () => {
    const [runs, setRuns] = useState<RunSummary[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        axios.get('/graphdash/runs')
            .then(res => {
                setRuns(res.data.runs || []);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch runs", err);
                setLoading(false);
            });
    }, []);

    return (
        <div className="p-6 h-full flex flex-col">
            <header className="flex items-center gap-3 mb-8">
                <div className="w-10 h-10 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center">
                    {/* Icon Removed */}
                </div>
                <div>
                    <h1 className="text-2xl font-bold">Results Viewer</h1>
                    <p className="text-slate-500">Comparative analysis of research runs.</p>
                </div>
            </header>

            {loading ? (
                <div className="flex-1 flex items-center justify-center text-slate-500">Loading metrics...</div>
            ) : runs.length === 0 ? (
                <div className="flex-1 flex items-center justify-center text-slate-500">No runs available yet.</div>
            ) : (
                <div className="bg-[#1a1f26] border border-slate-700 rounded-xl overflow-hidden">
                    <table className="w-full text-left">
                        <thead className="bg-[#0f1419] border-b border-slate-700 text-xs uppercase text-slate-500 font-medium">
                            <tr>
                                <th className="p-4">Run ID</th>
                                <th className="p-4">Gate Decision</th>
                                <th className="p-4 text-right">Horizon (Days)</th>
                                <th className="p-4 text-right">Universe Size</th>
                                <th className="p-4 text-right">Orders Generated</th>
                                <th className="p-4"></th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {runs.map(run => (
                                <tr key={run.run_id} className="hover:bg-slate-800/50 transition-colors">
                                    <td className="p-4 font-mono text-cyan-400 font-bold">{run.run_id}</td>
                                    <td className="p-4">
                                        <span className={`px-2 py-1 rounded text-xs font-bold ${run.gate_decision === 'PROMOTED' ? 'bg-green-500/20 text-green-400' :
                                            run.gate_decision === 'REJECTED' ? 'bg-red-500/20 text-red-400' :
                                                'bg-slate-700 text-slate-300'
                                            }`}>
                                            {run.gate_decision || 'PENDING'}
                                        </span>
                                    </td>
                                    <td className="p-4 text-right">{run.n_days}</td>
                                    <td className="p-4 text-right">{run.n_tickers}</td>
                                    <td className="p-4 text-right">{run.n_orders.toLocaleString()}</td>
                                    <td className="p-4 text-right">
                                        <Link to={`/runs/${run.run_id}`} className="text-slate-400 hover:text-cyan-400 inline-block">
                                            <ArrowRight size={18} />
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};
