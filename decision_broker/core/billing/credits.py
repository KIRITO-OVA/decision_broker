from decision_broker.core.db import get_db_connection, get_cursor, normalize_query, DATABASE_URL

def check_credits(user_id: str) -> int:
    """Returns the current credit balance for the user."""
    is_pg = bool(DATABASE_URL)
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(normalize_query("SELECT credits FROM users WHERE id = ?", is_pg), (user_id,))
        row = cursor.fetchone()
        if row:
            return row["credits"]
        return 0

def add_credits(user_id: str, amount: int) -> int:
    """Adds credits to the user. Returns new balance."""
    is_pg = bool(DATABASE_URL)
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(normalize_query("UPDATE users SET credits = credits + ? WHERE id = ?", is_pg), (amount, user_id))
        conn.commit()
        
        cursor.execute(normalize_query("SELECT credits FROM users WHERE id = ?", is_pg), (user_id,))
        row = cursor.fetchone()
        return row["credits"]
