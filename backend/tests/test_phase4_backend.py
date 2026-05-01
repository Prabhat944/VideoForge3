"""Phase 4 backend tests: filesystem scene storage, idempotency, real trends,
AI Agent Mode (autonomous pipeline), Content Calendar, media serving auth."""
import os
import time
import uuid
import pytest
import requests
from pathlib import Path

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", "/app/backend/media"))


# ------- helpers -------
def _create_project_with_script(authed):
    r = authed.post(f"{BASE_URL}/api/projects", json={
        "topic": f"TEST_phase4_{uuid.uuid4().hex[:6]}",
        "audience": "general", "duration_seconds": 30, "tone": "engaging",
        "language": "English", "style": "storytelling", "niche": "facts",
    })
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    r2 = authed.post(f"{BASE_URL}/api/projects/script", json={"project_id": pid}, timeout=120)
    assert r2.status_code == 200, r2.text
    return pid


# ---------------- Filesystem Scene Storage + Idempotency ----------------
class TestScenesFilesystem:
    @pytest.fixture(scope="class")
    def project_id(self, authed):
        return _create_project_with_script(authed)

    def test_scenes_post_starts_generation(self, authed, project_id):
        r = authed.post(f"{BASE_URL}/api/projects/scenes", json={"project_id": project_id}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("status") == "generating"
        assert isinstance(data.get("scenes"), list)
        assert len(data["scenes"]) >= 1
        for s in data["scenes"]:
            assert "index" in s and "duration" in s and "has_image" in s

    def test_scenes_idempotency_409_on_duplicate(self, authed, project_id):
        # Fire immediately after first call while still generating
        r = authed.post(f"{BASE_URL}/api/projects/scenes", json={"project_id": project_id}, timeout=30)
        assert r.status_code == 409, f"Expected 409 idempotency, got {r.status_code}: {r.text}"
        assert "progress" in r.text.lower() or "already" in r.text.lower()

    def test_scenes_complete_with_fs_storage(self, authed, project_id):
        # Poll scenes-status up to ~5 minutes
        deadline = time.time() + 300
        final = None
        while time.time() < deadline:
            r = authed.get(f"{BASE_URL}/api/projects/{project_id}/scenes-status", timeout=30)
            assert r.status_code == 200, r.text
            final = r.json()
            if final.get("status") == "complete":
                break
            time.sleep(10)
        assert final and final.get("status") == "complete", f"scenes did not complete: {final}"
        scenes = final.get("scenes", [])
        assert len(scenes) >= 1
        # At least one scene should be ready with an image_url
        ready = [s for s in scenes if s.get("image_status") == "ready"]
        if not ready:
            pytest.skip(f"All scenes failed (likely image API issue); status detail: {scenes}")
        s0 = ready[0]
        assert s0.get("image_url"), "image_url missing on ready scene"
        assert s0["image_url"].startswith("http")
        assert "/api/media/scenes/" in s0["image_url"]

    def test_scene_files_exist_on_disk(self, authed, project_id):
        pdir = MEDIA_ROOT / "scenes" / project_id
        assert pdir.exists(), f"Project scenes dir missing: {pdir}"
        files = list(pdir.glob("scene_*.png"))
        assert len(files) >= 1, f"No scene PNGs on disk in {pdir}"
        for f in files:
            assert f.stat().st_size > 0

    def test_project_doc_has_no_base64_image_data_url(self, authed, project_id):
        r = authed.get(f"{BASE_URL}/api/projects/{project_id}", timeout=30)
        assert r.status_code == 200
        proj = r.json()
        scene_images = proj.get("scene_images") or []
        assert scene_images, "scene_images missing on project"
        for s in scene_images:
            assert "image_data_url" not in s or not s.get("image_data_url"), \
                "scene_images must NOT contain image_data_url base64 in Mongo"
            assert s.get("image_path") is not None or s.get("status") == "failed"


# ---------------- Media Serving Auth ----------------
class TestMediaAuth:
    @pytest.fixture(scope="class")
    def ready_scene(self, authed):
        """Reuse most recent project with ready scene files."""
        r = authed.get(f"{BASE_URL}/api/projects", timeout=30)
        assert r.status_code == 200
        for p in r.json():
            pdir = MEDIA_ROOT / "scenes" / p["id"]
            if pdir.exists():
                pngs = sorted(pdir.glob("scene_*.png"))
                if pngs:
                    return {"project_id": p["id"], "filename": pngs[0].name}
        pytest.skip("No ready scene file available for media test")

    def test_media_no_auth_returns_401(self, ready_scene):
        url = f"{BASE_URL}/api/media/scenes/{ready_scene['project_id']}/{ready_scene['filename']}"
        r = requests.get(url, timeout=30)
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"

    def test_media_bearer_header_returns_png(self, authed, ready_scene):
        url = f"{BASE_URL}/api/media/scenes/{ready_scene['project_id']}/{ready_scene['filename']}"
        r = authed.get(url, timeout=30)
        assert r.status_code == 200, r.text
        assert r.headers.get("content-type", "").startswith("image/png")
        assert len(r.content) > 100

    def test_media_query_param_token_works(self, auth_token, ready_scene):
        url = f"{BASE_URL}/api/media/scenes/{ready_scene['project_id']}/{ready_scene['filename']}?token={auth_token}"
        r = requests.get(url, timeout=30)
        assert r.status_code == 200, f"token query failed: {r.status_code} {r.text[:200]}"
        assert r.headers.get("content-type", "").startswith("image/png")

    def test_media_nonexistent_file_returns_404(self, authed, ready_scene):
        url = f"{BASE_URL}/api/media/scenes/{ready_scene['project_id']}/nonexistent.png"
        r = authed.get(url, timeout=30)
        assert r.status_code == 404

    def test_media_foreign_project_returns_404(self, authed):
        # A random UUID user does not own
        fake_pid = str(uuid.uuid4())
        url = f"{BASE_URL}/api/media/scenes/{fake_pid}/scene_1.png"
        r = authed.get(url, timeout=30)
        assert r.status_code == 404


# ---------------- Trends: Reddit + YouTube with graceful fallback ----------------
class TestTrendsReal:
    def test_reddit_horror_returns_8_with_platform_field(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/trends?source=reddit&niche=horror", timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        trends = data.get("trends", [])
        # Reddit may IP-block → may fall back to static seed. Structure must be consistent.
        assert len(trends) >= 1 and len(trends) <= 8
        for t in trends:
            assert "title" in t and "viral_score" in t and "competition" in t
            assert "platform" in t

    def test_youtube_without_oauth_falls_back(self, authed):
        r = authed.get(f"{BASE_URL}/api/trends?source=youtube&niche=facts", timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "trends" in data
        # Without OAuth, falls back to seed/AI; structure check
        assert len(data["trends"]) >= 1

    def test_trends_unauth_still_works_ai_source(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/trends?source=ai&niche=facts", timeout=90)
        assert r.status_code == 200
        assert len(r.json().get("trends", [])) >= 1


# ---------------- AI Agent Mode ----------------
class TestAgentMode:
    def test_agent_run_returns_immediately(self, authed):
        t0 = time.time()
        r = authed.post(f"{BASE_URL}/api/agent/run", json={
            "topic": f"TEST_agent_{uuid.uuid4().hex[:6]} Amazing Space Facts",
            "niche": "facts", "voice": "alloy", "auto_publish": False,
            "duration_seconds": 30,
        }, timeout=30)
        elapsed = time.time() - t0
        assert r.status_code == 200, r.text
        data = r.json()
        assert "project_id" in data
        assert data.get("status") == "running"
        assert data.get("stage") == "queued"
        assert elapsed < 10, f"agent/run should return fast; took {elapsed:.1f}s"
        # Stash for status test
        TestAgentMode._pid = data["project_id"]

    def test_agent_status_returns_contract(self, authed):
        pid = getattr(TestAgentMode, "_pid", None)
        if not pid:
            pytest.skip("agent run not executed")
        # Poll a couple of times to see progression; don't wait for full completion
        stages_seen = set()
        for _ in range(6):
            r = authed.get(f"{BASE_URL}/api/agent/status/{pid}", timeout=30)
            assert r.status_code == 200, r.text
            data = r.json()
            for k in ("stage", "status", "error", "title", "video_url", "youtube_url",
                      "has_thumbnail", "project_status"):
                assert k in data, f"missing key {k} in agent status response"
            stages_seen.add(data.get("stage"))
            if data.get("status") in ("complete", "error"):
                break
            time.sleep(10)
        assert stages_seen, "no stages observed"
        # At least one of the expected agent stages should appear
        assert stages_seen & {"queued", "script", "voice", "thumbnail", "scenes", "render", "complete", "error"}

    def test_agent_status_unknown_project_404(self, authed):
        r = authed.get(f"{BASE_URL}/api/agent/status/{uuid.uuid4()}", timeout=30)
        assert r.status_code == 404


# ---------------- Content Calendar ----------------
class TestCalendar:
    def test_calendar_returns_contract(self, authed):
        r = authed.get(f"{BASE_URL}/api/calendar", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "items" in data and "today" in data
        assert isinstance(data["items"], list)

    def test_calendar_items_have_expected_fields(self, authed):
        r = authed.get(f"{BASE_URL}/api/calendar", timeout=30)
        assert r.status_code == 200
        items = r.json().get("items", [])
        if not items:
            pytest.skip("No calendar items for this user yet")
        for it in items:
            for k in ("project_id", "title", "thumbnail_url", "status", "scheduled_at",
                      "published_at", "youtube_url", "real", "when"):
                assert k in it, f"missing key {k} in calendar item"
            assert it["status"] in ("published", "scheduled", "rendered")
        # Sorted by `when`
        whens = [i.get("when") or "" for i in items]
        assert whens == sorted(whens)

    def test_calendar_requires_auth(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/calendar", timeout=30)
        assert r.status_code in (401, 403)


# ---------------- Regression: prior phase endpoints still work ----------------
class TestPhase123Regression:
    def test_auth_me(self, authed):
        r = authed.get(f"{BASE_URL}/api/auth/me", timeout=30)
        assert r.status_code == 200
        assert r.json().get("email")

    def test_projects_list(self, authed):
        r = authed.get(f"{BASE_URL}/api/projects", timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_voices_contract(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/voices", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "voices" in data
        assert len(data["voices"]) >= 19

    def test_billing_plans(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/billing/plans", timeout=30)
        assert r.status_code == 200

    def test_youtube_auth_url(self, authed):
        r = authed.get(f"{BASE_URL}/api/youtube/auth-url", timeout=30)
        assert r.status_code == 200
        # response uses key "url" (per server.py L616)
        data = r.json()
        url = data.get("url") or data.get("auth_url") or ""
        assert "accounts.google.com" in url

    def test_analytics_summary(self, authed):
        r = authed.get(f"{BASE_URL}/api/analytics/summary", timeout=30)
        assert r.status_code == 200
        data = r.json()
        for k in ("youtube_connected", "data_source"):
            assert k in data
