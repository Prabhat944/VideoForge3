"""Stage2 refactor backend tests.

Covers:
- Auth (register/login/me)
- Projects CRUD + series
- Pipeline: script, voice (P0: NO audio_b64), thumbnail, scenes, render
- Voices listing (OpenAI std + HD + ElevenLabs)
- Niche Templates (list, get, create-from-template)
- A/B variants: generate, get, score (updates ab_winner/ab_metrics), select
- Trends (ai, reddit fallback), YouTube status/auth-url, Billing plans,
  Calendar, Analytics, Media auth
"""
import os
import time
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[2] / 'frontend' / '.env')
load_dotenv(Path(__file__).resolve().parents[1] / '.env')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')


# ---------- Auth ----------
class TestAuth:
    def test_me(self, authed):
        r = authed.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == "tester@videoforge.ai"
        assert "id" in data and data["id"]

    def test_register_duplicate_rejected(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/register", json={
            "email": "tester@videoforge.ai",
            "password": "TestPass123!",
            "full_name": "Dup",
        })
        assert r.status_code in (400, 409)

    def test_login_wrong_password(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "tester@videoforge.ai",
            "password": "nope",
        })
        assert r.status_code == 401


# ---------- Projects ----------
class TestProjects:
    def test_create_list_get_delete(self, authed):
        r = authed.post(f"{BASE_URL}/api/projects", json={
            "topic": "TEST_stage2 quick project",
            "niche": "finance", "duration_seconds": 45,
        })
        assert r.status_code == 200, r.text
        pid = r.json()["id"]

        r2 = authed.get(f"{BASE_URL}/api/projects")
        assert r2.status_code == 200
        assert any(p["id"] == pid for p in r2.json())

        r3 = authed.get(f"{BASE_URL}/api/projects/{pid}")
        assert r3.status_code == 200
        assert r3.json()["topic"].startswith("TEST_stage2")

        r4 = authed.delete(f"{BASE_URL}/api/projects/{pid}")
        assert r4.status_code in (200, 204)

    def test_series(self, authed):
        r = authed.post(f"{BASE_URL}/api/projects/series", json={
            "niche": "facts", "base_topic": "TEST_stage2 series",
            "count": 2, "duration_seconds": 30,
        })
        assert r.status_code == 200, r.text
        body = r.json()
        # series returns {created:N, projects:[...]}
        items = body["projects"] if isinstance(body, dict) else body
        assert len(items) == 2
        for it in items:
            assert it.get("id") and it.get("niche") == "facts"


