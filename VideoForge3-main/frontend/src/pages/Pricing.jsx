import { Link } from "react-router-dom";
import api from "../lib/api";
import NavBar from "../components/NavBar";
import { Button } from "../components/ui/button";
import { Check, Sparkles, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { useAuth } from "../lib/auth";

const tiers = [
    {
        id: "free", name: "Free", price: 0, period: "forever",
        desc: "Perfect to test the waters.",
        features: ["100 credits/month", "Standard voices", "AI script & thumbnail", "Manual YouTube upload", "Basic analytics"],
        cta: "Start free", to: "/register", featured: false,
    },
    {
        id: "creator", name: "Creator", price: 29, period: "per month",
        desc: "For solo creators shipping weekly.",
        features: ["1,500 credits/month", "Premium voices (HD + ElevenLabs)", "Auto YouTube upload + scheduling", "Trends discovery", "Bulk series (10/click)", "A/B testing"],
        cta: "Go Creator", featured: true,
    },
    {
        id: "studio", name: "Studio", price: 99, period: "per month",
        desc: "For serious content factories.",
        features: ["Unlimited credits", "All ElevenLabs voices", "Multi-channel management", "30-video bulk series", "Priority generation", "Custom niche templates", "Analytics + insights"],
        cta: "Go Studio", featured: false,
    },
];

export default function Pricing() {
    const { user } = useAuth();
    const [busy, setBusy] = useState(null);

    const checkout = async (planId) => {
        if (!user) { window.location.href = "/register"; return; }
        setBusy(planId);
        try {
            const r = await api.post("/billing/checkout", {
                plan_id: planId,
                origin_url: window.location.origin,
            });
            window.location.href = r.data.url;
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Checkout failed");
            setBusy(null);
        }
    };

    return (
        <div className="min-h-screen bg-[#0A0A0B]" data-testid="pricing-page">
            <NavBar />
            <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">
                <div className="text-center max-w-3xl mx-auto">
                    <div className="font-mono-tag text-[#F23F42] mb-4">/ PRICING</div>
                    <h1 className="font-display text-5xl sm:text-6xl font-black tracking-tighter">
                        Pay for output. Not seats.
                    </h1>
                    <p className="mt-6 text-zinc-400 text-lg">
                        Start free. Upgrade when you're shipping weekly.
                    </p>
                </div>

                <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
                    {tiers.map((t) => (
                        <div key={t.name}
                            data-testid={`pricing-tier-${t.id}`}
                            className={`relative rounded-md p-8 ${
                                t.featured
                                    ? "border border-[#F23F42] bg-[#F23F42]/5 glow-red"
                                    : "border border-white/10 bg-[#121214]"
                            }`}>
                            {t.featured && (
                                <div className="absolute -top-3 left-8 font-mono-tag bg-[#F23F42] text-white px-3 py-1 rounded-md flex items-center gap-1.5">
                                    <Sparkles className="w-3 h-3" /> POPULAR
                                </div>
                            )}
                            <div className="font-display text-2xl font-bold">{t.name}</div>
                            <div className="mt-1 text-sm text-zinc-400">{t.desc}</div>
                            <div className="mt-6 flex items-baseline gap-2">
                                <div className="font-display text-5xl font-black tracking-tighter">${t.price}</div>
                                <div className="font-mono-tag text-zinc-500">/{t.period}</div>
                            </div>
                            {t.id === "free" ? (
                                <Link to="/register" className="block mt-6">
                                    <Button data-testid={`pricing-cta-${t.id}`}
                                        className="w-full h-12 rounded-md font-semibold bg-white/5 border border-white/10 text-white hover:bg-white/10">
                                        {t.cta}
                                    </Button>
                                </Link>
                            ) : (
                                <Button onClick={() => checkout(t.id)} disabled={busy === t.id}
                                    data-testid={`pricing-cta-${t.id}`}
                                    className={`w-full h-12 rounded-md font-semibold mt-6 ${
                                        t.featured
                                            ? "bg-[#F23F42] hover:bg-[#FF5C5E] text-white"
                                            : "bg-white/5 border border-white/10 text-white hover:bg-white/10"
                                    }`}>
                                    {busy === t.id ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                                    {t.cta}
                                </Button>
                            )}
                            <ul className="mt-8 space-y-3">
                                {t.features.map((f) => (
                                    <li key={f} className="flex items-start gap-3 text-sm text-zinc-300">
                                        <Check className="w-4 h-4 text-[#F23F42] flex-shrink-0 mt-0.5" />
                                        <span>{f}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>

                <div className="mt-20 border border-white/10 bg-[#121214] rounded-md p-8 max-w-3xl mx-auto text-center">
                    <h3 className="font-display text-2xl font-bold tracking-tight">Need just a few?</h3>
                    <p className="mt-2 text-zinc-400 text-sm">
                        Buy a credit pack: <span className="text-[#F23F42] font-semibold">$5 / 100 credits</span>.
                    </p>
                    <Button onClick={() => checkout("credits_100")} disabled={busy === "credits_100"}
                        data-testid="pricing-cta-credits_100"
                        className="mt-6 bg-white/5 border border-white/10 text-white hover:bg-white/10 rounded-md">
                        {busy === "credits_100" ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                        Buy 100 credits — $5
                    </Button>
                </div>
            </div>
        </div>
    );
}
