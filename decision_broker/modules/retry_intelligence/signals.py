from typing import Dict, Any

def collect_retry_signals(payload: Dict[str, Any]) -> Dict[str, float]:
    """
    Extracts deterministic signals for retry intelligence.
    Returns a dictionary of normalized signals (0.0 to 1.0).
    Enhanced with more nuanced error analysis and provider awareness.
    """
    error_type = payload.get("error_type", "").lower()
    attempt = payload.get("attempt_number", 1)
    max_attempts = payload.get("max_attempts", 3)
    latency = payload.get("latency_ms", 0)
    provider_status = payload.get("provider_status", "unknown").lower()
    is_idempotent = payload.get("is_idempotent", True)
    budget_remaining = payload.get("budget_remaining", 100)
    error_code = payload.get("error_code", 0)
    
    # Transient error detection (worth retrying)
    transient_errors = ["timeout", "rate_limit", "503", "502", "504", "connection_reset"]
    permanent_errors = ["401", "403", "404", "invalid_request", "auth_failed"]
    
    if any(e in error_type for e in transient_errors) or error_code in [429, 502, 503, 504]:
        transient_error = 1.0
    elif any(e in error_type for e in permanent_errors) or error_code in [400, 401, 403, 404]:
        transient_error = 0.0
    else:
        transient_error = 0.5  # Unknown error type
    
    # Attempts remaining
    if attempt >= max_attempts:
        attempts_remaining = 0.0
    else:
        attempts_remaining = 1.0 - (attempt / max_attempts)
    
    # Provider health
    provider_scores = {
        "healthy": 0.0,
        "degraded": 0.5,
        "outage": 1.0,
        "unknown": 0.3
    }
    provider_unhealthy = provider_scores.get(provider_status, 0.3)
    
    # Latency impact (slow responses suggest issues)
    if latency >= 10000:
        slow_response = 1.0
    elif latency >= 5000:
        slow_response = 0.7
    elif latency >= 2000:
        slow_response = 0.3
    else:
        slow_response = 0.0
    
    # Idempotency - safe to retry?
    safe_to_retry = 1.0 if is_idempotent else 0.0
    
    # Budget awareness
    if budget_remaining <= 0:
        budget_ok = 0.0
    elif budget_remaining <= 10:
        budget_ok = 0.3
    elif budget_remaining <= 50:
        budget_ok = 0.7
    else:
        budget_ok = 1.0
    
    return {
        "transient_error": transient_error,
        "attempts_remaining": attempts_remaining,
        "provider_unhealthy": provider_unhealthy,
        "slow_response": slow_response,
        "safe_to_retry": safe_to_retry,
        "budget_ok": budget_ok
    }
