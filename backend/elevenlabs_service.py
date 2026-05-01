"""ElevenLabs TTS integration."""
import os
import base64
import httpx

BASE = "https://api.elevenlabs.io/v1"


def _key() -> str:
    return os.environ.get("ELEVENLABS_API_KEY", "")


# Curated premium voices (popular ElevenLabs default voices)
ELEVEN_VOICES = [
    {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "gender": "female", "description": "Calm narrative, premium"},
    {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "female", "description": "Strong, confident"},
    {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "gender": "female", "description": "Soft, warm storyteller"},
    {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "gender": "male", "description": "Well-rounded narrator"},
    {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "gender": "male", "description": "Crisp, professional"},
    {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "gender": "male", "description": "Deep, dramatic"},
    {"id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam", "gender": "male", "description": "Raspy, authentic"},
]


async def synthesize_b64(text: str, voice_id: str, speed: float = 1.0) -> str:
    api_key = _key()
    if not api_key:
        raise RuntimeError("ElevenLabs key not configured")
    url = f"{BASE}/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text[:4000],
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "speed": max(0.7, min(1.2, speed))},
    }
    async with httpx.AsyncClient(timeout=120.0) as cli:
        r = await cli.post(url, headers=headers, json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"ElevenLabs error {r.status_code}: {r.text[:200]}")
        return base64.b64encode(r.content).decode("utf-8")
