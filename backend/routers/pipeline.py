"""Generation pipeline: script, voice, thumbnail, scenes, render, publish."""
import asyncio
import base64
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
from emergentintegrations.llm.openai.text_to_speech import OpenAITextToSpeech

import elevenlabs_service
import render_service
import storage_service
import youtube_service

from core.db import db
from core.config import EMERGENT_LLM_KEY, APP_BASE_URL
from core.deps import get_current_user, now_iso
from core.voices import VOICES, HD_VOICES
from core.schemas import (
    ScriptGenerateRequest, VoiceGenerateRequest, ThumbnailGenerateRequest,
    ScenesGenerateRequest, RenderRequest, PublishRequest,
    VariantGenerateRequest, SelectVariantRequest, VariantScoreRequest,
    ABWeightsUpdate,
)

router = APIRouter(tags=["pipeline"])

DEFAULT_AB_WEIGHTS = {"hook": 0.5, "title": 0.2, "overall": 0.3}


def _resolved_weights(proj: dict) -> dict:
    """Return normalised hook/title/overall weights for this project (default 50/20/30)."""
    w = (proj.get("ab_weights") or DEFAULT_AB_WEIGHTS).copy()
    total = float(w.get("hook", 0)) + float(w.get("title", 0)) + float(w.get("overall", 0))
    if total <= 0:
        return DEFAULT_AB_WEIGHTS
    return {k: float(w.get(k, 0)) / total for k in ("hook", "title", "overall")}


# ---------------- Script ----------------
@router.post("/projects/script")
async def generate_script(payload: ScriptGenerateRequest, current=Depends(get_current_user)):
    proj = await db.projects.find_one(
        {"id": payload.project_id, "user_id": current["id"]}, {"_id": 0}
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="LLM key not configured")

    style = payload.style or proj.get("style", "storytelling")
    word_count = max(80, int(proj["duration_seconds"] * 2.3))

    prompt = f"""You are an expert YouTube scriptwriter. Generate a video script.
Topic: {proj['topic']}
Audience: {proj['audience']}
Duration: ~{proj['duration_seconds']}s ({word_count} words)
Tone: {proj['tone']}
Language: {proj['language']}
Style: {style}
Niche: {proj['niche']}
Variant: {payload.variant}

Return STRICT JSON only:
{{
  "title": "catchy title under 60 chars",
  "description": "youtube description ~150 chars",
  "tags": ["tag1","tag2","tag3","tag4","tag5"],
  "hook": "opening 5-10 second attention grabber",
  "scenes": [
    {{"index":1,"visual_prompt":"description for image generation","narration":"voice over text","duration":10}}
  ],
  "cta": "subscribe/like message",
  "full_voiceover": "full concatenated narration"
}}
Make it viral, retention-focused. 4-6 scenes."""

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"script-{payload.project_id}-{payload.variant}",
            system_message="You write high-retention viral YouTube scripts. Return ONLY valid JSON.",
        ).with_model("openai", "gpt-4o-mini")
        resp = await chat.send_message(UserMessage(text=prompt))
        text = resp if isinstance(resp, str) else str(resp)
        match = re.search(r'\{[\s\S]*\}', text)
        if not match:
            raise ValueError("No JSON in response")
        script = json.loads(match.group())
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Script gen error: {error_msg}")
        
        # Check for budget exceeded error
        if "budget" in error_msg.lower() or "exceeded" in error_msg.lower():
            raise HTTPException(
                status_code=402,  # Payment Required
                detail="AI budget exceeded. Please add balance to your Universal Key in Profile → Universal Key → Add Balance"
            )
        
        raise HTTPException(status_code=500, detail=f"Script generation failed: {error_msg}")

    update = {
        "script": script,
        "title": script.get("title"),
        "description": script.get("description"),
        "status": "script_ready",
        "updated_at": now_iso(),
    }
    await db.projects.update_one({"id": payload.project_id}, {"$set": update})
    return {"script": script}


# ---------------- Voice ----------------
@router.get("/voices")
async def list_voices():
    elev = [{**v, "provider": "elevenlabs", "tier": "premium_plus"} for v in elevenlabs_service.ELEVEN_VOICES]
    return {"voices": VOICES + HD_VOICES + elev}


