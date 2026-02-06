from typing import Dict, Any

def decision_from_score(score: float) -> Dict[str, Any]:
    """
    Returns a deterministic decision based on the calculated score.
    """
    if score >= 0.75:
        return {
            "decision": "use_gpt_4",
            "reason": "high_accuracy_complex_task",
            "ttl": 3600
        }
    if score >= 0.55:
        return {
            "decision": "use_gpt_4o",
            "reason": "balanced_quality_latency",
            "ttl": 1800
        }
    return {
        "decision": "use_fast_small_model",
        "reason": "cost_or_latency_sensitive",
        "ttl": 900
    }
