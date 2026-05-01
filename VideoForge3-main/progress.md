# VideoForge AI — Progress Tracker

> Live status of build. Updated as work progresses.

## ✅ Completed

### Phase 4 — P0 + P1 features (2026-05-01)
- [x] **Scene image storage refactor** — moved from base64-in-Mongo to filesystem (`/app/backend/media/scenes/{project_id}/scene_N.png`). New `storage_service.py`. Project document now stores `image_url` + `image_path`; physical files served via `/api/media/{kind}/{project_id}/{filename}` with auth (Bearer header OR `?token=` query param for `<img>` tags).
- [x] **Idempotency guard** on `POST /api/projects/scenes` — returns HTTP 409 if `scenes_status == 'generating'` was set in the last 10 minutes. Verified: 1st call → 200, 2nd rapid call → 409.
- [x] **Real Reddit trends** integration via `/api/trends?source=reddit` (note: Reddit IP-blocks cloud requests; falls back to AI gracefully).
- [x] **Real YouTube Trends** via `/api/trends?source=youtube` using user's OAuth token (most-popular videos in their region).
- [x] **AI Agent Mode** — `POST /api/agent/run` orchestrates the entire pipeline (script → voice → thumbnail → scenes → render → optional auto-publish) as a background task. `GET /api/agent/status/{id}` returns current stage + status. Frontend page at `/agent` with 8-stage live progress timeline.
- [x] **Content Calendar** — `GET /api/calendar` returns all scheduled/published projects sorted chronologically, frontend page at `/calendar` with day-grouped timeline view + status pills.
- [x] **Navigation updated** with Agent and Calendar links.
- [x] **API helper `withAuth(url)`** for auth-protected `<img>` sources (appends `?token=...`).
- [x] **YouTube OAuth env-load timing fix** — youtube_service now reads env via `_env()` lazy-helper (was reading at module import → empty client_id).
- [x] **Phase 4 backend tests: 25/25 passing** + Phase 1/2/3 regression 47/48 (1 expected ElevenLabs skip).

