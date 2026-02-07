from typing import Dict, Any

def calculate_weighted_score(signals: Dict[str, Any], weights: Dict[str, float]) -> float:
    """
    Calculates a deterministic weighted score based on numerical signals.
    
    Args:
        signals: Dictionary of signal names to numerical values (0.0 to 1.0).
        weights: Dictionary of signal names to weight values (0.0 to 1.0).
        
    Returns:
        float: Weighted average score between 0.0 and 1.0.
    """
    if not signals or not weights:
        return 0.0
        
    total_weight = 0.0
    weighted_sum = 0.0
    
    for signal_name, weight in weights.items():
        if signal_name in signals:
            value = float(signals[signal_name])
            # Clamp value between 0.0 and 1.0
            value = max(0.0, min(1.0, value))
            
            weighted_sum += value * weight
            total_weight += weight
            
    if total_weight == 0.0:
        return 0.0
        
    return weighted_sum / total_weight
