import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "decision_broker.db")

def init_db():
    """Initializes the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        api_key TEXT UNIQUE NOT NULL,
        credits INTEGER DEFAULT 0
    )
    ''')
    
    # Pre-seed a test user if empty
    cursor.execute("SELECT count(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (id, api_key, credits) VALUES (?, ?, ?)", 
                      ("test_user", "sk_test_12345", 10))
        print("Initialized DB with test user: sk_test_12345 (10 credits)")
    
    conn.commit()
    conn.close()

@contextmanager
def get_db_connection():
    """Context manager for database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Initialize on import
init_db()
