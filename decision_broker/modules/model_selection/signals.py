from typing import Dict, Any

def collect_model_signals(payload: Dict[str, Any]) -> Dict[str, float]:
    """
    Extracts deterministic signals for model selection.
    Returns a dictionary of normalized signals (0.0 to 1.0).
    """
    return {
        "high_accuracy_need": 1.0 if payload.get("accuracy_priority") == "high" else 0.0,
        "low_latency_need": 1.0 if payload.get("latency_requirement_ms", 9999) <= 800 else 0.0,
        "large_context": 1.0 if payload.get("context_tokens", 0) >= 4000 else 0.0,
        "budget_sensitive": 1.0 if payload.get("budget_tier") == "low" else 0.0,
        "complex_task": 1.0 if payload.get("task_type") in ["code", "reasoning"] else 0.0
    }
