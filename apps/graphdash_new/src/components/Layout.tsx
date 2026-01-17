import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Play, Activity, Settings, Database, LineChart, BarChart2, Brain, Network } from 'lucide-react';
import { LiveClock } from './LiveClock';
import { AccountSummary } from './AccountSummary';

const NavItem = ({ to, icon: Icon, label }: { to: string, icon: any, label: string }) => {
    const location = useLocation();
    const navigate = useNavigate();
    const active = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'link';
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const strategyId = e.dataTransfer.getData('strategyId');
        if (strategyId) {
            // Auto-run navigation
            navigate(`${to}?strategy_id=${strategyId}&autorun=true`);
        }
    };

    return (
        <div
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className="group"
        >
            <Link to={to} className={`flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${active ? 'bg-slate-800 text-cyan-400 border-l-4 border-cyan-400' : 'text-slate-400 group-drag-over:bg-cyan-900/50 hover:bg-slate-800 hover:text-slate-200'}`}>
                <Icon size={18} />
                <span className="text-sm font-medium">{label}</span>
            </Link>
        </div>
    );
};

export const Layout = ({ children }: { children: React.ReactNode }) => {
    return (
        <div className="flex h-screen bg-[#0f1419] text-gray-100 font-sans">
            {/* Sidebar */}
            <div className="w-64 bg-[#1a1f26] border-r border-slate-700 flex flex-col">
                <div className="p-4 border-b border-slate-700 flex items-center gap-3">
                    <img src="/dashboard/brand_logo.png" alt="Synegious" className="w-10 h-10 object-contain opacity-90" />
                    <div>
                        <div className="font-bold text-lg leading-tight text-slate-100">Synegious Flows</div>
                        <div className="text-xs text-slate-500">Control Plane</div>
                    </div>
                </div>

                <nav className="flex-1 p-4 space-y-1">
                    <NavItem to="/" icon={LayoutDashboard} label="Pipeline Graph" />
                    <NavItem to="/control" icon={Play} label="Control Center" />
                    <NavItem to="/results" icon={LineChart} label="Results Viewer" />
                    <NavItem to="/playback" icon={Activity} label="Order Studio" />
                    <NavItem to="/research" icon={Database} label="Strategy Library" />
                    <NavItem to="/market" icon={BarChart2} label="Market Research" />
                    <NavItem to="/intelligence" icon={Brain} label="Deep Intelligence" />
                    <NavItem to="/nexus" icon={Network} label="Synegious Nexus" />
                </nav>

                <div className="p-4 border-t border-slate-700">
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                        <div className="w-2 h-2 rounded-full bg-green-500"></div>
                        System Online
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-auto flex flex-col">
                <header className="px-6 py-4 border-b border-slate-700 bg-[#1a1f26] flex justify-between items-center relative overflow-hidden">
                    {/* Truth Banner Background */}
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 via-blue-500 to-cyan-500 opacity-50"></div>

                    <div className="flex items-center gap-3 z-10">
                        <img src="/dashboard/brand_logo.png" alt="Synegious" className="w-8 h-8 object-contain invert opacity-90" />
                        <h1 className="font-semibold text-lg text-slate-200">Synegious Research Platform</h1>
                    </div>

                    <div className="flex items-center gap-4 z-10">
                        <AccountSummary />
                        <LiveClock />
                        <div className="px-4 py-2 rounded bg-cyan-500/10 text-cyan-400 text-xs font-bold border border-cyan-500/20 flex items-center gap-2 animate-pulse">
                            <span className="w-2 h-2 rounded-full bg-cyan-500"></span>
                            RESEARCH MODE ACTIVE
                        </div>
                        <span className="text-xs text-slate-500">v3.2.0</span>
                    </div>
                </header>
                <main className="p-6 flex-1 flex flex-col">
                    {children}
                </main>
            </div>
        </div>
    );
};
