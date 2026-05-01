import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Clapperboard, ArrowRight } from "lucide-react";

export default function Auth({ mode = "login" }) {
    const isLogin = mode === "login";
    const { login, register } = useAuth();
    const nav = useNavigate();
    const [form, setForm] = useState({ email: "", password: "", full_name: "" });
    const [busy, setBusy] = useState(false);

    const submit = async (e) => {
        e.preventDefault();
        setBusy(true);
        try {
            if (isLogin) {
                await login(form.email, form.password);
                toast.success("Welcome back");
            } else {
                if (!form.full_name) throw new Error("Name required");
                await register(form.email, form.password, form.full_name);
                toast.success("Account created");
            }
            nav("/dashboard");
        } catch (err) {
            toast.error(err?.response?.data?.detail || err.message || "Failed");
        } finally { setBusy(false); }
    };

    return (
        <div className="min-h-screen grid grid-cols-1 lg:grid-cols-2 bg-[#0A0A0B]">
            {/* Left - Form */}
            <div className="flex items-center justify-center p-8 lg:p-16">
                <div className="w-full max-w-md" data-testid={isLogin ? "login-form" : "register-form"}>
                    <Link to="/" className="flex items-center gap-2.5 mb-12">
                        <div className="w-8 h-8 rounded-md bg-[#F23F42] grid place-items-center glow-red">
                            <Clapperboard className="w-4 h-4 text-white" strokeWidth={2.5} />
                        </div>
                        <span className="font-display font-black text-lg tracking-tighter">VIDEOFORGE</span>
                    </Link>

                    <div className="font-mono-tag text-[#F23F42] mb-3">/ {isLogin ? "WELCOME BACK" : "JOIN US"}</div>
                    <h1 className="font-display text-4xl font-black tracking-tighter">
                        {isLogin ? "Sign in" : "Create account"}
                    </h1>
                    <p className="mt-3 text-zinc-400 text-sm">
                        {isLogin ? "Continue building your channel." : "Start with 100 free credits."}
                    </p>

                    <form onSubmit={submit} className="mt-10 space-y-5">
                        {!isLogin && (
                            <div>
                                <Label className="font-mono-tag text-zinc-500">Full name</Label>
                                <Input
                                    data-testid="register-name-input"
                                    type="text"
                                    value={form.full_name}
                                    onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                                    placeholder="Jane Creator"
                                    required
                                    className="mt-2 h-12 bg-[#121214] border-white/10 text-white focus-visible:ring-1 focus-visible:ring-[#F23F42] focus-visible:border-[#F23F42] rounded-md"
                                />
                            </div>
                        )}
                        <div>
                            <Label className="font-mono-tag text-zinc-500">Email</Label>
                            <Input
                                data-testid={isLogin ? "login-email-input" : "register-email-input"}
                                type="email"
                                value={form.email}
                                onChange={(e) => setForm({ ...form, email: e.target.value })}
                                placeholder="you@studio.com"
                                required
                                className="mt-2 h-12 bg-[#121214] border-white/10 text-white focus-visible:ring-1 focus-visible:ring-[#F23F42] focus-visible:border-[#F23F42] rounded-md"
                            />
                        </div>
                        <div>
                            <Label className="font-mono-tag text-zinc-500">Password</Label>
                            <Input
                                data-testid={isLogin ? "login-password-input" : "register-password-input"}
                                type="password"
                                value={form.password}
                                onChange={(e) => setForm({ ...form, password: e.target.value })}
                                placeholder="••••••••"
                                minLength={6}
                                required
                                className="mt-2 h-12 bg-[#121214] border-white/10 text-white focus-visible:ring-1 focus-visible:ring-[#F23F42] focus-visible:border-[#F23F42] rounded-md"
                            />
                        </div>
                        <Button
                            type="submit" disabled={busy}
                            data-testid={isLogin ? "login-submit-btn" : "register-submit-btn"}
                            className="w-full h-12 bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md font-semibold mt-4"
                        >
                            {busy ? "Please wait..." : (isLogin ? "Sign in" : "Create account")}
                            <ArrowRight className="ml-2 w-4 h-4" />
                        </Button>
                    </form>

                    <div className="mt-8 text-sm text-zinc-500">
                        {isLogin ? "New here?" : "Already have an account?"}{" "}
                        <Link
                            to={isLogin ? "/register" : "/login"}
                            className="text-[#F23F42] hover:text-[#FF5C5E] font-semibold"
                            data-testid={isLogin ? "go-to-register-link" : "go-to-login-link"}
                        >
                            {isLogin ? "Create account" : "Sign in"}
                        </Link>
                    </div>
                </div>
            </div>

            {/* Right - Visual */}
            <div className="hidden lg:block relative overflow-hidden border-l border-white/10">
                <div
                    className="absolute inset-0"
                    style={{
                        backgroundImage:
                            "url(https://images.unsplash.com/photo-1762009365851-c5b5b1aae3b9?crop=entropy&cs=srgb&fm=jpg&w=2000&q=85)",
                        backgroundSize: "cover", backgroundPosition: "center",
                    }}
                />
                <div className="absolute inset-0 bg-gradient-to-br from-black/70 via-black/40 to-[#F23F42]/20" />
                <div className="relative h-full flex items-end p-12">
                    <div className="max-w-md">
                        <div className="font-mono-tag text-[#F23F42] mb-3">/ TRUSTED BY 12,400+ CREATORS</div>
                        <p className="font-display text-3xl font-bold tracking-tighter leading-tight">
                            "I shipped 47 videos in my first month. My channel hit monetization in 60 days."
                        </p>
                        <div className="mt-6 text-zinc-400 text-sm">— Marcus K., Finance Channel</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
