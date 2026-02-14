import { useState, useEffect } from "react";
import axios from "axios";
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    BarChart, Bar, Cell, PieChart, Pie
} from "recharts";
import { Activity, Clock, RefreshCcw } from "lucide-react";

// --- CUSTOM COMPONENTS ---

const StatCard = ({ title, value, gradient, icon: IconComponent }) => {
    return (
        <div className={`relative p-6 rounded-2xl overflow-hidden border border-border shadow-xl group hover:scale-[1.02] transition-transform duration-300 ${gradient} bg-white dark:bg-transparent`}>
            {/* Background Glow - Dark Mode Only */}
            <div className="absolute -right-6 -top-6 w-24 h-24 bg-white/5 rounded-full blur-2xl group-hover:bg-white/10 transition-colors hidden dark:block"></div>

            <div className="relative z-10 flex flex-col h-full justify-between">
                <div className="flex justify-between items-start mb-4">
                    <div className="p-2 bg-gray-100 dark:bg-white/10 rounded-lg backdrop-blur-sm">
                        <IconComponent size={20} className="text-gray-700 dark:text-white/90" />
                    </div>
                    <Activity size={16} className="text-gray-400 dark:text-white/40" />
                </div>

                <div>
                    <h3 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">{value}</h3>
                    <p className="text-xs font-medium text-gray-500 dark:text-white/60 uppercase tracking-wider mt-1">{title}</p>
                </div>
            </div>
        </div>
    );
};

