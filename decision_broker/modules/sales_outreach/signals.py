from typing import Dict, Any

def collect_sales_signals(payload: Dict[str, Any]) -> Dict[str, float]:
    """
    Extracts deterministic signals from the payload.
    Returns a dictionary of normalized signals (0.0 to 1.0).
    """
    return {
        "recent_engagement": 1.0 if payload["lead_activity"]["opened_email"] else 0.0,
        "reply_signal": 1.0 if payload["lead_activity"]["replied"] else 0.0,
        "cooldown_respected": 1.0 if payload["last_contact_days"] >= 3 else 0.0,
        "business_hours": 1.0 if 9 <= payload["time_context"]["local_hour"] <= 17 else 0.0,
        "hiring_signal": 1.0 if payload["company_signals"]["recent_hiring"] else 0.0
    }
