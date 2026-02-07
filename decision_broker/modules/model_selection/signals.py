from typing import Dict, Any

def collect_model_signals(payload: Dict[str, Any]) -> Dict[str, float]:
    """
    Extracts deterministic signals for model selection.
    Returns a dictionary of normalized signals (0.0 to 1.0).
    Enhanced with more nuanced task and context awareness.
    """
    task_type = payload.get("task_type", "general").lower()
    accuracy = payload.get("accuracy_priority", "medium").lower()
    budget = payload.get("budget_tier", "medium").lower()
    latency = payload.get("latency_requirement_ms", 5000)
    context_tokens = payload.get("context_tokens", 0)
    
    # Accuracy needs
    accuracy_scores = {"critical": 1.0, "high": 0.9, "medium": 0.5, "low": 0.2}
    high_accuracy_need = accuracy_scores.get(accuracy, 0.5)
    
    # Latency needs (lower = more urgent)
    if latency <= 500:
        low_latency_need = 1.0
    elif latency <= 1000:
        low_latency_need = 0.8
    elif latency <= 3000:
        low_latency_need = 0.5
    else:
        low_latency_need = 0.0
    
    # Context size needs
    if context_tokens >= 100000:
        large_context = 1.0
    elif context_tokens >= 32000:
        large_context = 0.8
    elif context_tokens >= 8000:
        large_context = 0.5
    else:
        large_context = 0.0
    
    # Budget sensitivity
    budget_scores = {"free": 1.0, "low": 0.8, "medium": 0.4, "high": 0.1, "unlimited": 0.0}
    budget_sensitive = budget_scores.get(budget, 0.4)
    
    # Task complexity - which tasks need the best models
    complex_tasks = ["code", "reasoning", "math", "analysis", "legal", "medical"]
    moderate_tasks = ["writing", "summarization", "translation"]
    simple_tasks = ["chat", "classification", "extraction"]
    
    if task_type in complex_tasks:
        complex_task = 1.0
    elif task_type in moderate_tasks:
        complex_task = 0.5
    else:
        complex_task = 0.2
    
    # Multimodal needs
    needs_vision = 1.0 if payload.get("needs_vision", False) else 0.0
    needs_audio = 1.0 if payload.get("needs_audio", False) else 0.0
    
    return {
        "high_accuracy_need": high_accuracy_need,
        "low_latency_need": low_latency_need,
        "large_context": large_context,
        "budget_sensitive": budget_sensitive,
        "complex_task": complex_task,
        "needs_vision": needs_vision,
        "needs_audio": needs_audio
    }
