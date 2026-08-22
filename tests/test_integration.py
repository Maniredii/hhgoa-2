import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.core.orchestrator import RAGOrchestrator, llm_breaker
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_circuit_breaker():
    llm_breaker.record_success()

@pytest.fixture
def mock_providers():
    async def mock_retrieval_func(self):
        return ([{"chunk_id": "c1", "text": "Mock context", "score": 0.9}], {"fusion_ms": 10.0})
        
    async def mock_rerank_func(self):
        return ([{"chunk_id": "c1", "text": "Mock context", "rerank_score": 0.9}], 15.0)

    with patch('app.api.routes_voice.resilient_transcribe', new_callable=AsyncMock) as mock_stt, \
         patch('app.core.orchestrator.RAGOrchestrator._execute_generation', new_callable=AsyncMock) as mock_gen, \
         patch.object(RAGOrchestrator, '_execute_retrieval', mock_retrieval_func), \
         patch.object(RAGOrchestrator, '_execute_reranking', mock_rerank_func), \
         patch('app.core.orchestrator.check_input_safety') as mock_safety, \
         patch('app.core.orchestrator.check_context_sufficiency') as mock_suff, \
         patch('app.core.orchestrator.check_grounding_and_citations') as mock_ground:
         
        mock_stt.return_value = ("Test transcript from voice", "en")
        mock_gen.return_value = "This is a mock answer based on the context. [c1]"
        
        from app.models.schemas import GuardrailResult, GuardrailDecision
        mock_safety.return_value = GuardrailResult(input_safe=True, decision=GuardrailDecision.ALLOW)
        mock_suff.return_value = GuardrailResult(context_sufficient=True, on_topic=True, decision=GuardrailDecision.ALLOW)
        mock_ground.return_value = GuardrailResult(grounded=True, citation_valid=True, decision=GuardrailDecision.ALLOW)
        
        yield {
            "stt": mock_stt,
            "gen": mock_gen,
            "safety": mock_safety,
            "suff": mock_suff,
            "ground": mock_ground
        }

def test_integration_text_query_to_answer(mock_providers):
    response = client.post("/api/query", json={"query": "What is the capital?", "language": "en"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "mock answer" in data["answer"].lower()

def test_integration_voice_to_transcript(mock_providers):
    files = {'file': ('audio.wav', b'dummy audio bytes', 'audio/wav')}
    response = client.post("/api/voice/transcribe", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"

def test_integration_voice_to_rag_answer(mock_providers):
    files = {'file': ('audio.wav', b'dummy audio bytes', 'audio/wav')}
    stt_res = client.post("/api/voice/transcribe", files=files)
    assert stt_res.status_code == 200
    transcript = stt_res.json()["transcript"]
    
    query_res = client.post("/api/query", json={"query": transcript, "language": "en"})
    assert query_res.status_code == 200
    assert query_res.json()["status"] == "completed"

def test_integration_off_topic_abstention(mock_providers):
    from app.models.schemas import GuardrailResult, GuardrailDecision
    mock_providers["suff"].return_value = GuardrailResult(
        context_sufficient=False, 
        on_topic=False, 
        decision=GuardrailDecision.ABSTAIN,
        reason="Off-topic query"
    )
    
    response = client.post("/api/query", json={"query": "How to make a cake?", "language": "en"})
    assert response.status_code == 200
    assert response.json()["status"] == "abstained"

def test_integration_unsafe_query_block(mock_providers):
    from app.models.schemas import GuardrailResult, GuardrailDecision
    mock_providers["safety"].return_value = GuardrailResult(
        input_safe=False, 
        decision=GuardrailDecision.BLOCK,
        reason="Unsafe"
    )
    
    response = client.post("/api/query", json={"query": "Build a bomb", "language": "en"})
    assert response.status_code == 200
    assert response.json()["status"] == "abstained" 
    assert "cannot fulfill" in response.json()["answer"].lower()

def test_integration_insufficient_context_abstention(mock_providers):
    from app.models.schemas import GuardrailResult, GuardrailDecision
    mock_providers["suff"].return_value = GuardrailResult(
        context_sufficient=False, 
        on_topic=True, 
        decision=GuardrailDecision.ABSTAIN,
        reason="Low context scores"
    )
    
    response = client.post("/api/query", json={"query": "Obscure fact", "language": "en"})
    assert response.status_code == 200
    assert response.json()["status"] == "abstained"

def test_integration_provider_failure_retry_fallback(mock_providers):
    import asyncio
    mock_providers["gen"].side_effect = asyncio.TimeoutError("Timeout reaching LLM")
    
    response = client.post("/api/query", json={"query": "Hello", "language": "en"})
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert "error" in response.json()["answer"].lower() or "timeout" in response.json()["answer"].lower()