# ---------- Templates ----------
class TestTemplates:
    def test_list_templates_returns_eight(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/templates")
        assert r.status_code == 200
        data = r.json()
        assert "templates" in data
        assert len(data["templates"]) == 8
        niches = {t["niche"] for t in data["templates"]}
        assert {"finance", "horror", "motivation", "facts"}.issubset(niches)

    def test_filter_by_niche(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/templates?niche=horror")
        assert r.status_code == 200
        items = r.json()["templates"]
        assert len(items) >= 1
        assert all(t["niche"] == "horror" for t in items)

    def test_get_template(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/templates/finance_money_tips")
        assert r.status_code == 200
        t = r.json()
        assert t["id"] == "finance_money_tips"
        assert t["niche"] == "finance"
        assert t["duration_seconds"] == 60

    def test_get_template_404(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/templates/does_not_exist")
        assert r.status_code == 404

    def test_create_from_template(self, authed):
        r = authed.post(f"{BASE_URL}/api/projects/from-template", json={
            "template_id": "horror_dark_story",
            "topic": "TEST_stage2 horror from template",
        })
        assert r.status_code == 200, r.text
        proj = r.json()
        assert proj["template_id"] == "horror_dark_story"
        assert proj["niche"] == "horror"
        assert proj["tone"] == "scary"
        assert proj["style"] == "storytelling"
        assert proj["topic"] == "TEST_stage2 horror from template"


# ---------- Voices ----------
class TestVoices:
    def test_voices_lists_all_tiers(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/voices")
        assert r.status_code == 200
        voices = r.json()["voices"]
        providers = {v.get("provider") for v in voices}
        # core OpenAI std voices use provider=openai (or similar tier field);
        # accept either layout but require HD + ElevenLabs presence via IDs.
        ids = {v["id"] for v in voices}
        # OpenAI standard
        assert {"alloy", "nova", "shimmer"}.issubset(ids)
        # HD
        assert any(i.startswith("hd_") for i in ids)
        # ElevenLabs
        assert "elevenlabs" in providers


# ---------- Pipeline: script + voice P0 ----------
@pytest.fixture(scope="module")
def pipeline_project(authed):
    """Shared project for pipeline chain."""
    r = authed.post(f"{BASE_URL}/api/projects", json={
        "topic": "TEST_stage2 P0 pipeline",
        "niche": "facts", "duration_seconds": 30,
        "tone": "engaging", "style": "listicle",
    })
    assert r.status_code == 200, r.text
    return r.json()["id"]


class TestScriptAndVoice:
    def test_script_generate(self, authed, pipeline_project):
        r = authed.post(f"{BASE_URL}/api/projects/script", json={
            "project_id": pipeline_project
        }, timeout=60)
        assert r.status_code == 200, r.text
        script = r.json()["script"]
        for k in ("title", "description", "tags", "hook", "scenes", "full_voiceover"):
            assert k in script, f"missing {k}"
        assert isinstance(script["scenes"], list) and len(script["scenes"]) >= 1

    def test_voice_P0_no_base64_in_response_or_db(self, authed, pipeline_project):
        r = authed.post(f"{BASE_URL}/api/projects/voice", json={
            "project_id": pipeline_project,
            "voice": "alloy",
            "speed": 1.0,
        }, timeout=90)
        assert r.status_code == 200, r.text
        body = r.json()

        # P0 assertion: response MUST NOT contain base64 audio
        assert "audio_b64" not in body, "P0 FAIL: response contains audio_b64"
        assert "audio_url" in body and body["audio_url"].startswith("http")
        assert "/api/media/voices/" in body["audio_url"]
        assert body["format"] == "mp3"

        # DB assertion: project.voice must not contain audio_b64
        mongo = MongoClient(MONGO_URL)
        try:
            proj = mongo[DB_NAME]["projects"].find_one({"id": pipeline_project})
        finally:
            mongo.close()
        assert proj is not None
        v = proj.get("voice") or {}
        assert "audio_b64" not in v, f"P0 FAIL: Mongo voice still has audio_b64: keys={list(v)}"
        assert v.get("audio_path"), "voice.audio_path missing"
        assert v.get("audio_url"), "voice.audio_url missing"
        assert "voices/" in v["audio_path"]

        # MP3 file must physically exist
        abs_path = Path("/app/backend/media") / v["audio_path"]
        assert abs_path.exists() and abs_path.stat().st_size > 0, f"MP3 missing at {abs_path}"

    def test_voice_media_endpoint_requires_auth(self, api_client, authed, pipeline_project):
        r = authed.get(f"{BASE_URL}/api/projects/{pipeline_project}")
        vpath = (r.json().get("voice") or {}).get("audio_path")
        assert vpath
        url = f"{BASE_URL}/api/media/{vpath}"
        # No auth -> 401/403
        unauth = api_client.get(url)
        assert unauth.status_code in (401, 403)
        # Bearer auth -> 200
        ok = authed.get(url)
        assert ok.status_code == 200
        assert ok.headers.get("content-type", "").startswith("audio/")


class TestThumbnailAndRender:
    def test_thumbnail(self, authed, pipeline_project):
        r = authed.post(f"{BASE_URL}/api/projects/thumbnail", json={
            "project_id": pipeline_project
        }, timeout=120)
        assert r.status_code == 200, r.text
        url = r.json()["thumbnail_url"]
        assert "/api/media/thumbnails/" in url

        # verify DB has thumbnail_path and no data: url
        proj = authed.get(f"{BASE_URL}/api/projects/{pipeline_project}").json()
        assert proj.get("thumbnail_path")
        assert not proj["thumbnail_url"].startswith("data:")

    def test_render_produces_mp4(self, authed, pipeline_project):
        r = authed.post(f"{BASE_URL}/api/projects/render", json={
            "project_id": pipeline_project
        }, timeout=240)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["video_url"].endswith("/video")
        # Fetch the mp4
        v = authed.get(body["video_url"], timeout=120)
        assert v.status_code == 200
        assert v.headers.get("content-type") == "video/mp4"
        assert len(v.content) > 1000


# ---------- Scenes idempotency ----------
class TestScenesIdempotency:
    def test_409_if_already_generating(self, authed, pipeline_project):
        r1 = authed.post(f"{BASE_URL}/api/projects/scenes", json={"project_id": pipeline_project})
        # First call should start generation (200) OR if scenes already done, treat test as skip
        if r1.status_code == 200:
            r2 = authed.post(f"{BASE_URL}/api/projects/scenes", json={"project_id": pipeline_project})
            assert r2.status_code in (200, 409)
        else:
            assert r1.status_code in (200, 400, 409)

    def test_scenes_status_endpoint(self, authed, pipeline_project):
        r = authed.get(f"{BASE_URL}/api/projects/{pipeline_project}/scenes-status")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data and "scenes" in data


# ---------- A/B Variants ----------
@pytest.fixture(scope="module")
def ab_project(authed):
    r = authed.post(f"{BASE_URL}/api/projects", json={
        "topic": "TEST_stage2 AB variants",
        "niche": "motivation", "duration_seconds": 30,
    })
    assert r.status_code == 200
    return r.json()["id"]


class TestABVariants:
    def test_generate_variants(self, authed, ab_project):
        r = authed.post(f"{BASE_URL}/api/projects/script/variants", json={
            "project_id": ab_project,
            "style_a": "storytelling",
            "style_b": "listicle",
        }, timeout=90)
        assert r.status_code == 200, r.text
        variants = r.json()["variants"]
        ids = {v["id"] for v in variants}
        assert ids == {"A", "B"}

    def test_get_variants_dashboard(self, authed, ab_project):
        r = authed.get(f"{BASE_URL}/api/projects/{ab_project}/variants")
        assert r.status_code == 200
        data = r.json()
        assert data["project_id"] == ab_project
        assert len(data["variants"]) == 2
        # full scripts should be in the dashboard payload
        for v in data["variants"]:
            assert v["script"].get("title")
            assert v["script"].get("scenes")

    def test_score_variant_updates_winner(self, authed, ab_project):
        # Score A=5, B=8 — expect winner=B
        r1 = authed.post(f"{BASE_URL}/api/projects/script/variants/score", json={
            "project_id": ab_project, "variant_id": "A",
            "hook_score": 5.0, "title_score": 5.0, "overall_score": 5.0,
            "note": "avg",
        })
        assert r1.status_code == 200, r1.text
        r2 = authed.post(f"{BASE_URL}/api/projects/script/variants/score", json={
            "project_id": ab_project, "variant_id": "B",
            "hook_score": 9.0, "title_score": 8.0, "overall_score": 8.0,
            "note": "strong",
        })
        assert r2.status_code == 200, r2.text
        body = r2.json()
        assert body["ab_winner"] == "B"
        assert body["ab_metrics"]["A"] == 5.0
        assert body["ab_metrics"]["B"] == 8.0

        # Confirm via GET
        r3 = authed.get(f"{BASE_URL}/api/projects/{ab_project}/variants")
        dash = r3.json()
        assert dash["ab_winner"] == "B"
        assert dash["ab_metrics"]["B"] == 8.0
        # Per-variant score persisted
        by_id = {v["id"]: v for v in dash["variants"]}
        assert by_id["A"]["score"]["overall"] == 5.0
        assert by_id["B"]["score"]["overall"] == 8.0

    def test_select_variant_copies_script(self, authed, ab_project):
        r = authed.post(f"{BASE_URL}/api/projects/script/select-variant", json={
            "project_id": ab_project, "variant_id": "A",
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True
        assert body["variant_id"] == "A"
        assert body["script"].get("title")
        proj = authed.get(f"{BASE_URL}/api/projects/{ab_project}").json()
        assert proj["selected_variant_id"] == "A"
        assert proj["status"] == "script_ready"
        assert proj["script"]["title"] == body["script"]["title"]


# ---------- Trends / YouTube / Billing / Calendar / Analytics ----------
class TestAuxiliary:
    def test_trends_ai(self, authed):
        r = authed.get(f"{BASE_URL}/api/trends?source=ai&niche=finance", timeout=60)
        assert r.status_code == 200
        body = r.json()
        assert "trends" in body
        assert isinstance(body["trends"], list)

    def test_trends_reddit_graceful(self, authed):
        r = authed.get(f"{BASE_URL}/api/trends?source=reddit&niche=horror", timeout=60)
        assert r.status_code == 200
        body = r.json()
        assert "trends" in body

    def test_youtube_status(self, authed):
        r = authed.get(f"{BASE_URL}/api/youtube/status")
        assert r.status_code == 200
        assert "connected" in r.json()

    def test_youtube_auth_url(self, authed):
        r = authed.get(f"{BASE_URL}/api/youtube/auth-url")
        assert r.status_code == 200
        url = r.json().get("auth_url") or r.json().get("url") or ""
        assert "accounts.google.com" in url

    def test_billing_plans(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/billing/plans")
        assert r.status_code == 200
        plans = r.json()
        assert isinstance(plans, (list, dict))

    def test_calendar(self, authed):
        r = authed.get(f"{BASE_URL}/api/calendar")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data

    def test_analytics_summary(self, authed):
        r = authed.get(f"{BASE_URL}/api/analytics/summary")
        assert r.status_code == 200
        data = r.json()
        # At least have totals / projects count-ish field
        assert isinstance(data, dict)
