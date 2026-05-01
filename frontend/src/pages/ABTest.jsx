import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
    Beaker, ArrowRight, Loader2, Crown, Star, Trophy, Wand2, Hash, Film, ChevronLeft,
} from "lucide-react";

import api from "../lib/api";
import NavBar from "../components/NavBar";
import { Button } from "../components/ui/button";
import { Slider } from "../components/ui/slider";
import { Textarea } from "../components/ui/textarea";

const STYLE_OPTIONS = ["storytelling", "listicle", "documentary", "first-person", "dramatic", "educational"];

export default function ABTest() {
    const { id } = useParams();
    const nav = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [running, setRunning] = useState(false);
    const [styleA, setStyleA] = useState("storytelling");
    const [styleB, setStyleB] = useState("listicle");
    const [scores, setScores] = useState({});
    const [weights, setWeights] = useState({ hook: 50, title: 20, overall: 30 });
    const [savingWeights, setSavingWeights] = useState(false);

    const refresh = async () => {
        setLoading(true);
        try {
            const r = await api.get(`/projects/${id}/variants`);
            setData(r.data);
            const sm = {};
            (r.data.variants || []).forEach((v) => {
                const s = v.score || {};
                sm[v.id] = {
                    hook: s.hook ?? 5,
                    title: s.title ?? 5,
                    overall: s.overall ?? 5,
                    note: s.note ?? "",
                };
            });
            setScores(sm);
            const w = r.data.ab_weights || {};
            const total = (Number(w.hook) || 0) + (Number(w.title) || 0) + (Number(w.overall) || 0);
            const denom = total > 0 ? total : 1;
            setWeights({
                hook: Math.round(((Number(w.hook) || 0.5) / denom) * 100),
                title: Math.round(((Number(w.title) || 0.2) / denom) * 100),
                overall: Math.round(((Number(w.overall) || 0.3) / denom) * 100),
            });
        } catch (e) {
            toast.error("Failed to load A/B test");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { refresh(); }, [id]);

    const generateVariants = async () => {
        setRunning(true);
        try {
            await api.post("/projects/script/variants", {
                project_id: id, style_a: styleA, style_b: styleB,
            });
            toast.success("A/B variants generated");
            await refresh();
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Generation failed");
        } finally {
            setRunning(false);
        }
    };

    const submitScore = async (vid) => {
        const s = scores[vid] || {};
        try {
            const r = await api.post("/projects/script/variants/score", {
                project_id: id, variant_id: vid,
                hook_score: s.hook, title_score: s.title, overall_score: s.overall,
                note: s.note,
            });
            toast.success(`Saved · winner: ${r.data.ab_winner || vid}`);
            await refresh();
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Save failed");
        }
    };

    const pickWinner = async (vid) => {
        try {
            await api.post("/projects/script/select-variant", { project_id: id, variant_id: vid });
            toast.success(`Variant ${vid} chosen — back to wizard`);
            nav(`/wizard/${id}`);
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Selection failed");
        }
    };

    const saveWeights = async () => {
        setSavingWeights(true);
        try {
            const r = await api.post("/projects/script/variants/weights", {
                project_id: id,
                hook: weights.hook / 100,
                title: weights.title / 100,
                overall: weights.overall / 100,
            });
            toast.success(`Weights saved · winner: ${r.data.ab_winner || "—"}`);
            await refresh();
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Failed to save weights");
        } finally {
            setSavingWeights(false);
        }
    };

    const PRESETS = [
        { id: "hook", label: "Hook-heavy", w: { hook: 50, title: 20, overall: 30 } },
        { id: "balanced", label: "Balanced", w: { hook: 33, title: 33, overall: 34 } },
        { id: "title", label: "Title-CTR", w: { hook: 25, title: 50, overall: 25 } },
        { id: "overall", label: "Overall-driven", w: { hook: 20, title: 20, overall: 60 } },
    ];

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0A0A0B]">
                <NavBar />
                <div className="grid place-items-center py-32"><Loader2 className="w-8 h-8 text-[#F23F42] animate-spin" /></div>
            </div>
        );
    }

    const variants = data?.variants || [];
    const winner = data?.ab_winner;
    const metrics = data?.ab_metrics || {};

    return (
        <div className="min-h-screen bg-[#0A0A0B]" data-testid="ab-test-page">
            <NavBar />
            <div className="max-w-7xl mx-auto px-6 lg:px-12 py-10">
                {/* Top */}
                <div className="flex items-center justify-between flex-wrap gap-4 mb-8">
                    <div>
                        <Link to={`/wizard/${id}`} className="inline-flex items-center text-zinc-500 hover:text-white text-xs font-mono-tag mb-3">
                            <ChevronLeft className="w-3.5 h-3.5 mr-1" /> BACK TO WIZARD
                        </Link>
                        <div className="font-mono-tag text-[#F23F42] mb-2">/ A/B TEST RESULTS</div>
                        <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter" data-testid="ab-title">
                            Two scripts. One winner.
                        </h1>
                        <p className="mt-3 text-zinc-400 max-w-2xl">
                            Generate two competing versions of your script, score each on hook, title and overall feel —
                            we'll auto-pick the winner.
                        </p>
                        {data?.topic && (
                            <div className="mt-3 text-xs text-zinc-500 font-mono-tag">
                                TOPIC: <span className="text-zinc-300">{data.topic}</span>
                                {" · "} NICHE: <span className="text-zinc-300">{data.niche}</span>
                            </div>
                        )}
                    </div>

                    <div className="flex items-end gap-3 flex-wrap">
                        <div>
                            <label className="font-mono-tag text-xs text-zinc-500 block mb-1">VARIANT A STYLE</label>
                            <select
                                data-testid="style-a-select"
                                value={styleA} onChange={(e) => setStyleA(e.target.value)}
                                className="bg-[#121214] border border-white/10 rounded-md px-3 py-2 text-sm text-zinc-200">
                                {STYLE_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>
                        <div>
                            <label className="font-mono-tag text-xs text-zinc-500 block mb-1">VARIANT B STYLE</label>
                            <select
                                data-testid="style-b-select"
                                value={styleB} onChange={(e) => setStyleB(e.target.value)}
                                className="bg-[#121214] border border-white/10 rounded-md px-3 py-2 text-sm text-zinc-200">
                                {STYLE_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>
                        <Button
                            onClick={generateVariants} disabled={running}
                            data-testid="generate-variants-btn"
                            className="bg-[#F23F42] hover:bg-[#FF5C5E] text-white">
                            {running
                                ? (<><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating…</>)
                                : (<><Wand2 className="w-4 h-4 mr-2" /> Generate A/B</>)}
                        </Button>
                    </div>
                </div>

                {/* Empty state */}
                {variants.length === 0 && (
                    <div className="rounded-xl border border-dashed border-white/10 p-16 text-center">
                        <Beaker className="w-10 h-10 mx-auto text-zinc-600 mb-3" />
                        <h3 className="font-display text-2xl font-bold tracking-tight">No variants yet</h3>
                        <p className="text-zinc-500 mt-2">Pick two styles above and hit <span className="text-white">Generate A/B</span>.</p>
                    </div>
                )}

                {/* Side-by-side */}
                {variants.length > 0 && (
                    <div className="rounded-xl border border-white/10 bg-[#121214] p-5 mb-6" data-testid="ab-weights-panel">
                        <div className="flex items-start justify-between flex-wrap gap-3">
                            <div>
                                <div className="font-mono-tag text-xs text-zinc-500 mb-1">/ WEIGHTING</div>
                                <div className="font-display text-lg font-bold tracking-tight">How should we pick the winner?</div>
                                <p className="text-xs text-zinc-500 mt-1">
                                    Different niches reward different signals — drag to dial in. Values normalise automatically.
                                </p>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {PRESETS.map((p) => (
                                    <button key={p.id}
                                        data-testid={`weight-preset-${p.id}`}
                                        onClick={() => setWeights(p.w)}
                                        className="font-mono-tag text-[11px] uppercase px-3 py-1.5 rounded-md border border-white/10 text-zinc-300 hover:bg-white/5">
                                        {p.label}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div className="mt-5 grid sm:grid-cols-3 gap-5">
                            {[
                                { k: "hook", label: "Hook" },
                                { k: "title", label: "Title" },
                                { k: "overall", label: "Overall" },
                            ].map(({ k, label }) => (
                                <div key={k}>
                                    <div className="flex justify-between text-xs font-mono-tag text-zinc-500 mb-1">
                                        <span>{label.toUpperCase()}</span>
                                        <span className="text-zinc-200" data-testid={`weight-${k}-value`}>{weights[k]}%</span>
                                    </div>
                                    <Slider
                                        data-testid={`weight-${k}-slider`}
                                        min={0} max={100} step={5}
                                        value={[weights[k]]}
                                        onValueChange={(val) => setWeights((p) => ({ ...p, [k]: val[0] }))}
                                    />
                                </div>
                            ))}
                        </div>
                        <div className="mt-4 flex items-center justify-between flex-wrap gap-2">
                            <div className="text-[11px] font-mono-tag text-zinc-500">
                                NORMALISED: HOOK {Math.round((weights.hook / Math.max(weights.hook + weights.title + weights.overall, 1)) * 100)}%
                                · TITLE {Math.round((weights.title / Math.max(weights.hook + weights.title + weights.overall, 1)) * 100)}%
                                · OVERALL {Math.round((weights.overall / Math.max(weights.hook + weights.title + weights.overall, 1)) * 100)}%
                            </div>
                            <Button onClick={saveWeights} disabled={savingWeights}
                                data-testid="save-weights-btn"
                                className="bg-[#F23F42] hover:bg-[#FF5C5E] text-white">
                                {savingWeights
                                    ? (<><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Saving…</>)
                                    : "Save & recompute winner"}
                            </Button>
                        </div>
                    </div>
                )}

                <div className="grid md:grid-cols-2 gap-6">
                    {variants.map((v) => {
                        const isWinner = winner === v.id;
                        const score = scores[v.id] || { hook: 5, title: 5, overall: 5, note: "" };
                        const setS = (k, val) => setScores((p) => ({ ...p, [v.id]: { ...p[v.id], [k]: val } }));
                        return (
                            <motion.div
                                key={v.id}
                                initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                                data-testid={`variant-card-${v.id}`}
                                className={`relative rounded-xl border p-6 ${
                                    isWinner ? "border-[#F23F42]/60 bg-[#F23F42]/5"
                                             : "border-white/10 bg-[#121214]"
                                }`}>
                                {isWinner && (
                                    <div className="absolute top-4 right-4 inline-flex items-center gap-1 text-[#F23F42] font-mono-tag text-xs">
                                        <Trophy className="w-3.5 h-3.5" /> WINNER
                                    </div>
                                )}
                                <div className="font-mono-tag text-xs text-zinc-500">VARIANT {v.id}</div>
                                <div className="font-display text-2xl font-bold tracking-tight mt-1" data-testid={`variant-title-${v.id}`}>
                                    {v.script?.title || "(untitled)"}
                                </div>
                                <div className="text-xs text-zinc-500 mt-1">style · {v.style}</div>

                                <div className="mt-4 space-y-3 text-sm">
                                    <div>
                                        <div className="font-mono-tag text-xs text-zinc-500 mb-1">HOOK</div>
                                        <div className="text-zinc-300">{v.script?.hook || "—"}</div>
                                    </div>
                                    <div>
                                        <div className="font-mono-tag text-xs text-zinc-500 mb-1">DESCRIPTION</div>
                                        <div className="text-zinc-400">{v.script?.description || "—"}</div>
                                    </div>
                                    <div>
                                        <div className="font-mono-tag text-xs text-zinc-500 mb-1 flex items-center gap-1">
                                            <Film className="w-3 h-3" /> SCENES ({v.script?.scenes?.length || 0})
                                        </div>
                                        <ol className="text-zinc-400 text-xs space-y-1 list-decimal pl-4">
                                            {(v.script?.scenes || []).slice(0, 4).map((s, i) => (
                                                <li key={i}>{s.narration?.slice(0, 80)}…</li>
                                            ))}
                                        </ol>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                        {(v.script?.tags || []).slice(0, 5).map((t, i) => (
                                            <span key={i} className="inline-flex items-center text-[10px] font-mono-tag uppercase text-zinc-400 px-2 py-0.5 rounded border border-white/10">
                                                <Hash className="w-2.5 h-2.5 mr-0.5" />{t}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                {/* Scoring */}
                                <div className="mt-6 border-t border-white/10 pt-4 space-y-4">
                                    {[
                                        { k: "hook", label: "Hook strength" },
                                        { k: "title", label: "Title CTR feel" },
                                        { k: "overall", label: "Overall" },
                                    ].map(({ k, label }) => (
                                        <div key={k}>
                                            <div className="flex justify-between text-xs font-mono-tag text-zinc-500 mb-1">
                                                <span>{label.toUpperCase()}</span>
                                                <span className="text-zinc-300">{score[k]} / 10</span>
                                            </div>
                                            <Slider
                                                data-testid={`score-${v.id}-${k}`}
                                                min={0} max={10} step={0.5}
                                                value={[score[k]]}
                                                onValueChange={(val) => setS(k, val[0])}
                                            />
                                        </div>
                                    ))}
                                    <Textarea
                                        data-testid={`note-${v.id}`}
                                        placeholder="Notes (optional)"
                                        rows={2}
                                        value={score.note}
                                        onChange={(e) => setS("note", e.target.value)}
                                        className="bg-[#0A0A0B] border-white/10 text-sm"
                                    />
                                    <div className="grid grid-cols-2 gap-2">
                                        <Button onClick={() => submitScore(v.id)} variant="outline"
                                            data-testid={`save-score-${v.id}`}
                                            className="border-white/10 hover:bg-white/5">
                                            <Star className="w-4 h-4 mr-2" /> Save score
                                        </Button>
                                        <Button onClick={() => pickWinner(v.id)}
                                            data-testid={`pick-${v.id}`}
                                            className="bg-[#F23F42] hover:bg-[#FF5C5E]">
                                            <Crown className="w-4 h-4 mr-2" /> Pick winner
                                        </Button>
                                    </div>
                                    {metrics[v.id] !== undefined && (
                                        <div className="text-[11px] font-mono-tag text-zinc-500" data-testid={`weighted-${v.id}`}>
                                            WEIGHTED (HOOK 50% · TITLE 20% · OVERALL 30%): <span className="text-zinc-200">{Number(metrics[v.id]).toFixed(2)}</span> / 10
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        );
                    })}
                </div>

                {variants.length > 0 && (
                    <div className="mt-8 text-center">
                        <Link to={`/wizard/${id}`} data-testid="back-to-wizard"
                            className="inline-flex items-center text-zinc-300 hover:text-white">
                            Continue in wizard <ArrowRight className="w-4 h-4 ml-2" />
                        </Link>
                    </div>
                )}
            </div>
        </div>
    );
}
