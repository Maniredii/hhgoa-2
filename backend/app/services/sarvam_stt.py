import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

async def transcribe_audio(audio_data: bytes) -> str:
    if not settings.SARVAM_API_KEY:
        logger.warning("No Sarvam API Key provided. Returning mock transcript.")
        return "this is a mock transcript testing the rag system."

    url = "https://api.sarvam.ai/speech-to-text"
    headers = {
        "api-subscription-key": settings.SARVAM_API_KEY
    }
    
    files = {
        "file": ("audio.wav", audio_data, "audio/wav")
    }
    
    data = {
        "model": "saaras:v3"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, files=files, data=data, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            return result.get("transcript", "")
    except Exception as e:
        logger.error(f"Error calling Sarvam API: {e}")
        return ""
