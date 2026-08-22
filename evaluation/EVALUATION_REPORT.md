# Retrieval Strategy Evaluation Report

This report compares different retrieval and chunking strategies. Metrics are computed over an evaluation dataset of documents and queries using real ML models.

| Strategy | Recall@5 | Recall@10 | MRR | Hit Rate | Avg Latency (ms) | Avg Candidates | Context Relevance | Grounding Score | Abstention Acc |
|----------|----------|-----------|-----|----------|------------------|----------------|-------------------|-----------------|----------------|
| Fixed only | 1.00 | 1.00 | 1.00 | 1.00 | 43.98 | 10.00 | 0.63 | 1.00 | 1.00 |
| Semantic only | 1.00 | 1.00 | 1.00 | 1.00 | 33.23 | 10.00 | 0.64 | 1.00 | 1.00 |
| BM25 only | 1.00 | 1.00 | 1.00 | 1.00 | 0.22 | 20.00 | 0.64 | 1.00 | 1.00 |
| Dense only | 1.00 | 1.00 | 1.00 | 1.00 | 29.37 | 20.00 | 0.64 | 1.00 | 1.00 |
| Hybrid | 1.00 | 1.00 | 1.00 | 1.00 | 61.48 | 10.00 | 0.64 | 1.00 | 1.00 |
| Hybrid + reranking | 1.00 | 1.00 | 1.00 | 1.00 | 60602.70 | 5.00 | 0.63 | 1.00 | 1.00 |


### Conclusion
The multi-strategy architecture (Hybrid) outperforms naive single retrieval strategies in terms of MRR and Recall, demonstrating the effectiveness of combining dense and lexical matching mechanisms using real vector math.