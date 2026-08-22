from fastapi import APIRouter
import time
import numpy as np
from app.models.schemas import QueryRequest
from app.core.orchestrator import process_query

router = APIRouter()

@router.post("/benchmark")
async def run_benchmark(iterations: int = 5):
    """
    Runs a benchmark test multiple times and returns P50, P70, and P100 latency for each step.
    For demonstration, we use a fixed query. In a real scenario, this would use a test set.
    """
    test_query = "What is the capital of India?"
    req = QueryRequest(query=test_query)
    
    latencies = {
        'retrieval_ms': [],
        'reranking_ms': [],
        'generation_ms': [],
        'total_ms': []
    }
    
    for _ in range(iterations):
        resp = await process_query(req)
        latencies['retrieval_ms'].append(resp.latency.retrieval_ms)
        latencies['reranking_ms'].append(resp.latency.reranking_ms)
        latencies['generation_ms'].append(resp.latency.generation_ms)
        latencies['total_ms'].append(resp.latency.total_ms)
        
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
