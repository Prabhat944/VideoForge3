"""
VideoForge AI Phase 3 backend tests:
- HD voice tier (OpenAI tts-1-hd), free voice (tts-1)
- Per-scene image generation endpoint (/api/projects/scenes)
- Multi-scene render with crossfade
- YouTube analytics summary contract (youtube_connected, data_source)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/') or pytest.skip(
    "REACT_APP_BACKEND_URL not set", allow_module_level=True
)


# ---------------- Voices contract ----------------
class TestVoicesPhase3:
    def test_voices_contains_19_total(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/voices")
        assert r.status_code == 200, r.text
        voices = r.json().get("voices", [])
        assert len(voices) == 19, f"Expected 19 voices, got {len(voices)}"
        free = [v for v in voices if v.get("tier") == "free"]
        prem = [v for v in voices if v.get("tier") == "premium"]
        prem_plus = [v for v in voices if v.get("tier") == "premium_plus"]
        assert len(free) == 6
        assert len(prem) == 6
        assert len(prem_plus) == 7

    def test_hd_voice_ids_prefix(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/voices")
        assert r.status_code == 200
        voices = r.json().get("voices", [])
        hd = [v for v in voices if v.get("provider") == "openai_hd"]
        assert len(hd) == 6
        for v in hd:
            assert v["id"].startswith("hd_"), f"HD voice id missing prefix: {v['id']}"


# ---------------- HD + free voice generation ----------------
class TestHDVoiceGeneration:
    @pytest.fixture(scope="class")
    def project_id_with_script(self, authed):
        r = authed.post(f"{BASE_URL}/api/projects", json={
            "topic": "TEST_phase3_hd_voice",
            "audience": "general",
            "duration_seconds": 15,
            "niche": "general",
        })
        assert r.status_code == 200, r.text
        pid = r.json()["id"]
        rs = authed.post(f"{BASE_URL}/api/projects/script", json={"project_id": pid}, timeout=120)
        assert rs.status_code == 200, rs.text
        yield pid
        try:
            authed.delete(f"{BASE_URL}/api/projects/{pid}")
        except Exception:
            pass

    def test_free_tier_alloy_returns_openai(self, authed, project_id_with_script):
        pid = project_id_with_script
        r = authed.post(f"{BASE_URL}/api/projects/voice",
                        json={"project_id": pid, "voice": "alloy", "speed": 1.0},
                        timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["provider"] == "openai"
        assert d["voice_id"] == "alloy"
        assert d["format"] == "mp3"
        assert isinstance(d["audio_b64"], str) and len(d["audio_b64"]) > 1000

    def test_premium_tier_hd_alloy_returns_openai_hd(self, authed, project_id_with_script):
        pid = project_id_with_script
        r = authed.post(f"{BASE_URL}/api/projects/voice",
                        json={"project_id": pid, "voice": "hd_alloy", "speed": 1.0},
                        timeout=180)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["provider"] == "openai_hd", f"Expected openai_hd provider, got {d['provider']}"
        assert d["voice_id"] == "hd_alloy"
        assert d["format"] == "mp3"
        assert isinstance(d["audio_b64"], str) and len(d["audio_b64"]) > 1000

    def test_premium_tier_hd_nova_returns_openai_hd(self, authed, project_id_with_script):
        pid = project_id_with_script
        r = authed.post(f"{BASE_URL}/api/projects/voice",
                        json={"project_id": pid, "voice": "hd_nova", "speed": 1.0},
                        timeout=180)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["provider"] == "openai_hd"
        assert d["voice_id"] == "hd_nova"
        assert isinstance(d["audio_b64"], str) and len(d["audio_b64"]) > 1000


# ---------------- Per-scene image generation endpoint (background task) ----------------
class TestScenesEndpoint:
    """Phase 3 retest: POST /api/projects/scenes uses a BACKGROUND TASK pattern.
    The POST returns immediately (<5s) with status='generating'; client polls
    GET /api/projects/{id}/scenes-status until status=='complete'."""

    @pytest.fixture(scope="class")
    def project_with_script(self, authed):
        r = authed.post(f"{BASE_URL}/api/projects", json={
            "topic": "TEST_phase3_scenes_bgtask",
            "audience": "general",
            "duration_seconds": 20,
            "niche": "general",
        })
        pid = r.json()["id"]
        rs = authed.post(f"{BASE_URL}/api/projects/script", json={"project_id": pid}, timeout=120)
        assert rs.status_code == 200, rs.text
        yield pid
        try:
            authed.delete(f"{BASE_URL}/api/projects/{pid}")
        except Exception:
            pass

    def test_scenes_endpoint_returns_immediately(self, authed, project_with_script):
        """POST must return <5s with generating status (background task pattern)."""
        import time as _t
        pid = project_with_script
        t0 = _t.time()
        r = authed.post(f"{BASE_URL}/api/projects/scenes",
                        json={"project_id": pid}, timeout=10)
        elapsed = _t.time() - t0
        assert r.status_code == 200, r.text
        assert elapsed < 5.0, f"POST /projects/scenes took {elapsed:.1f}s, expected <5s (background task)"
        data = r.json()
        assert data.get("status") == "generating", f"Expected status='generating', got {data.get('status')}"
        assert "message" in data
        assert "scenes" in data and isinstance(data["scenes"], list)
        assert len(data["scenes"]) >= 1
        for s in data["scenes"]:
            assert "index" in s and "duration" in s and "has_image" in s
            assert s["has_image"] is False  # Initially no images

    def test_scenes_status_polling_completes(self, authed, project_with_script):
        """Poll GET /projects/{id}/scenes-status until status=='complete' (timeout 180s)."""
        import time as _t
        pid = project_with_script
        deadline = _t.time() + 180
        final = None
        while _t.time() < deadline:
            r = authed.get(f"{BASE_URL}/api/projects/{pid}/scenes-status", timeout=15)
            assert r.status_code == 200, r.text
            d = r.json()
            assert "status" in d and "scenes" in d
            for s in d["scenes"]:
                assert "index" in s and "duration" in s and "has_image" in s and "image_status" in s
                assert s["image_status"] in ("pending", "ready", "failed")
            if d["status"] == "complete":
                final = d
                break
            _t.sleep(5)
        assert final is not None, "scenes-status never reached 'complete' within 180s"
        # At least one scene should be ready
        ready = [s for s in final["scenes"] if s["image_status"] == "ready"]
        assert len(ready) >= 1, f"No scenes reached 'ready' status: {final}"

    def test_scenes_persisted_with_image_data_url(self, authed, project_with_script):
        """After complete, GET /api/projects/{id} must show scene_images with image_data_url."""
        pid = project_with_script
        g = authed.get(f"{BASE_URL}/api/projects/{pid}")
        assert g.status_code == 200, g.text
        proj = g.json()
        scene_images = proj.get("scene_images")
        assert isinstance(scene_images, list) and len(scene_images) >= 1
        ready = [s for s in scene_images if s.get("image_data_url")]
        assert len(ready) >= 1, f"No scene_images populated with image_data_url: {scene_images}"
        for s in ready:
            assert s["image_data_url"].startswith("data:image/"), s["image_data_url"][:40]

    def test_scenes_no_script_returns_400(self, authed):
        r = authed.post(f"{BASE_URL}/api/projects", json={
            "topic": "TEST_scenes_noscript", "duration_seconds": 10, "niche": "general",
        })
        pid = r.json()["id"]
        try:
            rr = authed.post(f"{BASE_URL}/api/projects/scenes",
                             json={"project_id": pid}, timeout=10)
            assert rr.status_code == 400, rr.text
            detail = (rr.json().get("detail") or "").lower()
            assert "script" in detail, f"Expected 'script' in error detail, got: {detail}"
        finally:
            authed.delete(f"{BASE_URL}/api/projects/{pid}")

    def test_scenes_nonexistent_project_returns_404(self, authed):
        rr = authed.post(f"{BASE_URL}/api/projects/scenes",
                         json={"project_id": "does-not-exist-xyz"}, timeout=10)
        assert rr.status_code == 404, rr.text

    def test_scenes_requires_auth(self, api_client):
        rr = api_client.post(f"{BASE_URL}/api/projects/scenes",
                             json={"project_id": "anything"}, timeout=10)
        assert rr.status_code in (401, 403), f"Expected 401/403, got {rr.status_code}"


# ---------------- Multi-scene render AFTER scenes complete ----------------
class TestMultiSceneRenderAfterScenes:
    """End-to-end: script -> scenes (bg) -> poll -> voice -> thumbnail -> render.
    Render MUST report scenes_used > 0 since scene_images are populated."""

    def test_render_uses_scenes(self, authed):
        import time as _t
        r = authed.post(f"{BASE_URL}/api/projects", json={
            "topic": "TEST_phase3_multiscene_render", "duration_seconds": 15, "niche": "general",
        })
        pid = r.json()["id"]
        try:
            assert authed.post(f"{BASE_URL}/api/projects/script",
                               json={"project_id": pid}, timeout=120).status_code == 200
            # Start scenes bg task
            sr = authed.post(f"{BASE_URL}/api/projects/scenes",
                             json={"project_id": pid}, timeout=10)
            assert sr.status_code == 200, sr.text
            # Poll until complete
            deadline = _t.time() + 180
            complete = False
            while _t.time() < deadline:
                ss = authed.get(f"{BASE_URL}/api/projects/{pid}/scenes-status", timeout=15)
                if ss.status_code == 200 and ss.json().get("status") == "complete":
                    complete = True
                    break
                _t.sleep(5)
            assert complete, "scenes-status did not complete within 180s"
            # Voice + thumb + render
            assert authed.post(f"{BASE_URL}/api/projects/voice",
                               json={"project_id": pid, "voice": "alloy"}, timeout=120).status_code == 200
            assert authed.post(f"{BASE_URL}/api/projects/thumbnail",
                               json={"project_id": pid}, timeout=180).status_code == 200
            rr = authed.post(f"{BASE_URL}/api/projects/render",
                             json={"project_id": pid}, timeout=240)
            assert rr.status_code == 200, rr.text
            data = rr.json()
            assert data.get("scenes_used", 0) > 0, f"Expected scenes_used>0 after scene gen, got {data}"
        finally:
            authed.delete(f"{BASE_URL}/api/projects/{pid}")


# ---------------- Multi-scene render ----------------
class TestMultiSceneRender:
    def test_render_returns_scenes_used(self, authed):
        """Verify render response includes scenes_used field (new in phase 3).
        Falls back to single-image path; scenes_used=0 is acceptable when no scenes generated."""
        # Build minimal pipeline
        r = authed.post(f"{BASE_URL}/api/projects", json={
            "topic": "TEST_phase3_render_contract", "duration_seconds": 10, "niche": "general"
        })
        pid = r.json()["id"]
        try:
            assert authed.post(f"{BASE_URL}/api/projects/script", json={"project_id": pid}, timeout=120).status_code == 200
            assert authed.post(f"{BASE_URL}/api/projects/voice", json={"project_id": pid, "voice": "alloy"}, timeout=120).status_code == 200
            assert authed.post(f"{BASE_URL}/api/projects/thumbnail", json={"project_id": pid}, timeout=180).status_code == 200
            rr = authed.post(f"{BASE_URL}/api/projects/render", json={"project_id": pid}, timeout=240)
            assert rr.status_code == 200, rr.text
            data = rr.json()
            assert "video_url" in data
            assert "video_path" in data
            assert "scenes_used" in data, "render response missing scenes_used (phase 3 contract)"
            assert isinstance(data["scenes_used"], int)
        finally:
            authed.delete(f"{BASE_URL}/api/projects/{pid}")


# ---------------- Analytics summary contract ----------------
class TestAnalyticsSummary:
    def test_analytics_requires_auth(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/analytics/summary")
        assert r.status_code == 401

    def test_analytics_contract_no_youtube(self, authed):
        # Ensure not connected
        authed.delete(f"{BASE_URL}/api/youtube/disconnect")
        r = authed.get(f"{BASE_URL}/api/analytics/summary", timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        # Contract fields
        for k in ("youtube_connected", "data_source", "totals", "rows", "series", "suggestions"):
            assert k in d, f"analytics/summary missing field: {k}"
        assert d["youtube_connected"] is False
        assert d["data_source"] == "synthetic"
        assert isinstance(d["totals"], dict)
        for tk in ("videos", "views", "likes", "watch_time_minutes", "avg_ctr"):
            assert tk in d["totals"]
        assert isinstance(d["rows"], list)
        assert isinstance(d["series"], list)
        assert len(d["series"]) == 14  # 14-day synthetic window
        for s in d["series"]:
            assert "date" in s and "views" in s and "watch_time" in s
        assert isinstance(d["suggestions"], list) and len(d["suggestions"]) >= 1

    def test_analytics_auth_url_has_analytics_scope(self, authed):
        """Phase 3 added yt-analytics.readonly scope to YouTube OAuth."""
        r = authed.get(f"{BASE_URL}/api/youtube/auth-url")
        assert r.status_code == 200, r.text
        url = r.json().get("url", "")
        assert "yt-analytics.readonly" in url or "yt-analytics" in url, (
            "yt-analytics.readonly scope not present in auth URL"
        )
