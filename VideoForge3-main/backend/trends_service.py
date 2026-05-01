"""Real trends sources: Reddit (anon JSON or OAuth), YouTube trending (OAuth required).

If REDDIT_CLIENT_ID/SECRET are set we use the official OAuth `client_credentials`
(installed-app/script-app) flow against oauth.reddit.com — this bypasses the cloud-IP
block that hits the anonymous www.reddit.com JSON endpoints.
"""
import os
import time
from typing import List, Optional
import httpx

REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "VideoForge/1.0 (trend-scraper)")

NICHE_SUBREDDITS = {
    "finance": ["personalfinance", "stocks", "investing", "Bogleheads"],
    "horror": ["nosleep", "TrueScaryStories", "Paranormal", "UnresolvedMysteries"],
    "motivation": ["GetMotivated", "selfimprovement", "DecidingToBeBetter"],
    "education": ["explainlikeimfive", "todayilearned", "AskHistorians"],
    "facts": ["todayilearned", "Damnthatsinteresting", "interestingasfuck"],
    "general": ["popular", "all", "AskReddit"],
}

# Cached app-only OAuth token for Reddit
_reddit_token_cache: dict = {"token": None, "expires_at": 0}


async def _reddit_app_token() -> Optional[str]:
    """Get + cache a Reddit application-only OAuth token (client_credentials)."""
    cid = os.environ.get("REDDIT_CLIENT_ID", "").strip()
    secret = os.environ.get("REDDIT_CLIENT_SECRET", "").strip()
    if not cid or not secret:
        return None

    now = int(time.time())
    if _reddit_token_cache["token"] and _reddit_token_cache["expires_at"] > now + 30:
        return _reddit_token_cache["token"]

    async with httpx.AsyncClient(timeout=15.0) as cli:
        try:
            r = await cli.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=(cid, secret),
                data={"grant_type": "client_credentials"},
                headers={"User-Agent": REDDIT_USER_AGENT},
            )
            if r.status_code != 200:
                return None
            data = r.json()
            tok = data.get("access_token")
            if not tok:
                return None
            _reddit_token_cache["token"] = tok
            _reddit_token_cache["expires_at"] = now + int(data.get("expires_in", 3600))
            return tok
        except Exception:
            return None


def _normalise_listing(post: dict, sub: str, niche: str) -> Optional[dict]:
    if post.get("stickied") or post.get("over_18"):
        return None
    title = post.get("title", "")
    if not title:
        return None
    score = int(post.get("score", 0))
    viral = min(100, max(40, int(40 + (score / 1000) * 30)))
    competition = "low" if score < 1000 else "medium" if score < 10000 else "high"
    return {
        "title": title[:120],
        "description": (post.get("selftext", "")[:140] or f"Trending on r/{sub}"),
        "viral_score": viral,
        "competition": competition,
        "suggested_tags": [niche, sub, "trending", "viral"],
        "platform": "reddit",
        "category": sub,
        "source_url": f"https://reddit.com{post.get('permalink', '')}",
        "score": score,
    }


async def fetch_reddit_trends(niche: str, limit: int = 8) -> List[dict]:
    subs = NICHE_SUBREDDITS.get(niche, NICHE_SUBREDDITS["general"])
    headers = {"User-Agent": REDDIT_USER_AGENT}
    out: List[dict] = []

    token = await _reddit_app_token()
    if token:
        # OAuth — bypasses cloud IP block
        headers["Authorization"] = f"Bearer {token}"
        base = "https://oauth.reddit.com"
    else:
        base = "https://www.reddit.com"

    async with httpx.AsyncClient(timeout=15.0, headers=headers) as cli:
        for sub in subs[:3]:
            try:
                r = await cli.get(f"{base}/r/{sub}/hot.json?limit=10")
                if r.status_code != 200:
                    continue
                data = r.json()
                for child in data.get("data", {}).get("children", []):
                    item = _normalise_listing(child.get("data", {}) or {}, sub, niche)
                    if item:
                        out.append(item)
            except Exception:
                continue

    seen = set()
    deduped = []
    for t in out:
        if t["title"] in seen:
            continue
        seen.add(t["title"])
        deduped.append(t)
    deduped.sort(key=lambda x: -x["viral_score"])
    return deduped[:limit]


