import time
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import VoiceTranscribeResponse
from app.services.sarvam_stt import transcribe_audio
from app.core.resiliency import with_retry, with_timeout

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_AUDIO_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".webm", ".wav", ".mp3", ".ogg", ".m4a"}

@with_retry(max_retries=2, base_delay=1.0)
@with_timeout(30.0)
async def resilient_transcribe(audio_data: bytes, filename: str):
    return await transcribe_audio(audio_data, file_name=filename)

@router.post("/voice/transcribe", response_model=VoiceTranscribeResponse)
async def voice_transcribe_endpoint(file: UploadFile = File(...)):
    start_stt = time.time()
    request_id = str(uuid.uuid4())
    
    # 1. Validation: Extension
    filename = file.filename or "audio.webm"
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported audio format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
        
    # 2. Validation: Read and size check
    audio_data = await file.read()
    if len(audio_data) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Audio file too large. Max size is 10MB.")
    if len(audio_data) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file.")
        
    # 3. Transcribe
    try:
        transcript, language = await resilient_transcribe(audio_data, filename)
    except Exception as e:
        logger.error(f"[Req: {request_id}] Transcription failed: {e}")
        raise HTTPException(status_code=502, detail="Speech-to-text service failed or timed out.")
        
    stt_ms = (time.time() - start_stt) * 1000
    
    if not transcript:
        raise HTTPException(status_code=422, detail="Could not understand audio.")
        
    return VoiceTranscribeResponse(
        transcript=transcript,
        language=language,
        request_id=request_id,
        latency_ms=stt_ms
    )
