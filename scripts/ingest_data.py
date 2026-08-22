import os
import json
import sqlite3
from datasets import load_dataset
from utils import semantic_chunking, fixed_size_chunking # We will implement these

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
CHUNKS_DIR = os.path.join(DATA_DIR, 'chunks')
DB_PATH = os.path.join(DATA_DIR, 'metadata.db')

def setup_directories():
    for d in [DATA_DIR, RAW_DIR, PROCESSED_DIR, CHUNKS_DIR]:
        os.makedirs(d, exist_ok=True)

def setup_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            doc_id TEXT,
            text TEXT,
            language TEXT,
            chunk_index INTEGER
        )
    ''')
    conn.commit()
    return conn

def download_and_chunk():
    print("Loading dataset...")
    # Loading a small subset of the training set for demonstration (e.g., hindi)
    try:
        ds = load_dataset('ai4bharat/MSMARCO-XI', 'hi', split='train[:1000]')
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    conn = setup_db()
    cursor = conn.cursor()

    print(f"Processing {len(ds)} items...")
    chunks_data = []

    for i, item in enumerate(ds):
        doc_id = f"doc_hi_{i}"
        text = item.get('passage', '') # Assuming it has a passage or text column
        if not text:
            continue
        
        # Simple fixed-size chunking for now
        # You could also apply semantic chunking if required
        words = text.split()
        chunk_size = 50
        overlap = 10
        
        chunk_idx = 0
        for j in range(0, len(words), chunk_size - overlap):
            chunk_text = ' '.join(words[j:j+chunk_size])
            if not chunk_text.strip():
                continue
            chunk_id = f"{doc_id}_{chunk_idx}"
            chunks_data.append({
                'chunk_id': chunk_id,
                'doc_id': doc_id,
                'text': chunk_text,
                'language': 'hi',
                'chunk_index': chunk_idx
            })
            
            cursor.execute('''
                INSERT OR REPLACE INTO chunks (chunk_id, doc_id, text, language, chunk_index)
                VALUES (?, ?, ?, ?, ?)
            ''', (chunk_id, doc_id, chunk_text, 'hi', chunk_idx))
            
            chunk_idx += 1

    conn.commit()
    conn.close()
    print(f"Saved {len(chunks_data)} chunks to metadata DB.")

if __name__ == "__main__":
    setup_directories()
    download_and_chunk()