async def fetch_youtube_trends(token_dict: dict, region_code: str = "US", limit: int = 8) -> Optional[List[dict]]:
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request as GoogleRequest
        from googleapiclient.discovery import build
        creds = Credentials(
            token=token_dict.get("access_token"),
            refresh_token=token_dict.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.environ.get("GOOGLE_CLIENT_ID"),
            client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
            scopes=token_dict.get("scopes"),
        )
        if not creds.valid and creds.refresh_token:
            creds.refresh(GoogleRequest())
        yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
        resp = yt.videos().list(
            part="snippet,statistics", chart="mostPopular",
            regionCode=region_code, maxResults=min(20, limit),
        ).execute()
        out = []
        for item in resp.get("items", []):
            sn = item["snippet"]
            st = item.get("statistics", {})
            views = int(st.get("viewCount", 0))
            viral = min(100, max(50, int(50 + (views / 1_000_000) * 8)))
            out.append({
                "title": sn["title"][:120],
                "description": sn.get("description", "")[:140] or f"Trending on YouTube · {sn.get('channelTitle', '')}",
                "viral_score": viral,
                "competition": "high" if views > 1_000_000 else "medium",
                "suggested_tags": (sn.get("tags") or [sn.get("channelTitle", "")])[:5],
                "platform": "youtube",
                "category": sn.get("categoryId", ""),
                "source_url": f"https://youtube.com/watch?v={item['id']}",
            })
        return out[:limit]
    except Exception:
        return None


# Niche → seed keywords used to query Google Trends rising/related queries.
NICHE_KEYWORDS = {
    "finance": ["personal finance", "stock market", "investing", "crypto"],
    "horror": ["horror story", "scary story", "true crime", "paranormal"],
    "motivation": ["motivation", "self improvement", "morning routine", "productivity"],
    "education": ["explained", "how it works", "history facts"],
    "facts": ["mind blowing facts", "did you know", "interesting facts"],
    "general": ["trending now", "viral"],
}


async def fetch_google_trends(niche: str, limit: int = 8) -> List[dict]:
    """Return rising / related Google searches via pytrends. Sync lib → run in thread.

    pytrends has no public API key; it relies on a public Google endpoint that is
    rate-limited but usually works from cloud IPs.
    """
    import asyncio

    def _run() -> List[dict]:
        try:
            from pytrends.request import TrendReq
        except Exception:
            return []
        keywords = NICHE_KEYWORDS.get(niche, NICHE_KEYWORDS["general"])
        out: List[dict] = []
        try:
            py = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
            for kw in keywords[:3]:
                try:
                    py.build_payload([kw], timeframe="now 7-d", geo="")
                    related = py.related_queries() or {}
                    bucket = related.get(kw) or {}
                    rising = bucket.get("rising")
                    top = bucket.get("top")
                    rows = []
                    if rising is not None and not rising.empty:
                        rows.extend(rising.head(6).to_dict("records"))
                    elif top is not None and not top.empty:
                        rows.extend(top.head(6).to_dict("records"))
                    for r in rows:
                        title = str(r.get("query", "")).strip()
                        if not title:
                            continue
                        try:
                            growth = int(r.get("value", 0) or 0)
                        except Exception:
                            growth = 0
                        # Rising values can be huge ("Breakout" = +5000) → log-flatten.
                        if growth >= 5000:
                            viral = 95
                        elif growth >= 1000:
                            viral = 88
                        elif growth >= 200:
                            viral = 78
                        else:
                            viral = 60 + min(15, growth // 20)
                        competition = "low" if growth < 200 else "medium" if growth < 1500 else "high"
                        out.append({
                            "title": title[:120],
                            "description": f"Rising query for '{kw}' · {growth}+ growth",
                            "viral_score": viral,
                            "competition": competition,
                            "suggested_tags": [niche, kw, "trending", "google"],
                            "platform": "google_trends",
                            "category": kw,
                            "source_url": f"https://trends.google.com/trends/explore?q={title.replace(' ', '+')}",
                            "growth": growth,
                        })
                except Exception:
                    continue
        except Exception:
            return []
        # Dedupe by title and return top N by viral_score
        seen = set()
        deduped = []
        for t in out:
            if t["title"].lower() in seen:
                continue
            seen.add(t["title"].lower())
            deduped.append(t)
        deduped.sort(key=lambda x: -x["viral_score"])
        return deduped[:limit]

    return await asyncio.to_thread(_run)
