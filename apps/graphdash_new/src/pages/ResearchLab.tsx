import React, { useEffect, useState } from 'react';
import { Database, FileJson } from 'lucide-react';
import axios from 'axios';

interface Run { run_id: string; }

export const ResearchLab = () => {
    const [runs, setRuns] = useState<Run[]>([]);
    const [selectedRun, setSelectedRun] = useState<string>('');
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        axios.get('/graphdash/runs').then(res => {
            const list = res.data.runs || [];
            setRuns(list);
            if (list.length > 0) setSelectedRun(list[0].run_id);
        });
    }, []);

    useEffect(() => {
        if (!selectedRun) return;
        setLoading(true);
        axios.get(`/graphdash/run/${selectedRun}/research`)
            .then(res => {
                setData(res.data);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, [selectedRun]);

    return (
        <div className="p-6 h-full flex flex-col">
            <header className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-orange-500/20 text-orange-400 flex items-center justify-center">
                        <Database size={24} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold">Research Lab</h1>
                        <p className="text-slate-500">Alpha signals, gate scores, and feature analysis.</p>
                    </div>
                </div>

                <select
                    className="bg-slate-800 border border-slate-700 rounded px-3 py-1 text-sm outline-none focus:border-cyan-500"
                    value={selectedRun}
                    onChange={e => setSelectedRun(e.target.value)}
                >
                    {runs.map(r => <option key={r.run_id} value={r.run_id}>{r.run_id}</option>)}
                </select>
            </header>

            <div className="flex-1 grid grid-cols-2 gap-6">
                {/* Gate Scores */}
                <div className="bg-[#1a1f26] border border-slate-700 rounded-xl p-4 flex flex-col">
                    <h3 className="font-semibold text-slate-200 mb-4 flex items-center gap-2">
                        <FileJson size={16} className="text-cyan-400" /> Gate Scores
                    </h3>
                    <div className="flex-1 bg-[#0f1419] rounded p-4 overflow-auto font-mono text-xs text-slate-400 whitespace-pre">
                        {loading ? "Loading..." : JSON.stringify(data?.gate, null, 2)}
                    </div>
                </div>

                {/* Leaderboard */}
                <div className="bg-[#1a1f26] border border-slate-700 rounded-xl p-4 flex flex-col">
                    <h3 className="font-semibold text-slate-200 mb-4 flex items-center gap-2">
                        <FileJson size={16} className="text-purple-400" /> Leaderboard & Calibration
                    </h3>
                    <div className="flex-1 bg-[#0f1419] rounded p-4 overflow-auto font-mono text-xs text-slate-400 whitespace-pre">
                        {loading ? "Loading..." : JSON.stringify(data?.leaderboard || data?.calibration, null, 2)}
                    </div>
                </div>
            </div>
        </div>
    );
};
