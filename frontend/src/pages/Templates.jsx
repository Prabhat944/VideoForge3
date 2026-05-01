import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
    Layers, Loader2, ArrowRight, DollarSign, Skull, Flame, Brain, Sparkles, Hash,
} from "lucide-react";

import api from "../lib/api";
import NavBar from "../components/NavBar";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";

const NICHE_META = {
    finance: { icon: DollarSign, color: "#10B981", label: "Finance" },
    horror: { icon: Skull, color: "#EF4444", label: "Horror" },
    motivation: { icon: Flame, color: "#F59E0B", label: "Motivation" },
    facts: { icon: Brain, color: "#8B5CF6", label: "Facts" },
    general: { icon: Sparkles, color: "#F23F42", label: "General" },
};

const FILTERS = ["all", "finance", "horror", "motivation", "facts"];

export default function Templates() {
    const nav = useNavigate();
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState("all");
    const [topicOverride, setTopicOverride] = useState({});
    const [usingId, setUsingId] = useState(null);

    useEffect(() => {
        api.get("/templates").then((r) => setItems(r.data.templates || [])).finally(() => setLoading(false));
    }, []);

    const filtered = useMemo(
        () => filter === "all" ? items : items.filter((t) => t.niche === filter),
        [items, filter]
    );

    const handleUseTemplate = async (tpl) => {
        setUsingId(tpl.id);
        try {
            const r = await api.post("/projects/from-template", {
                template_id: tpl.id,
                topic: topicOverride[tpl.id] || null,
            });
            toast.success("Project ready · jumping into wizard");
            nav(`/wizard/${r.data.id}`);
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Failed to use template");
        } finally {
            setUsingId(null);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0A0A0B]">
                <NavBar />
                <div className="grid place-items-center py-32"><Loader2 className="w-8 h-8 text-[#F23F42] animate-spin" /></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0A0A0B]" data-testid="templates-page">
            <NavBar />
            <div className="max-w-7xl mx-auto px-6 lg:px-12 py-12">
                <div className="font-mono-tag text-[#F23F42] mb-3">/ NICHE TEMPLATES</div>
                <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter">
                    Pre-tuned. Battle-tested. Ready to ship.
                </h1>
                <p className="mt-3 text-zinc-400 max-w-2xl">
                    Start from a template that already has the right tone, voice, thumbnail style and duration
                    for its niche — finance, horror, motivation or mind-bending facts.
                </p>

                {/* Filter pills */}
                <div className="mt-8 flex flex-wrap gap-2">
                    {FILTERS.map((f) => (
                        <button
                            key={f}
                            data-testid={`filter-${f}`}
                            onClick={() => setFilter(f)}
                            className={`px-4 py-1.5 rounded-full font-mono-tag text-xs uppercase transition ${
                                filter === f
                                    ? "bg-[#F23F42] text-white"
                                    : "border border-white/10 text-zinc-400 hover:text-white hover:bg-white/5"
                            }`}>
                            {f}
                        </button>
                    ))}
                </div>

                {/* Grid */}
                <div className="mt-8 grid md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {filtered.map((tpl) => {
                        const meta = NICHE_META[tpl.niche] || NICHE_META.general;
                        const Icon = meta.icon;
                        return (
                            <motion.div
                                key={tpl.id}
                                initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                                data-testid={`template-card-${tpl.id}`}
                                className="rounded-xl border border-white/10 bg-[#121214] p-5 hover:border-white/20 transition flex flex-col">
                                <div className="flex items-center gap-2">
                                    <div className="w-9 h-9 rounded-md grid place-items-center" style={{ backgroundColor: `${meta.color}22` }}>
                                        <Icon className="w-4 h-4" style={{ color: meta.color }} />
                                    </div>
                                    <div>
                                        <div className="font-mono-tag text-[10px] text-zinc-500 uppercase">{meta.label}</div>
                                        <div className="font-display text-lg font-bold tracking-tight" data-testid={`template-name-${tpl.id}`}>
                                            {tpl.name}
                                        </div>
                                    </div>
                                </div>
                                <p className="text-zinc-400 text-sm mt-3 leading-relaxed flex-1">{tpl.description}</p>

                                <div className="mt-3 grid grid-cols-3 gap-2 text-[11px] font-mono-tag uppercase text-zinc-500">
                                    <div>
                                        <div className="text-zinc-500">DUR</div>
                                        <div className="text-zinc-200">{tpl.duration_seconds}s</div>
                                    </div>
                                    <div>
                                        <div className="text-zinc-500">TONE</div>
                                        <div className="text-zinc-200">{tpl.tone}</div>
                                    </div>
                                    <div>
                                        <div className="text-zinc-500">VOICE</div>
                                        <div className="text-zinc-200">{tpl.voice}</div>
                                    </div>
                                </div>

                                <div className="mt-3 flex flex-wrap gap-1">
                                    {(tpl.default_tags || []).slice(0, 4).map((t, i) => (
                                        <span key={i} className="text-[10px] font-mono-tag text-zinc-400 px-2 py-0.5 rounded border border-white/10">
                                            <Hash className="w-2.5 h-2.5 inline mr-0.5" />{t}
                                        </span>
                                    ))}
                                </div>

                                <div className="mt-4 space-y-2">
                                    <Input
                                        data-testid={`topic-input-${tpl.id}`}
                                        placeholder={tpl.topic_template}
                                        value={topicOverride[tpl.id] || ""}
                                        onChange={(e) => setTopicOverride((p) => ({ ...p, [tpl.id]: e.target.value }))}
                                        className="bg-[#0A0A0B] border-white/10 text-sm"
                                    />
                                    <Button
                                        onClick={() => handleUseTemplate(tpl)}
                                        disabled={usingId === tpl.id}
                                        data-testid={`use-template-${tpl.id}`}
                                        className="w-full bg-[#F23F42] hover:bg-[#FF5C5E] text-white">
                                        {usingId === tpl.id
                                            ? (<><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Creating…</>)
                                            : (<><Layers className="w-4 h-4 mr-2" /> Use template <ArrowRight className="w-4 h-4 ml-1" /></>)}
                                    </Button>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>

                {filtered.length === 0 && (
                    <div className="mt-12 rounded-xl border border-dashed border-white/10 p-16 text-center">
                        <Layers className="w-10 h-10 mx-auto text-zinc-600 mb-3" />
                        <h3 className="font-display text-2xl font-bold tracking-tight">No templates in this niche yet.</h3>
                        <p className="text-zinc-500 mt-2">Try a different filter.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
