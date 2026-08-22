import os
import faiss
import pickle
import sqlite3
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from app.config import settings

# Global state for models and indexes
_vector_index = None
_bm25_index = None
_chunk_ids = None
_embedding_model = None

def get_db_connection():
    return sqlite3.connect(settings.DB_PATH)

def load_indexes():
    global _vector_index, _bm25_index, _chunk_ids, _embedding_model
    
    if _embedding_model is None:
        try:
            _embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        except:
            pass

    vector_path = os.path.join(settings.INDEX_DIR, 'vector.faiss')
    if os.path.exists(vector_path) and _vector_index is None:
        _vector_index = faiss.read_index(vector_path)

    bm25_path = os.path.join(settings.INDEX_DIR, 'bm25.pkl')
    if os.path.exists(bm25_path) and _bm25_index is None:
        with open(bm25_path, 'rb') as f:
            _bm25_index = pickle.load(f)

    chunk_ids_path = os.path.join(settings.INDEX_DIR, 'chunk_ids.pkl')
    if os.path.exists(chunk_ids_path) and _chunk_ids is None:
        with open(chunk_ids_path, 'rb') as f:
            _chunk_ids = pickle.load(f)

def retrieve(query: str, top_k: int = 20) -> List[Dict]:
    load_indexes()
    if not _vector_index or not _bm25_index or not _embedding_model:
        return []

    # 1. Vector Search
    query_emb = _embedding_model.encode([query])
    D, I = _vector_index.search(query_emb, top_k)
    
    vector_results = {}
    for score, idx in zip(D[0], I[0]):
        if idx != -1 and idx < len(_chunk_ids):
            chunk_id = _chunk_ids[idx]
            vector_results[chunk_id] = float(score)

    # 2. BM25 Search
    tokenized_query = query.split()
    bm25_scores = _bm25_index.get_scores(tokenized_query)
    
    # Get top_k from bm25
    top_bm25_indices = bm25_scores.argsort()[-top_k:][::-1]
    bm25_results = {}
    for idx in top_bm25_indices:
        chunk_id = _chunk_ids[idx]
        bm25_results[chunk_id] = float(bm25_scores[idx])

    # 3. Reciprocal Rank Fusion (RRF)
    rrf_scores = {}
    k = 60
    
    for rank, (chunk_id, _) in enumerate(sorted(vector_results.items(), key=lambda x: x[1])):
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (k + rank + 1)
        
    for rank, (chunk_id, _) in enumerate(sorted(bm25_results.items(), key=lambda x: x[1], reverse=True)):
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (k + rank + 1)

    # Get top fused candidates
    top_fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    # Fetch text from DB
    conn = get_db_connection()
    cursor = conn.cursor()
    
    final_candidates = []
    for chunk_id, score in top_fused:
        cursor.execute("SELECT text FROM chunks WHERE chunk_id = ?", (chunk_id,))
        row = cursor.fetchone()
        if row:
            final_candidates.append({
                'chunk_id': chunk_id,
                'text': row[0],
                'score': score
            })
            
    conn.close()
    return final_candidates
