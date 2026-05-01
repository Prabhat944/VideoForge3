from typing import List
import uuid
import json
import re
import logging

from fastapi import APIRouter, Depends, HTTPException

from emergentintegrations.llm.chat import LlmChat, UserMessage

from core.db import db
from core.deps import get_current_user, now_iso
from core.config import EMERGENT_LLM_KEY
from core.schemas import Project, ProjectCreate, SeriesRequest

router = APIRouter(tags=["projects"])


@router.post("/projects", response_model=Project)
async def create_project(payload: ProjectCreate, current=Depends(get_current_user)):
    pid = str(uuid.uuid4())
    doc = {
        "id": pid,
        "user_id": current["id"],
        "topic": payload.topic,
        "audience": payload.audience,
        "duration_seconds": payload.duration_seconds,
        "tone": payload.tone,
        "language": payload.language,
        "style": payload.style,
        "niche": payload.niche,
        "status": "draft",
        "title": None,
        "description": None,
        "script": None,
        "voice": None,
        "thumbnail_url": None,
        "youtube_video_id": None,
        "youtube_url": None,
        "scheduled_at": None,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.projects.insert_one(doc)
    doc.pop("_id", None)
    return Project(**doc)


@router.get("/projects", response_model=List[Project])
async def list_projects(current=Depends(get_current_user)):
    items = await db.projects.find(
        {"user_id": current["id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    return [Project(**i) for i in items]


@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str, current=Depends(get_current_user)):
    doc = await db.projects.find_one(
        {"id": project_id, "user_id": current["id"]}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    return Project(**doc)


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, current=Depends(get_current_user)):
    result = await db.projects.delete_one({"id": project_id, "user_id": current["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"ok": True}


@router.post("/projects/series")
async def create_series(payload: SeriesRequest, current=Depends(get_current_user)):
    if payload.count < 1 or payload.count > 30:
        raise HTTPException(status_code=400, detail="count must be 1-30")
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="LLM key not configured")

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"series-{uuid.uuid4()}",
            system_message="Return ONLY valid JSON. You are a YouTube content strategist.",
        ).with_model("openai", "gpt-4o-mini")
        prompt = (
            f"Generate {payload.count} unique sequential YouTube video topics for a series "
            f"on '{payload.base_topic}' in the '{payload.niche}' niche. "
            'Return JSON: {"topics": ["topic1", "topic2", ...]}'
        )
        resp = await chat.send_message(UserMessage(text=prompt))
        text = resp if isinstance(resp, str) else str(resp)
        match = re.search(r'\{[\s\S]*\}', text)
        topics = json.loads(match.group()).get("topics", []) if match else []
    except Exception as e:
        logging.warning(f"Series LLM fallback: {e}")
        topics = [f"{payload.base_topic} - Part {i+1}" for i in range(payload.count)]

    created = []
    for t in topics[: payload.count]:
        pid = str(uuid.uuid4())
        doc = {
            "id": pid, "user_id": current["id"], "topic": t,
            "audience": payload.audience, "duration_seconds": payload.duration_seconds,
            "tone": payload.tone, "language": payload.language, "style": payload.style,
            "niche": payload.niche, "status": "draft",
            "title": None, "description": None, "script": None, "voice": None,
            "thumbnail_url": None, "youtube_video_id": None, "youtube_url": None,
            "scheduled_at": None,
            "created_at": now_iso(), "updated_at": now_iso(),
        }
        await db.projects.insert_one(doc)
        doc.pop("_id", None)
        created.append(doc)
    return {"created": len(created), "projects": [Project(**c).model_dump() for c in created]}
