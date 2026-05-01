"""TTS voice presets for OpenAI standard, OpenAI HD, and ElevenLabs (provider+id)."""

VOICES = [
    {"id": "alloy", "name": "Alloy", "gender": "neutral", "description": "Balanced, clear narrator", "provider": "openai", "tier": "free"},
    {"id": "echo", "name": "Echo", "gender": "male", "description": "Warm masculine voice", "provider": "openai", "tier": "free"},
    {"id": "fable", "name": "Fable", "gender": "neutral", "description": "Storyteller, expressive", "provider": "openai", "tier": "free"},
    {"id": "onyx", "name": "Onyx", "gender": "male", "description": "Deep authoritative", "provider": "openai", "tier": "free"},
    {"id": "nova", "name": "Nova", "gender": "female", "description": "Bright energetic female", "provider": "openai", "tier": "free"},
    {"id": "shimmer", "name": "Shimmer", "gender": "female", "description": "Smooth calming female", "provider": "openai", "tier": "free"},
]

HD_VOICES = [
    {"id": "hd_alloy", "name": "Alloy HD", "gender": "neutral", "description": "Studio HD, balanced", "provider": "openai_hd", "tier": "premium", "base": "alloy"},
    {"id": "hd_echo", "name": "Echo HD", "gender": "male", "description": "Studio HD, warm masculine", "provider": "openai_hd", "tier": "premium", "base": "echo"},
    {"id": "hd_fable", "name": "Fable HD", "gender": "neutral", "description": "Studio HD, storyteller", "provider": "openai_hd", "tier": "premium", "base": "fable"},
    {"id": "hd_onyx", "name": "Onyx HD", "gender": "male", "description": "Studio HD, dramatic depth", "provider": "openai_hd", "tier": "premium", "base": "onyx"},
    {"id": "hd_nova", "name": "Nova HD", "gender": "female", "description": "Studio HD, energetic female", "provider": "openai_hd", "tier": "premium", "base": "nova"},
    {"id": "hd_shimmer", "name": "Shimmer HD", "gender": "female", "description": "Studio HD, smooth female", "provider": "openai_hd", "tier": "premium", "base": "shimmer"},
]
