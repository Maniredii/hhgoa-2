from fastapi import APIRouter, Response, status
import os
import time
from app.config import settings

router = APIRouter()

# Simple mocked metrics
START_TIME = time.time()
metrics_store = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0
}

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "VaaniRAG"}

@router.get("/ready")
async def readiness_check(response: Response):
    faiss_path = os.path.join(settings.INDEX_DIR, 'vector.faiss')
    bm25_path = os.path.join(settings.INDEX_DIR, 'bm25.pkl')
    
    if os.path.exists(faiss_path) and os.path.exists(bm25_path):
        return {"status": "ready"}
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "reason": "Indexes not found"}

@router.get("/metrics")
async def get_metrics():
    uptime = time.time() - START_TIME
    return {
        "uptime_seconds": uptime,
        "total_requests": metrics_store["total_requests"],
        "successful_requests": metrics_store["successful_requests"],
        "failed_requests": metrics_store["failed_requests"]
    }

