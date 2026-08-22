# VaaniRAG

## Problem
Building a RAG (Retrieval-Augmented Generation) system for Indic languages poses unique challenges. Users frequently send voice notes combining multiple dialects and languages. Standard lexical searches fail due to diverse spellings, while standard dense retrieval models struggle with cross-lingual nuances. Furthermore, achieving real-time latency while ensuring the model doesn't hallucinate or leak PII is a significant engineering hurdle.

## Solution
VaaniRAG is a production-ready, voice-driven RAG architecture optimized for low-latency Indic language support. It combines state-of-the-art Speech-to-Text (Sarvam API) with a multi-strategy retrieval pipeline (Dense + Sparse + Reranking) to provide highly accurate, grounded answers to user audio queries.

## Architecture
VaaniRAG features a decoupled React frontend and FastAPI backend. The `VaaniOrchestrator` securely manages the data flow from STT through Guardrails, Retrieval, Reranking, and Generation, utilizing circuit breakers to ensure system resiliency during partial model failures.
*(See `docs/ARCHITECTURE.md` for full details).*

## Voice Pipeline
Audio is captured locally via the browser's MediaRecorder API and sent to the backend. It is then transcribed via the Sarvam API, which is specialized for parsing complex Indic language speech into normalized text.

## Multi-Strategy Chunking
Documents are chunked simultaneously using both **Fixed Overlap** (for factual density) and **Sentence-Semantic** (for grammatical cohesion) strategies, ensuring the retrieval system has the best possible context blocks to choose from.
*(See `docs/CHUNKING.md` for full details).*

## Retrieval Architecture
The system concurrently queries a FAISS vector index (for semantic intent) and a RankBM25 sparse index (for exact keyword match). The results are fused using Reciprocal Rank Fusion (RRF).
*(See `docs/RETRIEVAL.md` for full details).*

## Reranking
Top candidates are passed through a Cross-Encoder (`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`). If the reranker times out or fails (e.g. CPU exhaustion), the circuit breaker seamlessly falls back to the hybrid fusion scores, ensuring zero downtime.

## RAG Harness
The final generation relies on GPT-4o-mini (configurable). The prompt strictly bounds the LLM to the retrieved context and forces it to emit citation brackets `[c123]` linking back to the source chunks. 

## Guardrails
Bi-directional guardrails inspect incoming queries for safety/relevance and validate outgoing answers for groundedness.
*(See `docs/GUARDRAILS.md` for full details).*

## Latency Optimization
FAISS and BM25 queries are executed in parallel via a `ThreadPoolExecutor`. The slower of the two dictates the retrieval bottleneck, rather than their sum. Telemetry is tracked at the millisecond level across the pipeline.

## Benchmark Methodology
The benchmark suite runs 100 diverse queries against the local API, tracking P50/P90/P99 latency percentiles at every single granular step of the pipeline.
*(See `docs/BENCHMARKING.md` for full details).*

## Evaluation Results
The multi-strategy architecture outperforms standard dense or BM25 retrieval across Recall, MRR, and Hit Rate. See `evaluation/EVALUATION_REPORT.md` for hard metrics.

## Dataset
Configured to ingest `ai4bharat/MSMARCO-XI`, a massive multilingual dataset.

## Setup
```bash
pip install -r requirements.txt
cd frontend && npm install
```

## Environment Variables
Copy `.env.example` to `.env`:
```env
SARVAM_API_KEY="your_sarvam_key"
LLM_PROVIDER="openai"
LLM_API_KEY="your_openai_key"
```

## Running Locally
**Backend**:
```bash
python -m uvicorn app.main:app --reload
```
**Frontend**:
```bash
cd frontend
npm run dev
```

## Running the Indexer
To download the dataset and build the SQLite/FAISS/BM25 local indices:
```bash
python scripts/ingest_dataset.py --max_rows 500
python scripts/build_indexes.py
```

## Running Benchmarks
```bash
python benchmarks/benchmark_pipeline.py --queries 50
```

## Running Tests
```bash
python -m pytest tests/
```

## Deployment
A `docker-compose.yml` is provided to deploy both the frontend and backend simultaneously.

## Limitations
- Cross-encoder reranking is CPU-intensive and requires GPUs for high-QPS production environments.
- Local SQLite metadata DB should be replaced with Postgres/pgvector for distributed scaling.

## Future Improvements
- Add semantic caching (e.g., Redis) to bypass the LLM entirely for repeated queries.
- Support streaming STT for lower perceived audio latency.
