# Multi-Strategy Chunking

VaaniRAG utilizes a multi-strategy chunking approach during ingestion to optimize retrieval performance for various types of queries.

## 1. Fixed Overlap Chunking
- **Methodology**: Documents are split into fixed sizes (e.g., 256 tokens) with a sliding window overlap (e.g., 50 tokens).
- **Purpose**: Preserves strict localized context and prevents word boundary loss. Highly effective for dense retrieval on factual queries.

## 2. Sentence-Semantic Chunking
- **Methodology**: Splits text based on natural punctuation boundaries (e.g., `.` `?` `!`).
- **Purpose**: Creates highly cohesive semantic units. This ensures that when the LLM generates a response, the context provided is complete and grammatically sound, drastically reducing hallucination risks from partial sentence fragments.

During retrieval, FAISS and BM25 search across *both* chunk types simultaneously. The reciprocal rank fusion automatically promotes the most relevant chunk structure for the specific user query.
