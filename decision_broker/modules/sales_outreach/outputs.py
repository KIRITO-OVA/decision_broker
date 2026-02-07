from typing import Dict, Any

def decision_from_score(score: float, signals: Dict[str, float] = None) -> Dict[str, Any]:
    """
    Returns a deterministic decision based on the calculated score.
    Enhanced with multi-channel recommendations and specific timing advice.
    """
    signals = signals or {}
    
    # Determine best channel based on signals
    def get_channel():
        engagement = signals.get("recent_engagement", 0.5)
        if engagement >= 0.8:
            return "call"  # Hot leads get direct calls
        elif engagement >= 0.5:
            return "email"  # Warm leads get emails
        else:
            return "linkedin"  # Cold leads get LinkedIn
    
    # Determine timing advice
    def get_timing_advice():
        business_hours = signals.get("business_hours", 0.5)
        day_score = signals.get("day_score", 0.5)
        
        if business_hours < 0.5:
            return "wait_until_business_hours"
        if day_score < 0.3:
            return "wait_until_weekday"
        return None
    
    timing = get_timing_advice()
    channel = get_channel()
    
    if score >= 0.80:
        return {
            "decision": f"contact_now_via_{channel}",
            "channel": channel,
            "reason": "high_engagement_optimal_timing",
            "ttl": 1800,  # 30 min - act fast!
            "priority": "high"
        }
    
    if score >= 0.65:
        return {
            "decision": "contact_now",
            "channel": channel,
            "reason": "good_signals_favorable_timing",
            "ttl": 3600,
            "priority": "medium"
        }
    
    if score >= 0.45:
        if timing:
            return {
                "decision": timing,
                "channel": channel,
                "reason": "moderate_signals_suboptimal_timing",
                "ttl": 7200,
                "priority": "low"
            }
        return {
            "decision": "nurture_with_content",
            "channel": "email",
            "reason": "warm_lead_needs_nurturing",
            "ttl": 14400,
            "priority": "low"
        }
    
    if score >= 0.25:
        return {
            "decision": "wait_and_monitor",
            "channel": "none",
            "reason": "low_engagement_wait_for_signals",
            "ttl": 86400,  # Check again tomorrow
            "priority": "none"
        }
    
    return {
        "decision": "do_not_contact",
        "channel": "none",
        "reason": "low_intent_or_bad_timing",
        "ttl": 172800,  # 2 days
        "priority": "none"
    }
