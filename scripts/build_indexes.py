import os
import json
import logging
import argparse
import numpy as np
import faiss
import pickle
from rank_bm25 import BM25Okapi

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Build FAISS and BM25 indexes.")
    parser.add_argument('--index_type', type=str, default='flat', choices=['flat', 'hnsw'], help='FAISS index type')
    return parser.parse_args()

def tokenize(text: str):
    # A simple whitespace and punctuation tokenizer for multilingual BM25.
    # In production, use a more sophisticated tokenizer (e.g., IndicNLP) if needed.
    import re
    text = text.lower()
    tokens = re.split(r'\W+', text)
    return [t for t in tokens if t]

def main():
    args = parse_args()
    
    emb_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'embeddings')
    chunks_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chunks', 'chunks.jsonl')
    index_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'indexes')
    os.makedirs(index_dir, exist_ok=True)
    
    emb_path = os.path.join(emb_dir, 'embeddings.npy')
    ids_path = os.path.join(emb_dir, 'chunk_ids.json')
    
    if not os.path.exists(emb_path) or not os.path.exists(chunks_path):
        logger.error("Embeddings or chunks not found. Run build_embeddings.py first.")
        return
        
    logger.info("Loading embeddings...")
    embeddings = np.load(emb_path)
    
    with open(ids_path, 'r', encoding='utf-8') as f:
        chunk_ids = json.load(f)
        
    d = embeddings.shape[1]
    logger.info(f"Loaded {embeddings.shape[0]} embeddings of dimension {d}.")
    
    # Build FAISS Index
    logger.info(f"Building FAISS {args.index_type} index...")
    if args.index_type == 'flat':
        # Inner Product for Cosine Similarity (assuming embeddings are normalized)
        faiss_index = faiss.IndexFlatIP(d)
    else:
        # HNSW for faster approximate search
        faiss_index = faiss.IndexHNSWFlat(d, 32)
        faiss_index.hnsw.efConstruction = 40
        
    faiss_index.add(embeddings)
    
    faiss_out_path = os.path.join(index_dir, 'vector.faiss')
    faiss.write_index(faiss_index, faiss_out_path)
    logger.info(f"FAISS index saved to {faiss_out_path}")
    
    # Build BM25 Index
    logger.info("Building BM25 index...")
    chunks = []
    with open(chunks_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
                
    # Create mapping dictionary for quick lookup during retrieval
    mapping = {c['id']: c for c in chunks}
    
    # Tokenize corpus
    tokenized_corpus = [tokenize(c['text']) for c in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    
    bm25_out_path = os.path.join(index_dir, 'bm25.pkl')
    with open(bm25_out_path, 'wb') as f:
        pickle.dump(bm25, f)
    logger.info(f"BM25 index saved to {bm25_out_path}")
    
    mapping_path = os.path.join(index_dir, 'chunk_mapping.pkl')
    with open(mapping_path, 'wb') as f:
        pickle.dump({'mapping': mapping, 'ids_list': chunk_ids}, f)
    logger.info(f"Chunk mapping saved to {mapping_path}")
    
    logger.info("Indexing complete!")

if __name__ == '__main__':
    main()
