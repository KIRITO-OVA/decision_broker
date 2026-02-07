import sqlite3
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import re

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "decision_broker.db")

# Subscription plan configurations
SUBSCRIPTION_PLANS = {
    "starter": {"price": 19900, "credits": 100, "name": "Starter"},
    "pro": {"price": 49900, "credits": 500, "name": "Professional"},
    "business": {"price": 99900, "credits": 2000, "name": "Business"}
}

DATABASE_URL = os.getenv("DATABASE_URL")

def normalize_query(query: str, is_postgres: bool = False) -> str:
    """Converts SQLite '?' placeholders to PostgreSQL '%s' if needed."""
    if is_postgres:
        return query.replace("?", "%s")
    return query

@contextmanager
def get_db_connection():
    """Context manager for database connection. Supports SQLite and PostgreSQL."""
    if DATABASE_URL:
        # PostgreSQL (Production)
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        try:
            yield conn
        finally:
            conn.close()
    else:
        # SQLite (Local Dev)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

def get_cursor(conn):
    """Returns a cursor that behaves like a dictionary."""
    if DATABASE_URL:
        return conn.cursor(cursor_factory=RealDictCursor)
    return conn.cursor()

def init_db():
    """Initializes the database with required tables."""
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        
        # PostgreSQL uses SERIAL for auto-increment, SQLite uses AUTOINCREMENT or just INTEGER PRIMARY KEY
        is_pg = bool(DATABASE_URL)
        
        # Users table with subscription support
        user_table_query = normalize_query('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            api_key TEXT UNIQUE NOT NULL,
            credits INTEGER DEFAULT 0,
            email TEXT,
            subscription_id TEXT,
            subscription_status TEXT DEFAULT 'none',
            subscription_plan TEXT,
            last_charged_at TEXT,
            low_balance_notified INTEGER DEFAULT 0
        )
        ''', is_pg)
        
        cursor.execute(user_table_query)
        
        # Crypto transactions table for duplicate protection
        crypto_table_query = normalize_query('''
        CREATE TABLE IF NOT EXISTS crypto_transactions (
            tx_hash TEXT PRIMARY KEY, 
            user_id TEXT, 
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''', is_pg)
        cursor.execute(crypto_table_query)

        # Pre-seed a test user if empty
        cursor.execute(normalize_query("SELECT count(*) FROM users", is_pg))
        count = cursor.fetchone()
        if is_pg:
            count_val = count['count'] if count else 0
        else:
            count_val = count[0] if count else 0

        if count_val == 0:
            cursor.execute(normalize_query("INSERT INTO users (id, api_key, credits) VALUES (?, ?, ?)", is_pg),
                          ("test_user", "sk_test_12345", 1000))
            print("Initialized DB with test user: sk_test_12345 (1000 credits)")
        
        # Add new columns only if they don't exist
        migration_cols = [
            ("email", "TEXT"),
            ("subscription_id", "TEXT"),
            ("subscription_status", "TEXT DEFAULT 'none'"),
            ("subscription_plan", "TEXT"),
            ("last_charged_at", "TEXT"),
            ("low_balance_notified", "INTEGER DEFAULT 0")
        ]
        
        # Get existing columns for 'users'
        if is_pg:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
            existing_cols = {row['column_name'] for row in cursor.fetchall()}
        else:
            cursor.execute("PRAGMA table_info(users)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            
        for col_name, col_type in migration_cols:
            if col_name not in existing_cols:
                print(f"[INFO] Adding missing column: {col_name}")
                cursor.execute(normalize_query(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}", is_pg))
        
        conn.commit()

def update_subscription(user_id: str, subscription_id: str, plan: str, status: str = "active"):
    """Update user's subscription info."""
    is_pg = bool(DATABASE_URL)
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            normalize_query("UPDATE users SET subscription_id = ?, subscription_plan = ?, subscription_status = ? WHERE id = ?", is_pg),
            (subscription_id, plan, status, user_id)
        )
        conn.commit()

def get_user_by_subscription(subscription_id: str):
    """Find user by their Razorpay subscription ID."""
    is_pg = bool(DATABASE_URL)
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(normalize_query("SELECT * FROM users WHERE subscription_id = ?", is_pg), (subscription_id,))
        return cursor.fetchone()

def mark_subscription_charged(user_id: str, credits_to_add: int):
    """Add credits and update last_charged timestamp."""
    from datetime import datetime
    is_pg = bool(DATABASE_URL)
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            normalize_query("UPDATE users SET credits = credits + ?, last_charged_at = ?, low_balance_notified = 0 WHERE id = ?", is_pg),
            (credits_to_add, datetime.now().isoformat(), user_id)
        )
        conn.commit()

def get_low_balance_users(threshold: int = 10):
    """Get users with low credits who haven't been notified."""
    is_pg = bool(DATABASE_URL)
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(
            normalize_query("SELECT * FROM users WHERE credits < ? AND low_balance_notified = 0 AND email IS NOT NULL", is_pg),
            (threshold,)
        )
        return cursor.fetchall()

def mark_low_balance_notified(user_id: str):
    """Mark user as notified about low balance."""
    is_pg = bool(DATABASE_URL)
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(normalize_query("UPDATE users SET low_balance_notified = 1 WHERE id = ?", is_pg), (user_id,))
        conn.commit()

# Removed top-level init_db() to prevent startup crashes.
# It is now called during the FastAPI startup event in server.py.
