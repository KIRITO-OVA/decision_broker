def score_to_confidence(score: float) -> float:
    """
    Converts a normalized score (0.0 to 1.0) to a confidence value.
    Rule-based deterministic conversion.
    """
    # Simple linear mapping for now, can be made more complex if needed.
    # Ensuring it stays within 0.0 to 1.0
    return max(0.0, min(1.0, score))

def calculate_confidence_level(score: float, required_threshold: float) -> str:
    """
    Returns a categorical confidence level.
    """
    if score >= 0.9:
        return "HIGH"
    elif score >= required_threshold:
        return "MEDIUM"
    else:
        return "LOW"
