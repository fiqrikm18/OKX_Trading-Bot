import { useState, useEffect } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import {
    LayoutDashboard,
    BarChart2,
    Calendar,
    Settings,
    User,
    Bell,
    Plus,
    Sun,
    Moon,
    Menu,
    X
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
    <div className="flex flex-col items-center gap-1 cursor-pointer group" onClick={onClick}>
        <div className={`p-3 rounded-xl transition-all ${active
            ? "bg-primary/10 text-primary shadow-lg shadow-primary/10"
            : "text-gray-500 hover:text-gray-300 hover:bg-surface"
            }`}>
            <Icon size={22} strokeWidth={2} />
        </div>
        <span className={`text-[10px] font-medium ${active ? "text-primary" : "text-gray-500 group-hover:text-gray-400"}`}>
            {label}
        </span>
    </div>
);

export default function Layout() {
    const { logout } = useAuth();
    const { theme, toggleTheme } = useTheme();
    const navigate = useNavigate();
    const location = useLocation();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const toggleMobileMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen);

    // Close mobile menu when route changes
    useEffect(() => {
        // eslint-disable-next-line react-hooks/exhaustive-deps
        if (isMobileMenuOpen) setIsMobileMenuOpen(false);
    }, [location.pathname]);

    return (
        <div className="flex min-h-screen bg-background text-gray-900 dark:text-white font-sans selection:bg-primary/30 transition-colors duration-300">
            {/* DESKTOP SIDEBAR */}
            <aside className="hidden md:flex w-20 border-r border-border flex-col items-center py-6 gap-8 bg-background sticky top-0 h-screen z-50">
                {/* Logo */}
                <button className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center text-white shadow-lg shadow-primary/20 hover:scale-105 transition-transform">
                    <Plus size={24} strokeWidth={3} />
                </button>

                {/* Navigation */}
                <nav className="flex flex-col gap-6 w-full flex-1">
                    <SidebarItem icon={LayoutDashboard} label="Dashboard" path="/" active={location.pathname === '/'} onClick={() => navigate('/')} />
                    <SidebarItem icon={BarChart2} label="Trades" path="/trades" active={location.pathname === '/trades'} onClick={() => navigate('/trades')} />
                    <SidebarItem icon={Calendar} label="Calendar" path="/calendar" active={location.pathname === '/calendar'} />
                    <SidebarItem icon={Settings} label="Settings" path="/settings" active={location.pathname === '/settings'} />
                    <SidebarItem icon={User} label="Account" path="/account" active={location.pathname === '/account'} onClick={logout} />
                </nav>

                {/* Theme Toggle */}
                <button onClick={toggleTheme} className="p-3 rounded-xl bg-surface text-gray-500 hover:text-primary transition-colors border border-border mb-4">
                    {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
                </button>
            </aside>

            {/* MOBILE SIDEBAR (DRAWER) */}
            <div className={`fixed inset-0 z-50 md:hidden transition-opacity duration-300 ${isMobileMenuOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}>
                {/* Backdrop */}
                <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={toggleMobileMenu} />

                {/* Drawer */}
                <div className={`absolute left-0 top-0 bottom-0 w-64 bg-surface border-r border-border shadow-2xl transform transition-transform duration-300 flex flex-col p-6 ${isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"}`}>
                    <div className="flex justify-between items-center mb-8">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center text-white shadow-lg shadow-primary/20">
                                <Plus size={20} strokeWidth={3} />
                            </div>
                            <span className="font-bold text-lg tracking-wide">TradingBot</span>
                        </div>
                        <button onClick={toggleMobileMenu} className="p-2 bg-background rounded-lg border border-border">
                            <X size={20} />
                        </button>
                    </div>

                    <nav className="flex flex-col gap-2 flex-1">
                        <div className={`p-3 rounded-xl flex items-center gap-3 cursor-pointer ${location.pathname === '/' ? "bg-primary/10 text-primary" : "text-gray-500"}`} onClick={() => navigate('/')}>
                            <LayoutDashboard size={20} />
                            <span className="font-medium">Dashboard</span>
                        </div>
                        <div className={`p-3 rounded-xl flex items-center gap-3 cursor-pointer ${location.pathname === '/trades' ? "bg-primary/10 text-primary" : "text-gray-500"}`} onClick={() => navigate('/trades')}>
                            <BarChart2 size={20} />
                            <span className="font-medium">Trades</span>
                        </div>
                        <div className="p-3 rounded-xl flex items-center gap-3 cursor-pointer text-gray-500">
                            <Calendar size={20} />
                            <span className="font-medium">Calendar</span>
                        </div>
                        <div className="p-3 rounded-xl flex items-center gap-3 cursor-pointer text-gray-500">
                            <Settings size={20} />
                            <span className="font-medium">Settings</span>
                        </div>
                    </nav>

                    <div className="mt-auto pt-6 border-t border-border flex flex-col gap-4">
                        <div className="flex items-center justify-between p-3 rounded-xl bg-background border border-border">
                            <span className="text-sm font-medium text-gray-500">Theme</span>
                            <button onClick={toggleTheme} className="p-2 rounded-lg bg-surface text-primary">
                                {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                            </button>
                        </div>
                        <button onClick={logout} className="w-full py-3 bg-danger/10 text-danger font-medium rounded-xl flex items-center justify-center gap-2">
                            <User size={18} /> Logout
                        </button>
                    </div>
                </div>
            </div>

            {/* MAIN CONTENT */}
            <main className="flex-1 flex flex-col min-w-0">
                {/* HEADER */}
                <header className="h-16 md:h-20 border-b border-border flex items-center justify-between px-4 md:px-8 bg-background/50 backdrop-blur-md sticky top-0 z-40 transition-colors duration-300">
                    <div className="flex items-center gap-4">
                        <button onClick={toggleMobileMenu} className="md:hidden p-2 text-gray-500 hover:text-primary">
                            <Menu size={24} />
                        </button>
                        <h1 className="text-lg md:text-xl font-bold dark:text-white text-gray-900 tracking-wide">
                            Dashboard
                        </h1>
                    </div>

                    <div className="flex items-center gap-3 md:gap-6">
                        {/* Date Range Picker - Hidden on small mobile */}
                        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 md:px-4 md:py-2 bg-surface rounded-lg border border-border text-xs text-gray-500 dark:text-gray-400">
                            <Calendar size={14} />
                            <span>Dec 24 - Jan 23</span>
                        </div>

                        {/* Notifications */}
                        <div className="relative">
                            <Bell size={20} className="text-gray-400 hover:text-primary cursor-pointer" />
                            <span className="absolute -top-1 -right-1 w-2 h-2 bg-success rounded-full"></span>
                        </div>

                        {/* User Profile */}
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-purple-500 border border-white/10" />
                    </div>
                </header>

                <div className="p-4 md:p-6 flex-1 overflow-y-auto custom-scrollbar">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
