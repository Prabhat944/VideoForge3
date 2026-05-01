import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import api from "../lib/api";
import NavBar from "../components/NavBar";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";
import { Eye, ThumbsUp, Clock, Percent, Lightbulb, Loader2, Youtube, Sparkles } from "lucide-react";

export default function Analytics() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get("/analytics/summary").then((r) => setData(r.data)).finally(() => setLoading(false));
    }, []);

    if (loading) return (
        <div className="min-h-screen bg-[#0A0A0B]"><NavBar />
            <div className="grid place-items-center py-32"><Loader2 className="w-8 h-8 text-[#F23F42] animate-spin" /></div>
        </div>
    );

    const stats = [
        { l: "Total Views", v: data.totals.views.toLocaleString(), i: Eye },
        { l: "Likes", v: data.totals.likes.toLocaleString(), i: ThumbsUp },
        { l: "Watch Time (min)", v: data.totals.watch_time_minutes.toLocaleString(), i: Clock },
        { l: "Avg CTR", v: `${data.totals.avg_ctr}%`, i: Percent },
    ];

    return (
        <div className="min-h-screen bg-[#0A0A0B]" data-testid="analytics-page">
            <NavBar />
            <div className="max-w-7xl mx-auto px-6 lg:px-12 py-12">
                <div className="font-mono-tag text-[#F23F42] mb-3">/ CHANNEL BRAIN</div>
                <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter">Analytics</h1>
                <p className="mt-3 text-zinc-400">Performance, retention, and AI recommendations.</p>

                {data.data_source === "youtube" ? (
                    <div className="mt-6 inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-emerald-500/30 bg-emerald-500/5" data-testid="analytics-real-badge">
                        <Youtube className="w-4 h-4 text-emerald-400" />
                        <span className="font-mono-tag text-emerald-400">LIVE · YOUTUBE DATA</span>
                    </div>
                ) : (
                    <div className="mt-6 inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-amber-500/30 bg-amber-500/5" data-testid="analytics-synthetic-badge">
                        <Sparkles className="w-4 h-4 text-amber-400" />
                        <span className="font-mono-tag text-amber-400">DEMO DATA · CONNECT YOUTUBE FOR LIVE METRICS</span>
                    </div>
                )}

                <div className="mt-10 grid grid-cols-2 lg:grid-cols-4 gap-px bg-white/10 rounded-md overflow-hidden border border-white/10">
                    {stats.map((s) => (
                        <div key={s.l} className="bg-[#121214] p-6">
                            <s.i className="w-5 h-5 text-[#F23F42]" />
                            <div className="font-display text-3xl font-black mt-4">{s.v}</div>
                            <div className="font-mono-tag text-zinc-500 mt-1">{s.l}</div>
                        </div>
                    ))}
                </div>

                <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2 border border-white/10 bg-[#121214] rounded-md p-6" data-testid="analytics-views-chart">
                        <div className="font-mono-tag text-zinc-500 mb-4">VIEWS · LAST 14 DAYS</div>
                        <ResponsiveContainer width="100%" height={300}>
                            <AreaChart data={data.series}>
                                <defs>
                                    <linearGradient id="vg" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#F23F42" stopOpacity={0.5} />
                                        <stop offset="100%" stopColor="#F23F42" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                                <XAxis dataKey="date" stroke="#52525B" tick={{ fontSize: 11 }} />
                                <YAxis stroke="#52525B" tick={{ fontSize: 11 }} />
                                <Tooltip contentStyle={{ background: "#121214", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6 }} />
                                <Area type="monotone" dataKey="views" stroke="#F23F42" strokeWidth={2} fill="url(#vg)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="border border-white/10 bg-[#121214] rounded-md p-6" data-testid="analytics-suggestions">
                        <div className="font-mono-tag text-[#F23F42] mb-4">/ AI SUGGESTIONS</div>
                        <ul className="space-y-3">
                            {data.suggestions.map((s, i) => (
                                <li key={i} className="flex items-start gap-3 text-sm text-zinc-300">
                                    <Lightbulb className="w-4 h-4 text-[#F23F42] flex-shrink-0 mt-0.5" />
                                    <span>{s}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                <div className="mt-8 border border-white/10 bg-[#121214] rounded-md overflow-hidden">
                    <div className="px-6 py-4 border-b border-white/10 font-mono-tag text-zinc-500">VIDEOS</div>
                    {data.rows.length === 0 ? (
                        <div className="p-12 text-center text-zinc-500">No published videos yet. Publish from the wizard to see data.</div>
                    ) : (
                        <div className="divide-y divide-white/5">
                            {data.rows.map((r, i) => (
                                <motion.div key={r.project_id}
                                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }}
                                    className="p-5 flex items-center gap-4 hover:bg-white/5 transition-colors"
                                    data-testid={`analytics-row-${r.project_id}`}>
                                    <div className="w-24 aspect-video rounded-md overflow-hidden bg-black flex-shrink-0">
                                        {r.thumbnail_url ? (
                                            <img src={r.thumbnail_url} alt="" className="w-full h-full object-cover" />
                                        ) : (
                                            <div className="w-full h-full bg-gradient-to-br from-zinc-800 to-black" />
                                        )}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="font-semibold truncate">{r.title}</div>
                                        <a href={r.youtube_url} target="_blank" rel="noreferrer" className="text-xs text-zinc-500 hover:text-[#F23F42]">
                                            {r.youtube_url}
                                        </a>
                                    </div>
                                    <div className="hidden sm:grid grid-cols-3 gap-6 text-right">
                                        <div>
                                            <div className="font-mono-tag text-zinc-500">VIEWS</div>
                                            <div className="font-display font-bold">{r.views.toLocaleString()}</div>
                                        </div>
                                        <div>
                                            <div className="font-mono-tag text-zinc-500">CTR</div>
                                            <div className="font-display font-bold">{r.ctr}%</div>
                                        </div>
                                        <div>
                                            <div className="font-mono-tag text-zinc-500">WATCH</div>
                                            <div className="font-display font-bold">{r.watch_time_minutes}m</div>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
