from typing import Dict, Any

def decision_from_score(score: float) -> Dict[str, Any]:
    """
    Returns a deterministic decision based on the calculated score.
    """
    if score >= 0.75:
        return {
            "decision": "contact_now",
            "reason": "high_engagement_good_timing",
            "ttl": 3600
        }
    if score >= 0.45:
        return {
            "decision": "wait",
            "reason": "moderate_signals",
            "ttl": 7200
        }
    return {
        "decision": "do_not_contact",
        "reason": "low_intent_or_bad_timing",
        "ttl": 14400
    }
