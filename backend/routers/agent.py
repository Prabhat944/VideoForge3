"""Autonomous agent: topic → publish in one call. Reuses pipeline helpers."""
import asyncio
import base64
import json
import logging
import os
import re
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
from emergentintegrations.llm.openai.text_to_speech import OpenAITextToSpeech

import render_service
import storage_service
import youtube_service

from core.db import db
from core.config import EMERGENT_LLM_KEY, APP_BASE_URL
from core.deps import get_current_user, now_iso
from core.schemas import AgentRunRequest
from core.voices import HD_VOICES
from routers.pipeline import _generate_scenes_background

router = APIRouter(tags=["agent"])


async def _agent_run_background(project_id: str, user_id: str, voice: str, auto_publish: bool, privacy: str):
    async def set_stage(stage: str, agent_state: str = "running", error: Optional[str] = None):
        update = {"agent_stage": stage, "agent_status": agent_state, "updated_at": now_iso()}
        if error:
            update["agent_error"] = error
        await db.projects.update_one({"id": project_id}, {"$set": update})

    try:
        await set_stage("script")
        proj = await db.projects.find_one({"id": project_id}, {"_id": 0})
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"agent-script-{project_id}",
            system_message="You write high-retention viral YouTube scripts. Return ONLY valid JSON.",
        ).with_model("openai", "gpt-4o-mini")
        word_count = max(80, int(proj["duration_seconds"] * 2.3))
        prompt = f"""Generate YouTube script. Topic: {proj['topic']}. Niche: {proj['niche']}.
Duration: ~{proj['duration_seconds']}s ({word_count} words). Tone: {proj['tone']}.
Return strict JSON: {{"title":"","description":"","tags":[],"hook":"","scenes":[{{"index":1,"visual_prompt":"","narration":"","duration":10}}],"cta":"","full_voiceover":""}}"""
        resp = await chat.send_message(UserMessage(text=prompt))
        text = resp if isinstance(resp, str) else str(resp)
        match = re.search(r'\{[\s\S]*\}', text)
        script = json.loads(match.group()) if match else None
        if not script:
            raise RuntimeError("Script gen failed")
        await db.projects.update_one(
            {"id": project_id},
            {"$set": {"script": script, "title": script.get("title"),
                      "description": script.get("description"), "status": "script_ready", "updated_at": now_iso()}},
        )

        await set_stage("voice")
        narration = script.get("full_voiceover") or " ".join(s.get("narration", "") for s in script.get("scenes", []))
        narration = narration[:4000]
        hd_voice = next((v for v in HD_VOICES if v["id"] == voice), None)
        tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
        if hd_voice:
            audio_b64 = await tts.generate_speech_base64(text=narration, model="tts-1-hd", voice=hd_voice["base"], speed=1.0, response_format="mp3")
        else:
            audio_b64 = await tts.generate_speech_base64(text=narration, model="tts-1", voice=voice, speed=1.0, response_format="mp3")
        voice_path = storage_service.save_voice(project_id, base64.b64decode(audio_b64))
        voice_url = f"{APP_BASE_URL}/api/media/{voice_path}"
        await db.projects.update_one(
            {"id": project_id},
            {"$set": {"voice": {"voice_id": voice, "provider": "openai_hd" if hd_voice else "openai",
                                "speed": 1.0, "audio_path": voice_path, "audio_url": voice_url,
                                "format": "mp3", "generated_at": now_iso()},
                      "status": "voice_ready", "updated_at": now_iso()}},
        )

        await set_stage("thumbnail")
        title = script.get("title") or proj["topic"]
        gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        thumb_prompt = f"YouTube thumbnail for '{title}'. Niche: {proj['niche']}. Cinematic, high contrast, vibrant, no text, 16:9, high CTR."

        def _gen_thumb_sync():
            return asyncio.run(gen.generate_images(prompt=thumb_prompt, model="gpt-image-1", number_of_images=1))

        thumb_imgs = await asyncio.to_thread(_gen_thumb_sync)
        if thumb_imgs:
            thumb_path = storage_service.save_thumbnail(project_id, thumb_imgs[0])
            thumb_url = f"{APP_BASE_URL}/api/media/{thumb_path}"
            await db.projects.update_one(
                {"id": project_id},
                {"$set": {"thumbnail_url": thumb_url, "thumbnail_path": thumb_path, "updated_at": now_iso()}},
            )

        await set_stage("scenes")
        await _generate_scenes_background(project_id, user_id)

        await set_stage("render")
        proj2 = await db.projects.find_one({"id": project_id}, {"_id": 0})
        scene_images = proj2.get("scene_images") or []
        v = proj2.get("voice") or {}
        audio_b64_full = storage_service.read_b64(v["audio_path"]) if v.get("audio_path") else v.get("audio_b64", "")
        thumb_data_url = (
            f"data:image/png;base64,{storage_service.read_b64(proj2['thumbnail_path'])}"
            if proj2.get("thumbnail_path") else proj2.get("thumbnail_url", "")
        )
        scenes_input = []
        for s in scene_images:
            if s.get("image_path"):
                img_data_url = f"data:image/png;base64,{storage_service.read_b64(s['image_path'])}"
            else:
                img_data_url = thumb_data_url
            scenes_input.append({"image_data_url": img_data_url, "duration": float(s.get("duration", 10))})
        if scenes_input:
            path = await render_service.render_scenes_mp4(
                scenes=scenes_input, audio_b64=audio_b64_full,
                narration=narration, project_id=project_id,
                fallback_image_data_url=thumb_data_url,
            )
        else:
            path = await render_service.render_mp4(
                thumbnail_data_url=thumb_data_url, audio_b64=audio_b64_full,
                narration=narration, project_id=project_id,
            )
        file_url = f"{APP_BASE_URL}/api/projects/{project_id}/video"
        await db.projects.update_one(
            {"id": project_id},
            {"$set": {"video_path": path, "video_url": file_url, "status": "rendered", "updated_at": now_iso()}},
        )

        if auto_publish:
            await set_stage("publish")
            yt_token = await db.youtube_tokens.find_one({"user_id": user_id}, {"_id": 0})
            if yt_token and path and os.path.exists(path):
                thumb_file = None
                if proj2.get("thumbnail_path"):
                    try:
                        thumb_file = str(storage_service.absolute_path(proj2["thumbnail_path"]))
                    except Exception:
                        thumb_file = None
                tags = script.get("tags", [])[:15]
                result = await asyncio.to_thread(
                    youtube_service.upload_video,
                    yt_token, path, title, script.get("description", ""), tags, privacy, "22", None, thumb_file,
                )
                await db.projects.update_one(
                    {"id": project_id},
                    {"$set": {
                        "youtube_video_id": result["video_id"],
                        "youtube_url": result["url"],
                        "uploaded_real": True,
                        "status": "published",
                        "updated_at": now_iso(),
                    }},
                )

        await set_stage("complete", "complete")
    except Exception as e:
        logging.error(f"Agent run failed: {e}")
        await set_stage("error", "error", str(e)[:200])


