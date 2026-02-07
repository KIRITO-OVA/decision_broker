from typing import Dict, Any
import random

def calculate_backoff(attempt: int, base_ms: int = 1000, max_ms: int = 60000) -> int:
    """Calculate exponential backoff with jitter."""
    backoff = min(base_ms * (2 ** attempt), max_ms)
    jitter = random.randint(0, int(backoff * 0.3))  # 30% jitter
    return backoff + jitter

def decision_from_score(score: float, signals: Dict[str, float] = None) -> Dict[str, Any]:
    """
    Returns deterministic retry decision based on score.
    Enhanced with exact wait times, backoff calculations, and provider switching.
    """
    signals = signals or {}
    
    attempt = int(signals.get("attempts_remaining", 1) * 3)  # Reverse calculate attempt
    provider_unhealthy = signals.get("provider_unhealthy", 0)
    transient_error = signals.get("transient_error", 0.5)
    budget_ok = signals.get("budget_ok", 1.0)
    
    # No budget - fail fast
    if budget_ok < 0.3:
        return {
            "decision": "fail_fast",
            "reason": "budget_exhausted",
            "wait_seconds": 0,
            "should_retry": False,
            "switch_provider": False,
            "ttl": 300
        }
    
    # Permanent error - don't retry
    if transient_error < 0.2:
        return {
            "decision": "fail_fast",
            "reason": "permanent_error_not_retriable",
            "wait_seconds": 0,
            "should_retry": False,
            "switch_provider": False,
            "ttl": 600
        }
    
    # Provider outage - switch immediately
    if provider_unhealthy >= 0.8 or score >= 0.85:
        return {
            "decision": "switch_provider",
            "reason": "provider_outage_detected",
            "wait_seconds": 0,
            "should_retry": True,
            "switch_provider": True,
            "ttl": 300
        }
    
    # High failure risk - backoff and maybe switch
    if score >= 0.65:
        wait_ms = calculate_backoff(attempt, base_ms=2000)
        return {
            "decision": "retry_with_long_backoff",
            "reason": "high_failure_risk_back_off",
            "wait_seconds": wait_ms // 1000,
            "wait_ms": wait_ms,
            "should_retry": True,
            "switch_provider": provider_unhealthy > 0.5,
            "ttl": 120
        }
    
    # Moderate risk - standard backoff
    if score >= 0.45:
        wait_ms = calculate_backoff(attempt, base_ms=1000)
        return {
            "decision": "retry_with_backoff",
            "reason": "transient_error_worth_retrying",
            "wait_seconds": wait_ms // 1000,
            "wait_ms": wait_ms,
            "should_retry": True,
            "switch_provider": False,
            "ttl": 60
        }
    
    # Low risk - quick retry
    if score >= 0.25:
        wait_ms = calculate_backoff(attempt, base_ms=500)
        return {
            "decision": "retry_immediately",
            "reason": "likely_transient_quick_retry",
            "wait_seconds": max(1, wait_ms // 1000),
            "wait_ms": wait_ms,
            "should_retry": True,
            "switch_provider": False,
            "ttl": 30
        }
    
    # Very low score - likely not worth retrying
    return {
        "decision": "fail_fast",
        "reason": "low_success_probability",
        "wait_seconds": 0,
        "should_retry": False,
        "switch_provider": False,
        "ttl": 600
    }
