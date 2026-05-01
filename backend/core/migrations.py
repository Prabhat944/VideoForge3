"""One-time migration: move legacy base64 voice/thumbnail blobs from Mongo to filesystem.

Idempotent: skipped fields that already have audio_path / thumbnail_path are left alone.
Run as a startup hook.
"""
import base64
import logging
from core.db import db


import storage_service
from core.config import APP_BASE_URL


async def migrate_base64_to_fs():
    moved_voices = 0
    moved_thumbs = 0

    # Voices: still base64 in voice.audio_b64
    cursor = db.projects.find(
        {"voice.audio_b64": {"$exists": True, "$ne": None},
         "$or": [{"voice.audio_path": {"$exists": False}}, {"voice.audio_path": None}]},
        {"_id": 0, "id": 1, "voice": 1},
    )
    async for p in cursor:
        try:
            voice = p.get("voice") or {}
            b64 = voice.get("audio_b64")
            if not b64:
                continue
            voice_path = storage_service.save_voice(p["id"], base64.b64decode(b64))
            voice_url = f"{APP_BASE_URL}/api/media/{voice_path}"
            await db.projects.update_one(
                {"id": p["id"]},
                {"$set": {"voice.audio_path": voice_path, "voice.audio_url": voice_url},
                 "$unset": {"voice.audio_b64": ""}},
            )
            moved_voices += 1
        except Exception as e:
            logging.warning(f"voice migration failed for {p.get('id')}: {e}")

    # Thumbnails: still data:image/...;base64 inline in thumbnail_url
    cursor = db.projects.find(
        {"thumbnail_url": {"$regex": "^data:image"},
         "$or": [{"thumbnail_path": {"$exists": False}}, {"thumbnail_path": None}]},
        {"_id": 0, "id": 1, "thumbnail_url": 1},
    )
    async for p in cursor:
        try:
            data_url = p.get("thumbnail_url") or ""
            if "," not in data_url:
                continue
            b64 = data_url.split(",", 1)[1]
            thumb_path = storage_service.save_thumbnail(p["id"], base64.b64decode(b64))
            thumb_url = f"{APP_BASE_URL}/api/media/{thumb_path}"
            await db.projects.update_one(
                {"id": p["id"]},
                {"$set": {"thumbnail_path": thumb_path, "thumbnail_url": thumb_url}},
            )
            moved_thumbs += 1
        except Exception as e:
            logging.warning(f"thumb migration failed for {p.get('id')}: {e}")

    if moved_voices or moved_thumbs:
        logging.info(f"[migration] moved {moved_voices} voice MP3s and {moved_thumbs} thumbnails to filesystem.")
    return {"voices": moved_voices, "thumbnails": moved_thumbs}
