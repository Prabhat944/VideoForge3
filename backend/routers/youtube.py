import logging
import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

import youtube_service

from core.db import db
from core.config import APP_BASE_URL
from core.deps import get_current_user, now_iso

router = APIRouter(tags=["youtube"])


@router.get("/youtube/status")
async def youtube_status(current=Depends(get_current_user)):
    yt = await db.youtube_tokens.find_one({"user_id": current["id"]}, {"_id": 0})
    if not yt:
        return {"connected": False}
    return {"connected": True, "channel": yt.get("channel")}


@router.get("/youtube/auth-url")
async def youtube_auth_url(current=Depends(get_current_user)):
    state = uuid.uuid4().hex
    await db.oauth_states.insert_one({
        "state": state, "user_id": current["id"], "created_at": now_iso(),
    })
    try:
        return {"url": youtube_service.auth_url(state)}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"OAuth init failed: {e}")


@router.get("/youtube/callback")
async def youtube_callback(code: str = "", state: str = "", error: str = ""):
    if error or not code:
        return RedirectResponse(url=f"{APP_BASE_URL}/dashboard?yt_error={error or 'no_code'}")
    s = await db.oauth_states.find_one({"state": state})
    if not s:
        return RedirectResponse(url=f"{APP_BASE_URL}/dashboard?yt_error=invalid_state")
    user_id = s["user_id"]
    await db.oauth_states.delete_one({"state": state})
    try:
        token_dict = youtube_service.exchange_code(code)
    except Exception as e:
        logging.error(f"OAuth exchange failed: {e}")
        return RedirectResponse(url=f"{APP_BASE_URL}/dashboard?yt_error=exchange_failed")
    channel = youtube_service.get_channel_info(token_dict)
    await db.youtube_tokens.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id, **token_dict, "channel": channel,
            "updated_at": now_iso(),
        }},
        upsert=True,
    )
    return RedirectResponse(url=f"{APP_BASE_URL}/dashboard?yt_connected=1")


@router.delete("/youtube/disconnect")
async def youtube_disconnect(current=Depends(get_current_user)):
    await db.youtube_tokens.delete_one({"user_id": current["id"]})
    return {"ok": True}
