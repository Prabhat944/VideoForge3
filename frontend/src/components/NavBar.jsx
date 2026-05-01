import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { Clapperboard, LogOut, Sparkles } from "lucide-react";
import { Button } from "./ui/button";

export default function NavBar() {
    const { user, logout } = useAuth();
    const nav = useNavigate();
    const loc = useLocation();
    const linkCls = (path) =>
        `font-mono-tag transition-colors ${loc.pathname.startsWith(path) ? "text-white" : "text-zinc-500 hover:text-white"}`;

    return (
        <header className="sticky top-0 z-50 border-b border-white/10 bg-black/60 backdrop-blur-xl">
            <div className="max-w-7xl mx-auto px-6 lg:px-12 h-16 flex items-center justify-between">
                <Link to="/" data-testid="nav-logo-link" className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-md bg-[#F23F42] grid place-items-center glow-red">
                        <Clapperboard className="w-4 h-4 text-white" strokeWidth={2.5} />
                    </div>
                    <span className="font-display font-black text-lg tracking-tighter">VIDEOFORGE</span>
                </Link>

                <nav className="hidden md:flex items-center gap-8">
                    {user ? (
                        <>
                            <Link to="/dashboard" className={linkCls("/dashboard")} data-testid="nav-dashboard-link">Dashboard</Link>
                            <Link to="/wizard" className={linkCls("/wizard")} data-testid="nav-wizard-link">New Video</Link>
                            <Link to="/templates" className={linkCls("/templates")} data-testid="nav-templates-link">Templates</Link>
                            <Link to="/agent" className={linkCls("/agent")} data-testid="nav-agent-link">Agent</Link>
                            <Link to="/trends" className={linkCls("/trends")} data-testid="nav-trends-link">Trends</Link>
                            <Link to="/calendar" className={linkCls("/calendar")} data-testid="nav-calendar-link">Calendar</Link>
                            <Link to="/analytics" className={linkCls("/analytics")} data-testid="nav-analytics-link">Analytics</Link>
                            <Link to="/pricing" className={linkCls("/pricing")} data-testid="nav-pricing-link">Pricing</Link>
                        </>
                    ) : (
                        <>
                            <a href="#features" className="font-mono-tag text-zinc-500 hover:text-white transition-colors">Features</a>
                            <Link to="/pricing" className={linkCls("/pricing")} data-testid="nav-pricing-link">Pricing</Link>
                        </>
                    )}
                </nav>

                <div className="flex items-center gap-3">
                    {user ? (
                        <>
                            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md border border-white/10 bg-white/5">
                                <Sparkles className="w-3.5 h-3.5 text-[#F23F42]" />
                                <span className="font-mono-tag text-zinc-300" data-testid="nav-credits">{user.credits} credits</span>
                            </div>
                            <Button
                                variant="ghost" size="sm"
                                onClick={() => { logout(); nav("/"); }}
                                data-testid="nav-logout-btn"
                                className="text-zinc-400 hover:text-white hover:bg-white/5"
                            >
                                <LogOut className="w-4 h-4" />
                            </Button>
                        </>
                    ) : (
                        <>
                            <Link to="/login" data-testid="nav-login-link">
                                <Button variant="ghost" size="sm" className="text-zinc-300 hover:text-white hover:bg-white/5">Sign in</Button>
                            </Link>
                            <Link to="/register" data-testid="nav-register-link">
                                <Button size="sm" className="bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md">Get started</Button>
                            </Link>
                        </>
                    )}
                </div>
            </div>
        </header>
    );
}