const SectionHeader = ({ title, actions }) => (
    <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-bold text-gray-900 dark:text-white tracking-wide flex items-center gap-2 transition-colors">
            {title}
            <span className="text-gray-400 cursor-pointer hover:text-primary transition-colors">
                <Activity size={14} />
            </span>
        </h2>
        {actions}
    </div>
);

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white/95 dark:bg-gray-800/95 backdrop-blur-md p-4 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700/50 min-w-[150px]">
                {label && (
                    <p className="text-sm font-bold text-gray-700 dark:text-gray-200 mb-2 border-b border-gray-200 dark:border-gray-700 pb-2">
                        {label}
                    </p>
                )}
                {payload.map((entry, index) => {
                    let formattedValue = entry.value;
                    let valueClass = "text-gray-900 dark:text-white";

                    // Currency Formatting for PnL
                    if (entry.name === 'PnL' || entry.name === 'Equity') {
                        formattedValue = `$${entry.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                        if (entry.name === 'PnL') {
                            valueClass = entry.value >= 0 ? "text-success" : "text-danger";
                        }
                    } else if (typeof entry.value === 'number') {
                        formattedValue = entry.value.toLocaleString();
                    }

                    return (
                        <div key={index} className="flex items-center justify-between gap-4 mb-1 last:mb-0">
                            <div className="flex items-center gap-2">
                                <div className="w-2.5 h-2.5 rounded-full shadow-sm" style={{ backgroundColor: entry.color || entry.fill }}></div>
                                <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
                                    {entry.name}:
                                </span>
                            </div>
                            <span className={`text-sm font-bold ${valueClass}`}>
                                {formattedValue} {entry.unit || ''}
                            </span>
                        </div>
                    );
                })}
            </div>
        );
    }
    return null;
};

export default function Dashboard() {
    const [stats, setStats] = useState({
        total_pnl: 0,
        win_rate: 0,
        profit_factor: 0,
        total_trades: 0,
        wins: 0,
        losses: 0,
        max_drawdown: 0
    });
    const [activeTrades, setActiveTrades] = useState({});
    const [closedTrades, setClosedTrades] = useState([]);
    const [equityHistory, setEquityHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [timeframe, setTimeframe] = useState('all');
    const [activeTab, setActiveTab] = useState('active');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, activeRes, closedRes, historyRes] = await Promise.all([
                    axios.get(`http://localhost:8000/stats/performance?timeframe=${timeframe}`),
                    axios.get("http://localhost:8000/trades/active"),
                    axios.get(`http://localhost:8000/trades/closed?timeframe=${timeframe}`),
                    axios.get(`http://localhost:8000/trades/history?timeframe=${timeframe}`)
                ]);

                setStats(statsRes.data);
                setActiveTrades(activeRes.data);
                setClosedTrades(closedRes.data);
                setEquityHistory(historyRes.data);
            } catch (err) {
                console.error("Error fetching data:", err);
            } finally {
                setLoading(false);
            }
        };

        const interceptor = axios.interceptors.response.use(
            (response) => response,
            (error) => {
                if (error.response?.status === 401) window.location.href = '/login';
                return Promise.reject(error);
            }
        );

        fetchData();
        const interval = setInterval(fetchData, 10000);

        return () => {
            clearInterval(interval);
            axios.interceptors.response.eject(interceptor);
        };
    }, [timeframe]); // Re-fetch when timeframe changes

    if (loading) return <div className="text-center p-20 text-gray-500 font-sans">Loading Dashboard...</div>;

    return (
        <div className="space-y-8 font-sans">

            {/* 0. GLOBAL FILTER ROW */}
            <div className="flex justify-between items-center">
                <h1 className="text-xl font-bold dark:text-white hidden">Dashboard</h1> {/* Hidden as it's in Layout */}
                <div className="flex bg-gray-100 dark:bg-surface rounded-lg p-1 border border-border">
                    {['daily', 'weekly', 'monthly', 'all'].map((filter) => (
                        <button
                            key={filter}
                            onClick={() => setTimeframe(filter)}
                            className={`px-4 py-2 text-sm font-medium capitalize transition-all rounded-md ${timeframe === filter
                                ? "text-white bg-success shadow-sm"
                                : "text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5"
                                }`}
                        >
                            {filter}
                        </button>
                    ))}
                </div>
            </div>

            {/* 1. STATS ROW */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
                <StatCard
                    title="Net Profit"
                    value={`$${(stats.total_pnl || 0).toFixed(2)}`}
                    gradient="dark:bg-card-purple"
                    icon={Activity}
                />
                <StatCard
                    title="Profit Factor"
                    value={(stats.profit_factor || 0).toFixed(2)}
                    gradient="dark:bg-card-blue"
                    icon={RefreshCcw}
                />
                <StatCard
                    title="Trades"
                    value={stats.total_trades || 0}
                    gradient="dark:bg-card-green"
                    icon={Clock}
                />
                <StatCard
                    title="Win Rate"
                    value={`${(stats.win_rate || 0).toFixed(0)}%`}
                    gradient="dark:bg-card-orange"
                    icon={Activity}
                />
                <StatCard
                    title="Max Drawdown"
                    value={`${(stats.max_drawdown || 0).toFixed(2)}%`}
                    gradient="dark:bg-card-red"
                    icon={Activity}
                />
            </div>

            {/* 2. MAIN CONTENT GRID */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* LEFT: CHART */}
                <div className="lg:col-span-2">
                    <SectionHeader title="Net Cumulative P&L" />
                    <div className="bg-white dark:bg-surface rounded-2xl p-1 border border-border shadow-xl dark:shadow-2xl relative overflow-hidden group">
                        {/* Chart Background Gradient - Dark Only */}
                        <div className="absolute inset-0 bg-gradient-to-b from-success/5 to-transparent pointer-events-none hidden dark:block" />

                        <div className="h-[350px] w-full p-4">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={equityHistory}>
                                    <defs>
                                        <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                                            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" strokeOpacity={0.5} vertical={false} className="dark:stroke-[#2e3137]" />
                                    <XAxis
                                        dataKey="timestamp"
                                        hide
                                        axisLine={false}
                                        tickLine={false}
                                    />
                                    <YAxis
                                        stroke="#9ca3af"
                                        tick={{ fill: '#9ca3af', fontSize: 10 }}
                                        domain={['auto', 'auto']}
                                        axisLine={false}
                                        tickLine={false}
                                        tickFormatter={(value) => `$${value}`}
                                    />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Area
                                        type="monotone"
                                        dataKey="equity"
                                        name="Equity"
                                        stroke="#10b981"
                                        strokeWidth={3}
                                        fillOpacity={1}
                                        fill="url(#colorEquity)"
                                        activeDot={{ r: 6, fill: '#fff', stroke: '#10b981', strokeWidth: 2 }}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>

                {/* RIGHT: TRADES PANEL */}
                <div>
                    {/* Trade List Container */}
                    <div className="bg-white dark:bg-surface rounded-2xl border border-border shadow-xl h-full flex flex-col">
                        <div className="p-4 border-b border-border flex justify-between items-center">
                            <h3 className="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                                Trades
                                {activeTab === 'history' && <span className="text-xs font-normal text-gray-500">({closedTrades.length})</span>}
                            </h3>
                            <div className="flex bg-gray-100 dark:bg-black/20 rounded-lg p-1">
                                <button
                                    onClick={() => setActiveTab('active')}
                                    className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${activeTab === 'active' ? 'bg-white dark:bg-surface shadow text-primary' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400'}`}
                                >
                                    Active
                                </button>
                                <button
                                    onClick={() => setActiveTab('history')}
                                    className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${activeTab === 'history' ? 'bg-white dark:bg-surface shadow text-primary' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400'}`}
                                >
                                    History
                                </button>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar max-h-[350px]">
                            {activeTab === 'active' ? (
                                // ACTIVE TRADES VIEW
                                Object.entries(activeTrades).length === 0 ? (
                                    <div className="h-full flex flex-col items-center justify-center text-gray-400 p-8">
                                        <Activity size={32} className="mb-2 opacity-50" />
                                        <p className="text-sm">No active trades</p>
                                    </div>
                                ) : (
                                    Object.entries(activeTrades).map(([symbol, trade]) => (
                                        <div key={symbol} className="p-3 rounded-xl bg-gray-50 dark:bg-black/20 border border-transparent hover:border-border transition-all">
                                            <div className="flex justify-between items-center mb-2">
                                                <span className="font-bold text-gray-900 dark:text-white">{symbol}</span>
                                                <span className={`text-xs font-medium px-2 py-0.5 rounded ${trade.unrealized_pnl >= 0 ? "bg-success/20 text-success" : "bg-danger/20 text-danger"}`}>
                                                    {trade.unrealized_pnl >= 0 ? "+" : ""}{trade.unrealized_pnl?.toFixed(2)}
                                                </span>
                                            </div>
                                            <div className="flex justify-between text-xs text-gray-500">
                                                <span>Entry: {trade.entry}</span>
                                                <span>Current: {trade.current_price}</span>
                                            </div>
                                        </div>
                                    ))
                                )
                            ) : (
                                // HISTORY TRADES VIEW
                                closedTrades.length === 0 ? (
                                    <div className="h-full flex flex-col items-center justify-center text-gray-400 p-8">
                                        <div className="flex flex-col items-center">
                                            <Clock size={32} className="mb-2 opacity-50" />
                                            <p className="text-sm">No trade history</p>
                                        </div>
                                    </div>
                                ) : (
                                    closedTrades.slice().reverse().map((trade, i) => (
                                        <div key={i} className="p-3 rounded-xl bg-gray-50 dark:bg-black/20 border border-transparent hover:border-border transition-all group">
                                            <div className="flex justify-between items-center mb-1">
                                                <div className="flex items-center gap-2">
                                                    <span className={`w-1.5 h-1.5 rounded-full ${trade.pnl >= 0 ? 'bg-success' : 'bg-danger'}`}></span>
                                                    <span className="font-bold text-gray-900 dark:text-white text-sm">{trade.symbol.split('/')[0]}</span>
                                                </div>
                                                <span className={`font-mono font-bold text-sm ${trade.pnl >= 0 ? "text-success" : "text-danger"}`}>
                                                    {trade.pnl >= 0 ? "+" : ""}{trade.pnl?.toFixed(2)}
                                                </span>
                                            </div>
                                            <div className="flex justify-between items-center text-[10px] text-gray-500">
                                                <span>{new Date(trade.closed_at).toLocaleDateString()}</span>
                                                <span className="opacity-0 group-hover:opacity-100 transition-opacity text-primary">View Details</span>
                                            </div>
                                        </div>
                                    ))
                                )
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* 3. ANALYTICS ROW */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* A. Asset Performance - Full Width */}
                <div className="bg-white dark:bg-surface rounded-2xl p-6 border border-border shadow-lg">
                    <SectionHeader title="Asset Performance" />
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                                layout="vertical"
                                data={Object.entries(closedTrades.reduce((acc, t) => {
                                    const symbol = t.symbol.split('/')[0];
                                    acc[symbol] = (acc[symbol] || 0) + (t.pnl || 0);
                                    return acc;
                                }, {})).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value).slice(0, 5)}
                                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                            >
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e7eb" strokeOpacity={0.5} className="dark:stroke-[#2e3137]" />
                                <XAxis type="number" hide />
                                <YAxis dataKey="name" type="category" tick={{ fill: '#9ca3af', fontSize: 12 }} width={50} axisLine={false} tickLine={false} />
                                <Tooltip cursor={{ fill: 'transparent' }} content={<CustomTooltip />} />
                                <Bar dataKey="value" name="PnL" radius={[0, 4, 4, 0]} barSize={20}>
                                    {
                                        Object.entries(closedTrades.reduce((acc, t) => {
                                            const symbol = t.symbol.split('/')[0];
                                            acc[symbol] = (acc[symbol] || 0) + (t.pnl || 0);
                                            return acc;
                                        }, {})).map(([name, value], index) => (
                                            <Cell key={`cell-${index}`} fill={value >= 0 ? '#10b981' : '#ef4444'} />
                                        ))
                                    }
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* B. Win/Loss Ratio */}
                <div className="bg-white dark:bg-surface rounded-2xl p-6 border border-border shadow-lg">
                    <SectionHeader title="Win/Loss Ratio" />
                    <div className="h-64 relative">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={[
                                        { name: 'Wins', value: stats.wins },
                                        { name: 'Losses', value: stats.losses }
                                    ]}
                                    innerRadius={60}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                    stroke="none"
                                >
                                    <Cell fill="#10b981" />
                                    <Cell fill="#ef4444" />
                                </Pie>
                                <Tooltip content={<CustomTooltip />} />
                                {/* Center Text */}
                            </PieChart>
                        </ResponsiveContainer>
                        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                            <span className="text-3xl font-bold text-gray-900 dark:text-white">
                                {stats.total_trades > 0 && !isNaN(stats.win_rate) ? stats.win_rate.toFixed(0) : "0"}%
                            </span>
                            <span className="text-xs text-gray-500 uppercase tracking-widest mt-1">Win Rate</span>
                        </div>
                    </div>
                </div>

                {/* C. PnL Distribution */}
                <div className="bg-white dark:bg-surface rounded-2xl p-6 border border-border shadow-lg">
                    <SectionHeader title="PnL Distribution" />
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={(() => {
                                const pnls = closedTrades.map(t => t.pnl).filter(p => p !== null);
                                if (pnls.length === 0) return [];
                                const min = Math.floor(Math.min(...pnls));
                                const max = Math.ceil(Math.max(...pnls));
                                const binCount = 10;
                                const step = (max - min) / binCount || 1;
                                const bins = Array.from({ length: binCount }, (_, i) => ({
                                    range: `${(min + i * step).toFixed(1)}`,
                                    count: 0
                                }));
                                pnls.forEach(pnl => {
                                    const index = Math.min(Math.floor((pnl - min) / step), binCount - 1);
                                    if (index >= 0) bins[index].count++;
                                });
                                return bins;
                            })()}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" strokeOpacity={0.5} className="dark:stroke-[#2e3137]" />
                                <XAxis dataKey="range" tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
                                <YAxis hide />
                                <Tooltip cursor={{ fill: 'transparent' }} content={<CustomTooltip />} />
                                <Bar dataKey="count" name="Frequency" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={30} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

            </div>
        </div>
    );
}
