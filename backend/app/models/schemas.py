from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PipelineStage(str, Enum):
    RECEIVED = "received"
    VALIDATED = "validated"
    CLASSIFIED = "classified"
    RETRIEVING = "retrieving"
    RERANKING = "reranking"
    GENERATING = "generating"
    VALIDATING = "validating"
    COMPLETED = "completed"
    ABSTAINED = "abstained"
    FAILED = "failed"

class GuardrailDecision(str, Enum):
    ALLOW = "ALLOW"
    ABSTAIN = "ABSTAIN"
    BLOCK = "BLOCK"
    RETRY = "RETRY"

class GuardrailResult(BaseModel):
    input_safe: bool = True
    on_topic: bool = True
    context_sufficient: bool = True
    grounded: bool = True
    citation_valid: bool = True
    confidence: float = 1.0
    decision: GuardrailDecision = GuardrailDecision.ALLOW
    reason: str = ""

class STTRequest(BaseModel):
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

class PipelineContext(BaseModel):
    request_id: str
    timestamp: float
    raw_query: str
    normalized_query: Optional[str] = None
    language: Optional[str] = None
    query_type: Optional[str] = None
    retrieval_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    reranked_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    context: Optional[str] = None
    answer: Optional[str] = None
    citations: List[SourceChunk] = Field(default_factory=list)
    guardrail_results: GuardrailResult = Field(default_factory=GuardrailResult)
    latency: Dict[str, float] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    status: PipelineStage = PipelineStage.RECEIVED

class VoiceTranscribeResponse(BaseModel):
    transcript: str
    language: str
    request_id: str
    latency_ms: float

class UnifiedRAGResponse(BaseModel):
    request_id: str
    query: str
    answer: str
    sources: List[SourceChunk]
    language: str
    confidence: float
    guardrails: GuardrailResult
    latency: Dict[str, float]
    status: str
