"""Unified media storage supporting both AWS S3 (production) and local filesystem (development).

Storage Strategy:
- If AWS_S3_BUCKET is configured → use S3 for persistence
- If not configured → use local filesystem
- Always stores base64 in MongoDB as ultimate fallback for renders
"""
import os
import base64
import shutil
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")

# S3 configuration (optional - only used if configured)
AWS_S3_BUCKET = os.environ.get("AWS_S3_BUCKET", "")
AWS_S3_REGION = os.environ.get("AWS_S3_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# Local filesystem configuration (fallback)
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", "/app/backend/media"))
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

# Initialize S3 client if configured
s3_client = None
USE_S3 = bool(AWS_S3_BUCKET and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)

if USE_S3:
    try:
        import boto3
        from botocore.exceptions import ClientError
        s3_client = boto3.client(
            's3',
            region_name=AWS_S3_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        logging.info(f"S3 storage enabled: bucket={AWS_S3_BUCKET}, region={AWS_S3_REGION}")
    except Exception as e:
        logging.error(f"Failed to initialize S3 client: {e}")
        USE_S3 = False
        s3_client = None
else:
    logging.info("S3 storage not configured, using local filesystem")


def _project_dir(project_id: str, kind: str) -> Path:
    """Create local directory for project media (used when S3 is not available)."""
    p = MEDIA_ROOT / kind / project_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def _s3_key(rel_path: str) -> str:
    """Convert relative path to S3 key."""
    return f"media/{rel_path}"


def _upload_to_s3(rel_path: str, data_bytes: bytes, content_type: str = "application/octet-stream") -> bool:
    """Upload bytes to S3. Returns True if successful, False otherwise."""
    if not USE_S3 or not s3_client:
        return False
    
    try:
        s3_client.put_object(
            Bucket=AWS_S3_BUCKET,
            Key=_s3_key(rel_path),
            Body=data_bytes,
            ContentType=content_type
        )
        logging.info(f"Uploaded to S3: {rel_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to upload to S3: {rel_path}, error: {e}")
        return False


def _download_from_s3(rel_path: str) -> Optional[bytes]:
    """Download bytes from S3. Returns None if not found or error."""
    if not USE_S3 or not s3_client:
        return None
    
    try:
        response = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key=_s3_key(rel_path))
        return response['Body'].read()
    except Exception as e:
        logging.warning(f"Failed to download from S3: {rel_path}, error: {e}")
        return None


def save_scene_image(project_id: str, scene_index: int, image_bytes: bytes) -> str:
    """Save scene image. Returns relative path."""
    rel_path = f"scenes/{project_id}/scene_{scene_index}.png"
    
    # Try S3 first if available
    if USE_S3:
        _upload_to_s3(rel_path, image_bytes, "image/png")
    
    # Also save locally as cache/fallback
    pdir = _project_dir(project_id, "scenes")
    fname = f"scene_{scene_index}.png"
    (pdir / fname).write_bytes(image_bytes)
    
    return rel_path


def save_thumbnail(project_id: str, image_bytes: bytes) -> str:
    """Save thumbnail. Returns relative path."""
    rel_path = f"thumbnails/{project_id}/thumb.png"
    
    # Try S3 first if available
    if USE_S3:
        _upload_to_s3(rel_path, image_bytes, "image/png")
    
    # Also save locally as cache/fallback
    pdir = _project_dir(project_id, "thumbnails")
    fname = "thumb.png"
    (pdir / fname).write_bytes(image_bytes)
    
    return rel_path


def save_voice(project_id: str, audio_bytes: bytes) -> str:
    """Save voice audio. Returns relative path."""
    rel_path = f"voices/{project_id}/voice.mp3"
    
    # Try S3 first if available
    if USE_S3:
        _upload_to_s3(rel_path, audio_bytes, "audio/mpeg")
    
    # Also save locally as cache/fallback
    pdir = _project_dir(project_id, "voices")
    fname = "voice.mp3"
    (pdir / fname).write_bytes(audio_bytes)
    
    return rel_path


def absolute_path(rel_path: str) -> Path:
    """Resolve a relative media path against MEDIA_ROOT, preventing path traversal."""
    p = (MEDIA_ROOT / rel_path).resolve()
    if not str(p).startswith(str(MEDIA_ROOT.resolve())):
        raise ValueError("Invalid media path")
    return p


def read_bytes(rel_path: str) -> bytes:
    """Read bytes from storage. Tries S3 first, then local filesystem.
    
    Raises FileNotFoundError if not found in either location.
    """
    # Try S3 first if available
    if USE_S3:
        s3_bytes = _download_from_s3(rel_path)
        if s3_bytes is not None:
            return s3_bytes
        logging.warning(f"File not found in S3, trying local filesystem: {rel_path}")
    
    # Fall back to local filesystem
    local_path = absolute_path(rel_path)
    if local_path.exists():
        return local_path.read_bytes()
    
    # File not found in either location
    raise FileNotFoundError(f"Media file not found: {rel_path}")


def read_b64(rel_path: str) -> str:
    """Read file as base64. Tries S3 first, then local filesystem.
    
    Raises FileNotFoundError if not found.
    """
    return base64.b64encode(read_bytes(rel_path)).decode("utf-8")


def cleanup_project(project_id: str):
    """Clean up project media from both S3 and local filesystem."""
    # Clean up S3 if enabled
    if USE_S3 and s3_client:
        for kind in ("scenes", "thumbnails", "voices"):
            try:
                # List and delete all objects with this project_id prefix
                prefix = f"media/{kind}/{project_id}/"
                response = s3_client.list_objects_v2(Bucket=AWS_S3_BUCKET, Prefix=prefix)
                if 'Contents' in response:
                    for obj in response['Contents']:
                        s3_client.delete_object(Bucket=AWS_S3_BUCKET, Key=obj['Key'])
                        logging.info(f"Deleted from S3: {obj['Key']}")
            except Exception as e:
                logging.error(f"Failed to cleanup S3 for {kind}/{project_id}: {e}")
    
    # Clean up local filesystem
    for kind in ("scenes", "thumbnails", "voices"):
        p = MEDIA_ROOT / kind / project_id
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
