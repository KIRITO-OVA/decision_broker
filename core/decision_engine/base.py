from abc import ABC, abstractmethod
from typing import Dict, Any, List
from decision_broker.schemas import DecisionRequest, DecisionResponse

class DecisionModule(ABC):
    
    @abstractmethod
    def validate_input(self, request: DecisionRequest) -> bool:
        """Validate if the request has necessary data for this module."""
        pass

    @abstractmethod
    def collect_signals(self, request: DecisionRequest) -> Dict[str, Any]:
        """Collect relevant signals from the request."""
        pass

    @abstractmethod
    def score(self, signals: Dict[str, Any]) -> float:
        """Calculate a normalized score (0.0 to 1.0) based on signals."""
        pass

    @abstractmethod
    def decide(self, request: DecisionRequest) -> DecisionResponse:
        """Execute the full decision pipeline."""
        pass
