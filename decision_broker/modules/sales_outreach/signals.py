from typing import Dict, Any

def collect_sales_signals(payload: Dict[str, Any]) -> Dict[str, float]:
    """
    Extracts deterministic signals from the payload.
    Returns a dictionary of normalized signals (0.0 to 1.0).
    Handles both simple and nested payload formats.
    """
    # Handle lead_activity - can be string or dict
    lead_activity = payload.get("lead_activity", {})
    if isinstance(lead_activity, str):
        # Simple format: "high", "medium", "low"
        recent_engagement = 1.0 if lead_activity == "high" else (0.5 if lead_activity == "medium" else 0.0)
        reply_signal = 1.0 if lead_activity == "high" else 0.0
    else:
        # Nested format
        recent_engagement = 1.0 if lead_activity.get("opened_email", False) else 0.0
        reply_signal = 1.0 if lead_activity.get("replied", False) else 0.0
    
    # Handle time_context - can have different key names
    time_context = payload.get("time_context", {})
    hour = time_context.get("hour", time_context.get("local_hour", 12))
    business_hours = 1.0 if 9 <= hour <= 17 else 0.0
    
    # Handle company_signals
    company_signals = payload.get("company_signals", {})
    hiring_signal = 1.0 if company_signals.get("recent_hiring", company_signals.get("recent_funding", False)) else 0.0
    
    # Handle last_contact_days
    last_contact_days = payload.get("last_contact_days", 0)
    cooldown_respected = 1.0 if last_contact_days >= 3 else 0.0
    
    return {
        "recent_engagement": recent_engagement,
        "reply_signal": reply_signal,
        "cooldown_respected": cooldown_respected,
        "business_hours": business_hours,
        "hiring_signal": hiring_signal
    }