@router.post("/projects/voice")
async def generate_voice(payload: VoiceGenerateRequest, current=Depends(get_current_user)):
    proj = await db.projects.find_one(
        {"id": payload.project_id, "user_id": current["id"]}, {"_id": 0}
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    if not proj.get("script"):
        raise HTTPException(status_code=400, detail="Generate script first")
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="LLM key not configured")

    text = proj["script"].get("full_voiceover") or " ".join(
        s.get("narration", "") for s in proj["script"].get("scenes", [])
    )
    text = text[:4000]

    hd_voice = next((v for v in HD_VOICES if v["id"] == payload.voice), None)
    is_elevenlabs = any(v["id"] == payload.voice for v in elevenlabs_service.ELEVEN_VOICES)

    try:
        if is_elevenlabs:
            audio_b64 = await elevenlabs_service.synthesize_b64(text, payload.voice, payload.speed)
            provider = "elevenlabs"
        elif hd_voice:
            tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
            audio_b64 = await tts.generate_speech_base64(
                text=text, model="tts-1-hd", voice=hd_voice["base"],
                speed=payload.speed, response_format="mp3",
            )
            provider = "openai_hd"
        else:
            tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
            audio_b64 = await tts.generate_speech_base64(
                text=text, model="tts-1", voice=payload.voice,
                speed=payload.speed, response_format="mp3",
            )
            provider = "openai"
    except Exception as e:
        error_msg = str(e)
        logging.error(f"TTS error: {error_msg}")
        
        # Check for budget exceeded error
        if "budget" in error_msg.lower() or "exceeded" in error_msg.lower():
            raise HTTPException(
                status_code=402,
                detail="AI budget exceeded. Please add balance to your Universal Key in Profile → Universal Key → Add Balance"
            )
        
        raise HTTPException(status_code=500, detail=f"Voice generation failed: {error_msg}")

    # Save MP3 to disk for local access, but also store base64 in DB for production/container deployments
    voice_path = storage_service.save_voice(payload.project_id, base64.b64decode(audio_b64))
    voice_url = f"{APP_BASE_URL}/api/media/{voice_path}"

    voice_data = {
        "voice_id": payload.voice,
        "provider": provider,
        "speed": payload.speed,
        "audio_path": voice_path,
        "audio_url": voice_url,
        "audio_b64": audio_b64,  # Store base64 as fallback for stateless deployments
        "format": "mp3",
        "generated_at": now_iso(),
    }
    await db.projects.update_one(
        {"id": payload.project_id},
        {"$set": {"voice": voice_data, "status": "voice_ready", "updated_at": now_iso()}},
    )
    return {
        "voice_id": payload.voice,
        "provider": provider,
        "audio_url": voice_url,
        "format": "mp3",
    }


# ---------------- Thumbnail ----------------
@router.post("/projects/thumbnail")
async def generate_thumbnail(payload: ThumbnailGenerateRequest, current=Depends(get_current_user)):
    proj = await db.projects.find_one(
        {"id": payload.project_id, "user_id": current["id"]}, {"_id": 0}
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="LLM key not configured")

    title = (proj.get("script") or {}).get("title") or proj["topic"]
    style = payload.style_prompt or "cinematic, high contrast, vibrant colors, dramatic lighting"
    prompt = (
        f"YouTube thumbnail for video titled '{title}'. "
        f"Niche: {proj['niche']}. Style: {style}. "
        "16:9 aspect ratio, eye-catching, bold composition, no text overlay, "
        "professional quality, high CTR design."
    )

    try:
        gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        images = await gen.generate_images(prompt=prompt, model="gpt-image-1", number_of_images=1)
        if not images:
            raise ValueError("No image returned")
        img_bytes = images[0]
        thumb_path = storage_service.save_thumbnail(payload.project_id, img_bytes)
        thumb_url = f"{APP_BASE_URL}/api/media/{thumb_path}"
        # Store base64 as fallback for stateless deployments
        thumb_b64_data_url = f"data:image/png;base64,{base64.b64encode(img_bytes).decode('utf-8')}"
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Thumbnail gen error: {error_msg}")
        
        # Check for budget exceeded error
        if "budget" in error_msg.lower() or "exceeded" in error_msg.lower():
            raise HTTPException(
                status_code=402,
                detail="AI budget exceeded. Please add balance to your Universal Key in Profile → Universal Key → Add Balance"
            )
        
        raise HTTPException(status_code=500, detail=f"Thumbnail generation failed: {error_msg}")

    await db.projects.update_one(
        {"id": payload.project_id},
        {"$set": {
            "thumbnail_url": thumb_url, 
            "thumbnail_path": thumb_path, 
            "thumbnail_b64": thumb_b64_data_url,  # Store base64 as fallback
            "updated_at": now_iso()
        }},
    )
    return {"thumbnail_url": thumb_url}


