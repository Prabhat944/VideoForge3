import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import api from "../lib/api";
import NavBar from "../components/NavBar";
import { Button } from "../components/ui/button";
import { Plus, Film, Eye, Clock, TrendingUp, ExternalLink, Trash2, Youtube, CheckCircle2, Unlink } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "../lib/auth";

const StatusBadge = ({ status }) => {
    const map = {
        draft: { c: "bg-white/5 text-zinc-400 border-white/10", l: "DRAFT" },
        script_ready: { c: "bg-blue-500/10 text-blue-400 border-blue-500/30", l: "SCRIPT" },
        voice_ready: { c: "bg-purple-500/10 text-purple-400 border-purple-500/30", l: "VOICE" },
        published: { c: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30", l: "LIVE" },
        scheduled: { c: "bg-amber-500/10 text-amber-400 border-amber-500/30", l: "SCHEDULED" },
    };
    const x = map[status] || map.draft;
    return <span className={`font-mono-tag px-2 py-1 rounded-md border ${x.c}`}>{x.l}</span>;
};

export default function Dashboard() {
    const { user } = useAuth();
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);

    const load = async () => {
        try {
            const r = await api.get("/projects");
            setProjects(r.data);
        } catch (e) { toast.error("Failed to load projects"); }
        finally { setLoading(false); }
    };

    useEffect(() => { load(); }, []);

    const remove = async (id) => {
        if (!window.confirm("Delete this project?")) return;
        try {
            await api.delete(`/projects/${id}`);
            toast.success("Deleted");
            load();
        } catch { toast.error("Failed"); }
    };

    const stats = [
        { l: "Projects", v: projects.length, i: Film },
        { l: "Published", v: projects.filter(p => p.status === "published" || p.status === "scheduled").length, i: TrendingUp },
        { l: "Drafts", v: projects.filter(p => p.status === "draft").length, i: Clock },
        { l: "Credits", v: user?.credits ?? 0, i: Eye },
    ];

    return (
        <div className="min-h-screen bg-[#0A0A0B]" data-testid="dashboard-page">
            <NavBar />
            <div className="max-w-7xl mx-auto px-6 lg:px-12 py-12">
                <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-12">
                    <div>
                        <div className="font-mono-tag text-[#F23F42] mb-3">/ STUDIO</div>
                        <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter">
                            Hello, {user?.full_name?.split(" ")[0] || "Creator"}.
                        </h1>
                        <p className="mt-3 text-zinc-400">Your AI video production line.</p>
                    </div>
                    <Link to="/wizard" data-testid="dashboard-new-video-btn">
                        <Button className="bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md h-12 px-6 font-semibold">
                            <Plus className="w-4 h-4 mr-2" /> New video
                        </Button>
                    </Link>
                </div>

                <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-white/10 mb-8 rounded-md overflow-hidden border border-white/10">
                    {stats.map((s) => (
                        <div key={s.l} className="bg-[#121214] p-6">
                            <s.i className="w-5 h-5 text-[#F23F42]" />
                            <div className="font-display text-3xl font-black mt-4">{s.v}</div>
                            <div className="font-mono-tag text-zinc-500 mt-1">{s.l}</div>
                        </div>
                    ))}
                </div>

                {/* YouTube Connection */}
                <div className="mb-12 border border-white/10 bg-[#121214] rounded-md p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4" data-testid="youtube-connection-card">
                    <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-md grid place-items-center ${yt.connected ? "bg-emerald-500/10 border border-emerald-500/30" : "bg-[#F23F42]/10 border border-[#F23F42]/30"}`}>
                            <Youtube className={`w-6 h-6 ${yt.connected ? "text-emerald-400" : "text-[#F23F42]"}`} />
                        </div>
                        <div>
                            <div className="font-display text-lg font-bold flex items-center gap-2">
                                {yt.connected ? <>YouTube connected <CheckCircle2 className="w-4 h-4 text-emerald-400" /></> : "Connect YouTube"}
                            </div>
                            <div className="text-xs text-zinc-500 mt-0.5">
                                {yt.connected
                                    ? `Channel: ${yt.channel?.title || "Connected"} · ${yt.channel?.subscribers?.toLocaleString?.() || 0} subs`
                                    : "Auto-publish your generated videos directly to your YouTube channel."}
                            </div>
                        </div>
                    </div>
                    {yt.connected ? (
                        <Button onClick={disconnectYouTube} variant="outline"
                            data-testid="youtube-disconnect-btn"
                            className="bg-white/5 border-white/10 text-white hover:bg-red-500/10 hover:text-red-400 rounded-md">
                            <Unlink className="w-4 h-4 mr-2" /> Disconnect
                        </Button>
                    ) : (
                        <Button onClick={connectYouTube}
                            data-testid="youtube-connect-btn"
                            className="bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md">
                            <Youtube className="w-4 h-4 mr-2" /> Connect channel
                        </Button>
                    )}
                </div>

                <div className="flex items-center justify-between mb-6">
                    <h2 className="font-display text-2xl font-bold tracking-tight">Your videos</h2>
                </div>

                {loading ? (
                    <div className="text-zinc-500 font-mono-tag">Loading...</div>
                ) : projects.length === 0 ? (
                    <div className="border border-dashed border-white/10 rounded-md p-16 text-center">
                        <Film className="w-12 h-12 text-zinc-700 mx-auto" strokeWidth={1.2} />
                        <div className="mt-4 font-display text-2xl font-bold">No videos yet</div>
                        <div className="mt-2 text-zinc-500">Spin up your first AI video in under 2 minutes.</div>
                        <Link to="/wizard">
                            <Button className="mt-6 bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md">
                                <Plus className="w-4 h-4 mr-2" /> Create video
                            </Button>
                        </Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {projects.map((p, i) => (
                            <motion.div
                                key={p.id}
                                initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.04 }}
                                className="border border-white/10 bg-[#121214] rounded-md overflow-hidden hover:border-white/30 transition-all"
                                data-testid={`project-card-${p.id}`}
                            >
                                <div className="aspect-video bg-black/50 relative overflow-hidden">
                                    {p.thumbnail_url ? (
                                        <img src={p.thumbnail_url} alt={p.title} className="w-full h-full object-cover" />
                                    ) : (
                                        <div className="w-full h-full grid place-items-center bg-gradient-to-br from-[#121214] to-black">
                                            <Film className="w-10 h-10 text-zinc-700" strokeWidth={1.2} />
                                        </div>
                                    )}
                                    <div className="absolute top-3 left-3"><StatusBadge status={p.status} /></div>
                                </div>
                                <div className="p-5">
                                    <div className="font-mono-tag text-zinc-500">{p.niche}</div>
                                    <div className="mt-2 font-semibold line-clamp-2">{p.title || p.topic}</div>
                                    <div className="mt-4 flex items-center gap-2">
                                        <Link to={`/wizard/${p.id}`} className="flex-1">
                                            <Button variant="outline" size="sm" className="w-full bg-white/5 border-white/10 text-white hover:bg-white/10 rounded-md" data-testid={`open-project-${p.id}`}>
                                                Open
                                            </Button>
                                        </Link>
                                        {p.youtube_url && (
                                            <a href={p.youtube_url} target="_blank" rel="noreferrer">
                                                <Button variant="outline" size="sm" className="bg-white/5 border-white/10 text-white hover:bg-white/10 rounded-md">
                                                    <ExternalLink className="w-4 h-4" />
                                                </Button>
                                            </a>
                                        )}
                                        <Button onClick={() => remove(p.id)} variant="outline" size="sm" className="bg-white/5 border-white/10 text-zinc-400 hover:bg-red-500/10 hover:text-red-400 rounded-md" data-testid={`delete-project-${p.id}`}>
                                            <Trash2 className="w-4 h-4" />
                                        </Button>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
