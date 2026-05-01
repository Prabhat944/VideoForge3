import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import api from "../lib/api";
import NavBar from "../components/NavBar";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Switch } from "../components/ui/switch";
import { Sparkles, Loader2, Bot, CheckCircle2, AlertCircle, Wand2, Mic, Image as ImageIcon, Video, Upload, Film } from "lucide-react";
import { toast } from "sonner";

const STAGES = [
    { k: "queued", label: "Queued", icon: Sparkles },
    { k: "script", label: "Script", icon: Wand2 },
    { k: "voice", label: "Voice", icon: Mic },
    { k: "thumbnail", label: "Thumbnail", icon: ImageIcon },
    { k: "scenes", label: "Scenes", icon: Film },
    { k: "render", label: "Render", icon: Video },
    { k: "publish", label: "Publish", icon: Upload },
    { k: "complete", label: "Complete", icon: CheckCircle2 },
];

const NICHES = ["general", "finance", "horror", "motivation", "education", "facts"];

export default function AgentMode() {
    const nav = useNavigate();
    const [form, setForm] = useState({
        topic: "",
        niche: "general",
        duration_seconds: 60,
        tone: "engaging",
        style: "storytelling",
        voice: "hd_alloy",
        auto_publish: false,
        youtube_privacy: "private",
    });
    const [running, setRunning] = useState(false);
    const [pid, setPid] = useState(null);
    const [progress, setProgress] = useState(null);

    const start = async () => {
        if (!form.topic.trim()) { toast.error("Topic required"); return; }
        setRunning(true);
        setProgress({ stage: "queued", status: "running" });
        try {
            const r = await api.post("/agent/run", form);
            setPid(r.data.project_id);
            toast.success("Agent started — sit back, this takes 3-5 minutes");
            const poll = async () => {
                try {
                    const s = await api.get(`/agent/status/${r.data.project_id}`);
                    setProgress(s.data);
                    if (s.data.status === "complete") {
                        toast.success("Agent run complete!");
                        setRunning(false);
                        return;
                    }
                    if (s.data.status === "error") {
                        toast.error(`Agent failed at ${s.data.stage}: ${s.data.error}`);
                        setRunning(false);
                        return;
                    }
                    setTimeout(poll, 5000);
                } catch (e) {
                    if (running) setTimeout(poll, 6000);
                }
            };
            setTimeout(poll, 4000);
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Agent failed to start");
            setRunning(false);
        }
    };

    const currentStageIdx = STAGES.findIndex(s => s.k === progress?.stage);

    return (
        <div className="min-h-screen bg-[#0A0A0B]" data-testid="agent-page">
            <NavBar />
            <div className="max-w-5xl mx-auto px-6 lg:px-12 py-12">
                <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-md bg-[#F23F42]/10 border border-[#F23F42]/30 grid place-items-center">
                        <Bot className="w-5 h-5 text-[#F23F42]" />
                    </div>
                    <div className="font-mono-tag text-[#F23F42]">/ AI AGENT MODE</div>
                </div>
                <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter">
                    Type a topic. Walk away.
                </h1>
                <p className="mt-3 text-zinc-400 max-w-2xl">
                    The agent runs the full pipeline end-to-end — script, voice, thumbnail, per-scene visuals, render, and (optionally) auto-publishes to your connected YouTube channel.
                </p>

                <div className="mt-12 grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Form */}
                    <div className="border border-white/10 bg-[#121214] rounded-md p-8" data-testid="agent-form">
                        <div className="font-mono-tag text-zinc-500 mb-4">CONFIG</div>
                        <div className="space-y-5">
                            <div>
                                <Label className="font-mono-tag text-zinc-500">Topic</Label>
                                <Textarea
                                    data-testid="agent-topic-input"
                                    rows={3} value={form.topic}
                                    onChange={(e) => setForm({ ...form, topic: e.target.value })}
                                    placeholder="e.g. Top 5 dark mysteries from the deep ocean"
                                    className="mt-2 bg-[#0A0A0B] border-white/10 text-white focus-visible:ring-1 focus-visible:ring-[#F23F42] rounded-md"
                                    disabled={running}
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <Field label="Niche" testId="agent-niche">
                                    <Select value={form.niche} onValueChange={(v) => setForm({ ...form, niche: v })} disabled={running}>
                                        <SelectTrigger className="h-11 bg-[#0A0A0B] border-white/10 text-white capitalize"><SelectValue /></SelectTrigger>
                                        <SelectContent className="bg-[#121214] border-white/10 text-white">
                                            {NICHES.map(n => <SelectItem key={n} value={n} className="capitalize">{n}</SelectItem>)}
                                        </SelectContent>
                                    </Select>
                                </Field>
                                <Field label="Duration (s)">
                                    <Input
                                        data-testid="agent-duration-input"
                                        type="number" value={form.duration_seconds} min={30} max={300} step={15}
                                        onChange={(e) => setForm({ ...form, duration_seconds: parseInt(e.target.value, 10) || 60 })}
                                        disabled={running}
                                        className="h-11 bg-[#0A0A0B] border-white/10 text-white rounded-md"
                                    />
                                </Field>
                            </div>
                            <Field label="Voice" testId="agent-voice">
                                <Select value={form.voice} onValueChange={(v) => setForm({ ...form, voice: v })} disabled={running}>
                                    <SelectTrigger className="h-11 bg-[#0A0A0B] border-white/10 text-white"><SelectValue /></SelectTrigger>
                                    <SelectContent className="bg-[#121214] border-white/10 text-white">
                                        <SelectItem value="alloy">Alloy (Free)</SelectItem>
                                        <SelectItem value="echo">Echo (Free)</SelectItem>
                                        <SelectItem value="hd_alloy">Alloy HD (Premium)</SelectItem>
                                        <SelectItem value="hd_nova">Nova HD (Premium)</SelectItem>
                                        <SelectItem value="hd_onyx">Onyx HD (Premium)</SelectItem>
                                    </SelectContent>
                                </Select>
                            </Field>

                            <div className="flex items-center justify-between border border-white/10 rounded-md p-4 bg-black/30">
                                <div>
                                    <div className="font-display font-bold flex items-center gap-2">Auto-publish to YouTube</div>
                                    <div className="text-xs text-zinc-500 mt-1">Requires connected YouTube channel</div>
                                </div>
                                <Switch
                                    data-testid="agent-autopublish-switch"
                                    checked={form.auto_publish}
                                    onCheckedChange={(v) => setForm({ ...form, auto_publish: v })}
                                    disabled={running}
                                    className="data-[state=checked]:bg-[#F23F42]"
                                />
                            </div>

                            {form.auto_publish && (
                                <Field label="Privacy">
                                    <Select value={form.youtube_privacy} onValueChange={(v) => setForm({ ...form, youtube_privacy: v })} disabled={running}>
                                        <SelectTrigger className="h-11 bg-[#0A0A0B] border-white/10 text-white"><SelectValue /></SelectTrigger>
                                        <SelectContent className="bg-[#121214] border-white/10 text-white">
                                            <SelectItem value="private">Private</SelectItem>
                                            <SelectItem value="unlisted">Unlisted</SelectItem>
                                            <SelectItem value="public">Public</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </Field>
                            )}

                            <Button onClick={start} disabled={running || !form.topic.trim()}
                                data-testid="agent-start-btn"
                                className="w-full h-12 bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md font-semibold mt-2">
                                {running ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Bot className="w-4 h-4 mr-2" />}
                                {running ? "Agent running..." : "Run agent"}
                            </Button>
                        </div>
                    </div>

                    {/* Progress */}
                    <div className="border border-white/10 bg-[#121214] rounded-md p-8" data-testid="agent-progress">
                        <div className="font-mono-tag text-zinc-500 mb-6">PROGRESS</div>
                        {!progress ? (
                            <div className="text-zinc-500 text-sm">Awaiting start signal...</div>
                        ) : progress.status === "error" ? (
                            <div className="border border-red-500/30 bg-red-500/5 rounded-md p-5">
                                <div className="flex items-center gap-3">
                                    <AlertCircle className="w-5 h-5 text-red-400" />
                                    <div className="font-display text-lg font-bold">Agent failed at {progress.stage}</div>
                                </div>
                                <div className="mt-2 text-xs text-zinc-500">{progress.error}</div>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {STAGES.map((s, i) => {
                                    const done = i < currentStageIdx || progress.status === "complete";
                                    const active = i === currentStageIdx && progress.status !== "complete";
                                    return (
                                        <motion.div key={s.k}
                                            initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.03 }}
                                            className={`flex items-center gap-3 p-3 rounded-md border ${
                                                active ? "bg-[#F23F42]/10 border-[#F23F42]/40 glow-red"
                                                    : done ? "bg-emerald-500/5 border-emerald-500/20"
                                                        : "bg-black/30 border-white/10"
                                            }`}>
                                            <div className={`w-8 h-8 rounded-md grid place-items-center ${
                                                active ? "bg-[#F23F42]" : done ? "bg-emerald-500/20 text-emerald-400" : "bg-white/5 text-zinc-500"
                                            }`}>
                                                {active ? <Loader2 className="w-4 h-4 animate-spin text-white" />
                                                    : done ? <CheckCircle2 className="w-4 h-4" />
                                                        : <s.icon className="w-4 h-4" />}
                                            </div>
                                            <span className={`font-display font-bold ${active ? "text-white" : done ? "text-emerald-300" : "text-zinc-500"}`}>
                                                {s.label}
                                            </span>
                                        </motion.div>
                                    );
                                })}
                                {progress.video_url && (
                                    <a href={progress.video_url} target="_blank" rel="noreferrer"
                                        className="block mt-4 text-emerald-400 text-xs hover:underline break-all">
                                        Video: {progress.video_url}
                                    </a>
                                )}
                                {progress.youtube_url && (
                                    <a href={progress.youtube_url} target="_blank" rel="noreferrer"
                                        className="block text-emerald-400 text-xs hover:underline break-all">
                                        Live: {progress.youtube_url}
                                    </a>
                                )}
                                {progress.status === "complete" && pid && (
                                    <Button onClick={() => nav(`/wizard/${pid}`)}
                                        className="w-full mt-4 bg-white/5 border border-white/10 text-white hover:bg-white/10 rounded-md">
                                        Open project
                                    </Button>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function Field({ label, children, testId }) {
    return (
        <div data-testid={testId}>
            <Label className="font-mono-tag text-zinc-500">{label}</Label>
            <div className="mt-2">{children}</div>
        </div>
    );
}
