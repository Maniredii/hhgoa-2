import time
import uuid
import logging
import asyncio
from typing import Dict, Any, List
from app.models.schemas import (
    PipelineContext, PipelineStage, SourceChunk, UnifiedRAGResponse, GuardrailDecision
)
from app.services.hybrid_retriever import retrieve_hybrid
from app.services.reranker import rerank
from app.services.generator import generate_answer
from app.core.guardrails import (
    check_input_safety, 
    check_context_sufficiency, 
    check_grounding_and_citations, 
    calculate_confidence
)
from app.core.resiliency import with_retry, with_timeout, CircuitBreaker, CircuitBreakerError

logger = logging.getLogger(__name__)

# Global circuit breaker for the LLM generator
llm_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)

class RAGOrchestrator:
    def __init__(self, raw_query: str, language: str = "en"):
        self.request_id = str(uuid.uuid4())
        self.ctx = PipelineContext(
            request_id=self.request_id,
            timestamp=time.time(),
            raw_query=raw_query,
            language=language
        )
        self.total_start_time = time.time()
        
    def _log_stage(self, stage_name: str, start: float, status: str):
        end = time.time()
        duration_ms = (end - start) * 1000
        self.ctx.latency[stage_name] = duration_ms
        logger.info(
            f"[Req: {self.request_id}] Stage: {stage_name} | "
            f"Start: {start:.3f} | End: {end:.3f} | "
            f"Duration: {duration_ms:.2f}ms | Status: {status}"
        )

    def transition(self, new_state: PipelineStage):
        self.ctx.status = new_state
        logger.debug(f"[Req: {self.request_id}] State transitioned to {new_state.value}")

    async def run(self) -> UnifiedRAGResponse:
        try:
            self.transition(PipelineStage.RECEIVED)
            
            # Stage 1: Input validation
            await self._stage_1_input_validation()
            
            # Stage 2: Query normalization
            await self._stage_2_query_normalization()
            
            # Stage 3: Language detection
            await self._stage_3_language_detection()
            
            # Stage 4: Query classification
            await self._stage_4_query_classification()
            
            # Stage 5: Safety check
            safe = await self._stage_5_safety_check()
            if not safe:
                self.transition(PipelineStage.ABSTAINED)
                return self._build_response()
                
            # Stage 6: Retrieval
            await self._stage_6_retrieval()
            
            # Stage 7: Candidate fusion (handled within retrieve_hybrid, but explicitly logged)
            await self._stage_7_candidate_fusion()
            
            # Stage 8: Reranking
            await self._stage_8_reranking()
            
            # Stage 9: Context construction
            await self._stage_9_context_construction()
            
            # Stage 11: Grounding validation (Context sufficiency check)
            sufficient = await self._stage_11_grounding_validation()
            if not sufficient:
                self.transition(PipelineStage.ABSTAINED)
                return self._build_response()
                
            # Stage 10: Answer generation
            success = await self._stage_10_answer_generation()
            if not success:
                self.transition(PipelineStage.ABSTAINED)
                return self._build_response()
                
            self.transition(PipelineStage.COMPLETED)
            
            # Stage 12: Final response formatting
            return await self._stage_12_final_response_formatting()
            
        except Exception as e:
            logger.error(f"[Req: {self.request_id}] Orchestrator failed: {e}")
            self.ctx.errors.append(str(e))
            self.transition(PipelineStage.FAILED)
            return self._build_response()

    async def _stage_1_input_validation(self):
        start = time.time()
        if not self.ctx.raw_query or not self.ctx.raw_query.strip():
            raise ValueError("Empty query provided")
        self.transition(PipelineStage.VALIDATED)
        self._log_stage("input_validation", start, "success")

    async def _stage_2_query_normalization(self):
        start = time.time()
        self.ctx.normalized_query = self.ctx.raw_query.strip()
        self._log_stage("query_normalization", start, "success")

    async def _stage_3_language_detection(self):
        start = time.time()
        # In a real app, use fasttext or langid. Here we use the provided lang.
        if not self.ctx.language:
            self.ctx.language = "en"
        self._log_stage("language_detection", start, "success")

    async def _stage_4_query_classification(self):
        start = time.time()
        self.ctx.query_type = "general_qa"
        self.transition(PipelineStage.CLASSIFIED)
        self._log_stage("query_classification", start, "success")

    async def _stage_5_safety_check(self) -> bool:
        start = time.time()
        res = check_input_safety(self.ctx.normalized_query)
        self.ctx.guardrail_results.input_safe = res.input_safe
        self.ctx.guardrail_results.decision = res.decision
        self.ctx.guardrail_results.reason = res.reason
        
        if res.decision == GuardrailDecision.BLOCK:
            self.ctx.answer = "I am sorry, but I cannot fulfill this request."
            self._log_stage("safety_check", start, "failed")
            return False
        self._log_stage("safety_check", start, "success")
        return True

    @with_timeout(5.0)
    async def _execute_retrieval(self):
        # We wrap the synchronous retriever in an async wrapper to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, retrieve_hybrid, self.ctx.normalized_query, 30)

    async def _stage_6_retrieval(self):
        start = time.time()
        self.transition(PipelineStage.RETRIEVING)
        try:
            # No retries for retrieval unless transient, we use fast-fail timeout
            candidates, metrics = await self._execute_retrieval()
            self.ctx.retrieval_candidates = candidates
            self.ctx.latency.update(metrics)
            self._log_stage("retrieval", start, "success")
        except Exception as e:
            self._log_stage("retrieval", start, f"failed: {e}")
            raise e

    async def _stage_7_candidate_fusion(self):
        start = time.time()
        # Hybrid retriever internally handled fusion, but we explicitly log the stage success
        self._log_stage("candidate_fusion", start, "success")

    @with_timeout(4.0)
    async def _execute_reranking(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, rerank, self.ctx.normalized_query, self.ctx.retrieval_candidates, 5)

    async def _stage_8_reranking(self):
        start = time.time()
        self.transition(PipelineStage.RERANKING)
        try:
            reranked, rerank_ms = await self._execute_reranking()
            self.ctx.reranked_candidates = reranked
            self._log_stage("reranking", start, "success")
        except asyncio.TimeoutError:
            self.ctx.reranked_candidates = self.ctx.retrieval_candidates[:5]
            self._log_stage("reranking", start, "timeout_fallback")
        except Exception as e:
            self.ctx.reranked_candidates = self.ctx.retrieval_candidates[:5]
            self._log_stage("reranking", start, f"failed_fallback: {e}")

    async def _stage_9_context_construction(self):
        start = time.time()
        self.ctx.citations = [
            SourceChunk(
                chunk_id=c['chunk_id'], 
                text=c['text'], 
                score=c.get('rerank_score', c.get('dense_score', 0.0))
            ) 
            for c in self.ctx.reranked_candidates
        ]
        self._log_stage("context_construction", start, "success")

    async def _stage_11_grounding_validation(self) -> bool:
        start = time.time()
        self.transition(PipelineStage.VALIDATING)
        res = check_context_sufficiency(self.ctx.reranked_candidates)
        
        self.ctx.guardrail_results.context_sufficient = res.context_sufficient
        self.ctx.guardrail_results.on_topic = res.on_topic
        
        if res.decision == GuardrailDecision.ABSTAIN:
            self.ctx.guardrail_results.decision = res.decision
            self.ctx.guardrail_results.reason = res.reason
            self.ctx.answer = "I don't have enough evidence in the retrieved dataset to answer that reliably."
            self._log_stage("context_validation", start, "abstained")
            return False
            
        self._log_stage("context_validation", start, "success")
        return True

    @with_retry(max_retries=2, base_delay=1.0)
    @with_timeout(10.0)
    async def _execute_generation(self):
        llm_breaker.check_state()
        try:
            result = await generate_answer(self.ctx.normalized_query, self.ctx.reranked_candidates)
            llm_breaker.record_success()
            return result
        except Exception as e:
            llm_breaker.record_failure()
            raise e

    async def _stage_10_answer_generation(self) -> bool:
        start = time.time()
        self.transition(PipelineStage.GENERATING)
        
        retries = 2
        answer = None
        for attempt in range(retries):
            try:
                answer = await self._execute_generation()
                
                # Grounding & Citation check
                res = check_grounding_and_citations(answer, self.ctx.reranked_candidates)
                self.ctx.guardrail_results.grounded = res.grounded
                self.ctx.guardrail_results.citation_valid = res.citation_valid
                
                if res.decision == GuardrailDecision.RETRY and attempt < retries - 1:
                    logger.warning(f"[Req: {self.request_id}] Missing citations. Retrying generation.")
                    continue
                elif res.decision == GuardrailDecision.RETRY:
                    self.ctx.guardrail_results.decision = GuardrailDecision.ABSTAIN
                    self.ctx.guardrail_results.reason = "Could not generate grounded answer with citations."
                    self.ctx.answer = "I don't have enough evidence in the retrieved dataset to answer that reliably."
                    self._log_stage("answer_generation", start, "abstained")
                    return False
                
                self.ctx.answer = answer
                self.ctx.guardrail_results.decision = GuardrailDecision.ALLOW
                self._log_stage("answer_generation", start, "success")
                return True
                
            except CircuitBreakerError as cbe:
                self.ctx.answer = "The AI generator service is currently degraded. Please try again later."
                self._log_stage("answer_generation", start, "circuit_breaker_open")
                raise cbe
            except Exception as e:
                self.ctx.answer = "Failed to generate an answer due to an internal timeout or provider error."
                self._log_stage("answer_generation", start, f"failed: {e}")
                raise e
                
        self.ctx.answer = "I could not generate a valid answer."
        self._log_stage("answer_generation", start, "failed")
        return False

    async def _stage_12_final_response_formatting(self) -> UnifiedRAGResponse:
        start = time.time()
        self._log_stage("final_response_formatting", start, "success")
        return self._build_response()
        
    def _build_response(self) -> UnifiedRAGResponse:
        self.ctx.latency['total_pipeline_ms'] = (time.time() - self.total_start_time) * 1000
        
        # Calculate confidence
        if self.ctx.status == PipelineStage.COMPLETED:
            top_score = self.ctx.reranked_candidates[0].get('rerank_score', 0.0) if self.ctx.reranked_candidates else 0.0
            dense_score = self.ctx.reranked_candidates[0].get('dense_score', 0.0) if self.ctx.reranked_candidates else 0.0
            conf = calculate_confidence(
                retrieval_relevance=dense_score,
                reranker_score=top_score,
                context_coverage=1.0 if self.ctx.guardrail_results.context_sufficient else 0.0,
                grounding_result=self.ctx.guardrail_results
            )
            self.ctx.guardrail_results.confidence = conf
        else:
            self.ctx.guardrail_results.confidence = 0.0
            
        return UnifiedRAGResponse(
            request_id=self.ctx.request_id,
            query=self.ctx.raw_query,
            answer=self.ctx.answer or "An unexpected error occurred.",
            sources=self.ctx.citations,
            language=self.ctx.language or "en",
            confidence=self.ctx.guardrail_results.confidence,
            guardrails=self.ctx.guardrail_results,
            latency=self.ctx.latency,
            status=self.ctx.status.value
        )
