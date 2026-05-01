import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import api from "../lib/api";
import NavBar from "../components/NavBar";
import { Button } from "../components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Loader2, TrendingUp, Flame, Wand2, RefreshCw } from "lucide-react";
import { toast } from "sonner";

const NICHES = ["general", "finance", "horror", "motivation", "education", "facts"];
const SOURCES = [
    { id: "ai", label: "AI Suggested" },
    { id: "youtube", label: "YouTube Trending" },
    { id: "reddit", label: "Reddit Hot" },
    { id: "google_trends", label: "Google Trends" },
];

export default function Trends() {
    const nav = useNavigate();
    const [niche, setNiche] = useState("general");
    const [source, setSource] = useState("ai");
    const [trends, setTrends] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetch = async () => {
        setLoading(true);
        try {
            const r = await api.get(`/trends?niche=${niche}&source=${source}`);
            setTrends(r.data.trends);
        } catch { toast.error("Failed to fetch trends"); }
        finally { setLoading(false); }
    };

    useEffect(() => { fetch(); /* eslint-disable-next-line */ }, [niche, source]);

    const pickTopic = async (t) => {
        try {
            const r = await api.post("/projects", {
                topic: t.title, audience: "general", duration_seconds: 60,
                tone: "engaging", language: "English",
                style: "storytelling", niche,
            });
            toast.success("Project created");
            nav(`/wizard/${r.data.id}`);
        } catch { toast.error("Failed"); }
    };

    return (
        <div className="min-h-screen bg-[#0A0A0B]" data-testid="trends-page">
            <NavBar />
            <div className="max-w-7xl mx-auto px-6 lg:px-12 py-12">
                <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-10">
                    <div>
                        <div className="font-mono-tag text-[#F23F42] mb-3">/ TREND ENGINE</div>
                        <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter">What's blowing up</h1>
                        <p className="mt-3 text-zinc-400">Trending video ideas with viral score & competition.</p>
                    </div>
                    <Button onClick={fetch} variant="outline"
                        data-testid="trends-refresh-btn"
                        className="bg-white/5 border-white/10 text-white hover:bg-white/10 rounded-md">
                        <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} /> Refresh
                    </Button>
                </div>

                <div className="flex flex-wrap items-center gap-2 mb-3">
                    {NICHES.map((n) => (
                        <button key={n} onClick={() => setNiche(n)}
                            data-testid={`trends-niche-${n}`}
                            className={`font-mono-tag px-3 py-1.5 rounded-md border transition-all capitalize ${
                                niche === n ? "bg-[#F23F42] border-[#F23F42] text-white" : "bg-white/5 border-white/10 text-zinc-400 hover:text-white"
                            }`}>
                            {n}
                        </button>
                    ))}
                </div>
                <div className="flex flex-wrap items-center gap-2 mb-10">
                    {SOURCES.map((s) => (
                        <button key={s.id} onClick={() => setSource(s.id)}
                            data-testid={`trends-source-${s.id}`}
                            className={`text-xs px-3 py-1.5 rounded-md border transition-all ${
                                source === s.id ? "bg-white/10 border-white/30 text-white" : "bg-transparent border-white/10 text-zinc-500 hover:text-white"
                            }`}>
                            {s.label}
                        </button>
                    ))}
                </div>

                {loading ? (
                    <div className="grid place-items-center py-20"><Loader2 className="w-8 h-8 text-[#F23F42] animate-spin" /></div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {trends.map((t, i) => (
                            <motion.div key={i}
                                initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
                                className="border border-white/10 bg-[#121214] rounded-md p-6 hover:border-white/30 transition-all"
                                data-testid={`trend-card-${i}`}>
                                <div className="flex items-center justify-between mb-3">
                                    <span className="font-mono-tag text-zinc-500">{t.platform}</span>
                                    <ScoreBadge score={t.viral_score} />
                                </div>
                                <h3 className="font-display text-lg font-bold tracking-tight">{t.title}</h3>
                                <p className="mt-2 text-sm text-zinc-400 line-clamp-2">{t.description}</p>
                                <div className="mt-4 flex flex-wrap gap-1.5">
                                    {(t.suggested_tags || []).slice(0, 4).map((tag) => (
                                        <span key={tag} className="text-[10px] font-mono-tag px-2 py-0.5 rounded-md border border-white/10 bg-black/30 text-zinc-400">
                                            #{tag}
                                        </span>
                                    ))}
                                </div>
                                <div className="mt-5 flex items-center justify-between">
                                    <span className={`font-mono-tag ${
                                        t.competition === "low" ? "text-emerald-400" :
                                        t.competition === "medium" ? "text-amber-400" : "text-red-400"
                                    }`}>
                                        {t.competition} comp
                                    </span>
                                    <Button onClick={() => pickTopic(t)} size="sm"
                                        data-testid={`trend-use-${i}`}
                                        className="bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md">
                                        <Wand2 className="w-3.5 h-3.5 mr-1.5" /> Use
                                    </Button>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

function ScoreBadge({ score }) {
    const color = score >= 85 ? "text-red-400" : score >= 70 ? "text-amber-400" : "text-zinc-400";
    return (
        <div className={`flex items-center gap-1 ${color}`}>
            <Flame className="w-3.5 h-3.5" />
            <span className="font-display font-black text-sm">{score}</span>
        </div>
    );
}
