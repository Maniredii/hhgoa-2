# VaaniRAG Architecture

## Overview
VaaniRAG is an end-to-end Voice-driven Retrieval-Augmented Generation (RAG) system designed specifically for Indic languages, optimized for low latency and high accuracy. It features a complete pipeline from audio ingestion via Sarvam STT, semantic + lexical retrieval over massive multilingual datasets (e.g., MSMARCO-XI), to constrained generation.

## Core Components

### 1. Frontend (React + Vite)
- **Audio Capture**: A React-based interface records the user's voice locally using standard MediaRecorder APIs.
- **Latency Monitoring**: Displays real-time breakdown of pipeline latencies (STT, Embeddings, FAISS, BM25, Fusion, Reranking, Generation).
- **Visualization**: Shows the step-by-step trace of the RAG pipeline.

### 2. Backend (FastAPI)
- **API Layer**: Exposes endpoints for `/api/voice`, `/api/query`, `/health`, `/ready`, and `/metrics`.
- **Orchestration**: The `VaaniOrchestrator` manages the sequential execution of STT, Retrieval, and Generation while handling errors via a Circuit Breaker.
- **Circuit Breaker & Fallbacks**: Uses `llm_breaker` to fail fast during repeated timeouts. If the Reranker fails or is unavailable, the system safely falls back to standard hybrid fusion results.

### 3. Data Ingestion & Indexing
- **Sources**: Configured to ingest standard HuggingFace datasets (`ai4bharat/MSMARCO-XI`).
- **Processing pipeline**: Records are deduped, hashed, and chunks are generated.
- **Storage**:
  - **SQLite**: Stores metadata, raw text, and document mappings.
  - **FAISS**: Dense vector index using `IndexFlatIP`.
  - **BM25**: Sparse inverted index via `RankBM25Okapi`.

### 4. Machine Learning Services
- **Speech-to-Text (STT)**: Integration with Sarvam API for highly accurate Indic language transcription.
- **Embeddings**: SentenceTransformers (e.g., `paraphrase-multilingual-MiniLM-L12-v2`).
- **Reranker**: Cross-encoder models (`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`) to triage hybrid results.
- **LLM**: GPT-4o-mini (or compatible provider) for evidence-bound final generation.

## Request Lifecycle
1. **User Speaks**: Audio recorded on frontend -> sent to `/api/voice`.
2. **STT**: Sent to Sarvam API, transcribed to text.
3. **Guardrails (Pre)**: Text checked for safety/policy violations.
4. **Embedding**: Text encoded into dense vectors.
5. **Retrieval**: Concurrent requests to FAISS and BM25.
6. **Fusion**: Results merged using Reciprocal Rank Fusion (RRF).
7. **Reranking**: Top-K results rescored using a cross-encoder.
8. **Generation**: Final context passed to LLM with strict grounding prompt.
9. **Guardrails (Post)**: (Optional) Output is validated.
10. **Response**: JSON returned containing the answer, citations, and granular latency metrics.
