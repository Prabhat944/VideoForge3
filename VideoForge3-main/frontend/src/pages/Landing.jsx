import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Button } from "../components/ui/button";
import NavBar from "../components/NavBar";
import { ArrowRight, Sparkles, Mic, Image as ImageIcon, Upload, TrendingUp, Wand2, Calendar, BarChart3, Zap } from "lucide-react";

const features = [
    { icon: TrendingUp, label: "Trend Discovery", desc: "Real-time trending topics from YouTube, Reddit & Google with viral score." },
    { icon: Wand2, label: "AI Script Engine", desc: "Hook → body → CTA, optimized for retention with multi-style A/B variants." },
    { icon: Mic, label: "Studio Voice", desc: "6 cinematic voices, emotion + speed control, instant preview." },
    { icon: ImageIcon, label: "Smart Thumbnails", desc: "AI-designed thumbnails proven to lift CTR up to 38%." },
    { icon: Calendar, label: "Auto Scheduling", desc: "Drop a 30-video series in one click. Bulk publish on autopilot." },
    { icon: BarChart3, label: "Channel Brain", desc: "Watch time, CTR, retention plus AI-driven content suggestions." },
];

const steps = [
    { n: "01", t: "Pick a topic", d: "Type one line or browse trends." },
    { n: "02", t: "AI writes", d: "Hook, scenes & CTA in seconds." },
    { n: "03", t: "Voice & visuals", d: "Cinematic voice + thumbnail." },
    { n: "04", t: "Publish to YouTube", d: "Schedule or auto-upload." },
];

export default function Landing() {
    return (
        <div className="min-h-screen bg-[#0A0A0B] text-white" data-testid="landing-page">
            <NavBar />

            {/* HERO */}
            <section className="relative overflow-hidden">
                <div
                    className="absolute inset-0 opacity-30 pointer-events-none"
                    style={{
                        backgroundImage:
                            "url(https://images.unsplash.com/photo-1762541693135-fb989de961e1?crop=entropy&cs=srgb&fm=jpg&w=2000&q=85)",
                        backgroundSize: "cover",
                        backgroundPosition: "center",
                    }}
                />
                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/60 to-[#0A0A0B]" />

                <div className="relative max-w-7xl mx-auto px-6 lg:px-12 pt-24 pb-32">
                    <motion.div
                        initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}
                        className="max-w-4xl"
                    >
                        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-white/10 bg-white/5 mb-8">
                            <Sparkles className="w-3.5 h-3.5 text-[#F23F42]" />
                            <span className="font-mono-tag text-zinc-300">Powered by GPT-5 · Nano Banana · TTS-1</span>
                        </div>
                        <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl xl:text-8xl font-black tracking-tighter leading-[0.95]">
                            Type a topic.<br />
                            Get a <span className="text-[#F23F42]">YouTube video</span>.<br />
                            Auto-publish.
                        </h1>
                        <p className="mt-8 text-lg sm:text-xl text-zinc-400 max-w-2xl leading-relaxed">
                            VideoForge turns one line of input into ready-to-publish YouTube videos —
                            script, voiceover, thumbnail and scheduled upload, end to end.
                        </p>
                        <div className="mt-10 flex flex-col sm:flex-row gap-4">
                            <Link to="/register" data-testid="hero-cta-start">
                                <Button size="lg" className="bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md px-8 h-14 text-base font-semibold glow-red">
                                    Start creating free
                                    <ArrowRight className="ml-2 w-5 h-5" />
                                </Button>
                            </Link>
                            <Link to="/pricing" data-testid="hero-cta-pricing">
                                <Button size="lg" variant="outline" className="rounded-md px-8 h-14 text-base bg-white/5 border-white/10 hover:bg-white/10 text-white">
                                    View pricing
                                </Button>
                            </Link>
                        </div>
                        <div className="mt-12 flex items-center gap-6 text-sm text-zinc-500">
                            <div className="flex items-center gap-2"><Zap className="w-4 h-4 text-[#F23F42]"/><span>Generates in &lt; 2 min</span></div>
                            <div className="flex items-center gap-2"><Upload className="w-4 h-4 text-[#F23F42]"/><span>Direct YouTube upload</span></div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* PIPELINE STEPS */}
            <section className="border-t border-white/10 py-24" id="features">
                <div className="max-w-7xl mx-auto px-6 lg:px-12">
                    <div className="font-mono-tag text-[#F23F42] mb-4">/ THE PIPELINE</div>
                    <h2 className="font-display text-4xl sm:text-5xl font-black tracking-tighter max-w-2xl">
                        From idea to upload, in four moves.
                    </h2>
                    <div className="mt-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-px bg-white/10">
                        {steps.map((s, i) => (
                            <motion.div
                                key={s.n}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.08 }}
                                className="bg-[#0A0A0B] p-8 hover:bg-[#121214] transition-colors"
                            >
                                <div className="font-display text-5xl font-black text-[#F23F42] tracking-tighter">{s.n}</div>
                                <div className="mt-6 text-xl font-semibold">{s.t}</div>
                                <div className="mt-2 text-sm text-zinc-500">{s.d}</div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* FEATURES */}
            <section className="border-t border-white/10 py-24">
                <div className="max-w-7xl mx-auto px-6 lg:px-12">
                    <div className="font-mono-tag text-[#F23F42] mb-4">/ FEATURE SET</div>
                    <h2 className="font-display text-4xl sm:text-5xl font-black tracking-tighter max-w-3xl">
                        Everything a faceless creator channel needs.
                    </h2>
                    <div className="mt-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {features.map((f, i) => (
                            <motion.div
                                key={f.label}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.05 }}
                                className="border border-white/10 bg-[#121214] p-8 rounded-md hover:border-white/30 transition-all hover:-translate-y-0.5"
                            >
                                <f.icon className="w-7 h-7 text-[#F23F42]" strokeWidth={1.8} />
                                <div className="mt-6 text-xl font-semibold">{f.label}</div>
                                <div className="mt-2 text-sm text-zinc-400 leading-relaxed">{f.desc}</div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA */}
            <section className="border-t border-white/10 py-32">
                <div className="max-w-4xl mx-auto px-6 lg:px-12 text-center">
                    <h2 className="font-display text-5xl sm:text-6xl font-black tracking-tighter">
                        Ship 30 videos this month.<br/>
                        <span className="text-[#F23F42]">Without filming any.</span>
                    </h2>
                    <p className="mt-6 text-zinc-400 text-lg max-w-xl mx-auto">
                        Start with 100 free credits. Build your channel on autopilot.
                    </p>
                    <Link to="/register" data-testid="footer-cta">
                        <Button size="lg" className="mt-10 bg-[#F23F42] hover:bg-[#FF5C5E] text-white rounded-md px-10 h-14 text-base font-semibold glow-red">
                            Get started — it's free
                            <ArrowRight className="ml-2 w-5 h-5" />
                        </Button>
                    </Link>
                </div>
            </section>

            <footer className="border-t border-white/10 py-10 text-center text-zinc-600 text-sm">
                © 2026 VideoForge AI · Built for creators who ship.
            </footer>
        </div>
    );
}
