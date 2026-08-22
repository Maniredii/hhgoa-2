import time
from fastapi import APIRouter, UploadFile, File
from app.models.schemas import RAGResponse, QueryRequest, LatencyMetrics
from app.services.sarvam_stt import transcribe_audio
from app.core.orchestrator import process_query

router = APIRouter()

@router.post("/voice", response_model=RAGResponse)
async def voice_endpoint(file: UploadFile = File(...)):
    # 1. Read audio
    audio_data = await file.read()
    
    # 2. STT
    start_stt = time.time()
    transcript = await transcribe_audio(audio_data)
    stt_ms = (time.time() - start_stt) * 1000
    
    if not transcript:
        metrics = LatencyMetrics(stt_ms=stt_ms, total_ms=stt_ms)
        return RAGResponse(
            answer="Could not transcribe audio.",
            sources=[],
            latency=metrics,
            is_abstained=True,
            error="STT failed"
        )
        
    # 3. Pass to query processor
    req = QueryRequest(query=transcript)
    response = await process_query(req)
    
    # Add STT latency to the response metrics
    response.latency.stt_ms = stt_ms
    response.latency.total_ms += stt_ms
    
    return response
