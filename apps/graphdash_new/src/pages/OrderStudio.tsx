import { useEffect, useState } from 'react';
import { Activity, Search } from 'lucide-react';
import axios from 'axios';

interface Run {
    run_id: string;
}

interface Order {
    order_id: string;
    ticker: string;
    side: string;
    qty: number;
    status: string;
    fill_avg_price: number;
}

export const OrderStudio = () => {
    const [runs, setRuns] = useState<Run[]>([]);
    const [selectedRun, setSelectedRun] = useState<string>('');
    const [orders, setOrders] = useState<Order[]>([]);
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
        axios.get(`/graphdash/run/${selectedRun}/tca/orders`)
            .then(res => {
                setOrders(res.data.orders || []);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, [selectedRun]);

    return (
        <div className="p-6 h-full flex flex-col">
            <header className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center">
                        <Activity size={24} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold">Order Studio</h1>
                        <p className="text-slate-500">Execution playback and order analysis.</p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-sm text-slate-400">Run:</span>
                    <select
                        className="bg-slate-800 border border-slate-700 rounded px-3 py-1 text-sm outline-none focus:border-cyan-500"
                        value={selectedRun}
                        onChange={e => setSelectedRun(e.target.value)}
                    >
                        {runs.map(r => <option key={r.run_id} value={r.run_id}>{r.run_id}</option>)}
                    </select>
                </div>
            </header>

            <div className="bg-[#1a1f26] border border-slate-700 rounded-xl flex-1 overflow-hidden flex flex-col">
                <div className="p-4 border-b border-slate-700 flex gap-2">
                    <div className="relative flex-1">
                        <Search size={16} className="absolute left-3 top-3 text-slate-500" />
                        <input type="text" placeholder="Search ticker or order ID..." className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-sm focus:border-cyan-500 outline-none" />
                    </div>
                </div>

                <div className="flex-1 overflow-auto">
                    <table className="w-full text-left">
                        <thead className="bg-[#0f1419] border-b border-slate-700 text-xs uppercase text-slate-500 font-medium sticky top-0">
                            <tr>
                                <th className="p-4">Ticker</th>
                                <th className="p-4">Side</th>
                                <th className="p-4 text-right">Qty</th>
                                <th className="p-4 text-right">Avg Price</th>
                                <th className="p-4">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {loading ? (
                                <tr><td colSpan={5} className="p-8 text-center text-slate-500">Loading orders...</td></tr>
                            ) : orders.length === 0 ? (
                                <tr><td colSpan={5} className="p-8 text-center text-slate-500">No orders found for this run.</td></tr>
                            ) : orders.map(order => (
                                <tr key={order.order_id} className="hover:bg-slate-800/50">
                                    <td className="p-4 font-bold">{order.ticker}</td>
                                    <td className={`p-4 font-bold ${order.side === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>{order.side}</td>
                                    <td className="p-4 text-right">{order.qty}</td>
                                    <td className="p-4 text-right text-mono">{order.fill_avg_price?.toFixed(2) || '-'}</td>
                                    <td className="p-4">
                                        <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${order.status === 'FILLED' ? 'bg-green-500/20 text-green-400' : 'bg-slate-700 text-slate-400'
                                            }`}>
                                            {order.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
