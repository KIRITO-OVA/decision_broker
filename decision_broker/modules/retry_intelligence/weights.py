# Signal weights for retry intelligence decisions
# Higher weights = more influence on final score

SIGNAL_WEIGHTS = {
    "transient_error": 0.25,        # Is this a retriable error type?
    "attempts_remaining": 0.20,     # Do we have attempts left?
    "provider_unhealthy": 0.20,     # Is the provider having issues?
    "safe_to_retry": 0.15,          # Is the operation idempotent?
    "budget_ok": 0.10,              # Do we have budget for retries?
    "slow_response": 0.10           # Was the response slow (indicating load)?
}