### Phase 1 — MVP (2026-05-01)
- [x] FastAPI backend bootstrap with MongoDB (Motor)
- [x] JWT auth (register, login, me) with bcrypt
- [x] Projects CRUD (`POST /api/projects`, list, get, delete)
- [x] AI script generation via GPT-4o-mini (hook + scenes + CTA + tags)
- [x] OpenAI TTS-1 voice generation (6 voices)
- [x] GPT Image 1 thumbnail generation
- [x] AI-generated trends discovery (cached 6h)
- [x] Bulk content series creation (1-30 videos)
- [x] Synthetic analytics dashboard
- [x] Tools comparison endpoint
- [x] React frontend: Landing, Auth (login/register), Dashboard, Wizard (5 steps), Trends, Analytics, Pricing
- [x] Cinematic dark theme (Obsidian #0A0A0B + Signal Red #F23F42, Bricolage Grotesque + IBM Plex Sans)
- [x] Sonner toasts, protected routes, auth context
- [x] **25/25 backend tests passing**

### Phase 2 — Real integrations (2026-05-01)
- [x] Real YouTube OAuth flow (`/api/youtube/auth-url`, `/api/youtube/callback`, `/api/youtube/status`, `/api/youtube/disconnect`)
- [x] Real `videos.insert` upload via YouTube Data API v3 with thumbnail + scheduling
- [x] FFmpeg single-image MP4 render (`/api/projects/render`) — 1920×1080, ken-burns, burnt-in subs
- [x] ElevenLabs voice integration (7 premium voices wired)
- [x] Stripe Checkout for Creator $29 / Studio $99 / 100-credits $5 packs
- [x] Stripe webhook + status polling with credit application
- [x] BillingSuccess page with payment polling
- [x] YouTube Connect button on Dashboard
- [x] Premium voice tab in Wizard
- [x] Render step (5/6) in Wizard
- [x] **46/47 backend tests passing** (1 ElevenLabs skip — see Known Limitations)

### Phase 3 — Premium UX & Real Analytics (2026-05-01)
- [x] OpenAI TTS-1-HD added as cloud-friendly Premium tier (6 HD voices: hd_alloy, hd_echo, hd_fable, hd_onyx, hd_nova, hd_shimmer)
- [x] Three-tier voice picker in Wizard (Free / Premium HD / ElevenLabs)
- [x] `POST /api/projects/scenes` — per-scene image generation via GPT Image 1 (background task)
- [x] `GET /api/projects/{id}/scenes-status` — polling endpoint for scene gen progress
- [x] **Event-loop fix**: `asyncio.to_thread(_gen_sync, prompt)` to keep FastAPI responsive during heavy image gen
- [x] Multi-scene MP4 rendering with crossfade transitions (`render_scenes_mp4`)
- [x] Real YouTube Data API video stats (views/likes/comments) for connected channels
- [x] Real YouTube Analytics API integration (14-day series, watch time, subs gained)
- [x] `data_source: 'youtube' | 'synthetic'` flag on `/api/analytics/summary`
- [x] Live/Demo data badge on Analytics page
- [x] Added `yt-analytics.readonly` OAuth scope
- [x] Wizard "Generate scenes" step with thumbnail grid + polling
- [x] Project model includes `scene_images`, `video_path`, `video_url`, `uploaded_real`, `scenes_status` fields
- [x] **Phase 3 backend pytest: 16/16 passing** (full TestScenesEndpoint + TestMultiSceneRender + TestAnalyticsSummary classes green)

## 🔄 In Progress / Verification
- [x] Phase 3 full pytest validated end-to-end (6/6 scenes endpoint + 2/2 multi-scene render + 3/3 analytics)

## 📋 Backlog (Prioritised)

### P0 — Production Readiness
- [x] ~~Migrate scene images from base64-in-Mongo to filesystem~~ ✅ Phase 4
- [x] ~~Idempotency check on `/projects/scenes`~~ ✅ Phase 4
- [ ] Move thumbnail and voice MP3 to filesystem too (currently still base64 in Mongo — risk diminished but not zero)
- [ ] Object storage (S3 / GCS) for true horizontal-scale (currently local disk)
- [ ] Rate limiting on AI endpoints

### P1 — Differentiating Features
- [x] ~~Real trend sources~~ (Reddit + YouTube via OAuth implemented; Reddit needs OAuth in cloud) ✅ Phase 4
- [x] ~~AI Agent Mode~~ ✅ Phase 4
- [x] ~~Content Calendar UI~~ ✅ Phase 4
- [ ] Reddit OAuth credentials integration to bypass cloud-IP block
- [ ] Google Trends via pytrends
- [ ] Per-project A/B test results dashboard
- [ ] Niche-specific templates pre-tuned for finance / horror / motivation / facts
- [ ] Multi-language UI translations

### P2 — Scale & Polish
- [ ] Channel multi-management (Studio tier)
- [ ] Voice cloning support (ElevenLabs Pro)
- [ ] Background music sync (royalty-free music library + ducking under voiceover)
- [ ] Brand kit (logo overlay, intro/outro stingers)
- [ ] Team seats + role-based access
- [ ] Webhook for "video published" events (third-party integrations)

## ⚠️ Known Limitations
1. **ElevenLabs free tier blocked from cloud IPs** — returns 401 `detected_unusual_activity`. Requires paid ElevenLabs plan to synthesize from this deployment. Workaround: use Premium HD tier (OpenAI tts-1-hd) which works on the Universal Key.
2. **Stripe `Session.retrieve` unsupported by Emergent's Stripe proxy** — payment status updates rely on the webhook; polling falls back to DB state. Works in production with a real Stripe key.
3. **YouTube real upload requires** — user to (a) click Connect on Dashboard and complete OAuth, (b) render an MP4 in step 5 of the wizard. Otherwise publish falls back to mock with `real:false` flag.
4. **Single-image base64 storage** in MongoDB document — fine for current scope but will hit BSON 16MB limit for projects with many scene images. Move to object storage planned for P0.
5. **Phase 3 pytest** has long total runtime (~5-10 min) due to real OpenAI HD voice + 6× GPT Image 1 calls; now confirmed passing 16/16.
6. **ffmpeg/ffprobe must remain installed** in container — `apt-get install -y ffmpeg` (verified present after deploy).

## 📂 Code Map
- `/app/backend/server.py` — FastAPI routes (~1100 lines)
- `/app/backend/youtube_service.py` — OAuth, upload, video stats, analytics
- `/app/backend/render_service.py` — FFmpeg single-image + multi-scene composition
- `/app/backend/elevenlabs_service.py` — ElevenLabs TTS wrapper
- `/app/frontend/src/pages/` — Landing, Auth, Dashboard, Wizard (6 steps), Trends, Analytics, Pricing, BillingSuccess
- `/app/frontend/src/components/` — NavBar, ProtectedRoute
- `/app/memory/PRD.md` — Full product requirements doc
- `/app/memory/test_credentials.md` — Test user

## 🔑 Test Credentials
`tester@videoforge.ai` / `TestPass123!`
