import pytest
from scripts.utils.processing import normalize_text, generate_id, deduplicate_passages, process_record

def test_normalization():
    # Whitespace
    assert normalize_text("  hello   world  \n ") == "hello world"
    # Unicode NFKC
    assert normalize_text("he\u2113\u2113o") == "hello" # \u2113 is script small l
    # Empty
    assert normalize_text(None) == ""
    assert normalize_text("") == ""

def test_deterministic_ids():
    text1 = "This is a test."
    text2 = "This is a test."
    text3 = "This is another test."
    
    assert generate_id(text1) == generate_id(text2)
    assert generate_id(text1) != generate_id(text3)

def test_duplicate_detection():
    passages = [
        {"passage_text": "Same content here", "is_selected": 0},
        {"passage_text": "Same content here ", "is_selected": 1},
        {"passage_text": "Different content", "is_selected": 0}
    ]
    unique = deduplicate_passages(passages)
    assert len(unique) == 2
    assert unique[0]["passage_text"] == "Same content here"
    assert unique[1]["passage_text"] == "Different content"

def test_process_malformed_records():
    # Missing fields
    record1 = {}
    doc1, pass1 = process_record(record1, "en")
    assert doc1['query'] == ""
    assert doc1['answer'] == ""
    assert doc1['passage_count'] == 0
    assert len(pass1) == 0
    
    # Weird type for answers
    record2 = {"query": "Q2", "answers": "Just a string answer"}
    doc2, pass2 = process_record(record2, "hi")
    assert doc2['answer'] == "Just a string answer"
    
    # Weird type for passages (dict of lists)
    record3 = {
        "query": "Q3", 
        "passages": {
            "passage_text": ["p1", "p2", "p1"],
            "is_selected": [1, 0, 0]
        }
    }
    doc3, pass3 = process_record(record3, "te")
    assert doc3['passage_count'] == 2 # 1 duplicate removed
    assert len(pass3) == 2
    assert pass3[0]['text'] == "p1"
    assert pass3[1]['text'] == "p2"

def test_missing_fields_graceful_handling():
    record = {"query": "Valid query", "answers": ["Ans1", "Ans2"]}
    doc, passages = process_record(record, "kn")
    assert doc['query'] == "Valid query"
    assert doc['answer'] == "Ans1 Ans2"
    assert doc['passage_count'] == 0
    assert len(passages) == 0
