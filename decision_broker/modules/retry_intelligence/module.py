from typing import Dict, Any
from decision_broker.core.decision_engine.base import DecisionModule
from decision_broker.core.decision_engine.scorer import calculate_weighted_score
from decision_broker.modules.retry_intelligence.signals import collect_retry_signals
from decision_broker.modules.retry_intelligence.weights import SIGNAL_WEIGHTS
from decision_broker.modules.retry_intelligence.outputs import decision_from_score
from decision_broker.schemas import DecisionRequest, DecisionResponse

class RetryIntelligenceModule(DecisionModule):

    def validate_input(self, request: DecisionRequest) -> bool:
        """
        Validates the payload has all required fields.
        """
        payload = request.payload
        required = [
            "error_type",
            "attempt_number",
            "max_attempts",
            "latency_ms",
            "provider_status",
            "is_idempotent",
            "budget_remaining"
        ]
        for key in required:
            if key not in payload:
                raise ValueError(f"Missing required field: {key}")
        return True

    def collect_signals(self, request: DecisionRequest) -> Dict[str, float]:
        """
        Collects signals using the signals module.
        """
        return collect_retry_signals(request.payload)

    def score(self, signals: Dict[str, float]) -> float:
        """
        Calculates score using the generic weighted scorer and defined weights.
        """
        return calculate_weighted_score(signals, SIGNAL_WEIGHTS)

    def decide(self, request: DecisionRequest) -> DecisionResponse:
        """
        Full decision pipeline: Validate -> Collect -> Score -> Output.
        """
        # 1. Collect Signals
        signals = self.collect_signals(request)
        
        # 2. Score
        score_val = self.score(signals)
        
        # 3. Decision Rules (pass signals for context-aware decisions)
        result = decision_from_score(score_val, signals)
        
        # 4. Construct Response
        return DecisionResponse(
            decision=result,
            confidence=score_val,
            reason_code=result["reason"],
            valid_for_seconds=result["ttl"]
        )