# ---------------- Scenes (background) ----------------
async def _generate_scenes_background(project_id: str, user_id: str):
    proj = await db.projects.find_one({"id": project_id, "user_id": user_id}, {"_id": 0})
    if not proj or not proj.get("script"):
        return
    scenes = proj["script"].get("scenes", []) or []
    scenes_to_gen = scenes[:6]
    placeholders = [
        {"index": s.get("index", i + 1), "duration": s.get("duration", 10), "image_url": None, "image_path": None, "status": "pending"}
        for i, s in enumerate(scenes_to_gen)
    ]
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {"scene_images": placeholders, "scenes_status": "generating",
                  "scenes_started_at": now_iso(), "updated_at": now_iso()}},
    )

    def _gen_sync(p: str) -> list:
        gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        return asyncio.run(gen.generate_images(prompt=p, model="gpt-image-1", number_of_images=1))

    for i, scene in enumerate(scenes_to_gen):
        prompt = (
            f"Cinematic 16:9 video scene visual. Topic: {proj['topic']}. Niche: {proj['niche']}. "
            f"Scene description: {scene.get('visual_prompt', '')}. "
            "Highly detailed, dramatic lighting, professional cinematography, no text overlay."
        )
        try:
            images = await asyncio.to_thread(_gen_sync, prompt)
            if images:
                rel_path = storage_service.save_scene_image(project_id, placeholders[i]["index"], images[0])
                # Store base64 as fallback for stateless deployments
                img_b64_data_url = f"data:image/png;base64,{base64.b64encode(images[0]).decode('utf-8')}"
                placeholders[i]["image_path"] = rel_path
                placeholders[i]["image_url"] = f"{APP_BASE_URL}/api/media/{rel_path}"
                placeholders[i]["image_data_url"] = img_b64_data_url  # Store base64 as fallback
                placeholders[i]["status"] = "ready"
            else:
                placeholders[i]["status"] = "failed"
        except Exception as e:
            logging.warning(f"Scene {i} failed: {e}")
            placeholders[i]["status"] = "failed"
        await db.projects.update_one(
            {"id": project_id},
            {"$set": {"scene_images": placeholders, "updated_at": now_iso()}},
        )
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {"scenes_status": "complete", "updated_at": now_iso()}},
    )


@router.post("/projects/scenes")
async def generate_scene_images(payload: ScenesGenerateRequest, current=Depends(get_current_user)):
    proj = await db.projects.find_one(
        {"id": payload.project_id, "user_id": current["id"]}, {"_id": 0}
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    if not proj.get("script"):
        raise HTTPException(status_code=400, detail="Generate script first")
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="LLM key not configured")

    if proj.get("scenes_status") == "generating":
        started = proj.get("scenes_started_at")
        if started:
            try:
                started_dt = datetime.fromisoformat(started)
                if datetime.now(timezone.utc) - started_dt < timedelta(minutes=10):
                    raise HTTPException(status_code=409, detail="Scene generation already in progress")
            except (ValueError, TypeError):
                pass

    scenes = proj["script"].get("scenes", []) or []
    if not scenes:
        raise HTTPException(status_code=400, detail="Script has no scenes")

    asyncio.create_task(_generate_scenes_background(payload.project_id, current["id"]))

    return {
        "scenes": [
            {"index": s.get("index", i + 1), "duration": s.get("duration", 10), "has_image": False}
            for i, s in enumerate(scenes[:6])
        ],
        "status": "generating",
        "message": "Scene generation started. Poll GET /api/projects/{id}/scenes-status for progress.",
    }


