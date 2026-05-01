import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import api, { withAuth } from "../lib/api";
import NavBar from "../components/NavBar";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Slider } from "../components/ui/slider";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import { toast } from "sonner";
import { ArrowRight, ArrowLeft, Wand2, Mic, Image as ImageIcon, Upload, Check, Play, Pause, Sparkles, Loader2, Film } from "lucide-react";

const STEPS = [
    { k: "info", label: "Topic", icon: Sparkles },
    { k: "script", label: "Script", icon: Wand2 },
    { k: "voice", label: "Voice", icon: Mic },
    { k: "thumbnail", label: "Visual", icon: ImageIcon },
    { k: "publish", label: "Publish", icon: Upload },
];

const NICHES = ["general", "finance", "horror", "motivation", "education", "facts"];
const STYLES = ["storytelling", "educational", "listicle", "documentary", "tutorial"];
const TONES = ["engaging", "educational", "scary", "inspiring", "humorous", "dramatic"];
const LANGUAGES = ["English", "Spanish", "French", "German", "Hindi", "Portuguese", "Japanese"];

export default function Wizard() {
    const { id } = useParams();
    const nav = useNavigate();
    const [stepIdx, setStepIdx] = useState(0);
    const [project, setProject] = useState(null);
    const [busy, setBusy] = useState(false);
    const [voices, setVoices] = useState([]);
    const audioRef = useRef(null);
    const [playing, setPlaying] = useState(false);

    // Form state
    const [info, setInfo] = useState({
        topic: "", audience: "general", duration_seconds: 60, tone: "engaging",
        language: "English", style: "storytelling", niche: "general",
    });
    const [voiceCfg, setVoiceCfg] = useState({ voice: "alloy", speed: 1.0 });
    const [thumbStyle, setThumbStyle] = useState("cinematic, high contrast, vibrant colors");
    const [pub, setPub] = useState({ title: "", description: "", tags: "", privacy: "public", schedule_at: "" });

    useEffect(() => {
        api.get("/voices").then((r) => setVoices(r.data.voices)).catch(() => {});
    }, []);

    useEffect(() => {
        if (id) {
            api.get(`/projects/${id}`).then((r) => {
                setProject(r.data);
                setInfo({
                    topic: r.data.topic, audience: r.data.audience,
                    duration_seconds: r.data.duration_seconds, tone: r.data.tone,
                    language: r.data.language, style: r.data.style, niche: r.data.niche,
                });
                if (r.data.script) {
                    setPub({
                        title: r.data.title || r.data.script.title || "",
                        description: r.data.description || r.data.script.description || "",
                        tags: (r.data.script.tags || []).join(", "),
                        privacy: "public", schedule_at: "",
                    });
                }
                // jump to right step
                if (r.data.youtube_video_id) setStepIdx(5);
                else if (r.data.video_path || r.data.video_url) setStepIdx(5);
                else if (r.data.thumbnail_url) setStepIdx(4);
                else if (r.data.voice) setStepIdx(3);
                else if (r.data.script) setStepIdx(2);
                else setStepIdx(1);
            }).catch(() => toast.error("Project not found"));
        }
    }, [id]);

    const createProject = async () => {
        if (!info.topic.trim()) { toast.error("Topic required"); return; }
        setBusy(true);
        try {
            const r = await api.post("/projects", info);
            setProject(r.data);
            nav(`/wizard/${r.data.id}`, { replace: true });
            setStepIdx(1);
            toast.success("Project created");
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Failed");
        } finally { setBusy(false); }
    };

    const generateScript = async () => {
        setBusy(true);
        try {
            const r = await api.post("/projects/script", { project_id: project.id, style: info.style });
            setProject({ ...project, script: r.data.script, title: r.data.script.title, description: r.data.script.description, status: "script_ready" });
            setPub({
                title: r.data.script.title,
                description: r.data.script.description,
                tags: (r.data.script.tags || []).join(", "),
                privacy: "public", schedule_at: "",
            });
            toast.success("Script generated");
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Generation failed");
        } finally { setBusy(false); }
    };

    const generateVoice = async () => {
        setBusy(true);
        try {
            const r = await api.post("/projects/voice", {
                project_id: project.id, voice: voiceCfg.voice, speed: voiceCfg.speed,
            });
            setProject({ ...project, voice: { audio_b64: r.data.audio_b64, voice_id: r.data.voice_id, format: "mp3" }, status: "voice_ready" });
            toast.success("Voice generated");
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Voice failed");
        } finally { setBusy(false); }
    };

    const generateThumbnail = async () => {
        setBusy(true);
        try {
            const r = await api.post("/projects/thumbnail", { project_id: project.id, style_prompt: thumbStyle });
            setProject({ ...project, thumbnail_url: r.data.thumbnail_url });
            toast.success("Thumbnail generated");
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Thumbnail failed");
        } finally { setBusy(false); }
    };

    const publish = async () => {
        if (!pub.title) { toast.error("Title required"); return; }
        setBusy(true);
        try {
            const r = await api.post("/projects/publish", {
                project_id: project.id,
                title: pub.title, description: pub.description,
                tags: pub.tags.split(",").map(t => t.trim()).filter(Boolean),
                privacy: pub.privacy,
                schedule_at: pub.schedule_at || null,
            });
            setProject({ ...project, youtube_video_id: r.data.video_id, youtube_url: r.data.url, status: r.data.status, uploaded_real: r.data.real });
            toast.success(r.data.real ? "Published to your YouTube channel" : (pub.schedule_at ? "Scheduled" : "Published (mocked - connect YouTube for real upload)"));
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Publish failed");
        } finally { setBusy(false); }
    };

    const renderVideo = async () => {
        setBusy(true);
        try {
            const r = await api.post("/projects/render", { project_id: project.id });
            setProject({ ...project, video_url: r.data.video_url, video_path: r.data.video_path, status: "rendered" });
            toast.success(r.data.scenes_used > 0 ? `Video rendered (${r.data.scenes_used} scenes)` : "Video rendered");
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Render failed");
        } finally { setBusy(false); }
    };

    const generateScenes = async () => {
        setBusy(true);
        try {
            await api.post("/projects/scenes", { project_id: project.id });
            toast.success("Scene generation started — this takes 1-2 min");
            // Poll for status
            const poll = async () => {
                try {
                    const r = await api.get(`/projects/${project.id}/scenes-status`);
                    const sc = r.data.scenes || [];
                    setProject((prev) => ({ ...prev, scene_images: sc.map(s => ({ ...s, image_data_url: s.has_image ? "ready" : null })) }));
                    if (r.data.status === "complete" || r.data.status === "idle") {
                        const ready = sc.filter(s => s.has_image).length;
                        toast.success(`${ready}/${sc.length} scene visuals ready`);
                        setBusy(false);
                        // Reload full project to get image_data_urls
                        const proj = await api.get(`/projects/${project.id}`);
                        setProject(proj.data);
                        return;
                    }
                    setTimeout(poll, 4000);
                } catch {
                    setBusy(false);
                }
            };
            setTimeout(poll, 3000);
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Scene generation failed");
            setBusy(false);
        }
    };

    const togglePlay = () => {
        if (!audioRef.current) return;
        if (playing) { audioRef.current.pause(); setPlaying(false); }
        else { audioRef.current.play(); setPlaying(true); }
    };

    const canNext = () => {
        if (stepIdx === 0) return !!project;
        if (stepIdx === 1) return !!project?.script;
        if (stepIdx === 2) return !!project?.voice;
        if (stepIdx === 3) return !!project?.thumbnail_url;
        if (stepIdx === 4) return !!project?.video_path || !!project?.video_url;
        return false;
    };

    return (
        <div className="min-h-screen bg-[#0A0A0B]" data-testid="wizard-page">
            <NavBar />
            <div className="max-w-7xl mx-auto px-6 lg:px-12 py-10">
                {/* Stepper */}
                <div className="flex items-center justify-between gap-2 mb-12 overflow-x-auto pb-2">
                    {STEPS.map((s, i) => {
                        const active = i === stepIdx;
                        const done = i < stepIdx;
                        return (
                            <div key={s.k} className="flex items-center gap-3 flex-1 min-w-fit">
                                <button
                                    onClick={() => project && i <= stepIdx && setStepIdx(i)}
                                    disabled={!project || i > stepIdx}
                                    data-testid={`wizard-step-${s.k}`}
                                    className={`flex items-center gap-3 px-4 py-2 rounded-md border transition-all ${
                                        active ? "bg-[#F23F42] border-[#F23F42] text-white glow-red"
                                            : done ? "bg-white/5 border-white/20 text-white"
                                                : "bg-transparent border-white/10 text-zinc-500"
                                    }`}
                                >
                                    {done ? <Check className="w-4 h-4" /> : <s.icon className="w-4 h-4" />}
                                    <span className="font-mono-tag">{i + 1}. {s.label}</span>
                                </button>
                                {i < STEPS.length - 1 && <div className={`flex-1 h-px ${done ? "bg-white/30" : "bg-white/10"}`} />}
                            </div>
                        );
                    })}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    {/* LEFT - inputs */}
                    <div className="lg:col-span-7">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={stepIdx}
                                initial={{ opacity: 0, x: 24 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -24 }}
                                transition={{ duration: 0.3 }}
                            >
                                {stepIdx === 0 && (
                                    <div className="border border-white/10 bg-[#121214] rounded-md p-8" data-testid="step-info">
                                        <div className="font-mono-tag text-[#F23F42]">/ STEP 01</div>
                                        <h2 className="font-display text-3xl font-black tracking-tighter mt-2">Brief us</h2>
                                        <p className="text-zinc-400 mt-2 text-sm">One line is enough. Add details if you want more control.</p>

                                        <div className="mt-8 space-y-5">
                                            <div>
                                                <Label className="font-mono-tag text-zinc-500">Topic / Idea</Label>
                                                <Textarea
                                                    data-testid="info-topic-input"
                                                    rows={3} value={info.topic}
                                                    onChange={(e) => setInfo({ ...info, topic: e.target.value })}
                                                    placeholder="e.g. Top 5 dark mysteries from the deep ocean"
                                                    className="mt-2 bg-[#0A0A0B] border-white/10 text-white focus-visible:ring-1 focus-visible:ring-[#F23F42] focus-visible:border-[#F23F42] rounded-md"
                                                />
                                            </div>

                                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                                                <FormSelect label="Niche" value={info.niche} onChange={(v) => setInfo({ ...info, niche: v })} options={NICHES} testId="info-niche-select" />
                                                <FormSelect label="Style" value={info.style} onChange={(v) => setInfo({ ...info, style: v })} options={STYLES} testId="info-style-select" />
                                                <FormSelect label="Tone" value={info.tone} onChange={(v) => setInfo({ ...info, tone: v })} options={TONES} testId="info-tone-select" />
                                                <FormSelect label="Language" value={info.language} onChange={(v) => setInfo({ ...info, language: v })} options={LANGUAGES} testId="info-language-select" />
                                            </div>

                                            <div>
                                                <Label className="font-mono-tag text-zinc-500">Audience</Label>
                                                <Input
                                                    data-testid="info-audience-input"
                                                    value={info.audience}
                                                    onChange={(e) => setInfo({ ...info, audience: e.target.value })}
                                                    placeholder="e.g. young adults interested in mystery"
                                                    className="mt-2 h-11 bg-[#0A0A0B] border-white/10 text-white focus-visible:ring-1 focus-visible:ring-[#F23F42] focus-visible:border-[#F23F42] rounded-md"
                                                />
                                            </div>

                                            <div>
                                                <Label className="font-mono-tag text-zinc-500">Duration · {info.duration_seconds}s</Label>
                                                <Slider
                                                    data-testid="info-duration-slider"
                                                    min={30} max={300} step={15} value={[info.duration_seconds]}
                                                    onValueChange={(v) => setInfo({ ...info, duration_seconds: v[0] })}
                                                    className="mt-3"
                                                />
                                            </div>
                                        </div>

                                        <Button
                                            onClick={createProject} disabled={busy || !info.topic.trim()}
                                            data-testid="info-create-project-btn"
                                            className="mt-8 bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md h-12 px-8 font-semibold"
                                        >
                                            {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                                            {project ? "Update & continue" : "Create project"} <ArrowRight className="ml-2 w-4 h-4" />
                                        </Button>
                                    </div>
                                )}

                                {stepIdx === 1 && (
                                    <div className="border border-white/10 bg-[#121214] rounded-md p-8" data-testid="step-script">
                                        <div className="font-mono-tag text-[#F23F42]">/ STEP 02</div>
                                        <h2 className="font-display text-3xl font-black tracking-tighter mt-2">Script</h2>
                                        <p className="text-zinc-400 mt-2 text-sm">GPT-5 writes hook → scenes → CTA optimised for retention.</p>

                                        {!project?.script ? (
                                            <div className="mt-8">
                                                <Button onClick={generateScript} disabled={busy}
                                                    data-testid="script-generate-btn"
                                                    className="bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md h-12 px-8 font-semibold">
                                                    {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Wand2 className="w-4 h-4 mr-2" />}
                                                    Generate with AI
                                                </Button>
                                            </div>
                                        ) : (
                                            <div className="mt-6 space-y-5">
                                                <div className="border border-white/10 bg-black/30 rounded-md p-5">
                                                    <div className="font-mono-tag text-[#F23F42]">HOOK</div>
                                                    <p className="mt-2 text-zinc-200">{project.script.hook}</p>
                                                </div>
                                                <div className="space-y-3">
                                                    <div className="font-mono-tag text-zinc-500">SCENES</div>
                                                    {(project.script.scenes || []).map((sc) => (
                                                        <div key={sc.index} className="border border-white/10 bg-black/30 rounded-md p-4">
                                                            <div className="flex items-center justify-between">
                                                                <span className="font-mono-tag text-[#F23F42]">SCENE {sc.index} · {sc.duration}s</span>
                                                            </div>
                                                            <div className="mt-2 text-xs text-zinc-500">{sc.visual_prompt}</div>
                                                            <p className="mt-2 text-zinc-200 text-sm leading-relaxed">{sc.narration}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                                <div className="border border-white/10 bg-black/30 rounded-md p-5">
                                                    <div className="font-mono-tag text-[#F23F42]">CTA</div>
                                                    <p className="mt-2 text-zinc-200">{project.script.cta}</p>
                                                </div>
                                                <div className="flex flex-wrap gap-3">
                                                    <Button onClick={generateScript} disabled={busy}
                                                        variant="outline" data-testid="script-regenerate-btn"
                                                        className="bg-white/5 border-white/10 text-white hover:bg-white/10 rounded-md">
                                                        {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Wand2 className="w-4 h-4 mr-2" />}
                                                        Regenerate
                                                    </Button>
                                                    <Link to={`/ab-test/${project.id}`} data-testid="open-ab-test-link">
                                                        <Button variant="outline"
                                                            className="bg-white/5 border-white/10 text-white hover:bg-white/10 rounded-md">
                                                            Open A/B test
                                                        </Button>
                                                    </Link>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {stepIdx === 2 && (
                                    <div className="border border-white/10 bg-[#121214] rounded-md p-8" data-testid="step-voice">
                                        <div className="font-mono-tag text-[#F23F42]">/ STEP 03</div>
                                        <h2 className="font-display text-3xl font-black tracking-tighter mt-2">Voice</h2>
                                        <p className="text-zinc-400 mt-2 text-sm">Pick a narrator. Studio-grade TTS.</p>

                                        <Tabs defaultValue="free" className="mt-6">
                                            <TabsList className="bg-black/30 border border-white/10 rounded-md">
                                                <TabsTrigger value="free" data-testid="voice-tab-free" className="data-[state=active]:bg-[#F23F42] data-[state=active]:text-white rounded-md font-mono-tag">FREE</TabsTrigger>
                                                <TabsTrigger value="premium" data-testid="voice-tab-premium" className="data-[state=active]:bg-[#F23F42] data-[state=active]:text-white rounded-md font-mono-tag">
                                                    <Crown className="w-3 h-3 mr-1.5" /> PREMIUM HD
                                                </TabsTrigger>
                                                <TabsTrigger value="premium_plus" data-testid="voice-tab-premium-plus" className="data-[state=active]:bg-[#F23F42] data-[state=active]:text-white rounded-md font-mono-tag">
                                                    <Crown className="w-3 h-3 mr-1.5" /> ELEVENLABS
                                                </TabsTrigger>
                                            </TabsList>
                                            <TabsContent value="free" className="mt-4">
                                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                                                    {voices.filter(v => v.tier === "free").map((v) => (
                                                        <VoiceCard key={v.id} v={v} active={voiceCfg.voice === v.id}
                                                            onClick={() => setVoiceCfg({ ...voiceCfg, voice: v.id })} />
                                                    ))}
                                                </div>
                                            </TabsContent>
                                            <TabsContent value="premium" className="mt-4">
                                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                                                    {voices.filter(v => v.tier === "premium").map((v) => (
                                                        <VoiceCard key={v.id} v={v} active={voiceCfg.voice === v.id}
                                                            onClick={() => setVoiceCfg({ ...voiceCfg, voice: v.id })} premium />
                                                    ))}
                                                </div>
                                                <p className="text-xs text-zinc-500 mt-3">OpenAI TTS-1-HD · cloud-friendly · works on the free Universal Key.</p>
                                            </TabsContent>
                                            <TabsContent value="premium_plus" className="mt-4">
                                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                                                    {voices.filter(v => v.tier === "premium_plus").map((v) => (
                                                        <VoiceCard key={v.id} v={v} active={voiceCfg.voice === v.id}
                                                            onClick={() => setVoiceCfg({ ...voiceCfg, voice: v.id })} premium />
                                                    ))}
                                                </div>
                                                <p className="text-xs text-amber-400/80 mt-3">⚠ ElevenLabs blocks free-tier usage from cloud IPs. Requires a paid ElevenLabs plan to synthesize.</p>
                                            </TabsContent>
                                        </Tabs>

                                        <div className="mt-8">
                                            <Label className="font-mono-tag text-zinc-500">Speed · {voiceCfg.speed.toFixed(2)}x</Label>
                                            <Slider data-testid="voice-speed-slider"
                                                min={0.5} max={2.0} step={0.05} value={[voiceCfg.speed]}
                                                onValueChange={(v) => setVoiceCfg({ ...voiceCfg, speed: v[0] })}
                                                className="mt-3"
                                            />
                                        </div>

                                        <Button onClick={generateVoice} disabled={busy}
                                            data-testid="voice-generate-btn"
                                            className="mt-8 bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md h-12 px-8 font-semibold">
                                            {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Mic className="w-4 h-4 mr-2" />}
                                            {project?.voice ? "Regenerate voice" : "Generate voice"}
                                        </Button>

                                        {project?.voice?.audio_b64 && (
                                            <div className="mt-6 border border-white/10 bg-black/30 rounded-md p-5">
                                                <div className="font-mono-tag text-zinc-500 mb-3">PREVIEW · {project.voice.provider?.toUpperCase()}</div>
                                                <div className="flex items-center gap-4">
                                                    <Button onClick={togglePlay} data-testid="voice-play-btn"
                                                        className="bg-[#F23F42] hover:bg-[#FF5C5E] rounded-full h-12 w-12 p-0">
                                                        {playing ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
                                                    </Button>
                                                    <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                                                        <div className="h-full bg-[#F23F42] w-1/2" />
                                                    </div>
                                                </div>
                                                <audio
                                                    ref={audioRef}
                                                    src={`data:audio/mp3;base64,${project.voice.audio_b64}`}
                                                    onEnded={() => setPlaying(false)}
                                                />
                                            </div>
                                        )}
                                    </div>
                                )}

                                {stepIdx === 3 && (
                                    <div className="border border-white/10 bg-[#121214] rounded-md p-8" data-testid="step-thumbnail">
                                        <div className="font-mono-tag text-[#F23F42]">/ STEP 04</div>
                                        <h2 className="font-display text-3xl font-black tracking-tighter mt-2">Thumbnail</h2>
                                        <p className="text-zinc-400 mt-2 text-sm">High-CTR thumbnail crafted by AI.</p>

                                        <div className="mt-6">
                                            <Label className="font-mono-tag text-zinc-500">Style direction</Label>
                                            <Textarea
                                                data-testid="thumbnail-style-input"
                                                rows={3} value={thumbStyle}
                                                onChange={(e) => setThumbStyle(e.target.value)}
                                                placeholder="e.g. dark cinematic, dramatic lighting, bold red accents"
                                                className="mt-2 bg-[#0A0A0B] border-white/10 text-white focus-visible:ring-1 focus-visible:ring-[#F23F42] rounded-md"
                                            />
                                        </div>

                                        <Button onClick={generateThumbnail} disabled={busy}
                                            data-testid="thumbnail-generate-btn"
                                            className="mt-6 bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md h-12 px-8 font-semibold">
                                            {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <ImageIcon className="w-4 h-4 mr-2" />}
                                            {project?.thumbnail_url ? "Regenerate" : "Generate thumbnail"}
                                        </Button>
                                    </div>
                                )}

                                {stepIdx === 4 && (
                                    <div className="border border-white/10 bg-[#121214] rounded-md p-8" data-testid="step-render">
                                        <div className="font-mono-tag text-[#F23F42]">/ STEP 05</div>
                                        <h2 className="font-display text-3xl font-black tracking-tighter mt-2">Render Video</h2>
                                        <p className="text-zinc-400 mt-2 text-sm">Generate per-scene visuals (recommended) then compose the final MP4 with crossfade transitions, voiceover, and burnt-in subtitles.</p>

                                        <div className="mt-6 border border-white/10 bg-black/30 rounded-md p-5">
                                            <div className="flex items-center justify-between mb-3 gap-4">
                                                <div className="min-w-0">
                                                    <div className="font-display font-bold">Per-scene visuals</div>
                                                    <div className="text-xs text-zinc-500 mt-1">
                                                        {project?.scene_images?.length
                                                            ? `${project.scene_images.filter(s => s.has_image || s.image_data_url).length} scene images ready`
                                                            : "Generate distinct images per scene for a cinematic multi-scene video."}
                                                    </div>
                                                </div>
                                                <Button onClick={generateScenes} disabled={busy} variant="outline"
                                                    data-testid="scenes-generate-btn"
                                                    className="bg-white/5 border-white/10 text-white hover:bg-white/10 rounded-md flex-shrink-0">
                                                    {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <ImageIcon className="w-4 h-4 mr-2" />}
                                                    {project?.scene_images?.length ? "Regenerate" : "Generate scenes"}
                                                </Button>
                                            </div>
                                            {project?.scene_images?.length > 0 && (
                                                <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mt-4">
                                                    {project.scene_images.map((s, i) => (
                                                        <div key={i} className="aspect-video rounded bg-black/40 border border-white/10 overflow-hidden grid place-items-center relative">
                                                            {s.image_url ? (
                                                                <img src={withAuth(s.image_url)} alt={`Scene ${s.index}`} className="w-full h-full object-cover" />
                                                            ) : (
                                                                <span className="font-mono-tag text-zinc-500">SC {s.index || i + 1}</span>
                                                            )}
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>

                                        {project?.video_url ? (
                                            <div className="mt-6 space-y-4">
                                                <div className="border border-emerald-500/30 bg-emerald-500/5 rounded-md p-5">
                                                    <div className="flex items-center gap-3">
                                                        <Check className="w-5 h-5 text-emerald-400" /> <span className="font-display text-lg font-bold">Video rendered</span>
                                                    </div>
                                                    <a href={project.video_url} target="_blank" rel="noreferrer" data-testid="render-download-link"
                                                        className="block mt-3 text-emerald-400 text-sm hover:underline break-all">
                                                        {project.video_url}
                                                    </a>
                                                </div>
                                                <Button onClick={renderVideo} disabled={busy} variant="outline"
                                                    data-testid="render-regenerate-btn"
                                                    className="bg-white/5 border-white/10 text-white hover:bg-white/10 rounded-md">
                                                    {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Video className="w-4 h-4 mr-2" />}
                                                    Re-render
                                                </Button>
                                            </div>
                                        ) : (
                                            <Button onClick={renderVideo} disabled={busy}
                                                data-testid="render-generate-btn"
                                                className="mt-6 bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md h-12 px-8 font-semibold">
                                                {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Video className="w-4 h-4 mr-2" />}
                                                Render MP4
                                            </Button>
                                        )}
                                        <p className="mt-4 text-xs text-zinc-500">Tip: scene generation takes 30-60s. Single-image render ~20s, multi-scene render 1-2 min.</p>
                                    </div>
                                )}

                                {stepIdx === 5 && (
                                    <div className="border border-white/10 bg-[#121214] rounded-md p-8" data-testid="step-publish">
                                        <div className="font-mono-tag text-[#F23F42]">/ STEP 06</div>
                                        <h2 className="font-display text-3xl font-black tracking-tighter mt-2">Publish</h2>
                                        <p className="text-zinc-400 mt-2 text-sm">
                                            {project?.video_path ? "Video ready. Will upload to your connected YouTube channel." : "No rendered video yet — will publish a placeholder. Render in step 5 to upload the real MP4."}
                                        </p>

                                        {project?.youtube_url ? (
                                            <div className="mt-8 border border-emerald-500/30 bg-emerald-500/5 rounded-md p-6" data-testid="publish-success">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-10 h-10 rounded-md bg-emerald-500/20 grid place-items-center">
                                                        <Check className="w-5 h-5 text-emerald-400" />
                                                    </div>
                                                    <div>
                                                        <div className="font-display text-xl font-bold">
                                                            {project.uploaded_real ? "Live on YouTube" : (project.status === "scheduled" ? "Scheduled" : "Published")}
                                                        </div>
                                                        <a href={project.youtube_url} target="_blank" rel="noreferrer" className="text-emerald-400 text-sm hover:underline">
                                                            {project.youtube_url}
                                                        </a>
                                                    </div>
                                                </div>
                                                <Button onClick={() => nav("/dashboard")} className="mt-6 bg-white/5 border border-white/10 text-white hover:bg-white/10 rounded-md">
                                                    Back to dashboard
                                                </Button>
                                            </div>
                                        ) : (
                                            <div className="mt-6 space-y-5">
                                                <div>
                                                    <Label className="font-mono-tag text-zinc-500">Title</Label>
                                                    <Input data-testid="publish-title-input" value={pub.title}
                                                        onChange={(e) => setPub({ ...pub, title: e.target.value })}
                                                        className="mt-2 h-11 bg-[#0A0A0B] border-white/10 text-white focus-visible:ring-1 focus-visible:ring-[#F23F42] rounded-md" />
                                                </div>
                                                <div>
                                                    <Label className="font-mono-tag text-zinc-500">Description</Label>
                                                    <Textarea data-testid="publish-description-input" rows={4} value={pub.description}
                                                        onChange={(e) => setPub({ ...pub, description: e.target.value })}
                                                        className="mt-2 bg-[#0A0A0B] border-white/10 text-white focus-visible:ring-1 focus-visible:ring-[#F23F42] rounded-md" />
                                                </div>
                                                <div>
                                                    <Label className="font-mono-tag text-zinc-500">Tags (comma separated)</Label>
                                                    <Input data-testid="publish-tags-input" value={pub.tags}
                                                        onChange={(e) => setPub({ ...pub, tags: e.target.value })}
                                                        className="mt-2 h-11 bg-[#0A0A0B] border-white/10 text-white focus-visible:ring-1 focus-visible:ring-[#F23F42] rounded-md" />
                                                </div>
                                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                                                    <FormSelect label="Privacy" value={pub.privacy}
                                                        onChange={(v) => setPub({ ...pub, privacy: v })}
                                                        options={["public", "unlisted", "private"]} testId="publish-privacy-select" />
                                                    <div>
                                                        <Label className="font-mono-tag text-zinc-500">Schedule (optional)</Label>
                                                        <Input data-testid="publish-schedule-input" type="datetime-local" value={pub.schedule_at}
                                                            onChange={(e) => setPub({ ...pub, schedule_at: e.target.value })}
                                                            className="mt-2 h-11 bg-[#0A0A0B] border-white/10 text-white focus-visible:ring-1 focus-visible:ring-[#F23F42] rounded-md" />
                                                    </div>
                                                </div>
                                                <Button onClick={publish} disabled={busy}
                                                    data-testid="publish-submit-btn"
                                                    className="mt-2 bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md h-12 px-8 font-semibold">
                                                    {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Upload className="w-4 h-4 mr-2" />}
                                                    {pub.schedule_at ? "Schedule upload" : "Publish now"}
                                                </Button>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </motion.div>
                        </AnimatePresence>

                        {/* Step nav */}
                        <div className="mt-6 flex items-center justify-between">
                            <Button
                                variant="ghost" onClick={() => setStepIdx(Math.max(0, stepIdx - 1))}
                                disabled={stepIdx === 0}
                                data-testid="wizard-prev-btn"
                                className="text-zinc-400 hover:text-white hover:bg-white/5"
                            >
                                <ArrowLeft className="w-4 h-4 mr-2" /> Back
                            </Button>
                            <Button
                                onClick={() => setStepIdx(Math.min(5, stepIdx + 1))}
                                disabled={stepIdx === 5 || !canNext()}
                                data-testid="wizard-next-btn"
                                className="bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-md"
                            >
                                Next <ArrowRight className="w-4 h-4 ml-2" />
                            </Button>
                        </div>
                    </div>

                    {/* RIGHT - sticky preview */}
                    <div className="lg:col-span-5">
                        <div className="lg:sticky lg:top-24 space-y-4">
                            <div className="border border-white/10 bg-[#121214] rounded-md overflow-hidden" data-testid="wizard-preview-card">
                                <div className="aspect-video bg-black relative">
                                    {project?.thumbnail_url ? (
                                        <img src={project.thumbnail_url} alt="thumbnail" className="w-full h-full object-cover" />
                                    ) : (
                                        <div className="absolute inset-0 grid place-items-center bg-gradient-to-br from-[#1a1a1d] to-black">
                                            <Film className="w-16 h-16 text-zinc-700" strokeWidth={1.2} />
                                        </div>
                                    )}
                                    {project?.voice?.audio_b64 && (
                                        <div className="absolute inset-0 grid place-items-center">
                                            <div className="w-16 h-16 rounded-full bg-[#F23F42] grid place-items-center glow-red">
                                                <Play className="w-7 h-7 text-white ml-1" />
                                            </div>
                                        </div>
                                    )}
                                </div>
                                <div className="p-5">
                                    <div className="font-mono-tag text-zinc-500">PROJECT PREVIEW</div>
                                    <div className="mt-2 font-display font-bold text-lg line-clamp-2">
                                        {project?.title || project?.topic || "Your video title appears here"}
                                    </div>
                                    <div className="mt-2 text-xs text-zinc-500 line-clamp-2">
                                        {project?.description || "Description will be generated by AI in step 2."}
                                    </div>
                                    <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                                        <PreviewStat label="Niche" v={info.niche} />
                                        <PreviewStat label="Length" v={`${info.duration_seconds}s`} />
                                        <PreviewStat label="Tone" v={info.tone} />
                                        <PreviewStat label="Lang" v={info.language} />
                                    </div>
                                </div>
                            </div>

                            {project?.script && (
                                <div className="border border-white/10 bg-[#121214] rounded-md p-5">
                                    <div className="font-mono-tag text-[#F23F42] mb-2">/ TAGS</div>
                                    <div className="flex flex-wrap gap-2">
                                        {(project.script.tags || []).slice(0, 8).map((t) => (
                                            <span key={t} className="font-mono-tag px-2 py-1 rounded-md border border-white/10 bg-black/30 text-zinc-300">
                                                #{t}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function VoiceCard({ v, active, onClick, premium }) {
    return (
        <button onClick={onClick}
            data-testid={`voice-option-${v.id}`}
            className={`text-left p-4 rounded-md border transition-all relative ${
                active ? "border-[#F23F42] bg-[#F23F42]/10 glow-red" : "border-white/10 bg-black/30 hover:border-white/30"
            }`}>
            {premium && <span className="absolute top-2 right-2 font-mono-tag text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">PRO</span>}
            <div className="font-display font-bold">{v.name}</div>
            <div className="font-mono-tag text-zinc-500 mt-1">{v.gender}</div>
            <div className="text-xs text-zinc-400 mt-2 line-clamp-2">{v.description}</div>
        </button>
    );
}

function FormSelect({ label, value, onChange, options, testId }) {
    return (
        <div>
            <Label className="font-mono-tag text-zinc-500">{label}</Label>
            <Select value={value} onValueChange={onChange}>
                <SelectTrigger data-testid={testId} className="mt-2 h-11 bg-[#0A0A0B] border-white/10 text-white focus:ring-1 focus:ring-[#F23F42] rounded-md capitalize">
                    <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#121214] border-white/10 text-white">
                    {options.map((o) => (
                        <SelectItem key={o} value={o} className="capitalize">{o}</SelectItem>
                    ))}
                </SelectContent>
            </Select>
        </div>
    );
}

function PreviewStat({ label, v }) {
    return (
        <div className="border border-white/10 bg-black/30 rounded-md p-2">
            <div className="font-mono-tag text-zinc-500 text-[10px]">{label}</div>
            <div className="text-white text-sm capitalize truncate">{v}</div>
        </div>
    );
}
