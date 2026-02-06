import sys
import os

# Ensure package in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decision_broker.core.billing.credits import check_credits

balance = check_credits("test_user")
print(f"Final Balance: {balance}")

if balance == 6:
    print("[PASS] Balance matches expected (6).")
else:
    print(f"[FAIL] Balance is {balance}, expected 6.")
