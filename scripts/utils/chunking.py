import re
import hashlib
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Unified Chunk Schema
class Chunk(BaseModel):
    id: str
    document_id: str
    passage_id: str
    parent_id: Optional[str] = None
    strategy: str
    language: str
    text: str
    token_count: int
    start_offset: int
    end_offset: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Helper for basic word-level token counting (heuristic for Indic/English)
def count_tokens(text: str) -> int:
    # A simple heuristic: split by whitespace. 
    # For production, replace with a proper tokenizer like tiktoken or a sentence-transformers tokenizer.
    return len(text.split())

def generate_chunk_id(strategy: str, passage_id: str, text: str) -> str:
    content = f"{strategy}:{passage_id}:{text}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def chunk_fixed_overlap(passage_text: str, passage_id: str, chunk_sizes: List[int] = [256, 384, 512], overlap_pct: float = 0.2) -> List[Chunk]:
    chunks = []
    words = passage_text.split()
    total_tokens = len(words)
    
    for size in chunk_sizes:
        overlap = int(size * overlap_pct)
        step = size - overlap
        if step <= 0:
            step = 1
            
        for i in range(0, total_tokens, step):
            chunk_words = words[i:i+size]
            if not chunk_words:
                continue
            chunk_text = " ".join(chunk_words)
            # Find approximate character offsets
            start_offset = passage_text.find(chunk_words[0]) if chunk_words else 0
            end_offset = start_offset + len(chunk_text)
            
            c = Chunk(
                id=generate_chunk_id(f"FIXED_{size}", passage_id, chunk_text),
                document_id="", passage_id=passage_id, strategy=f"FIXED_{size}",
                language="", text=chunk_text, token_count=len(chunk_words),
                start_offset=start_offset, end_offset=end_offset
            )
            chunks.append(c)
    return chunks

def chunk_sentence_semantic(passage_text: str, passage_id: str, max_tokens: int = 256) -> List[Chunk]:
    # Basic sentence splitter for multiple languages (using punctuation heuristics)
    # E.g., ., !, ?, and Hindi purna viram (।)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?।])\s+', passage_text) if s.strip()]
    
    chunks = []
    current_chunk_sentences = []
    current_tokens = 0
    start_char_idx = 0
    
    for sentence in sentences:
        tokens = count_tokens(sentence)
        if current_tokens + tokens > max_tokens and current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            c = Chunk(
                id=generate_chunk_id("SENTENCE_SEMANTIC", passage_id, chunk_text),
                document_id="", passage_id=passage_id, strategy="SENTENCE_SEMANTIC",
                language="", text=chunk_text, token_count=current_tokens,
                start_offset=start_char_idx, end_offset=start_char_idx + len(chunk_text)
            )
            chunks.append(c)
            # Find next start idx
            start_char_idx = passage_text.find(sentence, start_char_idx)
            current_chunk_sentences = [sentence]
            current_tokens = tokens
        else:
            if not current_chunk_sentences:
                start_char_idx = passage_text.find(sentence, max(0, start_char_idx))
            current_chunk_sentences.append(sentence)
            current_tokens += tokens
            
    if current_chunk_sentences:
        chunk_text = " ".join(current_chunk_sentences)
        c = Chunk(
            id=generate_chunk_id("SENTENCE_SEMANTIC", passage_id, chunk_text),
            document_id="", passage_id=passage_id, strategy="SENTENCE_SEMANTIC",
            language="", text=chunk_text, token_count=current_tokens,
            start_offset=start_char_idx, end_offset=start_char_idx + len(chunk_text)
        )
        chunks.append(c)
        
    return chunks

def chunk_paragraph_aware(passage_text: str, passage_id: str, max_tokens: int = 512) -> List[Chunk]:
    paragraphs = [p.strip() for p in passage_text.split('\n\n') if p.strip()]
    chunks = []
    
    start_char_idx = 0
    for para in paragraphs:
        tokens = count_tokens(para)
        
        # If paragraph is too big, fall back to sentence chunking for just this paragraph
        if tokens > max_tokens:
            sub_chunks = chunk_sentence_semantic(para, passage_id, max_tokens)
            for sc in sub_chunks:
                sc.strategy = "PARAGRAPH_AWARE_SPLIT"
                # Adjust offsets
                sc.start_offset += start_char_idx
                sc.end_offset += start_char_idx
                sc.id = generate_chunk_id(sc.strategy, passage_id, sc.text)
                chunks.append(sc)
            start_char_idx += len(para) + 2 # rough offset update
        else:
            start_char_idx = passage_text.find(para, start_char_idx)
            c = Chunk(
                id=generate_chunk_id("PARAGRAPH_AWARE", passage_id, para),
                document_id="", passage_id=passage_id, strategy="PARAGRAPH_AWARE",
                language="", text=para, token_count=tokens,
                start_offset=start_char_idx, end_offset=start_char_idx + len(para)
            )
            chunks.append(c)
            start_char_idx += len(para)
            
    return chunks

