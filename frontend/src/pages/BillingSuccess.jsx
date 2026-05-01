import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import api from "../lib/api";
import NavBar from "../components/NavBar";
import { Button } from "../components/ui/button";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";

export default function BillingSuccess() {
    const [params] = useSearchParams();
    const sessionId = params.get("session_id");
    const nav = useNavigate();
    const [status, setStatus] = useState("checking");
    const [data, setData] = useState(null);

    useEffect(() => {
        if (!sessionId) { setStatus("invalid"); return; }
        let attempts = 0;
        const max = 8;
        const poll = async () => {
            try {
                const r = await api.get(`/billing/status/${sessionId}`);
                setData(r.data);
                if (r.data.payment_status === "paid") {
                    setStatus("paid");
                    // Refresh user
                    api.get("/auth/me").then((u) => {
                        localStorage.setItem("vf_user", JSON.stringify(u.data));
                    });
                    return;
                }
                if (r.data.status === "expired") { setStatus("expired"); return; }
                if (++attempts < max) setTimeout(poll, 2000);
                else setStatus("timeout");
            } catch {
                if (++attempts < max) setTimeout(poll, 2000);
                else setStatus("error");
            }
        };
        poll();
    }, [sessionId]);

    return (
        <div className="min-h-screen bg-[#0A0A0B]" data-testid="billing-success-page">
            <NavBar />
            <div className="max-w-2xl mx-auto px-6 py-24 text-center">
                <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
                    {status === "checking" && (
                        <>
                            <Loader2 className="w-16 h-16 text-[#F23F42] mx-auto animate-spin" />
                            <h1 className="font-display text-4xl font-black tracking-tighter mt-8">Confirming payment...</h1>
                            <p className="mt-3 text-zinc-400">Please wait, this should only take a few seconds.</p>
                        </>
                    )}
                    {status === "paid" && (
                        <>
                            <CheckCircle2 className="w-20 h-20 text-emerald-500 mx-auto" />
                            <h1 className="font-display text-5xl font-black tracking-tighter mt-8">You're in.</h1>
                            <p className="mt-4 text-zinc-400 text-lg">
                                Payment received. {data && `${(data.amount_total / 100).toFixed(2)} ${data.currency.toUpperCase()}`}.
                                Credits added to your account.
                            </p>
                            <Button onClick={() => nav("/dashboard")} data-testid="billing-success-dashboard-btn"
                                className="mt-10 bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md h-12 px-8 font-semibold">
                                Go to dashboard
                            </Button>
                        </>
                    )}
                    {(status === "expired" || status === "error" || status === "timeout" || status === "invalid") && (
                        <>
                            <XCircle className="w-20 h-20 text-red-500 mx-auto" />
                            <h1 className="font-display text-4xl font-black tracking-tighter mt-8">
                                {status === "expired" ? "Session expired" : "Payment not confirmed"}
                            </h1>
                            <p className="mt-3 text-zinc-400">Please try again or contact support if charged.</p>
                            <Button onClick={() => nav("/pricing")} variant="outline"
                                className="mt-8 bg-white/5 border-white/10 text-white hover:bg-white/10 rounded-md">
                                Back to pricing
                            </Button>
                        </>
                    )}
                </motion.div>
            </div>
        </div>
    );
}