@router.get("/projects/{project_id}/scenes-status")
async def scenes_status(project_id: str, current=Depends(get_current_user)):
    proj = await db.projects.find_one(
        {"id": project_id, "user_id": current["id"]},
        {"_id": 0, "scene_images": 1, "scenes_status": 1},
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    scene_images = proj.get("scene_images") or []
    return {
        "status": proj.get("scenes_status", "idle"),
        "scenes": [
            {
                "index": s.get("index"),
                "duration": s.get("duration"),
                "has_image": bool(s.get("image_url") or s.get("image_path")),
                "image_url": s.get("image_url"),
                "image_status": s.get("status", "pending"),
            }
            for s in scene_images
        ],
    }


# ---------------- Render ----------------
def _audio_b64_for(voice: dict) -> str:
    """Get audio base64, trying filesystem first, falling back to DB."""
    if voice.get("audio_path"):
        try:
            return storage_service.read_b64(voice["audio_path"])
        except FileNotFoundError:
            # File doesn't exist on filesystem (container restart/ephemeral storage)
            # Fall back to base64 from database
            logging.warning(f"Voice file not found on filesystem: {voice['audio_path']}, using DB fallback")
            pass
    # Return audio_b64 from database (fallback for stateless deployments)
    return voice.get("audio_b64", "")


def _thumb_data_url(proj: dict) -> str:
    """Get thumbnail data URL, trying filesystem first, falling back to DB base64."""
    # Try reading from filesystem if path exists
    if proj.get("thumbnail_path"):
        try:
            return f"data:image/png;base64,{storage_service.read_b64(proj['thumbnail_path'])}"
        except FileNotFoundError:
            # File doesn't exist on filesystem, try to use base64 from DB
            logging.warning(f"Thumbnail file not found on filesystem: {proj['thumbnail_path']}, using DB fallback")
            if proj.get("thumbnail_b64"):
                return proj["thumbnail_b64"]
    
    # Check if we have base64 stored in DB
    if proj.get("thumbnail_b64"):
        return proj["thumbnail_b64"]
    
    # Fall back to thumbnail_url
    thumb_url = proj.get("thumbnail_url", "") or ""
    if thumb_url.startswith("data:"):
        return thumb_url
    if "/api/media/thumbnails/" in thumb_url:
        try:
            rel = thumb_url.split("/api/media/", 1)[-1]
            return f"data:image/png;base64,{storage_service.read_b64(rel)}"
        except FileNotFoundError:
            logging.warning(f"Thumbnail file not found for URL: {thumb_url}")
            # Return empty data URL as last resort
            return "data:image/png;base64,"
    return thumb_url


@router.post("/projects/render")
async def render_video(payload: RenderRequest, current=Depends(get_current_user)):
    proj = await db.projects.find_one(
        {"id": payload.project_id, "user_id": current["id"]}, {"_id": 0}
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    if not proj.get("thumbnail_url"):
        raise HTTPException(status_code=400, detail="Generate thumbnail first")
    voice = proj.get("voice") or {}
    if not (voice.get("audio_path") or voice.get("audio_b64")):
        raise HTTPException(status_code=400, detail="Generate voice first")

    audio_b64 = _audio_b64_for(voice)
    thumb_data_url = _thumb_data_url(proj)

    narration = (proj.get("script") or {}).get("full_voiceover") or " ".join(
        s.get("narration", "") for s in (proj.get("script") or {}).get("scenes", [])
    )
    scene_images = proj.get("scene_images") or []
    try:
        if scene_images and any(s.get("image_path") or s.get("image_data_url") for s in scene_images):
            scenes_input = []
            for s in scene_images:
                if s.get("image_path"):
                    try:
                        img_data_url = f"data:image/png;base64,{storage_service.read_b64(s['image_path'])}"
                    except FileNotFoundError:
                        logging.warning(f"Scene image file not found: {s['image_path']}, using fallback")
                        img_data_url = s.get("image_data_url") or thumb_data_url
                elif s.get("image_data_url"):
                    img_data_url = s["image_data_url"]
                else:
                    img_data_url = thumb_data_url
                scenes_input.append({
                    "image_data_url": img_data_url,
                    "duration": float(s.get("duration", 10)),
                })
            path = await render_service.render_scenes_mp4(
                scenes=scenes_input, audio_b64=audio_b64, narration=narration,
                project_id=payload.project_id, fallback_image_data_url=thumb_data_url,
            )
        else:
            path = await render_service.render_mp4(
                thumbnail_data_url=thumb_data_url, audio_b64=audio_b64,
                narration=narration, project_id=payload.project_id,
            )
    except Exception as e:
        logging.error(f"render failed: {e}")
        raise HTTPException(status_code=500, detail=f"Render failed: {e}")

    file_url = f"{APP_BASE_URL}/api/projects/{payload.project_id}/video"
    await db.projects.update_one(
        {"id": payload.project_id},
        {"$set": {"video_path": path, "video_url": file_url, "status": "rendered", "updated_at": now_iso()}},
    )
    return {"video_url": file_url, "video_path": path, "scenes_used": len(scene_images)}


@router.get("/projects/{project_id}/video")
async def get_project_video(project_id: str, current=Depends(get_current_user)):
    proj = await db.projects.find_one(
        {"id": project_id, "user_id": current["id"]}, {"_id": 0}
    )
    if not proj or not proj.get("video_path") or not os.path.exists(proj["video_path"]):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(proj["video_path"], media_type="video/mp4", filename=f"{project_id}.mp4")


# ---------------- Publish ----------------
@router.post("/projects/publish")
async def publish_youtube(payload: PublishRequest, current=Depends(get_current_user)):
    proj = await db.projects.find_one(
        {"id": payload.project_id, "user_id": current["id"]}, {"_id": 0}
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    yt_token = await db.youtube_tokens.find_one({"user_id": current["id"]}, {"_id": 0})

    if yt_token and proj.get("video_path") and os.path.exists(proj["video_path"]):
        thumb_path = None
        if proj.get("thumbnail_path"):
            try:
                thumb_path = str(storage_service.absolute_path(proj["thumbnail_path"]))
            except Exception:
                thumb_path = None
        elif proj.get("thumbnail_url", "").startswith("data:"):
            try:
                tp = Path(render_service.RENDER_DIR) / f"{payload.project_id}_thumb.png"
                tp.write_bytes(base64.b64decode(proj["thumbnail_url"].split(",", 1)[1]))
                thumb_path = str(tp)
            except Exception:
                thumb_path = None
        try:
            result = await asyncio.to_thread(
                youtube_service.upload_video,
                yt_token, proj["video_path"], payload.title, payload.description,
                payload.tags, payload.privacy, "22", payload.schedule_at, thumb_path,
            )
        except Exception as e:
            logging.error(f"yt upload failed: {e}")
            raise HTTPException(status_code=500, detail=f"YouTube upload failed: {e}")

        update = {
            "title": payload.title, "description": payload.description,
            "status": "scheduled" if payload.schedule_at else "published",
            "youtube_video_id": result["video_id"], "youtube_url": result["url"],
            "scheduled_at": payload.schedule_at, "uploaded_real": True,
            "updated_at": now_iso(),
        }
        await db.projects.update_one({"id": payload.project_id}, {"$set": update})
        await db.analytics.update_one(
            {"project_id": payload.project_id},
            {"$set": {
                "project_id": payload.project_id, "user_id": current["id"],
                "youtube_video_id": result["video_id"],
                "views": 0, "likes": 0, "comments": 0,
                "ctr": 0.0, "watch_time_minutes": 0.0,
                "created_at": now_iso(),
            }},
            upsert=True,
        )
        return {"video_id": result["video_id"], "url": result["url"], "status": update["status"], "real": True}

    fake_video_id = uuid.uuid4().hex[:11]
    youtube_url = f"https://youtube.com/watch?v={fake_video_id}"
    update = {
        "title": payload.title, "description": payload.description,
        "status": "scheduled" if payload.schedule_at else "published",
        "youtube_video_id": fake_video_id, "youtube_url": youtube_url,
        "scheduled_at": payload.schedule_at, "uploaded_real": False,
        "updated_at": now_iso(),
    }
    await db.projects.update_one({"id": payload.project_id}, {"$set": update})
    await db.analytics.update_one(
        {"project_id": payload.project_id},
        {"$set": {
            "project_id": payload.project_id, "user_id": current["id"],
            "youtube_video_id": fake_video_id,
            "views": 0, "likes": 0, "comments": 0,
            "ctr": 0.0, "watch_time_minutes": 0.0,
            "avg_view_duration": 0.0, "subscribers_gained": 0,
            "created_at": now_iso(),
        }},
        upsert=True,
    )
    return {"video_id": fake_video_id, "url": youtube_url, "status": update["status"], "real": False}


# ---------------- Tools comparison (legacy) ----------------
@router.get("/tools/compare")
async def compare_tools():
    return {
        "script": [
            {"name": "GPT-5 (Premium)", "tier": "premium", "cost_per_video": 0.05, "speed_seconds": 8, "quality": 95, "selected": True},
            {"name": "GPT-4o-mini (Free)", "tier": "free", "cost_per_video": 0.01, "speed_seconds": 5, "quality": 78, "selected": False},
        ],
        "voice": [
            {"name": "OpenAI TTS HD (Premium)", "tier": "premium", "cost_per_video": 0.30, "speed_seconds": 12, "quality": 92, "selected": False},
            {"name": "OpenAI TTS Standard (Free)", "tier": "free", "cost_per_video": 0.10, "speed_seconds": 8, "quality": 84, "selected": True},
            {"name": "ElevenLabs (Premium+)", "tier": "premium+", "cost_per_video": 0.80, "speed_seconds": 15, "quality": 98, "selected": False},
        ],
        "video": [
            {"name": "AI Slideshow + TTS (Free)", "tier": "free", "cost_per_video": 0.50, "speed_seconds": 60, "quality": 75, "selected": True},
            {"name": "Runway Gen-3 (Premium+)", "tier": "premium+", "cost_per_video": 5.00, "speed_seconds": 240, "quality": 95, "selected": False},
            {"name": "Pika Labs (Premium)", "tier": "premium", "cost_per_video": 2.50, "speed_seconds": 180, "quality": 88, "selected": False},
        ],
        "thumbnail": [
            {"name": "GPT Image 1 (Premium)", "tier": "premium", "cost_per_video": 0.04, "speed_seconds": 10, "quality": 92, "selected": True},
            {"name": "Stock Image (Free)", "tier": "free", "cost_per_video": 0.0, "speed_seconds": 1, "quality": 60, "selected": False},
        ],
    }


# ---------------- A/B Variants ----------------
@router.post("/projects/script/variants")
async def generate_variants(payload: VariantGenerateRequest, current=Depends(get_current_user)):
    proj = await db.projects.find_one(
        {"id": payload.project_id, "user_id": current["id"]}, {"_id": 0}
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="LLM key not configured")

    word_count = max(80, int(proj["duration_seconds"] * 2.3))

    async def _gen(style: str, label: str) -> dict:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"ab-{payload.project_id}-{label}",
            system_message="You write high-retention viral YouTube scripts. Return ONLY valid JSON.",
        ).with_model("openai", "gpt-4o-mini")
        prompt = f"""Generate YouTube script. Variant {label}.
Topic: {proj['topic']}. Niche: {proj['niche']}. Duration: ~{proj['duration_seconds']}s ({word_count} words).
Tone: {proj['tone']}. Style: {style}.
Return strict JSON: {{"title":"","description":"","tags":[],"hook":"","scenes":[{{"index":1,"visual_prompt":"","narration":"","duration":10}}],"cta":"","full_voiceover":""}}"""
        resp = await chat.send_message(UserMessage(text=prompt))
        text = resp if isinstance(resp, str) else str(resp)
        match = re.search(r'\{[\s\S]*\}', text)
        if not match:
            raise RuntimeError(f"No JSON in variant {label}")
        return json.loads(match.group())

    try:
        a, b = await asyncio.gather(
            _gen(payload.style_a, "A"),
            _gen(payload.style_b, "B"),
        )
    except Exception as e:
        logging.error(f"Variants gen failed: {e}")
        raise HTTPException(status_code=500, detail=f"Variant generation failed: {e}")

    variants = [
        {"id": "A", "label": f"Style A: {payload.style_a}", "style": payload.style_a, "script": a, "score": None},
        {"id": "B", "label": f"Style B: {payload.style_b}", "style": payload.style_b, "script": b, "score": None},
    ]
    await db.projects.update_one(
        {"id": payload.project_id},
        {"$set": {"script_variants": variants, "ab_winner": None, "ab_metrics": None, "updated_at": now_iso()}},
    )
    return {"variants": [{"id": v["id"], "label": v["label"], "style": v["style"],
                          "title": v["script"].get("title"),
                          "scene_count": len(v["script"].get("scenes", [])),
                          "tags": v["script"].get("tags", [])} for v in variants]}


@router.get("/projects/{project_id}/variants")
async def get_variants(project_id: str, current=Depends(get_current_user)):
    """Full A/B dashboard payload: both scripts side-by-side + scores + winner."""
    proj = await db.projects.find_one(
        {"id": project_id, "user_id": current["id"]},
        {"_id": 0, "id": 1, "topic": 1, "niche": 1, "script_variants": 1,
         "selected_variant_id": 1, "ab_winner": 1, "ab_metrics": 1, "ab_weights": 1},
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "project_id": proj["id"],
        "topic": proj["topic"],
        "niche": proj["niche"],
        "variants": proj.get("script_variants") or [],
        "selected_variant_id": proj.get("selected_variant_id"),
        "ab_winner": proj.get("ab_winner"),
        "ab_metrics": proj.get("ab_metrics") or {},
        "ab_weights": proj.get("ab_weights") or DEFAULT_AB_WEIGHTS,
    }


@router.post("/projects/script/select-variant")
async def select_variant(payload: SelectVariantRequest, current=Depends(get_current_user)):
    proj = await db.projects.find_one(
        {"id": payload.project_id, "user_id": current["id"]}, {"_id": 0}
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    variants = proj.get("script_variants") or []
    chosen = next((v for v in variants if v["id"] == payload.variant_id), None)
    if not chosen:
        raise HTTPException(status_code=404, detail="Variant not found")
    script = chosen["script"]
    await db.projects.update_one(
        {"id": payload.project_id},
        {"$set": {
            "script": script,
            "title": script.get("title"),
            "description": script.get("description"),
            "selected_variant_id": payload.variant_id,
            "ab_winner": payload.variant_id,
            "status": "script_ready",
            "updated_at": now_iso(),
        }},
    )
    return {"ok": True, "variant_id": payload.variant_id, "script": script}


@router.post("/projects/script/variants/weights")
async def set_ab_weights(payload: ABWeightsUpdate, current=Depends(get_current_user)):
    """Set per-project A/B winner weighting. Recomputes ab_winner from existing scores."""
    proj = await db.projects.find_one(
        {"id": payload.project_id, "user_id": current["id"]}, {"_id": 0}
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    weights = {"hook": payload.hook, "title": payload.title, "overall": payload.overall}
    norm = _resolved_weights({"ab_weights": weights})

    variants = proj.get("script_variants") or []
    metrics = {}
    for v in variants:
        s = v.get("score") or {}
        if not s:
            continue
        weighted = round(
            norm["hook"] * float(s.get("hook", 0) or 0)
            + norm["title"] * float(s.get("title", 0) or 0)
            + norm["overall"] * float(s.get("overall", 0) or 0),
            2,
        )
        s["weighted"] = weighted
        metrics[v["id"]] = weighted
    winner = max(metrics.items(), key=lambda kv: kv[1])[0] if metrics else None

    await db.projects.update_one(
        {"id": payload.project_id},
        {"$set": {
            "ab_weights": weights,
            "script_variants": variants,
            "ab_metrics": metrics,
            "ab_winner": winner,
            "updated_at": now_iso(),
        }},
    )
    return {"ok": True, "ab_weights": weights, "normalised": norm,
            "ab_metrics": metrics, "ab_winner": winner}


@router.post("/projects/script/variants/score")
async def score_variant(payload: VariantScoreRequest, current=Depends(get_current_user)):
    """Persist user-provided rating for an A/B variant; aggregate into ab_metrics."""
    proj = await db.projects.find_one(
        {"id": payload.project_id, "user_id": current["id"]}, {"_id": 0}
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    variants = proj.get("script_variants") or []
    found = False
    for v in variants:
        if v["id"] == payload.variant_id:
            v["score"] = {
                "hook": payload.hook_score,
                "title": payload.title_score,
                "overall": payload.overall_score,
                "note": payload.note,
                "scored_at": now_iso(),
            }
            found = True
    if not found:
        raise HTTPException(status_code=404, detail="Variant not found")

    norm = _resolved_weights(proj)
    metrics = {}
    for v in variants:
        s = v.get("score") or {}
        if not s:
            continue
        weighted = round(
            norm["hook"] * float(s.get("hook", 0) or 0)
            + norm["title"] * float(s.get("title", 0) or 0)
            + norm["overall"] * float(s.get("overall", 0) or 0),
            2,
        )
        s["weighted"] = weighted
        metrics[v["id"]] = weighted
    winner = max(metrics.items(), key=lambda kv: kv[1])[0] if metrics else None

    await db.projects.update_one(
        {"id": payload.project_id},
        {"$set": {"script_variants": variants, "ab_metrics": metrics,
                  "ab_winner": winner, "updated_at": now_iso()}},
    )
    return {"ok": True, "ab_metrics": metrics, "ab_winner": winner, "weights": proj.get("ab_weights") or DEFAULT_AB_WEIGHTS}
