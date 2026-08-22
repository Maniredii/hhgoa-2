import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.core.orchestrator import RAGOrchestrator, llm_breaker
from app.models.schemas import GuardrailResult, GuardrailDecision, PipelineStage

@pytest.fixture(autouse=True)
def reset_breaker():
    llm_breaker.record_success()

@pytest.fixture
def mock_retriever():
    with patch('app.core.orchestrator.retrieve_hybrid') as mock:
        mock.return_value = ([{"chunk_id": "c1", "text": "Dummy text", "score": 0.9}], {"fusion_ms": 10.0})
        yield mock

@pytest.fixture
def mock_reranker():
    with patch('app.core.orchestrator.rerank') as mock:
        mock.return_value = ([{"chunk_id": "c1", "text": "Dummy text", "rerank_score": 0.9}], 10.0)
        yield mock

@pytest.fixture
def mock_generator():
    with patch('app.core.orchestrator.generate_answer', new_callable=AsyncMock) as mock:
        mock.return_value = "This is a mock answer. [c1]"
        yield mock

@pytest.mark.asyncio
async def test_orchestrator_success(mock_retriever, mock_reranker, mock_generator):
    orchestrator = RAGOrchestrator(raw_query="Valid query here", language="en")

    gr_safe = GuardrailResult(input_safe=True, decision=GuardrailDecision.ALLOW)
    gr_suff = GuardrailResult(context_sufficient=True, on_topic=True, decision=GuardrailDecision.ALLOW)
    gr_ground = GuardrailResult(grounded=True, citation_valid=True, decision=GuardrailDecision.ALLOW)

    with patch('app.core.orchestrator.check_input_safety', return_value=gr_safe), \
         patch('app.core.orchestrator.check_context_sufficiency', return_value=gr_suff), \
         patch('app.core.orchestrator.check_grounding_and_citations', return_value=gr_ground):

        response = await orchestrator.run()

    assert response.status == PipelineStage.COMPLETED.value
    assert "mock answer" in response.answer

@pytest.mark.asyncio
async def test_orchestrator_context_abstain(mock_retriever, mock_reranker):
    orchestrator = RAGOrchestrator(raw_query="Random query", language="en")

    gr_safe = GuardrailResult(input_safe=True, decision=GuardrailDecision.ALLOW)
    gr_suff = GuardrailResult(context_sufficient=False, on_topic=False, decision=GuardrailDecision.ABSTAIN)

    with patch('app.core.orchestrator.check_input_safety', return_value=gr_safe), \
         patch('app.core.orchestrator.check_context_sufficiency', return_value=gr_suff):

        response = await orchestrator.run()

    assert response.status == PipelineStage.ABSTAINED.value

@pytest.mark.asyncio
async def test_orchestrator_retry(mock_retriever, mock_reranker, mock_generator):
    orchestrator = RAGOrchestrator(raw_query="Retry query", language="en")

    gr_safe = GuardrailResult(input_safe=True, decision=GuardrailDecision.ALLOW)
    gr_suff = GuardrailResult(context_sufficient=True, on_topic=True, decision=GuardrailDecision.ALLOW)
    gr_retry = GuardrailResult(grounded=False, citation_valid=False, decision=GuardrailDecision.RETRY)
    gr_ground = GuardrailResult(grounded=True, citation_valid=True, decision=GuardrailDecision.ALLOW)

    with patch('app.core.orchestrator.check_input_safety', return_value=gr_safe), \
         patch('app.core.orchestrator.check_context_sufficiency', return_value=gr_suff), \
         patch('app.core.orchestrator.check_grounding_and_citations', side_effect=[gr_retry, gr_ground]):

        response = await orchestrator.run()

    assert response.status == PipelineStage.COMPLETED.value
