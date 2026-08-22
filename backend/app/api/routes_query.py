from fastapi import APIRouter
from app.models.schemas import QueryRequest, RAGResponse
from app.core.orchestrator import process_query

router = APIRouter()

@router.post("/query", response_model=RAGResponse)
async def query_endpoint(req: QueryRequest):
    return await process_query(req)
