# VideoForge AI — Product Requirements Document

## Original Problem Statement
Build a full-stack AI-powered SaaS platform that automatically generates and publishes YouTube-ready videos from minimal user input. Pipeline: Topic → Trends → Script → Voice → Visuals → Render → Auto-Publish to YouTube. Includes analytics, series planner, A/B testing, multi-language, niche templates, and Free/Paid tiers.

## User Personas
- Faceless content creators scaling YouTube channels (finance, horror, motivation, facts)
- Marketing teams producing volume video content
- Solo entrepreneurs building personal brands without filming

## Tech Stack
- Backend: FastAPI (Python 3.11) + Motor (MongoDB) + FFmpeg
- Frontend: React 19 + Tailwind + Shadcn UI + Framer Motion + Recharts
- Auth: JWT (email/password, bcrypt)
- AI: Emergent Universal LLM Key for GPT-4o-mini (script & trends), OpenAI TTS-1 (voice), GPT Image 1 (thumbnails)
- Premium voice: ElevenLabs (eleven_multilingual_v2)
- Video: FFmpeg slideshow + ken-burns + burnt-in subtitles → MP4
- Distribution: YouTube Data API v3 OAuth
- Billing: Stripe (Emergent test key)

## What's Implemented

### Phase 1 (2026-05-01)
- JWT auth (register/login/me)
- Projects CRUD
- AI Trends API (6h cached)
- Script generation (GPT-4o-mini) with hook/scenes/CTA/tags + A/B variants
- Voice generation (OpenAI TTS, 6 voices)
- Thumbnail generation (GPT Image 1)
- Bulk content series (1-30 videos)
- Analytics dashboard (synthetic)
- Tools comparison
- Frontend: Landing, Auth, Dashboard, 5-step Wizard, Trends, Analytics, Pricing

### Phase 2 (2026-05-01)
- **Real YouTube OAuth + upload**: `/api/youtube/auth-url`, `/api/youtube/callback`, `/api/youtube/status`, `/api/youtube/disconnect`. Real `videos.insert` with thumbnail upload + scheduling support.
- **FFmpeg video render**: `/api/projects/render` produces MP4 (1920x1080, slow ken-burns zoom, AAC audio, burnt-in subtitle SRT). Served via `/api/projects/{id}/video` (auth-protected).
- **ElevenLabs premium voices**: 7 curated voices added to `/api/voices`, used when ElevenLabs voice_id selected. ⚠️ ElevenLabs free tier blocked from cloud IPs — requires paid plan to actually synthesize.
- **Stripe checkout**: `/api/billing/plans`, `/api/billing/checkout`, `/api/billing/status/{id}`, `/api/webhook/stripe`. Plans: Creator $29 (1500 credits), Studio $99 (unlimited), Credits pack $5 (100). Auto-credits on webhook + polling fallback.
- **Frontend additions**: BillingSuccess page, YouTube Connect card on Dashboard, Premium voice tab in Wizard, Render step (step 5/6) in Wizard, Stripe checkout buttons on Pricing.
- **Tests**: 46/47 backend tests pass (1 skipped: ElevenLabs 401 from cloud IP — expected).

## Architecture Notes
- Backend modules: `server.py` (routes), `youtube_service.py` (OAuth/upload), `render_service.py` (FFmpeg), `elevenlabs_service.py` (TTS)
- All routes prefixed `/api`. Bearer JWT auth.
- MongoDB collections: `users`, `projects`, `trends_cache`, `analytics`, `youtube_tokens`, `oauth_states`, `payment_transactions`
- Stripe Emergent proxy supports create but NOT retrieve sessions; we gracefully fall back to DB state and rely on webhook for paid status

## Backlog (Prioritised)
### P0
- Real video composition with multi-scene support (per-scene image generation + transitions)
- ElevenLabs paid plan or alternative cloud-friendly TTS for premium tier
- Real YouTube analytics ingestion (replace synthetic data once user has uploads)

### P1
- Real trend sources (YouTube trending API, Reddit, Google Trends)
- Multi-language UI translations
- Content calendar with drag-drop scheduling
- A/B test results dashboard

### P2
- AI Agent Mode (autonomous topic → upload loop)
- Niche-specific templates (finance/horror/motivation pre-tuned)
- Channel multi-management for Studio tier
- Object storage for media assets (currently base64 in MongoDB)

## Known Limitations
- ElevenLabs free tier blocked from cloud/proxy IPs; user needs paid plan for premium voices to work in this deployment
- Stripe Session.retrieve unsupported by Emergent proxy; payment status updates via webhook (works in production)
- Video render is single-image slideshow; multi-scene composition is a backlog item

## Test Credentials
See `/app/memory/test_credentials.md`. `tester@videoforge.ai` / `TestPass123!`
