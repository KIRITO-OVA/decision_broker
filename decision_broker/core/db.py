import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "decision_broker.db")

# Subscription plan configurations
SUBSCRIPTION_PLANS = {
    "starter": {"price": 19900, "credits": 100, "name": "Starter"},
    "pro": {"price": 49900, "credits": 500, "name": "Professional"},
    "business": {"price": 99900, "credits": 2000, "name": "Business"}
}

def init_db():
    """Initializes the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table with subscription support
    cursor.execute('''
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
    ''')
    
    # Pre-seed a test user if empty
    cursor.execute("SELECT count(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (id, api_key, credits) VALUES (?, ?, ?)", 
                      ("test_user", "sk_test_12345", 1000))
        print("Initialized DB with test user: sk_test_12345 (1000 credits)")
    
    # Add new columns if they don't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN subscription_id TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN subscription_status TEXT DEFAULT 'none'")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN subscription_plan TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_charged_at TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN low_balance_notified INTEGER DEFAULT 0")
    except:
        pass
    
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

def update_subscription(user_id: str, subscription_id: str, plan: str, status: str = "active"):
    """Update user's subscription info."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET subscription_id = ?, subscription_plan = ?, subscription_status = ? WHERE id = ?",
            (subscription_id, plan, status, user_id)
        )
        conn.commit()

def get_user_by_subscription(subscription_id: str):
    """Find user by their Razorpay subscription ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE subscription_id = ?", (subscription_id,))
        return cursor.fetchone()

def mark_subscription_charged(user_id: str, credits_to_add: int):
    """Add credits and update last_charged timestamp."""
    from datetime import datetime
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET credits = credits + ?, last_charged_at = ?, low_balance_notified = 0 WHERE id = ?",
            (credits_to_add, datetime.now().isoformat(), user_id)
        )
        conn.commit()

def get_low_balance_users(threshold: int = 10):
    """Get users with low credits who haven't been notified."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE credits < ? AND low_balance_notified = 0 AND email IS NOT NULL",
            (threshold,)
        )
        return cursor.fetchall()

def mark_low_balance_notified(user_id: str):
    """Mark user as notified about low balance."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET low_balance_notified = 1 WHERE id = ?", (user_id,))
        conn.commit()

# Initialize on import
init_db()
