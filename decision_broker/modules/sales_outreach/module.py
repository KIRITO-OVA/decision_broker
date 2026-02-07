from typing import Dict, Any
from decision_broker.core.decision_engine.base import DecisionModule
from decision_broker.core.decision_engine.scorer import calculate_weighted_score
from decision_broker.modules.sales_outreach.signals import collect_sales_signals
from decision_broker.modules.sales_outreach.weights import SIGNAL_WEIGHTS
from decision_broker.modules.sales_outreach.outputs import decision_from_score
from decision_broker.schemas import DecisionRequest, DecisionResponse

class SalesOutreachModule(DecisionModule):

    def validate_input(self, request: DecisionRequest) -> bool:
        """
        Validates the payload has all required fields.
        """
        payload = request.payload
        required = ["lead_activity", "last_contact_days", "time_context", "company_signals"]
        for key in required:
            if key not in payload:
                raise ValueError(f"Missing required field: {key}")
        return True

    def collect_signals(self, request: DecisionRequest) -> Dict[str, float]:
        """
        Collects signals using the signals module.
        """
        return collect_sales_signals(request.payload)

    def score(self, signals: Dict[str, float]) -> float:
        """
        Calculates score using the generic weighted scorer and defined weights.
        """
        # Aliasing for compatibility if needed, but using direct core function is better
        return calculate_weighted_score(signals, SIGNAL_WEIGHTS)

    def decide(self, request: DecisionRequest) -> DecisionResponse:
        """
        Full decision pipeline: Validate -> Collect -> Score -> Output.
        """
        # 1. Collect Signals
        signals = self.collect_signals(request)
        
        # 2. Score
        # Using built-in score method which uses locally defined weights
        score_val = self.score(signals)
        
        # 3. Decision Rules
        result = decision_from_score(score_val)
        
        # 4. Construct Response
        return DecisionResponse(
            decision=result,
            confidence=score_val, # Using score as confidence proxy strictly for now
            reason_code=result["reason"],
            valid_for_seconds=result["ttl"]
        )
