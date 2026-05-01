"""Static niche templates pre-tuned for common YouTube verticals."""

NICHE_TEMPLATES = {
    "finance_money_tips": {
        "id": "finance_money_tips",
        "name": "Money Tips Reel",
        "niche": "finance",
        "description": "Punchy 5-tip listicle on personal finance — proven CTR pattern.",
        "duration_seconds": 60, "tone": "engaging", "style": "listicle",
        "thumbnail_style": "Bold text, money-green and gold, dollar bills, dramatic close-up of cash, high contrast",
        "voice": "hd_onyx",
        "topic_template": "5 money habits that quietly made me rich",
        "default_tags": ["finance", "money", "investing", "wealth", "tips"],
    },
    "finance_market_news": {
        "id": "finance_market_news",
        "name": "Market News Brief",
        "niche": "finance",
        "description": "Quick analysis of a trending stock/macro event.",
        "duration_seconds": 90, "tone": "educational", "style": "documentary",
        "thumbnail_style": "Stock chart background, red/green candles, breaking news banner",
        "voice": "hd_echo",
        "topic_template": "What just happened to {STOCK} — a 90-second breakdown",
        "default_tags": ["stocks", "markets", "news", "investing"],
    },
    "horror_dark_story": {
        "id": "horror_dark_story",
        "name": "Dark Story",
        "niche": "horror",
        "description": "First-person creepy story with cliffhanger hook.",
        "duration_seconds": 120, "tone": "scary", "style": "storytelling",
        "thumbnail_style": "Dark forest, fog, single eerie figure, deep blue and red palette, cinematic horror lighting",
        "voice": "hd_onyx",
        "topic_template": "I was alone in the woods when I heard footsteps...",
        "default_tags": ["horror", "scary", "darkstories", "paranormal", "mystery"],
    },
    "horror_unsolved": {
        "id": "horror_unsolved",
        "name": "Unsolved Mystery",
        "niche": "horror",
        "description": "Documentary-style cold case or unexplained event.",
        "duration_seconds": 180, "tone": "dramatic", "style": "documentary",
        "thumbnail_style": "Vintage photo, red question mark, evidence board aesthetic, sepia and red",
        "voice": "hd_fable",
        "topic_template": "The case of {NAME} — a mystery that's never been solved",
        "default_tags": ["unsolved", "mystery", "truecrime", "creepy"],
    },
    "motivation_success": {
        "id": "motivation_success",
        "name": "Success Mindset",
        "niche": "motivation",
        "description": "High-energy speech about discipline / hustle / mindset.",
        "duration_seconds": 60, "tone": "inspiring", "style": "storytelling",
        "thumbnail_style": "Dramatic sunrise, silhouetted athlete, gold and orange tones, bold lighting",
        "voice": "hd_onyx",
        "topic_template": "The 1% who succeed do this every morning",
        "default_tags": ["motivation", "success", "mindset", "discipline", "hustle"],
    },
    "motivation_morning": {
        "id": "motivation_morning",
        "name": "Morning Routine",
        "niche": "motivation",
        "description": "5-step morning routine of high performers.",
        "duration_seconds": 75, "tone": "inspiring", "style": "listicle",
        "thumbnail_style": "Sunrise over mountains, productivity dashboard, warm orange tones",
        "voice": "hd_nova",
        "topic_template": "The morning routine that 10x'd my productivity",
        "default_tags": ["morningroutine", "productivity", "habits", "motivation"],
    },
    "facts_did_you_know": {
        "id": "facts_did_you_know",
        "name": "Did You Know?",
        "niche": "facts",
        "description": "Mind-blowing trivia rapid-fire with snappy hook.",
        "duration_seconds": 45, "tone": "engaging", "style": "listicle",
        "thumbnail_style": "Bright pop colors, surprised facial expression, bold yellow and red, exclamation mark",
        "voice": "hd_nova",
        "topic_template": "5 facts that will break your brain",
        "default_tags": ["facts", "didyouknow", "interesting", "education", "viral"],
    },
    "facts_history": {
        "id": "facts_history",
        "name": "Hidden History",
        "niche": "facts",
        "description": "Surprising historical events told as a tight story.",
        "duration_seconds": 90, "tone": "educational", "style": "documentary",
        "thumbnail_style": "Sepia-toned vintage photo collage, parchment background, gold border",
        "voice": "hd_fable",
        "topic_template": "The forgotten event that changed history forever",
        "default_tags": ["history", "facts", "education", "interesting"],
    },
}


# Helpers used by both the templates router and the wizard ingestion path.
def get_template(template_id: str):
    return NICHE_TEMPLATES.get(template_id)


def list_templates(niche: str = None):
    items = list(NICHE_TEMPLATES.values())
    if niche:
        items = [t for t in items if t["niche"] == niche]
    return items
