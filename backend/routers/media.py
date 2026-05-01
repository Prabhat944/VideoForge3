"""Auth-protected static media files (scenes, thumbnails, voices)."""
from typing import Optional
import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials

import storage_service

from core.db import db
from core.deps import security
from core.config import JWT_SECRET, JWT_ALGORITHM

router = APIRouter(tags=["media"])


@router.get("/media/{kind}/{project_id}/{filename}")
async def serve_media(
    kind: str, project_id: str, filename: str,
    token: Optional[str] = None,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """Auth via Bearer header OR ?token=<jwt> query (for <img> tags). Verifies project ownership."""
    auth_token = (creds.credentials if creds else None) or token
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = pyjwt.decode(auth_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    proj = await db.projects.find_one(
        {"id": project_id, "user_id": user_id}, {"_id": 0, "id": 1}
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    rel = f"{kind}/{project_id}/{filename}"
    try:
        path = storage_service.absolute_path(rel)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    media_types = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                   "mp3": "audio/mpeg", "mp4": "video/mp4"}
    ext = filename.rsplit(".", 1)[-1].lower()
    return FileResponse(path, media_type=media_types.get(ext, "application/octet-stream"))
