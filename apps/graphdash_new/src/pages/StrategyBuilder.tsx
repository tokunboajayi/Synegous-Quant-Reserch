import { useEffect, useState } from 'react';
import axios from 'axios';
import {
    Database, Search, BookOpen, Copy, Play,
    TrendingUp, BarChart2, Zap,
    RefreshCw, ArrowUpRight, ArrowDownRight, Activity, Layers, X
} from 'lucide-react';
import { BacktestPanel } from '../components/BacktestPanel';

// Types
interface Signal {
    signal_id: string;
    name: string;
    type: string;
    parameters: Record<string, any>;
    weight: number;
}

interface Rule {
    rule_id: string;
    condition: string;
    action: string;
    size?: number;
}

interface Strategy {
    strategy_id: string;
    name: string;
    description: string;
    type: string;
    signals: Signal[];
    entry_rules: Rule[];
    exit_rules: Rule[];
    parameters: Record<string, any>;
    code?: string;
    is_template: boolean;
    author: string;
    last_sharpe?: number;
    last_return?: number;
}

// Category metadata
const CATEGORIES = [
    { id: 'momentum', label: 'Momentum', icon: TrendingUp, color: 'text-green-400', bg: 'bg-green-500/20' },
    { id: 'mean_reversion', label: 'Mean Reversion', icon: RefreshCw, color: 'text-blue-400', bg: 'bg-blue-500/20' },
    { id: 'factor', label: 'Factor', icon: BarChart2, color: 'text-purple-400', bg: 'bg-purple-500/20' },
    { id: 'statistical_arb', label: 'Statistical Arb', icon: Activity, color: 'text-cyan-400', bg: 'bg-cyan-500/20' },
    { id: 'custom', label: 'Volatility & Execution', icon: Zap, color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
];

export const StrategyBuilder = () => {
    const [strategies, setStrategies] = useState<Strategy[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
    const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
    const [showTemplatesOnly, setShowTemplatesOnly] = useState(true);
    const [showBacktest, setShowBacktest] = useState(false);

    // Fetch strategies on mount
    useEffect(() => {
        fetchStrategies();
    }, []);

    const fetchStrategies = async () => {
        setLoading(true);
        try {
            const res = await axios.get('/strategies');
            setStrategies(res.data);
        } catch (e) {
            console.error('Failed to fetch strategies', e);
        }
        setLoading(false);
    };

    // Filter strategies
    const filteredStrategies = strategies.filter(s => {
        const matchesSearch = s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            s.description.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesCategory = !selectedCategory || s.type === selectedCategory;
        const matchesTemplate = !showTemplatesOnly || s.is_template;
        return matchesSearch && matchesCategory && matchesTemplate;
    });

    // Group by type for display
    const groupedStrategies = CATEGORIES.map(cat => ({
        ...cat,
        strategies: filteredStrategies.filter(s => s.type === cat.id)
    })).filter(g => g.strategies.length > 0);

    // Duplicate a template
    const handleDuplicate = async (strategyId: string) => {
        const name = prompt('Enter a name for your strategy:');
        if (!name) return;

        try {
            const res = await axios.post(`/strategies/${strategyId}/duplicate`, { new_name: name });
            setStrategies([res.data, ...strategies]);
            setSelectedStrategy(res.data);
        } catch (e) {
            console.error('Failed to duplicate', e);
        }
    };

    // Category icon component
    const getCategoryIcon = (type: string) => {
        const cat = CATEGORIES.find(c => c.id === type);
        if (cat) {
            const Icon = cat.icon;
            return <Icon size={16} className={cat.color} />;
        }
        return <Layers size={16} className="text-slate-400" />;
    };

    return (
        <div className="p-6 h-full flex flex-col">
            {/* Header */}
            <header className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/30 to-cyan-500/30 flex items-center justify-center border border-purple-500/30">
                        <Database size={24} className="text-purple-400" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-slate-100">Strategy Library</h1>
                        <p className="text-slate-500 text-sm">115+ quantitative trading strategies for every market condition</p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-500">{filteredStrategies.length} strategies</span>
                    <button
                        onClick={() => setShowTemplatesOnly(!showTemplatesOnly)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${showTemplatesOnly
                            ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                            : 'bg-slate-800 text-slate-400 border border-slate-700'
                            }`}
                    >
                        {showTemplatesOnly ? 'Templates Only' : 'All Strategies'}
                    </button>
                </div>
            </header>

            {/* Search & Filters */}
            <div className="flex gap-4 mb-6">
                {/* Search */}
                <div className="flex-1 relative">
                    <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input
                        type="text"
                        placeholder="Search strategies..."
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 bg-[#1a1f26] border border-slate-700 rounded-lg text-sm outline-none focus:border-cyan-500 transition-colors"
                    />
                </div>

                {/* Category Filter */}
                <div className="flex gap-2">
                    <button
                        onClick={() => setSelectedCategory(null)}
                        className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${!selectedCategory
                            ? 'bg-slate-700 text-white'
                            : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                            }`}
                    >
                        All
                    </button>
                    {CATEGORIES.map(cat => (
                        <button
                            key={cat.id}
                            onClick={() => setSelectedCategory(selectedCategory === cat.id ? null : cat.id)}
                            className={`px-3 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${selectedCategory === cat.id
                                ? `${cat.bg} ${cat.color} border border-current/30`
                                : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                                }`}
                        >
                            <cat.icon size={14} />
                            {cat.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex gap-6 overflow-hidden">
                {/* Strategy List */}
                <div className="flex-1 overflow-auto space-y-6">
                    {loading ? (
                        <div className="text-center py-12 text-slate-500">Loading strategies...</div>
                    ) : groupedStrategies.length === 0 ? (
                        <div className="text-center py-12 text-slate-500">No strategies found</div>
                    ) : (
                        groupedStrategies.map(group => (
                            <div key={group.id}>
                                {/* Category Header */}
                                <div className="flex items-center gap-2 mb-3">
                                    <div className={`w-8 h-8 rounded-lg ${group.bg} flex items-center justify-center`}>
                                        <group.icon size={16} className={group.color} />
                                    </div>
                                    <h2 className={`font-semibold ${group.color}`}>{group.label}</h2>
                                    <span className="text-slate-600 text-sm">({group.strategies.length})</span>
                                </div>

                                {/* Strategy Cards */}
                                <div className="grid grid-cols-2 gap-3">
                                    {group.strategies.map(strategy => (
                                        <div
                                            key={strategy.strategy_id}
                                            onClick={() => setSelectedStrategy(strategy)}
                                            className={`p-4 bg-[#1a1f26] border rounded-xl cursor-pointer transition-all hover:border-slate-600 ${selectedStrategy?.strategy_id === strategy.strategy_id
                                                ? 'border-cyan-500/50 bg-cyan-500/5'
                                                : 'border-slate-700/50'
                                                }`}
                                        >
                                            <div className="flex items-start justify-between mb-2">
                                                <h3 className="font-medium text-slate-200 text-sm">{strategy.name}</h3>
                                                {strategy.is_template && (
                                                    <span className="px-1.5 py-0.5 text-[10px] bg-slate-700 text-slate-400 rounded">
                                                        TEMPLATE
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-xs text-slate-500 line-clamp-2 mb-3">{strategy.description}</p>

                                            <div className="flex items-center gap-2 text-xs">
                                                {strategy.signals.length > 0 && (
                                                    <span className="text-slate-600">{strategy.signals.length} signals</span>
                                                )}
                                                {strategy.last_sharpe && (
                                                    <span className={`${strategy.last_sharpe > 1 ? 'text-green-400' : 'text-slate-500'}`}>
                                                        SR: {strategy.last_sharpe.toFixed(2)}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Strategy Detail Panel */}
                <div className="w-96 bg-[#1a1f26] border border-slate-700 rounded-xl overflow-hidden flex flex-col">
                    {selectedStrategy ? (
                        <>
                            {/* Detail Header */}
                            <div className="p-4 border-b border-slate-700 bg-slate-800/30">
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        {getCategoryIcon(selectedStrategy.type)}
                                        <span className="text-xs text-slate-500 uppercase">{selectedStrategy.type.replace('_', ' ')}</span>
                                    </div>
                                    {/* Quick Action Buttons */}
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleDuplicate(selectedStrategy.strategy_id)}
                                            className="flex items-center gap-1 px-2 py-1 bg-cyan-500/20 text-cyan-400 rounded text-xs hover:bg-cyan-500/30 transition-colors"
                                            title="Use Template"
                                        >
                                            <Copy size={12} />
                                            Clone
                                        </button>
                                        <button
                                            onClick={() => setShowBacktest(true)}
                                            className="flex items-center gap-1 px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs hover:bg-green-500/30 transition-colors"
                                            title="Run Backtest"
                                        >
                                            <Play size={12} />
                                            Test
                                        </button>
                                    </div>
                                </div>
                                <h2 className="text-lg font-bold text-slate-100">{selectedStrategy.name}</h2>
                                <p className="text-sm text-slate-400 mt-1 line-clamp-2">{selectedStrategy.description}</p>
                            </div>

                            {/* Detail Content */}
                            <div className="flex-1 overflow-auto p-4 space-y-4">
                                {/* Signals */}
                                {selectedStrategy.signals.length > 0 && (
                                    <div>
                                        <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2">Signals</h3>
                                        <div className="space-y-2">
                                            {selectedStrategy.signals.map(signal => (
                                                <div key={signal.signal_id} className="p-2 bg-slate-800/50 rounded-lg text-sm">
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-slate-300">{signal.name}</span>
                                                        <span className="text-xs text-slate-500">{signal.type}</span>
                                                    </div>
                                                    {Object.keys(signal.parameters).length > 0 && (
                                                        <div className="text-xs text-slate-500 mt-1">
                                                            {JSON.stringify(signal.parameters)}
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Entry Rules */}
                                {selectedStrategy.entry_rules.length > 0 && (
                                    <div>
                                        <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1">
                                            <ArrowUpRight size={12} className="text-green-400" />
                                            Entry Rules
                                        </h3>
                                        <div className="space-y-1">
                                            {selectedStrategy.entry_rules.map(rule => (
                                                <div key={rule.rule_id} className="p-2 bg-green-500/10 border border-green-500/20 rounded text-xs text-green-400 font-mono">
                                                    {rule.condition} → {rule.action}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Exit Rules */}
                                {selectedStrategy.exit_rules.length > 0 && (
                                    <div>
                                        <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1">
                                            <ArrowDownRight size={12} className="text-red-400" />
                                            Exit Rules
                                        </h3>
                                        <div className="space-y-1">
                                            {selectedStrategy.exit_rules.map(rule => (
                                                <div key={rule.rule_id} className="p-2 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-400 font-mono">
                                                    {rule.condition} → {rule.action}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Parameters */}
                                {Object.keys(selectedStrategy.parameters).length > 0 && (
                                    <div>
                                        <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2">Parameters</h3>
                                        <div className="bg-slate-800/50 rounded-lg p-3">
                                            <pre className="text-xs text-slate-400 overflow-auto">
                                                {JSON.stringify(selectedStrategy.parameters, null, 2)}
                                            </pre>
                                        </div>
                                    </div>
                                )}

                                {/* Custom Code */}
                                {selectedStrategy.code && (
                                    <div>
                                        <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2">Code</h3>
                                        <pre className="bg-[#0d1117] p-3 rounded-lg text-xs text-slate-300 overflow-auto font-mono">
                                            {selectedStrategy.code}
                                        </pre>
                                    </div>
                                )}
                            </div>

                            {/* Actions */}
                            <div className="p-4 border-t border-slate-700 flex gap-2">
                                <button
                                    onClick={() => handleDuplicate(selectedStrategy.strategy_id)}
                                    className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-cyan-500/20 text-cyan-400 rounded-lg hover:bg-cyan-500/30 transition-colors text-sm font-medium"
                                >
                                    <Copy size={16} />
                                    Use Template
                                </button>
                                <button
                                    onClick={() => setShowBacktest(true)}
                                    className="flex items-center justify-center gap-2 px-4 py-2.5 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-colors"
                                >
                                    <Play size={16} />
                                </button>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-slate-500 p-6">
                            <BookOpen size={48} className="mb-4 opacity-30" />
                            <p className="text-center">Select a strategy to view details</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Backtest Modal */}
            {showBacktest && selectedStrategy && (
                <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-8">
                    <div className="w-full max-w-4xl max-h-[90vh] overflow-auto">
                        <div className="relative">
                            <button
                                onClick={() => setShowBacktest(false)}
                                className="absolute -top-3 -right-3 w-8 h-8 bg-slate-800 border border-slate-700 rounded-full flex items-center justify-center text-slate-400 hover:text-white z-10"
                            >
                                <X size={16} />
                            </button>
                            <BacktestPanel
                                strategyId={selectedStrategy.strategy_id}
                                strategyName={selectedStrategy.name}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
