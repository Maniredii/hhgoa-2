# Retrieval Architecture

VaaniRAG utilizes a heavily parallelized Hybrid Retrieval pipeline. 

## 1. Dense Retrieval (FAISS)
- **Model**: SentenceTransformers (`paraphrase-multilingual-MiniLM-L12-v2`)
- **Index**: FAISS `IndexFlatIP` (Inner Product).
- **Function**: Excels at semantic matching, capturing intent and synonymous phrases even if exact keywords are missing. Highly effective for conceptual queries in Indic languages.

## 2. Sparse Retrieval (BM25)
- **Model**: `RankBM25Okapi`
- **Function**: Excels at exact keyword matching. Crucial for queries containing specific nouns, acronyms, or proper names that dense embeddings might blur out.

## 3. Hybrid Fusion (RRF)
- Both indices are queried asynchronously.
- Results are normalized and merged using **Reciprocal Rank Fusion (RRF)**:
  `Score = 1 / (k + rank)`
- This ensures that a chunk which ranks highly in both systems receives the maximum possible weight.

## 4. Cross-Encoder Reranking
- **Model**: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`
- The top-K candidates from the Fusion step are passed to a Cross-Encoder.
- Unlike Bi-Encoders (FAISS), Cross-Encoders evaluate the query and the chunk simultaneously through self-attention, providing a much more accurate relevance score.
- **Resiliency**: If the reranker times out or errors, the `VaaniOrchestrator` automatically falls back to the hybrid fusion scores to ensure zero downtime.
