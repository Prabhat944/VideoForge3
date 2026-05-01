"""
VideoForge AI backend regression tests.
Covers: auth, trends, projects CRUD, script, voice, thumbnail, publish,
analytics, series, tools/compare, auth-guards.
"""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/') or pytest.skip(
    "REACT_APP_BACKEND_URL not set", allow_module_level=True
)


# ---------------- Health ----------------
class TestHealth:
    def test_root(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"
        assert data.get("service") == "VideoForge AI"


# ---------------- Auth ----------------
class TestAuth:
    def test_register_new_user(self, api_client, fresh_email):
        r = api_client.post(f"{BASE_URL}/api/auth/register", json={
            "email": fresh_email,
            "password": "TempPass123!",
            "full_name": "Fresh User",
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert "token" in data and isinstance(data["token"], str) and len(data["token"]) > 10
        assert data["user"]["email"] == fresh_email.lower()
        assert data["user"]["full_name"] == "Fresh User"
        assert data["user"]["plan"] == "free"
        assert data["user"]["credits"] == 100
        assert "id" in data["user"]

    def test_register_duplicate_returns_400(self, api_client):
        email = f"TEST_dup_{uuid.uuid4().hex[:6]}@videoforge.ai"
        r1 = api_client.post(f"{BASE_URL}/api/auth/register", json={
            "email": email, "password": "TempPass123!", "full_name": "Dup"
        })
        assert r1.status_code == 200
        r2 = api_client.post(f"{BASE_URL}/api/auth/register", json={
            "email": email, "password": "TempPass123!", "full_name": "Dup"
        })
        assert r2.status_code == 400
        assert "already" in r2.json().get("detail", "").lower()

    def test_login_success(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "tester@videoforge.ai",
            "password": "TestPass123!",
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert "token" in data
        assert data["user"]["email"] == "tester@videoforge.ai"

    def test_login_invalid_returns_401(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "tester@videoforge.ai",
            "password": "wrong-password",
        })
        assert r.status_code == 401

    def test_me_with_token(self, authed):
        r = authed.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["email"] == "tester@videoforge.ai"
        assert "id" in data
        assert "full_name" in data

    def test_me_without_token_401(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 401

    def test_me_with_invalid_token_401(self, api_client):
        s = requests.Session()
        s.headers.update({"Authorization": "Bearer not-a-valid-token"})
        r = s.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 401


# ---------------- Tools Compare (public) ----------------
class TestToolsCompare:
    def test_compare_tools(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/tools/compare")
        assert r.status_code == 200
        data = r.json()
        for key in ("script", "voice", "video", "thumbnail"):
            assert key in data and isinstance(data[key], list) and len(data[key]) > 0
            for item in data[key]:
                assert {"name", "tier", "cost_per_video", "quality", "selected"}.issubset(item.keys())


# ---------------- Voices (public) ----------------
class TestVoices:
    def test_list_voices(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/voices")
        assert r.status_code == 200
        voices = r.json().get("voices", [])
        # Phase 3: 6 OpenAI free (tts-1) + 6 OpenAI HD (tts-1-hd) + 7 ElevenLabs = 19
        assert len(voices) == 19
        ids = {v["id"] for v in voices}
        assert {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}.issubset(ids)
        # HD prefix set
        assert {"hd_alloy", "hd_echo", "hd_fable", "hd_onyx", "hd_nova", "hd_shimmer"}.issubset(ids)
        # ElevenLabs Rachel
        assert "21m00Tcm4TlvDq8ikWAM" in ids
        providers = {v.get("provider") for v in voices}
        assert {"openai", "openai_hd", "elevenlabs"}.issubset(providers)
        eleven_count = sum(1 for v in voices if v.get("provider") == "elevenlabs")
        hd_count = sum(1 for v in voices if v.get("provider") == "openai_hd")
        free_count = sum(1 for v in voices if v.get("provider") == "openai")
        assert eleven_count == 7
        assert hd_count == 6
        assert free_count == 6


# ---------------- Trends ----------------
class TestTrends:
    def test_trends_ai_horror(self, api_client):
        # First call may hit LLM; use long timeout
        r = api_client.get(f"{BASE_URL}/api/trends", params={"niche": "horror", "source": "ai"}, timeout=90)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "trends" in data and isinstance(data["trends"], list) and len(data["trends"]) >= 1
        t0 = data["trends"][0]
        for key in ("title", "description", "viral_score", "competition", "suggested_tags", "platform", "category"):
            assert key in t0, f"missing {key} in trend"

    def test_trends_cached_on_second_call(self, api_client):
        # Warm cache
        api_client.get(f"{BASE_URL}/api/trends", params={"niche": "facts", "source": "ai"}, timeout=90)
        r = api_client.get(f"{BASE_URL}/api/trends", params={"niche": "facts", "source": "ai"}, timeout=15)
        assert r.status_code == 200
        # Cached flag should typically be True for second hit within 6h
        assert r.json().get("cached") is True


# ---------------- Projects CRUD ----------------
class TestProjectsCRUD:
    def test_create_project_requires_auth(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/projects", json={"topic": "x"})
        assert r.status_code == 401

    def test_create_list_get_delete_flow(self, authed):
        # Create
        payload = {
            "topic": "TEST_Haunted Abandoned Hospitals",
            "audience": "18-35 horror fans",
            "duration_seconds": 45,
            "tone": "eerie",
            "language": "English",
            "style": "storytelling",
            "niche": "horror",
        }
        r = authed.post(f"{BASE_URL}/api/projects", json=payload)
        assert r.status_code == 200, r.text
        proj = r.json()
        assert proj["topic"] == payload["topic"]
        assert proj["status"] == "draft"
        assert proj["niche"] == "horror"
        pid = proj["id"]
        assert isinstance(pid, str)

        # List
        r = authed.get(f"{BASE_URL}/api/projects")
        assert r.status_code == 200
        items = r.json()
        assert any(p["id"] == pid for p in items)

        # Get
        r = authed.get(f"{BASE_URL}/api/projects/{pid}")
        assert r.status_code == 200
        assert r.json()["id"] == pid

        # Delete
        r = authed.delete(f"{BASE_URL}/api/projects/{pid}")
        assert r.status_code == 200
        assert r.json().get("ok") is True

        # GET after delete -> 404
        r = authed.get(f"{BASE_URL}/api/projects/{pid}")
        assert r.status_code == 404

    def test_get_unknown_project_404(self, authed):
        r = authed.get(f"{BASE_URL}/api/projects/does-not-exist-{uuid.uuid4().hex[:6]}")
        assert r.status_code == 404


# ---------------- Full Pipeline: script -> voice -> thumbnail -> publish -> analytics ----------------
@pytest.fixture(scope="module")
def pipeline_project(authed):
    """Create a project dedicated to pipeline tests."""
    r = authed.post(f"{BASE_URL}/api/projects", json={
        "topic": "TEST_5 Weird Facts About Deep Space",
        "audience": "curious adults",
        "duration_seconds": 30,  # short to keep voice/tts small
        "tone": "engaging",
        "language": "English",
        "style": "facts",
        "niche": "facts",
    })
    assert r.status_code == 200, r.text
    proj = r.json()
    yield proj
    # cleanup
    try:
        authed.delete(f"{BASE_URL}/api/projects/{proj['id']}")
    except Exception:
        pass


class TestPipeline:
    def test_01_script_generate(self, authed, pipeline_project):
        pid = pipeline_project["id"]
        r = authed.post(f"{BASE_URL}/api/projects/script",
                        json={"project_id": pid}, timeout=120)
        assert r.status_code == 200, r.text
        script = r.json().get("script")
        assert isinstance(script, dict)
        assert isinstance(script.get("title"), str) and len(script["title"]) > 0
        assert isinstance(script.get("scenes"), list) and len(script["scenes"]) >= 1
        assert isinstance(script.get("tags"), list) and len(script["tags"]) >= 1
        # Persistence verification
        g = authed.get(f"{BASE_URL}/api/projects/{pid}")
        assert g.status_code == 200
        pdata = g.json()
        assert pdata["status"] == "script_ready"
        assert pdata["title"] == script["title"]
        assert pdata["script"]["title"] == script["title"]

    def test_02_voice_generate(self, authed, pipeline_project):
        pid = pipeline_project["id"]
        r = authed.post(f"{BASE_URL}/api/projects/voice",
                        json={"project_id": pid, "voice": "alloy", "speed": 1.0},
                        timeout=120)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["voice_id"] == "alloy"
        assert data["format"] == "mp3"
        assert isinstance(data["audio_b64"], str) and len(data["audio_b64"]) > 1000
        # Persistence
        g = authed.get(f"{BASE_URL}/api/projects/{pid}")
        assert g.json()["status"] == "voice_ready"

    def test_03_voice_requires_script(self, authed):
        # Fresh project without script
        r = authed.post(f"{BASE_URL}/api/projects", json={
            "topic": "TEST_no_script_yet", "duration_seconds": 20, "niche": "general"
        })
        pid = r.json()["id"]
        try:
            r = authed.post(f"{BASE_URL}/api/projects/voice",
                            json={"project_id": pid, "voice": "alloy"})
            assert r.status_code == 400
            assert "script" in r.json().get("detail", "").lower()
        finally:
            authed.delete(f"{BASE_URL}/api/projects/{pid}")

    def test_04_thumbnail_generate(self, authed, pipeline_project):
        pid = pipeline_project["id"]
        # GPT Image 1 can take 30-90s
        r = authed.post(f"{BASE_URL}/api/projects/thumbnail",
                        json={"project_id": pid}, timeout=180)
        assert r.status_code == 200, r.text
        data = r.json()
        url = data.get("thumbnail_url", "")
        assert url.startswith("data:image/png;base64,")
        assert len(url) > 2000  # real image produces sizable b64
        # Persistence
        g = authed.get(f"{BASE_URL}/api/projects/{pid}")
        assert g.json()["thumbnail_url"].startswith("data:image/png;base64,")

    def test_05_publish_immediate(self, authed, pipeline_project):
        pid = pipeline_project["id"]
        r = authed.post(f"{BASE_URL}/api/projects/publish", json={
            "project_id": pid,
            "title": "TEST Publish Title",
            "description": "TEST publish description",
            "tags": ["test", "videoforge"],
            "privacy": "public",
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "published"
        assert isinstance(data["video_id"], str) and len(data["video_id"]) == 11
        assert data["url"].startswith("https://youtube.com/watch?v=")
        # Persistence
        g = authed.get(f"{BASE_URL}/api/projects/{pid}")
        pdata = g.json()
        assert pdata["status"] == "published"
        assert pdata["youtube_video_id"] == data["video_id"]

    def test_06_publish_scheduled(self, authed):
        # separate project for scheduled variant
        r = authed.post(f"{BASE_URL}/api/projects", json={
            "topic": "TEST_scheduled_pub", "duration_seconds": 20, "niche": "general"
        })
        pid = r.json()["id"]
        try:
            r = authed.post(f"{BASE_URL}/api/projects/publish", json={
                "project_id": pid,
                "title": "TEST Sched",
                "description": "TEST sched desc",
                "tags": [],
                "schedule_at": "2030-01-01T00:00:00+00:00",
            })
            assert r.status_code == 200
            assert r.json()["status"] == "scheduled"
        finally:
            authed.delete(f"{BASE_URL}/api/projects/{pid}")

    def test_07_analytics_summary(self, authed):
        r = authed.get(f"{BASE_URL}/api/analytics/summary")
        assert r.status_code == 200, r.text
        data = r.json()
        assert "totals" in data and "rows" in data and "series" in data and "suggestions" in data
        assert isinstance(data["series"], list) and len(data["series"]) == 14
        for s in data["series"]:
            assert {"date", "views", "watch_time"}.issubset(s.keys())
        assert data["totals"]["videos"] >= 1
        assert data["totals"]["views"] > 0


# ---------------- Series (bulk) ----------------
class TestSeries:
    def test_series_bulk_create(self, authed):
        r = authed.post(f"{BASE_URL}/api/projects/series", json={
            "niche": "facts",
            "base_topic": "TEST_Space Mysteries",
            "count": 3,
            "duration_seconds": 30,
        }, timeout=90)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["created"] == 3
        assert len(data["projects"]) == 3
        ids = [p["id"] for p in data["projects"]]
        # cleanup
        for pid in ids:
            authed.delete(f"{BASE_URL}/api/projects/{pid}")

    def test_series_invalid_count(self, authed):
        r = authed.post(f"{BASE_URL}/api/projects/series", json={
            "niche": "facts", "base_topic": "x", "count": 0
        })
        assert r.status_code == 400

    def test_series_requires_auth(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/projects/series", json={
            "niche": "facts", "base_topic": "x", "count": 3
        })
        assert r.status_code == 401
