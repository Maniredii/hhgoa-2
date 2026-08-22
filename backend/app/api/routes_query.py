from fastapi import APIRouter
from app.models.schemas import QueryRequest, UnifiedRAGResponse
from app.core.orchestrator import RAGOrchestrator

router = APIRouter()

@router.post("/query", response_model=UnifiedRAGResponse)
async def query_endpoint(req: QueryRequest):
    orchestrator = RAGOrchestrator(raw_query=req.query, language=req.language)
    return await orchestrator.run()
