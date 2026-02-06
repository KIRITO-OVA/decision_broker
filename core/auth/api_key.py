from typing import Optional
from decision_broker.core.db import get_db_connection

def validate_api_key(api_key: str) -> Optional[str]:
    """
    Validates the API key.
    Returns user_id if valid, None otherwise.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE api_key = ?", (api_key,))
        row = cursor.fetchone()
        
        if row:
            return row["id"]
        return None
