import pytest
from app.services.reranker import rerank

def test_rerank_no_candidates():
    res, latency = rerank("query", [])
    assert len(res) == 0

def test_rerank_with_candidates():
    candidates = [
        {"chunk_id": "c1", "text": "This is a test document"},
        {"chunk_id": "c2", "text": "Another one"}
    ]
    res, latency = rerank("query", candidates, top_k=2)
    assert len(res) == 2
