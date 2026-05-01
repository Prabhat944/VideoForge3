import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../lib/api";
import NavBar from "../components/NavBar";
import { motion } from "framer-motion";
import { Calendar, Loader2, Youtube, Clock, Film, ExternalLink, CheckCircle2 } from "lucide-react";

function formatDate(iso) {
    if (!iso) return "—";
    try {
        const d = new Date(iso);
        return d.toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
    } catch { return iso; }
}

function groupByDay(items) {
    const out = {};
    for (const it of items) {
        const when = it.scheduled_at || it.published_at || it.when;
        if (!when) continue;
        const d = new Date(when);
        const key = `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")}`;
        out[key] = out[key] || { date: d, items: [] };
        out[key].items.push(it);
    }
    return Object.entries(out).sort(([a], [b]) => a.localeCompare(b));
}

export default function CalendarPage() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get("/calendar").then((r) => setData(r.data)).finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0A0A0B]">
                <NavBar />
                <div className="grid place-items-center py-32"><Loader2 className="w-8 h-8 text-[#F23F42] animate-spin" /></div>
            </div>
        );
    }

    const groups = groupByDay(data.items);
    const scheduled = data.items.filter(i => i.status === "scheduled");
    const published = data.items.filter(i => i.status === "published");

    return (
        <div className="min-h-screen bg-[#0A0A0B]" data-testid="calendar-page">
            <NavBar />
            <div className="max-w-7xl mx-auto px-6 lg:px-12 py-12">
                <div className="font-mono-tag text-[#F23F42] mb-3">/ CONTENT CALENDAR</div>
                <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter">
                    Your publish queue.
                </h1>
                <p className="mt-3 text-zinc-400">All scheduled and published videos in one timeline.</p>

                {/* Stats */}
                <div className="mt-10 grid grid-cols-2 lg:grid-cols-3 gap-px bg-white/10 rounded-md overflow-hidden border border-white/10">
                    <Stat icon={Clock} label="Scheduled" value={scheduled.length} />
                    <Stat icon={CheckCircle2} label="Published" value={published.length} />
                    <Stat icon={Youtube} label="Real uploads" value={data.items.filter(i => i.real).length} />
                </div>

                {data.items.length === 0 ? (
                    <div className="mt-12 border border-dashed border-white/10 rounded-md p-16 text-center" data-testid="calendar-empty">
                        <Calendar className="w-12 h-12 text-zinc-700 mx-auto" strokeWidth={1.2} />
                        <div className="mt-4 font-display text-2xl font-bold">Empty calendar</div>
                        <div className="mt-2 text-zinc-500">Schedule or publish a video to see it here.</div>
                        <Link to="/wizard">
                            <button className="mt-6 bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md px-5 h-11 font-semibold">
                                Create video
                            </button>
                        </Link>
                    </div>
                ) : (
                    <div className="mt-12 space-y-4">
                        {groups.map(([key, g], idx) => (
                            <motion.div
                                key={key} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.04 }}
                                className="grid grid-cols-1 md:grid-cols-[140px_1fr] gap-4 md:gap-8 border border-white/10 bg-[#121214] rounded-md p-6"
                                data-testid={`calendar-day-${key}`}
                            >
                                <div className="md:border-r md:border-white/10 md:pr-6">
                                    <div className="font-display text-3xl font-black tracking-tighter">
                                        {g.date.getDate()}
                                    </div>
                                    <div className="font-mono-tag text-zinc-500 mt-1">
                                        {g.date.toLocaleDateString("en-US", { month: "short", weekday: "short" })}
                                    </div>
                                </div>
                                <div className="space-y-3">
                                    {g.items.map((it) => (
                                        <Link to={`/wizard/${it.project_id}`} key={it.project_id}
                                            className="flex items-center gap-4 p-3 rounded-md border border-white/5 bg-black/30 hover:border-white/20 transition-all"
                                            data-testid={`calendar-item-${it.project_id}`}>
                                            <div className="w-20 aspect-video rounded bg-black flex-shrink-0 overflow-hidden">
                                                {it.thumbnail_url ? (
                                                    <img src={it.thumbnail_url} alt="" className="w-full h-full object-cover" />
                                                ) : (
                                                    <div className="w-full h-full bg-gradient-to-br from-zinc-800 to-black grid place-items-center">
                                                        <Film className="w-5 h-5 text-zinc-700" />
                                                    </div>
                                                )}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="font-semibold truncate">{it.title}</div>
                                                <div className="text-xs text-zinc-500 mt-0.5">{formatDate(it.when)}</div>
                                            </div>
                                            <StatusPill status={it.status} real={it.real} />
                                            {it.youtube_url && (
                                                <a href={it.youtube_url} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}
                                                    className="text-zinc-500 hover:text-[#F23F42]">
                                                    <ExternalLink className="w-4 h-4" />
                                                </a>
                                            )}
                                        </Link>
                                    ))}
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

function Stat({ icon: Icon, label, value }) {
    return (
        <div className="bg-[#121214] p-6">
            <Icon className="w-5 h-5 text-[#F23F42]" />
            <div className="font-display text-3xl font-black mt-4">{value}</div>
            <div className="font-mono-tag text-zinc-500 mt-1">{label}</div>
        </div>
    );
}

function StatusPill({ status, real }) {
    const map = {
        scheduled: { c: "bg-amber-500/10 text-amber-400 border-amber-500/30", l: "SCHEDULED" },
        published: real
            ? { c: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30", l: "LIVE" }
            : { c: "bg-blue-500/10 text-blue-400 border-blue-500/30", l: "MOCK" },
        rendered: { c: "bg-purple-500/10 text-purple-400 border-purple-500/30", l: "RENDERED" },
    };
    const x = map[status] || { c: "bg-white/5 text-zinc-400 border-white/10", l: status?.toUpperCase() || "" };
    return <span className={`font-mono-tag px-2 py-1 rounded-md border ${x.c}`}>{x.l}</span>;
}
