import time
import logging
from app.models.schemas import QueryRequest, RAGResponse, LatencyMetrics, SourceChunk
from app.services.hybrid_retriever import retrieve
from app.services.reranker import rerank
from app.services.generator import generate_answer
from app.core.guardrails import validate_query, validate_context

logger = logging.getLogger(__name__)

async def process_query(req: QueryRequest) -> RAGResponse:
    metrics = LatencyMetrics()
    start_total = time.time()
    
    # 1. Guardrail: Off-topic detection
    if not validate_query(req.query):
        metrics.total_ms = (time.time() - start_total) * 1000
        return RAGResponse(
            answer="I am sorry, but I can only answer questions related to the provided dataset.",
            sources=[],
            latency=metrics,
            is_abstained=True
        )

    # 2. Retrieval
    start_retrieval = time.time()
    candidates = retrieve(req.query, top_k=20)
    metrics.retrieval_ms = (time.time() - start_retrieval) * 1000
    
    # 3. Reranking
    start_rerank = time.time()
    reranked = rerank(req.query, candidates, top_k=5)
    metrics.reranking_ms = (time.time() - start_rerank) * 1000
    
    # 4. Guardrail: Context sufficiency
    if not validate_context(reranked):
        metrics.total_ms = (time.time() - start_total) * 1000
        return RAGResponse(
            answer="I do not have enough context to answer this question reliably.",
            sources=[],
            latency=metrics,
            is_abstained=True
        )

    # 5. Generation
    start_gen = time.time()
    answer = await generate_answer(req.query, reranked)
    metrics.generation_ms = (time.time() - start_gen) * 1000
    
    metrics.total_ms = (time.time() - start_total) * 1000
    
    sources = [SourceChunk(chunk_id=c['chunk_id'], text=c['text'], score=c['score']) for c in reranked]
    
    return RAGResponse(
        answer=answer,
        sources=sources,
        latency=metrics,
        is_abstained=False
    )
