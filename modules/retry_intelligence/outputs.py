from typing import Dict, Any

def decision_from_score(score: float) -> Dict[str, Any]:
    """
    Returns deterministic retry decision based on score.
    """
    if score >= 0.75:
        return {
            "decision": "switch_provider",
            "reason": "high_failure_risk",
            "ttl": 300
        }
    if score >= 0.5:
        return {
            "decision": "retry_with_backoff",
            "reason": "moderate_risk",
            "ttl": 120
        }
    if score >= 0.3:
        return {
            "decision": "retry_immediately",
            "reason": "low_risk_retry",
            "ttl": 60
        }
    return {
        "decision": "fail_fast",
        "reason": "non_retriable_or_costly",
        "ttl": 600
    }
