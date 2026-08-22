import os
import sqlite3
import pickle
import faiss
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
INDEX_DIR = os.path.join(DATA_DIR, 'indexes')
DB_PATH = os.path.join(DATA_DIR, 'metadata.db')

def build_indexes():
    os.makedirs(INDEX_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if table exists
    try:
        cursor.execute("SELECT chunk_id, text FROM chunks")
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        print("No chunks table found. Please run ingest_data.py first.")
        return

    if not rows:
        print("No data found in chunks table.")
        return

    chunk_ids = [row[0] for row in rows]
    texts = [row[1] for row in rows]

    print(f"Building index for {len(texts)} chunks...")

    # 1. Build FAISS Vector Index
    print("Loading embedding model...")
    # using a multilingual model since it's an Indic dataset
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2') 
    print("Encoding texts...")
    embeddings = model.encode(texts, show_progress_bar=True)
    
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    
    faiss.write_index(index, os.path.join(INDEX_DIR, 'vector.faiss'))
    
    # Save chunk IDs mapping
    with open(os.path.join(INDEX_DIR, 'chunk_ids.pkl'), 'wb') as f:
        pickle.dump(chunk_ids, f)
        
    print("FAISS index built and saved.")

    # 2. Build BM25 Index
    print("Building BM25 index...")
    tokenized_texts = [text.split() for text in texts]
    bm25 = BM25Okapi(tokenized_texts)
    
    with open(os.path.join(INDEX_DIR, 'bm25.pkl'), 'wb') as f:
        pickle.dump(bm25, f)
        
    print("BM25 index built and saved.")

if __name__ == "__main__":
    build_indexes()
