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
    
    # Handle time_context - enhanced with time-of-day and day-of-week awareness
    time_context = payload.get("time_context", {})
    hour = time_context.get("hour", time_context.get("local_hour", 12))
    weekday = time_context.get("weekday", time_context.get("day", "tuesday")).lower()
    
    # Best hours: 10-12am and 2-4pm
    if 10 <= hour <= 12 or 14 <= hour <= 16:
        business_hours = 1.0
    elif 9 <= hour <= 17:
        business_hours = 0.7
    else:
        business_hours = 0.0
    
    # Best days: Tuesday, Wednesday, Thursday
    day_score = {
        "monday": 0.6,
        "tuesday": 1.0,
        "wednesday": 1.0,
        "thursday": 0.9,
        "friday": 0.5,
        "saturday": 0.1,
        "sunday": 0.0
    }.get(weekday, 0.5)
    
    # Handle company_signals
    company_signals = payload.get("company_signals", {})
    hiring_signal = 1.0 if company_signals.get("recent_hiring", company_signals.get("recent_funding", False)) else 0.0
    growth_signal = 1.0 if company_signals.get("growth_rate", 0) > 20 else 0.5
    tech_match = 1.0 if company_signals.get("uses_similar_tech", False) else 0.5
    
    # Handle last_contact_days
    last_contact_days = payload.get("last_contact_days", 0)
    if last_contact_days >= 7:
        cooldown_respected = 1.0
    elif last_contact_days >= 3:
        cooldown_respected = 0.7
    elif last_contact_days >= 1:
        cooldown_respected = 0.3
    else:
        cooldown_respected = 0.0
    
    # Urgency signals
    urgency = payload.get("urgency", "normal").lower()
    urgency_score = {"hot": 1.0, "warm": 0.7, "normal": 0.5, "cold": 0.2}.get(urgency, 0.5)
    
    # Preferred channel
    preferred_channel = payload.get("preferred_channel", "any").lower()
    
    return {
        "recent_engagement": recent_engagement,
        "reply_signal": reply_signal,
        "cooldown_respected": cooldown_respected,
        "business_hours": business_hours,
        "day_score": day_score,
        "hiring_signal": hiring_signal,
        "growth_signal": growth_signal,
        "tech_match": tech_match,
        "urgency_score": urgency_score
    }
