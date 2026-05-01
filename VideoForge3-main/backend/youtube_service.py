"""YouTube Data API v3 OAuth + upload."""
import os
from typing import Optional
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def _env() -> dict:
    return {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        "redirect_uri": os.environ.get("GOOGLE_REDIRECT_URI", ""),
    }


def _client_config() -> dict:
    e = _env()
    return {
        "web": {
            "client_id": e["client_id"],
            "client_secret": e["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [e["redirect_uri"]],
        }
    }


def auth_url(state: str) -> str:
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES, state=state)
    flow.redirect_uri = _env()["redirect_uri"]
    url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
    return url


def exchange_code(code: str) -> dict:
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES)
    flow.redirect_uri = _env()["redirect_uri"]
    flow.fetch_token(code=code)
    creds = flow.credentials
    return {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
        "scopes": creds.scopes,
    }


def _build_creds(token_dict: dict) -> Credentials:
    e = _env()
    return Credentials(
        token=token_dict.get("access_token"),
        refresh_token=token_dict.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=e["client_id"],
        client_secret=e["client_secret"],
        scopes=token_dict.get("scopes", SCOPES),
    )


def get_channel_info(token_dict: dict) -> Optional[dict]:
    try:
        creds = _build_creds(token_dict)
        if not creds.valid and creds.refresh_token:
            creds.refresh(GoogleRequest())
        yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
        resp = yt.channels().list(part="snippet,statistics", mine=True).execute()
        items = resp.get("items", [])
        if not items:
            return None
        it = items[0]
        return {
            "channel_id": it["id"],
            "title": it["snippet"]["title"],
            "thumbnail": it["snippet"]["thumbnails"]["default"]["url"],
            "subscribers": int(it["statistics"].get("subscriberCount", 0)),
            "videos": int(it["statistics"].get("videoCount", 0)),
            "views": int(it["statistics"].get("viewCount", 0)),
        }
    except Exception:
        return None


def get_video_stats(token_dict: dict, video_ids: list) -> dict:
    """Returns {video_id: {views, likes, comments}} via YouTube Data API."""
    if not video_ids:
        return {}
    try:
        creds = _build_creds(token_dict)
        if not creds.valid and creds.refresh_token:
            creds.refresh(GoogleRequest())
        yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
        out = {}
        # API allows 50 ids per call
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i:i + 50]
            resp = yt.videos().list(part="statistics,snippet", id=",".join(chunk)).execute()
            for item in resp.get("items", []):
                stats = item.get("statistics", {})
                out[item["id"]] = {
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                    "title": item["snippet"]["title"],
                    "published_at": item["snippet"]["publishedAt"],
                }
        return out
    except Exception:
        return {}


def get_analytics_report(token_dict: dict, days: int = 14) -> Optional[dict]:
    """Calls YouTube Analytics API for channel-wide metrics over the last N days."""
    try:
        from datetime import datetime, timedelta
        creds = _build_creds(token_dict)
        if not creds.valid and creds.refresh_token:
            creds.refresh(GoogleRequest())
        ya = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
        end = datetime.utcnow().date()
        start = end - timedelta(days=days)
        resp = ya.reports().query(
            ids="channel==MINE",
            startDate=start.isoformat(),
            endDate=end.isoformat(),
            metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained",
            dimensions="day",
        ).execute()
        rows = resp.get("rows", []) or []
        series = []
        for r in rows:
            series.append({
                "date": r[0][5:],  # MM-DD
                "views": int(r[1] or 0),
                "watch_time": int(r[2] or 0),
                "avg_duration": int(r[3] or 0),
                "subs_gained": int(r[4] or 0),
            })
        return {"series": series}
    except Exception:
        return None


def upload_video(
    token_dict: dict,
    file_path: str,
    title: str,
    description: str,
    tags: list,
    privacy: str = "public",
    category_id: str = "22",
    publish_at: Optional[str] = None,
    thumbnail_path: Optional[str] = None,
) -> dict:
    creds = _build_creds(token_dict)
    if not creds.valid and creds.refresh_token:
        creds.refresh(GoogleRequest())
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)

    status = {"privacyStatus": "private" if publish_at else privacy, "selfDeclaredMadeForKids": False}
    if publish_at:
        status["publishAt"] = publish_at  # ISO 8601 RFC3339

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:15],
            "categoryId": category_id,
        },
        "status": status,
    }

    media = MediaFileUpload(file_path, mimetype="video/mp4", resumable=True, chunksize=-1)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = req.next_chunk()
    video_id = response["id"]

    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            yt.thumbnails().set(videoId=video_id, media_body=thumbnail_path).execute()
        except Exception:
            pass

    return {
        "video_id": video_id,
        "url": f"https://youtube.com/watch?v={video_id}",
        "scheduled": bool(publish_at),
    }
