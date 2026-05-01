from datetime import datetime, timezone
from fastapi import APIRouter, Depends

from core.db import db
from core.deps import get_current_user

router = APIRouter(tags=["calendar"])


@router.get("/calendar")
async def calendar(current=Depends(get_current_user)):
    """Returns scheduled and recently published projects sorted by date."""
    now = datetime.now(timezone.utc)
    items = await db.projects.find(
        {"user_id": current["id"], "status": {"$in": ["published", "scheduled", "rendered"]}},
        {"_id": 0, "id": 1, "title": 1, "topic": 1, "thumbnail_url": 1, "status": 1,
         "scheduled_at": 1, "updated_at": 1, "youtube_url": 1, "uploaded_real": 1},
    ).to_list(500)
    result = []
    for p in items:
        when = p.get("scheduled_at") or p.get("updated_at")
        result.append({
            "project_id": p["id"],
            "title": p.get("title") or p.get("topic"),
            "thumbnail_url": p.get("thumbnail_url"),
            "status": p.get("status"),
            "scheduled_at": p.get("scheduled_at"),
            "published_at": p.get("updated_at") if p.get("status") == "published" else None,
            "youtube_url": p.get("youtube_url"),
            "real": bool(p.get("uploaded_real")),
            "when": when,
        })
    result.sort(key=lambda x: x.get("when") or "")
    return {"items": result, "today": now.isoformat()}
