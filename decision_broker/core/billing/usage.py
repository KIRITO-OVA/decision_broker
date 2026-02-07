from decision_broker.core.db import get_db_connection, get_cursor, normalize_query, DATABASE_URL

def deduct_credit(user_id: str, amount: int = 1) -> bool:
    """
    Deducts credits if sufficient balance exists.
    Returns True if deduction successful, False if insufficient funds.
    """
    is_pg = bool(DATABASE_URL)
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        
        # Check balance first
        cursor.execute(normalize_query("SELECT credits FROM users WHERE id = ?", is_pg), (user_id,))
        row = cursor.fetchone()
        
        if not row or row["credits"] < amount:
            return False
            
        # Deduct
        cursor.execute(normalize_query("UPDATE users SET credits = credits - ? WHERE id = ?", is_pg), (amount, user_id))
        conn.commit()
        return True
