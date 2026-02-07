from decision_broker.core.db import get_db_connection, get_cursor, normalize_query, DATABASE_URL

def validate_api_key(api_key: str) -> Optional[str]:
    """
    Validates the API key.
    Returns user_id if valid, None otherwise.
    """
    is_pg = bool(DATABASE_URL)
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(normalize_query("SELECT id FROM users WHERE api_key = ?", is_pg), (api_key,))
        row = cursor.fetchone()
        
        if row:
            return row["id"]
        return None
