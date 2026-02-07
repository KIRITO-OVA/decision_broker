from typing import Dict, Any

# Model database with capabilities and costs
MODELS = {
    "gpt-4-turbo": {
        "tier": "premium",
        "context": 128000,
        "cost_per_1k": 0.01,
        "latency": "medium",
        "strengths": ["reasoning", "code", "analysis"]
    },
    "gpt-4o": {
        "tier": "premium",
        "context": 128000,
        "cost_per_1k": 0.005,
        "latency": "fast",
        "strengths": ["multimodal", "general", "vision"]
    },
    "claude-3-opus": {
        "tier": "premium",
        "context": 200000,
        "cost_per_1k": 0.015,
        "latency": "medium",
        "strengths": ["writing", "analysis", "long_context"]
    },
    "claude-3-sonnet": {
        "tier": "balanced",
        "context": 200000,
        "cost_per_1k": 0.003,
        "latency": "fast",
        "strengths": ["general", "code", "writing"]
    },
    "gemini-1.5-pro": {
        "tier": "balanced",
        "context": 1000000,
        "cost_per_1k": 0.0025,
        "latency": "fast",
        "strengths": ["long_context", "multimodal", "reasoning"]
    },
    "gpt-3.5-turbo": {
        "tier": "economy",
        "context": 16000,
        "cost_per_1k": 0.0005,
        "latency": "very_fast",
        "strengths": ["chat", "simple", "fast"]
    },
    "llama-3-70b": {
        "tier": "economy",
        "context": 8000,
        "cost_per_1k": 0.0007,
        "latency": "fast",
        "strengths": ["general", "open_source"]
    },
    "mistral-large": {
        "tier": "balanced",
        "context": 32000,
        "cost_per_1k": 0.002,
        "latency": "fast",
        "strengths": ["code", "reasoning", "multilingual"]
    }
}

def decision_from_score(score: float, signals: Dict[str, float] = None) -> Dict[str, Any]:
    """
    Returns a deterministic model recommendation based on the calculated score.
    Enhanced with specific model recommendations, cost estimates, and fallbacks.
    """
    signals = signals or {}
    
    needs_vision = signals.get("needs_vision", 0) > 0.5
    large_context = signals.get("large_context", 0) > 0.5
    budget_sensitive = signals.get("budget_sensitive", 0) > 0.7
    complex_task = signals.get("complex_task", 0)
    
    # Vision tasks
    if needs_vision:
        return {
            "decision": "gpt-4o",
            "fallback": "gemini-1.5-pro",
            "reason": "vision_capability_required",
            "cost_estimate": "$0.005/1k tokens",
            "ttl": 3600
        }
    
    # Very long context
    if large_context:
        return {
            "decision": "gemini-1.5-pro",
            "fallback": "claude-3-opus",
            "reason": "long_context_required",
            "cost_estimate": "$0.0025/1k tokens", 
            "ttl": 3600
        }
    
    # Premium tier - complex tasks, high accuracy
    if score >= 0.75:
        return {
            "decision": "gpt-4-turbo",
            "fallback": "claude-3-opus",
            "reason": "high_accuracy_complex_task",
            "cost_estimate": "$0.01/1k tokens",
            "ttl": 3600
        }
    
    # Balanced tier - good quality, reasonable cost
    if score >= 0.55:
        if budget_sensitive:
            return {
                "decision": "claude-3-sonnet",
                "fallback": "mistral-large",
                "reason": "balanced_quality_budget_conscious",
                "cost_estimate": "$0.003/1k tokens",
                "ttl": 1800
            }
        return {
            "decision": "gpt-4o",
            "fallback": "claude-3-sonnet",
            "reason": "balanced_quality_speed",
            "cost_estimate": "$0.005/1k tokens",
            "ttl": 1800
        }
    
    # Economy tier - simple tasks, cost priority
    if score >= 0.35:
        return {
            "decision": "gpt-3.5-turbo",
            "fallback": "llama-3-70b",
            "reason": "cost_optimized",
            "cost_estimate": "$0.0005/1k tokens",
            "ttl": 900
        }
    
    # Ultra-economy
    return {
        "decision": "llama-3-70b",
        "fallback": "gpt-3.5-turbo",
        "reason": "maximum_cost_savings",
        "cost_estimate": "$0.0007/1k tokens",
        "ttl": 900
    }
