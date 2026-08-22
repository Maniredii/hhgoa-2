from typing import List, Dict

def validate_query(query: str) -> bool:
    """
    Check if the query is out-of-topic or malicious.
    For this hackathon implementation, we use a simple keyword check.
    In production, this could be a lightweight classifier.
    """
    if not query or len(query.strip()) < 2:
        return False
        
    off_topic_keywords = ['ignore all previous instructions', 'write a poem', 'recipe for']
    query_lower = query.lower()
    
    for kw in off_topic_keywords:
        if kw in query_lower:
            return False
            
    return True

def validate_context(reranked_chunks: List[Dict]) -> bool:
    """
    Ensure we have sufficient context to answer the query.
    If the best chunk has a very low score, we abstain.
    """
    if not reranked_chunks:
        return False
        
    # Check if the top chunk score is above a threshold
    # Since we are using a cross-encoder, scores are typically logits.
    # Let's say if it's < -2.0, it's very unrelated.
    best_score = reranked_chunks[0].get('score', -999)
    if best_score < -5.0: # Configurable threshold
        return False
        
    return True
