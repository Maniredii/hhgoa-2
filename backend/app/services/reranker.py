import time
import logging
import concurrent.futures
from typing import List, Dict, Tuple
from sentence_transformers import CrossEncoder
from app.config import settings

logger = logging.getLogger(__name__)

_cross_encoder = None

def get_reranker():
    global _cross_encoder
    if _cross_encoder is None:
        try:
            logger.info(f"Loading reranker model: {settings.RERANKER_MODEL}")
            _cross_encoder = CrossEncoder(settings.RERANKER_MODEL)
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            _cross_encoder = None
    return _cross_encoder

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

def _predict_scores(model, pairs):
    return model.predict(pairs)

def rerank(query: str, candidates: List[Dict], top_k: int = 5, timeout: float = 3.0) -> Tuple[List[Dict], float]:
    """
    Reranks candidates using a cross-encoder model.
    Returns (top_candidates, reranking_latency_ms).
    """
    start_time = time.time()
    
    if not candidates:
        logger.warning("No candidates provided for reranking.")
        return [], 0.0

    model = get_reranker()
    
    if not model:
        logger.warning("Reranker model unavailable. Falling back to hybrid ranking.")
        latency_ms = (time.time() - start_time) * 1000
        return candidates[:top_k], latency_ms

    pairs = [(query, c['text']) for c in candidates]
    
    try:
        future = _executor.submit(_predict_scores, model, pairs)
        scores = future.result(timeout=timeout)
            
        for idx, c in enumerate(candidates):
            c['rerank_score'] = float(scores[idx])
            
        reranked = sorted(candidates, key=lambda x: x.get('rerank_score', 0.0), reverse=True)
        latency_ms = (time.time() - start_time) * 1000
        return reranked[:top_k], latency_ms
        
    except concurrent.futures.TimeoutError:
        logger.error(f"Reranking timed out after {timeout} seconds. Falling back to hybrid ranking.")
        latency_ms = (time.time() - start_time) * 1000
        return candidates[:top_k], latency_ms
    except Exception as e:
        logger.error(f"Reranking failed with error: {e}. Falling back to hybrid ranking.")
        latency_ms = (time.time() - start_time) * 1000
        return candidates[:top_k], latency_ms
