from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class STTRequest(BaseModel):
    # Depending on how frontend sends audio (e.g., base64 or multipart)
    audio_base64: Optional[str] = None

class QueryRequest(BaseModel):
    query: str
    language: Optional[str] = "en"

class SourceChunk(BaseModel):
    chunk_id: str
    text: str
    score: float

class LatencyMetrics(BaseModel):
    stt_ms: float = 0
    retrieval_ms: float = 0
    reranking_ms: float = 0
    generation_ms: float = 0
    total_ms: float = 0

class RAGResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    latency: LatencyMetrics
    is_abstained: bool = False
    error: Optional[str] = None
