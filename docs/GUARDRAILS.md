# Guardrails System

VaaniRAG implements a bi-directional guardrail system to ensure enterprise safety, prompt injection defense, and output grounding.

## Pre-Retrieval Guardrails (Input)
Before any API calls are made, the incoming text query is evaluated:
1. **Safety Checks**: Blocks known harmful intent, PII leakage attempts, and prompt injection patterns (e.g., "ignore previous instructions").
2. **Relevance/Off-Topic Filtering**: Evaluates if the query is reasonably answerable by the domain index. If it is entirely unrelated (e.g., "write a python script" against a medical index), it halts execution immediately, saving STT, Retrieval, and LLM costs.

## Post-Retrieval Guardrails (Output/Grounding)
1. **Answer Groundedness**: The LLM is strictly prompted to use *only* retrieved evidence. If the evidence is insufficient, it is instructed to explicitly abstain: *"I don't have enough evidence..."*
2. **Hallucination Detection**: The system validates that the generated answer does not contain facts external to the retrieved chunks.
3. **Citations**: The LLM is forced to emit bracketed source citations `[c123]`. The frontend visualizes these citations, mapping them directly to the underlying data source.
