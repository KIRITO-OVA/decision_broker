# Signal weights for model selection decisions
# Higher weights = more influence on final score

SIGNAL_WEIGHTS = {
    "high_accuracy_need": 0.25,     # How critical is accuracy?
    "complex_task": 0.20,           # Is the task complex?
    "large_context": 0.15,          # Do we need long context?
    "low_latency_need": 0.15,       # Is speed critical?
    "budget_sensitive": 0.10,       # Is cost a concern?
    "needs_vision": 0.10,           # Does task need image understanding?
    "needs_audio": 0.05             # Does task need audio processing?
}
