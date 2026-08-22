from fastapi import APIRouter
import time
import numpy as np
from app.models.schemas import QueryRequest
from app.core.orchestrator import RAGOrchestrator

router = APIRouter()

@router.post("/benchmark")
async def run_benchmark(iterations: int = 5):
    """
    Runs a benchmark test multiple times and returns P50, P70, and P100 latency for each step.
    For demonstration, we use a fixed query. In a real scenario, this would use a test set.
    """
    test_query = "What is the capital of India?"
    
    latencies = {
        'retrieval_ms': [],
        'reranking_ms': [],
        'generation_ms': [],
        'total_ms': []
    }
    
    for _ in range(iterations):
        orchestrator = RAGOrchestrator(raw_query=test_query)
        resp = await orchestrator.run()
        latencies['retrieval_ms'].append(resp.latency.get('faiss_ms', 0) + resp.latency.get('bm25_ms', 0) + resp.latency.get('fusion_ms', 0))
        latencies['reranking_ms'].append(resp.latency.get('reranking_ms', 0))
        latencies['generation_ms'].append(resp.latency.get('generation_ms', 0))
        latencies['total_ms'].append(resp.latency.get('total_pipeline_ms', 0))
        
    results = {}
    for k, v in latencies.items():
        if v:
            results[k] = {
                'p50': np.percentile(v, 50),
                'p70': np.percentile(v, 70),
                'p100': np.max(v)
            }
            
    return {
        "iterations": iterations,
        "query": test_query,
        "metrics": results
    }
