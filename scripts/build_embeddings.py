import os
import json
import logging
import argparse
import numpy as np
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Generate embeddings for chunks.")
    parser.add_argument('--model', type=str, default='paraphrase-multilingual-MiniLM-L12-v2', help='Embedding model')
    parser.add_argument('--batch_size', type=int, default=128, help='Batch size for embedding generation')
    return parser.parse_args()

def main():
    args = parse_args()
    logger.info(f"Loading embedding model: {args.model}")
    model = SentenceTransformer(args.model)
    
    chunks_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chunks', 'chunks.jsonl')
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'embeddings')
    os.makedirs(output_dir, exist_ok=True)
    
    emb_path = os.path.join(output_dir, 'embeddings.npy')
    ids_path = os.path.join(output_dir, 'chunk_ids.json')
    
    if not os.path.exists(chunks_path):
        logger.error(f"Chunks file not found at {chunks_path}. Run ingest_dataset.py first.")
        return

    logger.info("Reading chunks...")
    chunks = []
    with open(chunks_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
                
    logger.info(f"Loaded {len(chunks)} chunks.")
    
    texts = [c['text'] for c in chunks]
    chunk_ids = [c['id'] for c in chunks]
    
    logger.info(f"Generating embeddings with batch size {args.batch_size}...")
    # Generate embeddings. The encode method handles batching automatically.
    # We normalize to allow Inner Product (FAISS IndexFlatIP) to act as Cosine Similarity.
    embeddings = model.encode(texts, batch_size=args.batch_size, show_progress_bar=True, normalize_embeddings=True)
    
    logger.info(f"Saving embeddings to {emb_path}")
    np.save(emb_path, embeddings)
    
    logger.info(f"Saving chunk mapping to {ids_path}")
    with open(ids_path, 'w', encoding='utf-8') as f:
        json.dump(chunk_ids, f, indent=2)
        
    logger.info("Embedding generation complete!")

if __name__ == '__main__':
    main()
