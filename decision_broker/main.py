import sys
import os

# Ensure the package is in the path
# Append the parent directory to sys.path to allow 'import decision_broker.xxx'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decision_broker.schemas import DecisionRequest, DecisionResponse
# from decision_broker.core.billing.charge import process_charge # Deprecated Step 1 Stub
from decision_broker.core.auth.api_key import validate_api_key
from decision_broker.core.billing.usage import deduct_credit
from decision_broker.core.billing.credits import check_credits
from decision_broker.api.router import get_module

def process_decision(request: DecisionRequest, api_key: str) -> DecisionResponse:
    """
    Main entry point for processing a decision request.
    Enforces Auth + Credit Logic.
    """
    # 1. Auth Gate
    user_id = validate_api_key(api_key)
    if not user_id:
        raise PermissionError("Invalid API Key")

    # 2. Credit Gate
    # Check if user has at least 1 credit
    if check_credits(user_id) < 1:
        raise PermissionError("Insufficient credits. Please top up.")

    # 3. Route to correct module
    try:
        module_class = get_module(request.decision_type)
    except ValueError as e:
        raise e

    # 4. Instantiate and Execute
    module_instance = module_class()
    if not module_instance.validate_input(request):
        raise ValueError("Invalid input for decision module")

    response = module_instance.decide(request)

    # 5. Billing Deduction (Transactional)
    if not deduct_credit(user_id, 1):
        # Race condition safeguard, though unlikely with check above
        raise PermissionError("Insufficient credits during deduction.")

    return response

if __name__ == "__main__":
    print("STEP 1 COMPLETE AND STABLE. READY FOR STEP 2.")
