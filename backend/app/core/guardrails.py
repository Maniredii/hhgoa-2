import re
import numpy as np
from typing import List, Dict, Any, Tuple
from app.models.schemas import GuardrailResult, GuardrailDecision

def check_input_safety(query: str) -> GuardrailResult:
    """
    Detect harmful requests, illegal instructions, explicit unsafe content, 
    and prompt injection attempts.
    """
    if not query or len(query.strip()) < 2:
        return GuardrailResult(
            input_safe=False,
            decision=GuardrailDecision.BLOCK,
            reason="Query is empty or too short."
        )
        
    query_lower = query.lower()
    
    # 1. Prompt injection heuristics
    injection_keywords = [
        'ignore all previous instructions', 'system prompt', 
        'you are now', 'bypassing', 'override', 'forget everything'
    ]
    for kw in injection_keywords:
        if kw in query_lower:
            return GuardrailResult(
                input_safe=False,
                decision=GuardrailDecision.BLOCK,
                reason="Potential prompt injection attempt detected."
            )
            
    # 2. Harmful/illegal heuristics (very basic list for hackathon)
    unsafe_keywords = ['how to build a bomb', 'illegal', 'hack into']
    for kw in unsafe_keywords:
        if kw in query_lower:
            return GuardrailResult(
                input_safe=False,
                decision=GuardrailDecision.BLOCK,
                reason="Unsafe or illegal content detected."
            )
            
    return GuardrailResult(
        input_safe=True,
        decision=GuardrailDecision.ALLOW,
        reason="Input is safe."
    )

def check_context_sufficiency(reranked_chunks: List[Dict]) -> GuardrailResult:
    """
    Calculate top_score, mean_top_score, score_gap, number_of_relevant_chunks.
    If evidence is insufficient, return ABSTAIN.
    """
    if not reranked_chunks:
        return GuardrailResult(
            context_sufficient=False,
            on_topic=False,
            decision=GuardrailDecision.ABSTAIN,
            reason="No context retrieved."
        )

    # Use rerank_score if available, otherwise fallback to dense_score
    scores = [c.get('rerank_score', c.get('dense_score', 0.0)) for c in reranked_chunks]
    
    top_score = scores[0]
    # For cross-encoder, a score < 0.0 is often considered highly irrelevant.
    # We use -1.0 as a safe threshold for "off topic".
    
    if top_score < -1.0:
        return GuardrailResult(
            context_sufficient=False,
            on_topic=False,
            decision=GuardrailDecision.ABSTAIN,
            reason=f"Top score ({top_score:.2f}) is below relevance threshold."
        )
        
    # Calculate metrics
    mean_top_score = float(np.mean(scores[:3])) if len(scores) >= 3 else float(np.mean(scores))
    score_gap = top_score - scores[-1] if len(scores) > 1 else 0.0
    number_of_relevant_chunks = sum(1 for s in scores if s > -1.0)
    
    if number_of_relevant_chunks == 0 or mean_top_score < -1.5:
        return GuardrailResult(
            context_sufficient=False,
            on_topic=True, # It might be on topic but poorly supported
            decision=GuardrailDecision.ABSTAIN,
            reason=f"Insufficient evidence. Mean top score: {mean_top_score:.2f}"
        )
        
    return GuardrailResult(
        context_sufficient=True,
        on_topic=True,
        decision=GuardrailDecision.ALLOW,
        reason="Context is sufficient."
    )

def check_grounding_and_citations(answer: str, chunks: List[Dict]) -> GuardrailResult:
    """
    Every factual answer must reference retrieved source IDs.
    Returns RETRY if missing citations, ALLOW if valid.
    """
    if not answer or "I don't have enough evidence" in answer or "I am sorry" in answer:
        return GuardrailResult(
            grounded=True,
            citation_valid=True,
            decision=GuardrailDecision.ALLOW,
            reason="Abstention response bypasses grounding check."
        )

    # Check for citation format, e.g. [c1], [chunk_123]
    citation_pattern = r'\[(.*?)\]'
    citations_found = re.findall(citation_pattern, answer)
    
    valid_chunk_ids = {str(c.get('chunk_id')) for c in chunks}
    
    # We want at least one citation for a generated factual answer
    if not citations_found:
        return GuardrailResult(
            grounded=False,
            citation_valid=False,
            decision=GuardrailDecision.RETRY,
            reason="No citations found in the generated answer."
        )
        
    # Validate that the citations match actual chunks provided
    valid = any(c in valid_chunk_ids for c in citations_found)
    if not valid:
        return GuardrailResult(
            grounded=False,
            citation_valid=False,
            decision=GuardrailDecision.RETRY,
            reason="Citations found do not match retrieved chunks."
        )
        
    return GuardrailResult(
        grounded=True,
        citation_valid=True,
        decision=GuardrailDecision.ALLOW,
        reason="Answer is grounded and contains valid citations."
    )

def calculate_confidence(
    retrieval_relevance: float, 
    reranker_score: float, 
    context_coverage: float, 
    grounding_result: GuardrailResult
) -> float:
    """
    Calculate an answer confidence score (0.0 - 1.0) based on multiple metrics.
    """
    if grounding_result.decision != GuardrailDecision.ALLOW:
        return 0.0
        
    # Normalize scores (assuming reranker logits roughly -10 to +10)
    normalized_reranker = max(0.0, min(1.0, (reranker_score + 5) / 10.0))
    
    confidence = (
        0.3 * retrieval_relevance +
        0.4 * normalized_reranker +
        0.2 * context_coverage +
        0.1 * (1.0 if grounding_result.grounded else 0.0)
    )
    return min(1.0, max(0.0, confidence))
