import { useEffect, useState } from 'react';
import axios from 'axios';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';
import type { Run } from '../types';
import { Link } from 'react-router-dom';
import { Activity, AlertTriangle, ArrowRight } from 'lucide-react';

// ... (lines omitted)


export const PipelineGraph = () => {
    const [runs, setRuns] = useState<Run[]>([]);

    // Polling for runs
    useEffect(() => {
        const fetchRuns = async () => {
            try {
                const res = await axios.get('/control/runs');
                setRuns(res.data);
            } catch (e) { console.error(e); }
        };
        fetchRuns();
        const interval = setInterval(fetchRuns, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="h-full flex flex-col">
            <h2 className="text-2xl font-bold mb-6 text-slate-200 flex items-center gap-2">
                <Activity className="text-cyan-400" size={24} />
                Run Activity
            </h2>

            <div className="flex-1 grid grid-cols-1 gap-6 h-full">
                <div className="bg-[#1a1f26] border border-slate-700 rounded-xl overflow-hidden flex flex-col h-full">
                    <div className="p-4 bg-slate-800/50 border-b border-slate-700 font-semibold text-slate-300">
                        Recent Runs
                    </div>
                    <div className="flex-1 overflow-auto">
                        <table className="w-full text-left">
                            <thead className="bg-[#15191e] text-slate-400 text-xs uppercase">
                                <tr>
                                    <th className="p-4">Run ID</th>
                                    <th className="p-4">Status</th>
                                    <th className="p-4">Created</th>
                                    <th className="p-4">Artifacts</th>
                                    <th className="p-4"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {runs.map(run => (
                                    <tr key={run.run_id} className="hover:bg-slate-800/20 transition-colors">
                                        <td className="p-4 font-mono text-cyan-400">
                                            <Link to={`/runs/${run.run_id}`} className="hover:underline">{run.run_id}</Link>
                                        </td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded text-xs font-bold ${run.status === 'COMPLETED' ? 'bg-green-500/20 text-green-400' :
                                                run.status === 'RUNNING' ? 'bg-blue-500/20 text-blue-400 animate-pulse' :
                                                    run.status === 'FAILED' ? 'bg-red-500/20 text-red-400' :
                                                        'bg-slate-700 text-slate-400'
                                                }`}>
                                                {run.status}
                                            </span>
                                            {run.sensitivity_warning && (
                                                <div className="group relative ml-2 inline-block align-middle">
                                                    <AlertTriangle size={16} className="text-yellow-500 animate-pulse cursor-help" />
                                                    <span className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 px-2 py-1 bg-black border border-yellow-500 text-yellow-500 text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-50">
                                                        Simulators Disagree
                                                    </span>
                                                </div>
                                            )}
                                        </td>
                                        <td className="p-4 text-slate-400 text-sm">{new Date(run.created_at).toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true, month: 'numeric', day: 'numeric', year: 'numeric' })}</td>
                                        <td className="p-4">
                                            <Link to={`/artifacts/${run.run_id}/index`} className="text-slate-500 hover:text-slate-300 text-sm">
                                                View Files
                                            </Link>
                                        </td>
                                        <td className="p-4 text-right">
                                            <Link to={`/runs/${run.run_id}`} className="text-slate-400 hover:text-cyan-400 inline-block p-2 border border-slate-700 rounded-lg hover:border-cyan-400 transition-all">
                                                <ArrowRight size={18} />
                                            </Link>
                                        </td>
                                    </tr>
                                ))}
                                {runs.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="p-8 text-center text-slate-500">No runs found. Start one in Control Center.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};
