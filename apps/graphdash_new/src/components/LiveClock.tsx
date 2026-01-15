import { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';

export const LiveClock = () => {
    const [time, setTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => setTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
    };

    const formatDate = (date: Date) => {
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    };

    return (
        <div className="flex items-center gap-2 px-3 py-2 bg-slate-800/50 rounded-lg border border-slate-700">
            <Clock size={16} className="text-cyan-400" />
            <div className="text-right">
                <div className="text-sm font-mono text-slate-200">{formatTime(time)}</div>
                <div className="text-xs text-slate-500">{formatDate(time)}</div>
            </div>
        </div>
    );
};
