import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from core.db import db
from core.deps import get_current_user, now_iso
from core.schemas import Project, CreateFromTemplateRequest
from core.niche_templates import NICHE_TEMPLATES

router = APIRouter(tags=["templates"])


@router.get("/templates")
async def list_templates(niche: Optional[str] = None):
    items = list(NICHE_TEMPLATES.values())
    if niche:
        items = [t for t in items if t["niche"] == niche]
    return {"templates": items}


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    t = NICHE_TEMPLATES.get(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return t


@router.post("/projects/from-template", response_model=Project)
async def create_from_template(payload: CreateFromTemplateRequest, current=Depends(get_current_user)):
    tpl = NICHE_TEMPLATES.get(payload.template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    pid = str(uuid.uuid4())
    doc = {
        "id": pid, "user_id": current["id"],
        "topic": payload.topic or tpl["topic_template"],
        "audience": "general",
        "duration_seconds": tpl["duration_seconds"],
        "tone": tpl["tone"], "language": "English",
        "style": tpl["style"], "niche": tpl["niche"],
        "status": "draft",
        "title": None, "description": None, "script": None, "voice": None,
        "thumbnail_url": None, "thumbnail_path": None,
        "youtube_video_id": None, "youtube_url": None,
        "scheduled_at": None, "scene_images": None, "scenes_status": None,
        "video_path": None, "video_url": None, "uploaded_real": None,
        "template_id": tpl["id"],
        "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.projects.insert_one(doc)
    doc.pop("_id", None)
    return Project(**doc)
