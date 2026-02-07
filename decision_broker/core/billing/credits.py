from decision_broker.core.db import get_db_connection

def check_credits(user_id: str) -> int:
    """Returns the current credit balance for the user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return row["credits"]
        return 0

def add_credits(user_id: str, amount: int) -> int:
    """Adds credits to the user. Returns new balance."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET credits = credits + ? WHERE id = ?", (amount, user_id))
        conn.commit()
        
        cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return row["credits"]
