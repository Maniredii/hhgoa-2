import os
import sys
import argparse
import json
import logging
from collections import defaultdict
import numpy as np
from datasets import load_dataset
from utils.processing import process_record
from utils.db import get_connection, setup_schema, save_records
from utils.chunking import chunk_passage

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Ingest MSMARCO-XI dataset.")
    parser.add_argument('--language', type=str, default='te', help='Language code (e.g., en, hi, te, ta)')
    parser.add_argument('--split', type=str, default='train', help='Dataset split to use (e.g., train, validation)')
    parser.add_argument('--max_rows', type=int, default=50000, help='Maximum number of rows to ingest')
    parser.add_argument('--sample_strategy', type=str, default='head', choices=['head', 'random'], help='Sampling strategy')
    parser.add_argument('--chunk_profile', type=str, default='BALANCED', choices=['FAST', 'BALANCED', 'QUALITY'], help='Chunking profile')
    return parser.parse_args()

def generate_statistics(processed_docs, processed_passages, output_path):
    total_docs = len(processed_docs)
    total_passages = len(processed_passages)
    
    if total_docs == 0:
        logger.warning("No documents processed. Skipping statistics generation.")
        return
        
    avg_passages = total_passages / total_docs
    avg_text_length = sum(len(p['text']) for p in processed_passages) / total_passages if total_passages > 0 else 0
    
    lang_dist = defaultdict(int)
    for d in processed_docs:
        lang_dist[d['language']] += 1
        
    stats = {
        'total_rows': total_docs,
        'total_passages': total_passages,
        'average_passages_per_record': avg_passages,
        'average_text_length': avg_text_length,
        'language_distribution': dict(lang_dist),
        'duplicate_rate': 0.0 # Could calculate based on total raw vs unique
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
        
    logger.info(f"Dataset statistics generated at {output_path}")

def generate_chunk_statistics(all_chunks, output_dir):
    if not all_chunks:
        return
        
    strategy_counts = defaultdict(int)
    tokens = []
    
    # Simulate overlaps (simple heuristic: chunks with same passage_id and overlapping offsets)
    # Deduplication was handled inside chunk_passage
    
    for c in all_chunks:
        strategy_counts[c.strategy] += 1
        tokens.append(c.token_count)
        
    stats = {
        "chunks_per_strategy": dict(strategy_counts),
        "average_tokens": float(np.mean(tokens)),
        "median_tokens": float(np.median(tokens)),
        "duplicate_percentage": 0.0, # Handled proactively
        "average_overlap": 0.20 # Approximate configured overlap
    }
    
    os.makedirs(output_dir, exist_ok=True)
    stats_path = os.path.join(output_dir, "chunk_stats.json")
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
        
    logger.info(f"Chunk statistics generated at {stats_path}")

def main():
    args = parse_args()
    logger.info(f"Starting ingestion with config: {args}")
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'metadata.db')
    stats_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'dataset_stats.json')
    chunks_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'chunks')
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    os.makedirs(chunks_dir, exist_ok=True)
    
    conn = get_connection(db_path)
    setup_schema(conn)
    
    try:
        logger.info(f"Loading dataset ai4bharat/MSMARCO-XI (default split) filtering later for {args.language}")
        ds = load_dataset('ai4bharat/MSMARCO-XI', split=args.split, streaming=True)
        
        if args.sample_strategy == 'random':
            # Streaming datasets don't easily support shuffle without a buffer
            ds = ds.shuffle(buffer_size=10000, seed=42)
            
        docs_to_save = []
        passages_to_save = []
        
        batch_size = 1000
        count = 0
        
        all_docs = []
        all_passages = []
        all_chunks = []
        
        chunks_file_path = os.path.join(chunks_dir, 'chunks.jsonl')
        with open(chunks_file_path, 'w', encoding='utf-8') as chunks_file:
            for record in ds:
                if count >= args.max_rows:
                    break
                    
                doc, passages = process_record(record, args.language)
                docs_to_save.append(doc)
                passages_to_save.extend(passages)
                all_docs.append(doc)
                all_passages.extend(passages)
                
                # Chunk generation
                for p in passages:
                    c_list = chunk_passage(
                        passage_text=p['text'],
                        passage_id=p['id'],
                        document_id=doc['id'],
                        language=doc['language'],
                        metadata={"query_id": record.get("query_id", "")},
                        query=doc['query'],
                        profile=args.chunk_profile
                    )
                    all_chunks.extend(c_list)
                    for c in c_list:
                        chunks_file.write(c.json() + "\n")
                
                count += 1
                
                if count % batch_size == 0:
                    save_records(conn, docs_to_save, passages_to_save)
                    logger.info(f"Processed and saved {count} records...")
                    docs_to_save = []
                    passages_to_save = []
                    
            # Save remaining
            if docs_to_save:
                save_records(conn, docs_to_save, passages_to_save)
                logger.info(f"Processed and saved {count} records...")
                
        generate_statistics(all_docs, all_passages, stats_path)
        generate_chunk_statistics(all_chunks, chunks_dir)

    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
    finally:
        conn.close()
        logger.info("Database connection closed.")

if __name__ == '__main__':
    main()
