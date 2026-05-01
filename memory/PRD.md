# VideoForge AI — PRD

> Generated/updated by E1 — stage2-modular release · 2026-05-01

## Original Problem Statement
Clone `https://github.com/Prabhat944/VideoForge2/tree/stage2`, run end-to-end, then complete:
- **P0**: move thumbnail + voice MP3 from base64-in-Mongo to filesystem.
- **P0**: modularise the 1496-line `server.py` into APIRouter files (auth/projects/pipeline/agent/billing/youtube/media).
- **P1**: Reddit OAuth credentials integration to bypass cloud-IP block.
- **P1**: Per-project A/B test results dashboard.
- **P1**: Niche-specific pre-tuned templates (finance / horror / motivation / facts).

## Architecture (post-stage2)
```
backend/
├── server.py                     # ~70 lines — mounts /api router + 11 sub-routers
├── core/
│   ├── config.py                 # env via load_dotenv
│   ├── db.py                     # single Motor client + db
│   ├── deps.py                   # JWT bearer, hash/verify password, get_current_user, now_iso
│   ├── schemas.py                # all Pydantic models
│   ├── voices.py                 # VOICES + HD_VOICES presets
│   ├── niche_templates.py        # 8 templates × 4 niches
│   └── migrations.py             # startup migration: legacy base64 → filesystem
├── routers/
│   ├── auth.py                   # /auth/register, /auth/login, /auth/me
│   ├── projects.py               # CRUD + /projects/series
│   ├── pipeline.py               # /script, /voice (FS), /thumbnail, /scenes, /render, /publish + A/B
│   ├── agent.py                  # /agent/run, /agent/status (background pipeline)
│   ├── billing.py                # /billing/plans, /checkout, /status, /webhook/stripe
│   ├── youtube.py                # OAuth status/auth-url/callback/disconnect
│   ├── media.py                  # /media/{kind}/{pid}/{file} (auth-protected)
│   ├── trends.py                 # AI / Reddit (OAuth or anon) / YouTube trending
│   ├── templates.py              # /templates listing + /projects/from-template
│   ├── calendar.py               # /calendar
│   └── analytics.py              # /analytics/summary
├── elevenlabs_service.py         # ElevenLabs TTS wrapper
├── render_service.py             # ffmpeg single-image + multi-scene render
├── youtube_service.py            # YouTube Data API + Analytics API
├── trends_service.py             # Reddit (oauth+anon) + YouTube most-popular
└── storage_service.py            # disk persistence for scenes / thumbnails / voices

frontend/src/pages/
├── Templates.jsx                 # NEW — niche template browser
├── ABTest.jsx                    # NEW — per-project A/B dashboard
└── …existing pages unchanged
```

## P0 — Storage migration (DONE)
- `POST /api/projects/voice` writes the MP3 to `/app/backend/media/voices/{project_id}/voice.mp3` and stores `voice.audio_path` + `voice.audio_url`. Response no longer contains `audio_b64`.
- `POST /api/projects/thumbnail` already wrote PNG to disk in stage1 — confirmed.
- Startup migration `core/migrations.migrate_base64_to_fs()` is idempotent: detects legacy `voice.audio_b64` and `thumbnail_url` `data:` blobs, writes them to disk and unsets the base64 field. Verified zero legacy blobs in the test DB after run.

## P0 — Modularisation (DONE)
`server.py` reduced from **1744** → **~70 lines**. The full feature surface lives under `core/` and `routers/` with clean dependency injection (`Depends(get_current_user)`).

## P1 — Reddit OAuth (DONE / inert)
`trends_service.fetch_reddit_trends()` now obtains a `client_credentials` token from Reddit when `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` are set in `backend/.env`, then queries `oauth.reddit.com` (bypasses cloud-IP block). When credentials are absent the path falls back to anonymous `www.reddit.com` JSON, then to AI / static fallback. Token is cached in-process for 1 h.

## P1 — A/B Test Results Dashboard (DONE)
Backend:
- `POST /api/projects/script/variants` — generate two scripts (style A / B) in parallel.
- `GET /api/projects/{id}/variants` — full dashboard payload incl. both scripts, scores, winner, metrics.
- `POST /api/projects/script/variants/score` — persist hook/title/overall (+ optional note); auto-recomputes `ab_winner` as the variant with the highest `overall`.
- `POST /api/projects/script/select-variant` — copy the chosen script onto `project.script` and set `selected_variant_id` / `ab_winner` / `status=script_ready`.

Frontend:
- `/ab-test/:id` — side-by-side comparison page with Title, Hook, Description, top scenes, Tags, three sliders (hook / title / overall) + Note, "Save score" + "Pick winner" buttons. Winner card glows red and shows trophy.
- Wizard step 2 (Script) gains an "Open A/B test" button.

## P1 — Niche Templates (DONE)
Backend (`core/niche_templates.py`) — 8 templates × 4 niches:
- finance: `finance_money_tips`, `finance_market_news`
- horror: `horror_dark_story`, `horror_unsolved`
- motivation: `motivation_success`, `motivation_morning`
- facts: `facts_did_you_know`, `facts_history`

Each template carries `duration_seconds`, `tone`, `style`, `voice` preset, `thumbnail_style`, default tags and a `topic_template`. Endpoints:
- `GET /api/templates` (optional `?niche=`)
- `GET /api/templates/{id}` (404 on miss)
- `POST /api/projects/from-template` → creates a project pre-tuned with `template_id` recorded.

Frontend `/templates` — filterable niche pill row (all/finance/horror/motivation/facts), template cards with icon, duration / tone / voice meta and a "Use template" CTA that creates the project and jumps into the wizard.

## What's working end-to-end (verified by testing agent · 54/54 tests green)
- Auth, projects CRUD, series.
- Script → Voice (FS) → Thumbnail (FS) → Scenes (FS, async) → Render (ffmpeg MP4) → Publish.
- A/B variants, **weighted scoring** (hook 50% / title 20% / overall 30%), winner selection.
- Niche templates browse + create-from-template.
- Trends — AI / Reddit / YouTube **+ Google Trends (pytrends)** rising queries.
- Auth-protected media serving (`?token=` for `<img>` & `<audio>`).
- Stripe checkout flow against Emergent's Stripe proxy.
- Startup base64-→-FS migration is idempotent.

## Known limitations (pre-existing)
- ElevenLabs free tier 401s from cloud IPs → use OpenAI HD tier instead.
- Stripe `Session.retrieve` not supported by the Emergent proxy → state polled via DB after webhook.
- Reddit credentials env vars are blank by default; populate to activate real Reddit pulls.

## Test credentials
`tester@videoforge.ai` / `TestPass123!` (auto-registered).

## Backlog
**P0**: object storage (S3 / GCS) for true horizontal scale; rate-limit AI endpoints.
**P1**: Google Trends via pytrends; multi-language UI translations.
**P2**: channel multi-management (Studio tier), voice cloning, BGM with ducking, brand kit, team seats, "video published" webhook.
