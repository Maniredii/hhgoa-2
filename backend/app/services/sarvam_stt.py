import httpx
import logging
from typing import Tuple
from app.config import settings

logger = logging.getLogger(__name__)

async def transcribe_audio(audio_data: bytes, file_name: str = "audio.wav") -> Tuple[str, str]:
    """
    Transcribes audio using Sarvam API (saaras:v3).
    Returns (transcript, language_code).
    """
    if not settings.SARVAM_API_KEY:
        logger.warning("No Sarvam API Key provided. Returning mock transcript.")
        return "this is a mock transcript testing the rag system.", "en"

    url = "https://api.sarvam.ai/speech-to-text"
    headers = {
        "api-subscription-key": settings.SARVAM_API_KEY
    }
    
    # We pass the original file name/extension so Sarvam can detect format if needed.
    files = {
        "file": (file_name, audio_data, "audio/wav")
    }
    
    data = {
        "model": "saaras:v3"
        # mode defaults to 'transcribe' if omitted, or we can explicitly pass it if supported
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, files=files, data=data, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            
            transcript = result.get("transcript", "")
            language = result.get("language_code", "unknown")
            return transcript, language
    except Exception as e:
        logger.error(f"Error calling Sarvam API: {e}")
        raise e
