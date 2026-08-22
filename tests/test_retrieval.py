import pytest
from backend.app.services.hybrid_retriever import (
    _min_max_normalize,
    retrieve_hybrid,
    retrieve_rrf,
    _chunk_mapping
)
import backend.app.services.hybrid_retriever as hr

# Mock dependencies to avoid loading massive models/indexes in tests
class MockFAISS:
    def search(self, query_emb, top_k):
        # returns dummy distances and indices
        return [[0.9, 0.8, 0.7]], [[0, 1, 2]]

class MockEmbeddingModel:
    def encode(self, texts, normalize_embeddings=True):
        return [[0.1]*384]

class MockBM25:
    def get_scores(self, tokenized_query):
        import numpy as np
        return np.array([0.5, 1.5, 0.2, 0.8])

@pytest.fixture(autouse=True)
def mock_retrieval_globals(monkeypatch):
    # Mock the globals in hybrid_retriever
    monkeypatch.setattr(hr, '_faiss_index', MockFAISS())
    monkeypatch.setattr(hr, '_embedding_model', MockEmbeddingModel())
    monkeypatch.setattr(hr, '_bm25_index', MockBM25())
    
    mock_mapping = {
        'mapping': {
            'c1': {'text': 'Duplicate text', 'metadata': {}},
            'c2': {'text': 'Unique text', 'metadata': {}},
            'c3': {'text': 'Duplicate text', 'metadata': {}},
            'c4': {'text': 'Another text', 'metadata': {}}
        },
        'ids_list': ['c1', 'c2', 'c3', 'c4']
    }
    monkeypatch.setattr(hr, '_chunk_mapping', mock_mapping)
    
    # Disable load_indexes since we are mocking them
    monkeypatch.setattr(hr, 'load_indexes', lambda: None)

def test_min_max_normalize():
    scores = {'a': 10.0, 'b': 20.0, 'c': 15.0}
    norm = _min_max_normalize(scores)
    
    assert norm['a'] == 0.0
    assert norm['b'] == 1.0
    assert norm['c'] == 0.5

def test_min_max_normalize_constant():
    scores = {'a': 5.0, 'b': 5.0}
    norm = _min_max_normalize(scores)
    assert norm['a'] == 1.0
    assert norm['b'] == 1.0

def test_retrieve_hybrid_determinism_and_deduplication():
    # Calling retrieve_hybrid twice with same parameters should return exactly same ordered candidates
    candidates1 = retrieve_hybrid("test query", top_k=5)
    candidates2 = retrieve_hybrid("test query", top_k=5)
    
    assert len(candidates1) > 0
    assert len(candidates1) == len(candidates2)
    for c1, c2 in zip(candidates1, candidates2):
        assert c1['candidate_id'] == c2['candidate_id']
        assert c1['strategy'] == "HYBRID_WEIGHTED"

def test_retrieve_rrf_determinism():
    candidates1 = retrieve_rrf("test query", top_k=5)
    candidates2 = retrieve_rrf("test query", top_k=5)
    
    assert len(candidates1) > 0
    assert len(candidates1) == len(candidates2)
    for c1, c2 in zip(candidates1, candidates2):
        assert c1['candidate_id'] == c2['candidate_id']
        assert c1['strategy'] == "HYBRID_RRF"
        assert c1['rrf_score'] > 0.0

def test_duplicate_removal_logic():
    # If our system had logic to remove duplicate text, it would be here.
    # Currently hybrid_retriever removes duplicate chunk_ids.
    # Let's ensure candidate list doesn't have duplicate chunk_ids
    candidates = retrieve_hybrid("test query", top_k=10)
    seen_ids = set()
    for c in candidates:
        assert c['chunk_id'] not in seen_ids
        seen_ids.add(c['chunk_id'])
