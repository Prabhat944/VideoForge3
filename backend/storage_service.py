"""File-based media storage for scene images, voice MP3s, and rendered videos.

Replaces base64-in-Mongo for large assets. Files served via auth-protected
/api/media route in server.py. Paths are relative to MEDIA_ROOT.
"""
import os
import base64
import shutil
import uuid
from pathlib import Path
from typing import Optional

MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", "/app/backend/media"))
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)


def _project_dir(project_id: str, kind: str) -> Path:
    p = MEDIA_ROOT / kind / project_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_scene_image(project_id: str, scene_index: int, image_bytes: bytes) -> str:
    """Save scene image to disk. Returns relative path used in URL."""
    pdir = _project_dir(project_id, "scenes")
    fname = f"scene_{scene_index}.png"
    (pdir / fname).write_bytes(image_bytes)
    return f"scenes/{project_id}/{fname}"


def save_thumbnail(project_id: str, image_bytes: bytes) -> str:
    pdir = _project_dir(project_id, "thumbnails")
    fname = "thumb.png"
    (pdir / fname).write_bytes(image_bytes)
    return f"thumbnails/{project_id}/{fname}"


def save_voice(project_id: str, audio_bytes: bytes) -> str:
    pdir = _project_dir(project_id, "voices")
    fname = "voice.mp3"
    (pdir / fname).write_bytes(audio_bytes)
    return f"voices/{project_id}/{fname}"


def absolute_path(rel_path: str) -> Path:
    """Resolve a relative media path against MEDIA_ROOT, preventing path traversal."""
    p = (MEDIA_ROOT / rel_path).resolve()
    if not str(p).startswith(str(MEDIA_ROOT.resolve())):
        raise ValueError("Invalid media path")
    return p


def read_bytes(rel_path: str) -> bytes:
    return absolute_path(rel_path).read_bytes()


def read_b64(rel_path: str) -> str:
    return base64.b64encode(read_bytes(rel_path)).decode("utf-8")


def cleanup_project(project_id: str):
    for kind in ("scenes", "thumbnails", "voices"):
        p = MEDIA_ROOT / kind / project_id
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
