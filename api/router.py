from typing import Dict, Type
from decision_broker.core.decision_engine.base import DecisionModule
from decision_broker.modules.sales_outreach.module import SalesOutreachModule
from decision_broker.modules.model_selection.module import ModelSelectionModule
from decision_broker.modules.retry_intelligence.module import RetryIntelligenceModule

# Registry mapping decision_type string to the Module class
_MODULE_REGISTRY: Dict[str, Type[DecisionModule]] = {}

def register_module(decision_type: str, module_class: Type[DecisionModule]):
    """Registers a decision module."""
    _MODULE_REGISTRY[decision_type] = module_class

# Register Step 2 Module
register_module("sales_outreach", SalesOutreachModule)
# Register Step 3 Module
register_module("model_selection", ModelSelectionModule)
# Register Step 4 Module
register_module("retry_intelligence", RetryIntelligenceModule)

def get_module(decision_type: str) -> Type[DecisionModule]:
    """
    Retrieves the decision module class for the given type.
    Raises ValueError if not found.
    """
    if decision_type not in _MODULE_REGISTRY:
        raise ValueError(f"Unknown decision type: {decision_type}")
    return _MODULE_REGISTRY[decision_type]
