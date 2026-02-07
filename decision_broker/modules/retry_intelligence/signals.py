from typing import Dict, Any

def collect_retry_signals(payload: Dict[str, Any]) -> Dict[str, float]:
    """
    Extracts signals for retry logic.
    """
    return {
        "retry_safe": 1.0 if payload.get("is_idempotent") else 0.0,
        "near_limit": 1.0 if payload.get("attempt_number", 0) >= payload.get("max_attempts", 1) - 1 else 0.0,
        "provider_unhealthy": 1.0 if payload.get("provider_status") != "healthy" else 0.0,
        "latency_high": 1.0 if payload.get("latency_ms", 0) > 1000 else 0.0,
        "budget_low": 1.0 if payload.get("budget_remaining") == "low" else 0.0
    }
