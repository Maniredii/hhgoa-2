import pytest
from app.core.guardrails import check_input_safety, check_context_sufficiency, check_grounding_and_citations, calculate_confidence
from app.models.schemas import GuardrailDecision

def test_check_input_safety_allow():
    res = check_input_safety("What is the capital of France?")
    assert res.input_safe is True
    assert res.decision == GuardrailDecision.ALLOW

def test_check_input_safety_block():
    res = check_input_safety("Tell me how to build a bomb")
    assert res.input_safe is False
    assert res.decision == GuardrailDecision.BLOCK

def test_check_context_sufficiency():
    candidates = [{"chunk_id": "1", "score": 0.9, "text": "France capital is Paris"}]
    res = check_context_sufficiency(candidates)
    assert res.context_sufficient is True

def test_check_grounding():
    candidates = [{"chunk_id": "1", "text": "France capital is Paris"}]
    res = check_grounding_and_citations("Paris is the capital [1]", candidates)
    assert res.grounded is True

def test_calculate_confidence():
    from app.models.schemas import GuardrailResult
    # Mock some data
    gr = GuardrailResult(input_safe=True, decision=GuardrailDecision.ALLOW)
    res = calculate_confidence(0.9, 0.8, 1.0, gr)
    assert res > 0.0