@router.post("/agent/run")
async def agent_run(payload: AgentRunRequest, current=Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="LLM key not configured")
    pid = str(uuid.uuid4())
    doc = {
        "id": pid, "user_id": current["id"], "topic": payload.topic,
        "audience": payload.audience, "duration_seconds": payload.duration_seconds,
        "tone": payload.tone, "language": payload.language, "style": payload.style,
        "niche": payload.niche, "status": "agent_running",
        "agent_stage": "queued", "agent_status": "running",
        "title": None, "description": None, "script": None, "voice": None,
        "thumbnail_url": None, "youtube_video_id": None, "youtube_url": None,
        "scheduled_at": None, "scene_images": None, "scenes_status": None,
        "video_path": None, "video_url": None, "uploaded_real": None,
        "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.projects.insert_one(doc)
    asyncio.create_task(_agent_run_background(pid, current["id"], payload.voice, payload.auto_publish, payload.youtube_privacy))
    return {"project_id": pid, "status": "running", "stage": "queued"}


@router.get("/agent/status/{project_id}")
async def agent_status(project_id: str, current=Depends(get_current_user)):
    proj = await db.projects.find_one(
        {"id": project_id, "user_id": current["id"]},
        {"_id": 0, "agent_stage": 1, "agent_status": 1, "agent_error": 1, "youtube_url": 1,
         "video_url": 1, "thumbnail_url": 1, "title": 1, "status": 1},
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "stage": proj.get("agent_stage", "queued"),
        "status": proj.get("agent_status", "running"),
        "error": proj.get("agent_error"),
        "title": proj.get("title"),
        "video_url": proj.get("video_url"),
        "youtube_url": proj.get("youtube_url"),
        "has_thumbnail": bool(proj.get("thumbnail_url")),
        "project_status": proj.get("status"),
    }
