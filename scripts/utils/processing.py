import unicodedata
import re
import hashlib
from typing import List, Dict, Any, Tuple

def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace."""
    if not text:
        return ""
    # NFKC normalizes compatibility characters
    text = unicodedata.normalize('NFKC', text)
    # Normalize whitespace (replace multiple spaces/newlines with a single space)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def generate_id(content: str) -> str:
    """Generate a deterministic SHA-256 ID based on content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def deduplicate_passages(passages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate passages based on normalized text content.
    Returns the unique passages preserving the original text.
    """
    seen_hashes = set()
    unique_passages = []
    
    for p in passages:
        # Assuming passage text is in 'passage_text' or similar key
        # Handle different possible schema variations
        text = p.get('passage_text', p.get('text', ''))
        
        normalized = normalize_text(text)
        if not normalized:
            continue
            
        p_hash = generate_id(normalized)
        
        if p_hash not in seen_hashes:
            seen_hashes.add(p_hash)
            unique_passages.append(p)
            
    return unique_passages

def process_record(record: Dict[str, Any], lang: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Process a single MS MARCO record.
    Returns (document_dict, list_of_passages).
    """
    query = record.get('query', '')
    answers = record.get('answers', [])
    if isinstance(answers, list):
        answer_text = ' '.join(answers)
    else:
        answer_text = str(answers)
        
    passages = record.get('passages', [])
    if not isinstance(passages, list):
        if isinstance(passages, dict):
            # Sometimes Huggingface datasets formats lists of dicts as dict of lists
            # e.g., {'passage_text': [...], 'is_selected': [...]}
            if 'passage_text' in passages:
                passages = [{'passage_text': t, 'is_selected': s} 
                           for t, s in zip(passages.get('passage_text', []), passages.get('is_selected', []))]
            else:
                passages = []
        else:
            passages = []
            
    # Normalize query for hashing
    norm_query = normalize_text(query)
    
    # Generate deterministic document ID
    # Use language and normalized query
    source_str = f"{lang}:{norm_query}"
    doc_id = generate_id(source_str)
    
    # Deduplicate passages
    unique_passages = deduplicate_passages(passages)
    
    document = {
        'id': doc_id,
        'language': lang,
        'query': query,  # preserve original
        'answer': answer_text,
        'passage_count': len(unique_passages),
        'source_hash': doc_id,
        'metadata': record.get('translation_metadata', {})
    }
    
    processed_passages = []
    for idx, p in enumerate(unique_passages):
        p_text = p.get('passage_text', p.get('text', ''))
        p_id = generate_id(f"{doc_id}:{idx}:{normalize_text(p_text)}")
        
        processed_passages.append({
            'id': p_id,
            'document_id': doc_id,
            'language': lang,
            'text': p_text, # preserve original
            'passage_index': idx,
            'metadata_json': p
        })
        
    return document, processed_passages
