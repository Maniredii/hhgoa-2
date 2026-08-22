# Benchmarking Methodology

VaaniRAG includes an automated benchmarking suite to measure end-to-end pipeline latency across a representative sample of queries.

## Methodology

### 1. Query Set
The benchmark executes against 100 queries designed to mimic real-world distribution:
- **Short English Keywords**: Standard factual lookups.
- **Long English Reasoning**: Complex queries requiring multi-sentence comprehension.
- **Indic Languages**: Queries in Hindi, Tamil, Telugu, and Malayalam to test cross-lingual retrieval latency.
- **Off-Topic / Harmful**: Queries designed to trigger the Pre-Retrieval Guardrails (measuring short-circuit efficiency).

### 2. Execution
- Queries are executed sequentially against the local `/api/query` endpoint.
- Sequential execution is intentional to measure raw single-request pipeline latency without triggering external HTTP 429 Rate Limits from the LLM/STT providers.

### 3. Granular Telemetry
The backend injects precise `time.time()` measurements at every stage of the `VaaniOrchestrator` pipeline. 
The benchmark parses these JSON fields:
- `stt_ms`: Sarvam API audio transcription time.
- `embedding_ms`: Dense vector encoding time.
- `faiss_ms`: Vector index lookup time.
- `bm25_ms`: Lexical index lookup time.
- `fusion_ms`: Reciprocal Rank Fusion time.
- `reranking_ms`: Cross-encoder scoring time.
- `generation_ms`: LLM streaming/generation time.
- `e2e_ms`: Total HTTP round-trip time.

### 4. Aggregation
Results are compiled into Mean, Min, Max, and Percentiles (P50, P70, P90, P95, P99).
The data is output to:
- `benchmarks/results.json`
- `benchmarks/results.csv`
- `benchmarks/LATENCY_REPORT.md`
