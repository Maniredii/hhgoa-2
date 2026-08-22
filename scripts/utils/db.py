import sqlite3
import json
from typing import Dict, List, Any

def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def setup_schema(conn: sqlite3.Connection):
    """Create tables if they don't exist according to the specified schema."""
    cursor = conn.cursor()
    
    # Documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            language TEXT,
            query TEXT,
            answer TEXT,
            passage_count INTEGER,
            source_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Passages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passages (
            id TEXT PRIMARY KEY,
            document_id TEXT,
            language TEXT,
            text TEXT,
            passage_index INTEGER,
            metadata_json TEXT,
            FOREIGN KEY(document_id) REFERENCES documents(id)
        )
    ''')
    
    # Indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_doc_lang ON documents(language)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pass_doc ON passages(document_id)')
    
    conn.commit()

def save_records(conn: sqlite3.Connection, documents: List[Dict], passages: List[Dict]):
    """
    Save documents and passages.
    Uses INSERT OR IGNORE to handle determinism/resumability.
    """
    cursor = conn.cursor()
    
    # Insert documents
    doc_data = [
        (d['id'], d['language'], d['query'], d['answer'], d['passage_count'], d['source_hash'])
        for d in documents
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO documents (id, language, query, answer, passage_count, source_hash)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', doc_data)
    
    # Insert passages
    pass_data = [
        (p['id'], p['document_id'], p['language'], p['text'], p['passage_index'], json.dumps(p.get('metadata_json', {})))
        for p in passages
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO passages (id, document_id, language, text, passage_index, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', pass_data)
    
    conn.commit()