def chunk_parent_child(passage_text: str, passage_id: str) -> List[Chunk]:
    # Parent chunk is the whole passage
    parent = Chunk(
        id=generate_chunk_id("PARENT_CHILD_PARENT", passage_id, passage_text),
        document_id="", passage_id=passage_id, strategy="PARENT_CHILD_PARENT",
        language="", text=passage_text, token_count=count_tokens(passage_text),
        start_offset=0, end_offset=len(passage_text)
    )
    
    # Children are sentences
    children = chunk_sentence_semantic(passage_text, passage_id, max_tokens=128)
    for c in children:
        c.parent_id = parent.id
        c.strategy = "PARENT_CHILD_CHILD"
        c.id = generate_chunk_id("PARENT_CHILD_CHILD", passage_id, c.text)
        
    return [parent] + children

def chunk_query_aware(passage_text: str, passage_id: str, query: str) -> List[Chunk]:
    # In a real impl, we'd use sentence-transformers to score sentences against the query here.
    # For now, we mock it by picking sentences that contain query keywords.
    if not query:
        return []
        
    query_words = set(query.lower().split())
    sentences = [s.strip() for s in re.split(r'(?<=[.!?।])\s+', passage_text) if s.strip()]
    
    scored_sentences = []
    for s in sentences:
        s_words = set(s.lower().split())
        score = len(query_words.intersection(s_words))
        if score > 0:
            scored_sentences.append(s)
            
    if not scored_sentences:
        return []
        
    chunk_text = " ".join(scored_sentences[:3]) # Top 3 scoring sentences
    start_offset = passage_text.find(scored_sentences[0]) if scored_sentences else 0
    
    c = Chunk(
        id=generate_chunk_id("QUERY_AWARE", passage_id, chunk_text),
        document_id="", passage_id=passage_id, strategy="QUERY_AWARE",
        language="", text=chunk_text, token_count=count_tokens(chunk_text),
        start_offset=start_offset, end_offset=start_offset + len(chunk_text)
    )
    return [c]

def chunk_metadata_aware(chunks: List[Chunk], metadata: Dict[str, Any], language: str, document_id: str) -> List[Chunk]:
    for c in chunks:
        c.metadata.update(metadata)
        c.metadata['chunk_strategy'] = c.strategy
        c.metadata['parent_document'] = document_id
        c.metadata['original_passage'] = c.passage_id
        
        c.language = language
        c.document_id = document_id
    return chunks

def deduplicate_chunks(chunks: List[Chunk]) -> List[Chunk]:
    seen = set()
    unique = []
    for c in chunks:
        # We can deduplicate by text and strategy, or just by ID
        if c.id not in seen:
            seen.add(c.id)
            unique.append(c)
    return unique

def chunk_passage(passage_text: str, passage_id: str, document_id: str, language: str, 
                  metadata: Dict[str, Any] = {}, query: str = "", profile: str = "BALANCED") -> List[Chunk]:
    
    all_chunks = []
    
    if profile in ["FAST", "QUALITY"]:
        all_chunks.extend(chunk_paragraph_aware(passage_text, passage_id))
        
    if profile in ["FAST", "BALANCED", "QUALITY"]:
        all_chunks.extend(chunk_sentence_semantic(passage_text, passage_id))
        
    if profile in ["BALANCED", "QUALITY"]:
        all_chunks.extend(chunk_fixed_overlap(passage_text, passage_id))
        all_chunks.extend(chunk_parent_child(passage_text, passage_id))
        
    if profile == "QUALITY" and query:
        all_chunks.extend(chunk_query_aware(passage_text, passage_id, query))
        
    # Deduplicate
    unique_chunks = deduplicate_chunks(all_chunks)
    
    # Apply metadata
    final_chunks = chunk_metadata_aware(unique_chunks, metadata, language, document_id)
    
    return final_chunks
