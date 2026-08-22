import pytest
from scripts.utils.chunking import (
    chunk_fixed_overlap, 
    chunk_sentence_semantic,
    chunk_paragraph_aware,
    chunk_parent_child,
    chunk_query_aware,
    chunk_metadata_aware,
    deduplicate_chunks,
    chunk_passage,
    Chunk
)

def test_chunk_fixed_overlap():
    text = " ".join([f"word{i}" for i in range(100)])
    chunks = chunk_fixed_overlap(text, "p1", chunk_sizes=[20], overlap_pct=0.2)
    
    assert len(chunks) > 1
    # Check overlap (size 20, overlap 4 -> step 16)
    assert chunks[0].token_count == 20
    assert chunks[0].strategy == "FIXED_20"
    assert chunks[1].token_count == 20
    
    # Overlap logic: first chunk ends at word19, second chunk starts at word16
    assert "word16" in chunks[0].text
    assert "word16" in chunks[1].text

def test_chunk_sentence_semantic():
    text = "This is sentence one. This is sentence two! And sentence three."
    chunks = chunk_sentence_semantic(text, "p2", max_tokens=6)
    
    # 3 sentences, 4 tokens each (approx). Max tokens 6.
    # So chunk 1: "This is sentence one."
    # Chunk 2: "This is sentence two!"
    # Chunk 3: "And sentence three."
    
    assert len(chunks) == 3
    assert chunks[0].text == "This is sentence one."
    assert chunks[1].text == "This is sentence two!"
    assert chunks[2].text == "And sentence three."

def test_chunk_paragraph_aware():
    text = "Paragraph one is here.\n\nParagraph two is here."
    chunks = chunk_paragraph_aware(text, "p3")
    
    assert len(chunks) == 2
    assert chunks[0].text == "Paragraph one is here."
    assert chunks[1].text == "Paragraph two is here."

def test_chunk_parent_child():
    text = "This is parent. It has children."
    chunks = chunk_parent_child(text, "p4")
    
    assert len(chunks) == 2 # 1 parent + 1 grouped child
    assert chunks[0].strategy == "PARENT_CHILD_PARENT"
    assert chunks[0].text == text
    
    assert chunks[1].strategy == "PARENT_CHILD_CHILD"
    assert chunks[1].parent_id == chunks[0].id

def test_deduplicate_chunks():
    c1 = Chunk(id="1", document_id="d1", passage_id="p1", strategy="S1", language="en", text="text", token_count=1, start_offset=0, end_offset=4)
    c2 = Chunk(id="1", document_id="d1", passage_id="p1", strategy="S1", language="en", text="text", token_count=1, start_offset=0, end_offset=4)
    c3 = Chunk(id="2", document_id="d1", passage_id="p1", strategy="S2", language="en", text="other", token_count=1, start_offset=0, end_offset=5)
    
    unique = deduplicate_chunks([c1, c2, c3])
    assert len(unique) == 2

def test_chunk_metadata_aware():
    c1 = Chunk(id="1", document_id="", passage_id="p1", strategy="S1", language="", text="text", token_count=1, start_offset=0, end_offset=4)
    
    metadata = {"custom_field": "value"}
    updated = chunk_metadata_aware([c1], metadata, "en", "doc1")
    
    assert updated[0].language == "en"
    assert updated[0].document_id == "doc1"
    assert updated[0].metadata["custom_field"] == "value"
    assert updated[0].metadata["chunk_strategy"] == "S1"

def test_chunk_passage_orchestration():
    text = "This is a test passage. It has multiple sentences.\n\nAnd multiple paragraphs."
    chunks = chunk_passage(text, passage_id="p1", document_id="doc1", language="en", profile="BALANCED")
    
    # BALANCED includes sentence, fixed, parent-child
    strategies = [c.strategy for c in chunks]
    assert "SENTENCE_SEMANTIC" in strategies
    assert "PARENT_CHILD_PARENT" in strategies
    assert "PARENT_CHILD_CHILD" in strategies
    
    # Check that metadata got applied
    for c in chunks:
        assert c.document_id == "doc1"
        assert c.language == "en"
