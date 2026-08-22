from typing import List, Dict
from sentence_transformers import CrossEncoder

_cross_encoder = None

def get_reranker():
    global _cross_encoder
    if _cross_encoder is None:
        try:
            # We use a lightweight multilingual cross-encoder
            _cross_encoder = CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')
        except:
            pass
    return _cross_encoder

def rerank(query: str, candidates: List[Dict], top_k: int = 5) -> List[Dict]:
    if not candidates:
        return []
        
    model = get_reranker()
    if not model:
        # Fallback to returning original top_k if model fails to load
        return candidates[:top_k]

    # Cross encoder takes pairs: (query, text)
    pairs = [(query, c['text']) for c in candidates]
    scores = model.predict(pairs)
    
    # Attach scores and sort
    for idx, c in enumerate(candidates):
        c['score'] = float(scores[idx])
        
    # Sort by new cross-encoder score descending
    reranked = sorted(candidates, key=lambda x: x['score'], reverse=True)
    return reranked[:top_k]
