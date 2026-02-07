from decision_broker.core.db import get_db_connection

def deduct_credit(user_id: str, amount: int = 1) -> bool:
    """
    Deducts credits if sufficient balance exists.
    Returns True if deduction successful, False if insufficient funds.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check balance first
        cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row or row["credits"] < amount:
            return False
            
        # Deduct
        cursor.execute("UPDATE users SET credits = credits - ? WHERE id = ?", (amount, user_id))
        conn.commit()
        return True
