import json
import logging
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import jwt as pyjwt
from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials

from emergentintegrations.llm.chat import LlmChat, UserMessage

import trends_service

from core.db import db
from core.config import EMERGENT_LLM_KEY, JWT_SECRET, JWT_ALGORITHM
from core.deps import security, now_iso

router = APIRouter(tags=["trends"])

TREND_NICHES = {
    "finance": ["Investing", "Stocks", "Crypto", "Personal Finance", "Business"],
    "horror": ["Dark stories", "Paranormal", "True crime", "Urban legends"],
    "motivation": ["Self improvement", "Productivity", "Mindset"],
    "education": ["Science", "History", "Math tricks", "Language"],
    "facts": ["Mind blowing facts", "Did you know", "Top 10 lists"],
    "general": ["Trending", "Viral", "Popular"],
}


@router.get("/trends")
async def get_trends(
    niche: str = "general",
    source: str = "ai",
    creds_optional: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    cache_key = f"{niche}:{source}"
    cached = await db.trends_cache.find_one({"key": cache_key}, {"_id": 0})
    if cached:
        cached_at = datetime.fromisoformat(cached["cached_at"])
        if datetime.now(timezone.utc) - cached_at < timedelta(hours=6):
            return {"trends": cached["trends"], "source": source, "cached": True}

    trends = []

    if source == "reddit":
        try:
            trends = await trends_service.fetch_reddit_trends(niche, limit=8)
        except Exception as e:
            logging.warning(f"Reddit trends failed: {e}")

    elif source == "youtube" and creds_optional:
        try:
            payload = pyjwt.decode(creds_optional.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            yt_token = await db.youtube_tokens.find_one({"user_id": user_id}, {"_id": 0})
            if yt_token:
                yt_trends = await trends_service.fetch_youtube_trends(yt_token, "US", 8)
                if yt_trends:
                    trends = yt_trends
        except Exception as e:
            logging.warning(f"YouTube trends failed: {e}")

    elif source == "google_trends":
        try:
            gt = await trends_service.fetch_google_trends(niche, limit=8)
            if gt:
                trends = gt
        except Exception as e:
            logging.warning(f"Google Trends failed: {e}")

    if not trends and source == "ai" and EMERGENT_LLM_KEY:
        try:
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"trends-{uuid.uuid4()}",
                system_message="You are a YouTube trend analyst. Return ONLY valid JSON.",
            ).with_model("openai", "gpt-4o-mini")
            sub_topics = TREND_NICHES.get(niche, TREND_NICHES["general"])
            prompt = (
                f"Generate 8 trending viral YouTube video ideas for the niche '{niche}' "
                f"covering sub-topics: {', '.join(sub_topics)}. "
                "For each return: title (catchy), description (1 sentence), viral_score (0-100), "
                "competition (low/medium/high), suggested_tags (3-5 tags array), platform "
                "(one of youtube/reddit/google_trends), category (one of the sub-topics). "
                'Return JSON: {"trends": [{...}]}'
            )
            resp = await chat.send_message(UserMessage(text=prompt))
            text = resp if isinstance(resp, str) else str(resp)
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                data = json.loads(match.group())
                trends = data.get("trends", [])
        except Exception as e:
            logging.warning(f"AI trends fallback: {e}")

    if not trends:
        sub_topics = TREND_NICHES.get(niche, TREND_NICHES["general"])
        trends = [
            {
                "title": f"{topic}: 7 Things You Didn't Know",
                "description": f"Surprising insights about {topic} every viewer needs.",
                "viral_score": 70 + (i * 3) % 25,
                "competition": ["low", "medium", "high"][i % 3],
                "suggested_tags": [topic.lower(), "viral", "trending", niche],
                "platform": ["youtube", "reddit", "google_trends"][i % 3],
                "category": topic,
            }
            for i, topic in enumerate(sub_topics * 2)
        ][:8]

    await db.trends_cache.update_one(
        {"key": cache_key},
        {"$set": {"key": cache_key, "trends": trends, "cached_at": now_iso()}},
        upsert=True,
    )
    return {"trends": trends, "source": source, "cached": False}
