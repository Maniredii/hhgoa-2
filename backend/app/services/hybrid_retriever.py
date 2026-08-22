import os
import time
import faiss
import pickle
import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from app.config import settings

logger = logging.getLogger(__name__)

# Global state
_faiss_index = None
_bm25_index = None
_chunk_mapping = None
_embedding_model = None

def load_indexes():
    global _faiss_index, _bm25_index, _chunk_mapping, _embedding_model
    
    if _embedding_model is None:
        model_name = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        logger.info(f"Loading embedding model: {model_name}")
        try:
            _embedding_model = SentenceTransformer(model_name)
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            
    vector_path = os.path.join(settings.INDEX_DIR, 'vector.faiss')
    if os.path.exists(vector_path) and _faiss_index is None:
        logger.info("Loading FAISS index...")
        _faiss_index = faiss.read_index(vector_path)

    bm25_path = os.path.join(settings.INDEX_DIR, 'bm25.pkl')
    if os.path.exists(bm25_path) and _bm25_index is None:
        logger.info("Loading BM25 index...")
        with open(bm25_path, 'rb') as f:
            _bm25_index = pickle.load(f)

    mapping_path = os.path.join(settings.INDEX_DIR, 'chunk_mapping.pkl')
    if os.path.exists(mapping_path) and _chunk_mapping is None:
        logger.info("Loading chunk mappings...")
        with open(mapping_path, 'rb') as f:
            _chunk_mapping = pickle.load(f)

def tokenize(text: str) -> List[str]:
    import re
    return [t for t in re.split(r'\W+', text.lower()) if t]

def _build_candidate(chunk_id: str, score: float, strategy: str, exact_scores: Dict[str, float]) -> Dict:
    chunk_data = _chunk_mapping['mapping'].get(chunk_id, {})
    return {
        'candidate_id': f"{chunk_id}_{strategy}",
        'chunk_id': chunk_id,
        'text': chunk_data.get('text', ''),
        'dense_score': exact_scores.get('dense', 0.0),
        'bm25_score': exact_scores.get('bm25', 0.0),
        'rrf_score': exact_scores.get('rrf', 0.0),
        'strategy': strategy,
        'metadata': chunk_data.get('metadata', {})
    }

def retrieve_dense(query: str, top_k: int = 20) -> Dict[str, float]:
    start_time = time.time()
    if not _faiss_index or not _embedding_model:
        return {}, 0.0
        
    query_emb = _embedding_model.encode([query], normalize_embeddings=True)
    D, I = _faiss_index.search(query_emb, top_k * 2) # Get more to allow filtering
    
    results = {}
    ids_list = _chunk_mapping['ids_list']
    for score, idx in zip(D[0], I[0]):
        if idx != -1 and idx < len(ids_list):
            chunk_id = ids_list[idx]
            results[chunk_id] = float(score)
            
    return results, time.time() - start_time

def retrieve_bm25(query: str, top_k: int = 20) -> Dict[str, float]:
    start_time = time.time()
    if not _bm25_index:
        return {}, 0.0
        
    tokenized_query = tokenize(query)
    scores = _bm25_index.get_scores(tokenized_query)
    
    # Get top indices
    top_indices = scores.argsort()[-top_k*2:][::-1]
    
    results = {}
    ids_list = _chunk_mapping['ids_list']
    for idx in top_indices:
        if idx < len(ids_list):
            chunk_id = ids_list[idx]
            results[chunk_id] = float(scores[idx])
            
    return results, time.time() - start_time

def _min_max_normalize(scores: Dict[str, float]) -> Dict[str, float]:
    if not scores:
        return {}
    vals = list(scores.values())
    min_val, max_val = min(vals), max(vals)
    if max_val == min_val:
        return {k: 1.0 for k in scores}
    return {k: (v - min_val) / (max_val - min_val) for k, v in scores.items()}

def retrieve_hybrid(query: str, top_k: int = 20, dense_weight: float = 0.65, bm25_weight: float = 0.35) -> List[Dict]:
    load_indexes()
    
    dense_scores, dense_time = retrieve_dense(query, top_k)
    bm25_scores, bm25_time = retrieve_bm25(query, top_k)
    
    start_fusion = time.time()
    
    norm_dense = _min_max_normalize(dense_scores)
    norm_bm25 = _min_max_normalize(bm25_scores)
    
    all_keys = set(norm_dense.keys()).union(set(norm_bm25.keys()))
    
    fused_scores = {}
    for k in all_keys:
        d_score = norm_dense.get(k, 0.0)
        b_score = norm_bm25.get(k, 0.0)
        fused_scores[k] = (d_score * dense_weight) + (b_score * bm25_weight)
        
    # Sort and take top_k
    top_fused = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    # Format candidates
    candidates = []
    seen = set()
    for chunk_id, fused_score in top_fused:
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        
        # Simple duplicate text removal just in case multiple strategies emitted exact same text
        chunk_data = _chunk_mapping['mapping'].get(chunk_id, {})
        text = chunk_data.get('text', '')
        if not text:
            continue
            
        exact_scores = {
            'dense': dense_scores.get(chunk_id, 0.0),
            'bm25': bm25_scores.get(chunk_id, 0.0),
            'rrf': 0.0
        }
        
        cand = _build_candidate(chunk_id, fused_score, "HYBRID_WEIGHTED", exact_scores)
        candidates.append(cand)
        
    fusion_time = time.time() - start_fusion
    logger.info(f"Retrieval latency - Dense: {dense_time:.4f}s, BM25: {bm25_time:.4f}s, Fusion: {fusion_time:.4f}s")
    
    return candidates

def retrieve_rrf(query: str, top_k: int = 20, k: int = 60) -> List[Dict]:
    load_indexes()
    
    dense_scores, dense_time = retrieve_dense(query, top_k)
    bm25_scores, bm25_time = retrieve_bm25(query, top_k)
    
    start_fusion = time.time()
    
    rrf_scores = {}
    
    # Sort descending
    sorted_dense = sorted(dense_scores.items(), key=lambda x: x[1], reverse=True)
    sorted_bm25 = sorted(bm25_scores.items(), key=lambda x: x[1], reverse=True)
    
    for rank, (chunk_id, _) in enumerate(sorted_dense):
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
        
    for rank, (chunk_id, _) in enumerate(sorted_bm25):
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
        
    top_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    candidates = []
    seen = set()
    for chunk_id, rrf_score in top_rrf:
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        
        chunk_data = _chunk_mapping['mapping'].get(chunk_id, {})
        text = chunk_data.get('text', '')
        if not text:
            continue
            
        exact_scores = {
            'dense': dense_scores.get(chunk_id, 0.0),
            'bm25': bm25_scores.get(chunk_id, 0.0),
            'rrf': rrf_score
        }
        
        cand = _build_candidate(chunk_id, rrf_score, "HYBRID_RRF", exact_scores)
        candidates.append(cand)
        
    fusion_time = time.time() - start_fusion
    logger.info(f"RRF Retrieval latency - Dense: {dense_time:.4f}s, BM25: {bm25_time:.4f}s, Fusion: {fusion_time:.4f}s")
    
    return candidates
