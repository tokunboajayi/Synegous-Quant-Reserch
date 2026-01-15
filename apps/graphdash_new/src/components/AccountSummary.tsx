import { useEffect, useState } from 'react';
import axios from 'axios';
import { Wallet, TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

interface AccountStatus {
    connected: boolean;
    equity?: number;
    buying_power?: number;
    cash?: number;
    pnl_day?: number;
    pnl_day_pct?: number;
    status?: string;
}

export const AccountSummary = () => {
    const [account, setAccount] = useState<AccountStatus | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchStatus = async () => {
        try {
            const res = await axios.get('/alpaca/status');
            setAccount(res.data);
        } catch (e) {
            console.error('Failed to fetch Alpaca status', e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="animate-pulse h-8 w-48 bg-slate-800 rounded"></div>;
    if (!account?.connected) return null;

    const isPositive = (account.pnl_day || 0) >= 0;

    return (
        <div className="flex items-center gap-6 px-4 py-1.5 bg-slate-800/40 rounded-lg border border-slate-700/50 backdrop-blur-sm">
            {/* Equity */}
            <div className="flex flex-col">
                <span className="text-[10px] uppercase text-slate-500 font-bold tracking-wider leading-none mb-1">Total Equity</span>
                <div className="flex items-center gap-1.5 font-mono font-bold text-slate-100 italic">
                    <Wallet size={12} className="text-cyan-400" />
                    ${account.equity?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
            </div>

            {/* Daily P&L */}
            <div className="flex flex-col">
                <span className="text-[10px] uppercase text-slate-500 font-bold tracking-wider leading-none mb-1">Today</span>
                <div className={`flex items-center gap-1.5 font-mono font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                    {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                    {isPositive ? '+' : ''}${Math.abs(account.pnl_day || 0).toLocaleString()} ({account.pnl_day_pct}%)
                </div>
            </div>

            {/* Buying Power */}
            <div className="flex flex-col border-l border-slate-700/50 pl-4">
                <span className="text-[10px] uppercase text-slate-500 font-bold tracking-wider leading-none mb-1">Buying Power</span>
                <div className="flex items-center gap-1.5 font-mono font-bold text-slate-400">
                    <DollarSign size={12} />
                    ${account.buying_power?.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </div>
            </div>

            {/* Status */}
            <div className="flex flex-col border-l border-slate-700/50 pl-4">
                <span className="text-[10px] uppercase text-slate-500 font-bold tracking-wider leading-none mb-1">Account</span>
                <div className="flex items-center gap-1.5 font-bold text-[10px]">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                    {account.status?.toUpperCase()} (PAPER)
                </div>
            </div>
        </div>
    );
};
