import json 
from unittest.mock import patch

import main
import ai_manager
import logic_manager
import data_manager

# -------------------------------------------------------------------------
# OFFLINE TEST SCENARIOS FOR LOGIC_MANAGER FUNCTIONS
# -------------------------------------------------------------------------
TEST_SCENARIOS = [
    {
        "scenario_name": "Scenario 1: Standard Input (No Override)",
        "description": "Tests logic_manager accepting AI output directly without applying overrides.",
        "complaint": {
            "complaint_id": "CMP-1003",
            "name": "David Lim",
            "email": "david@example.com",
            "phone": "81112222",
            "outlet_id": "OUT-03",
            "datetime": "2026-10-11T14:15:00",
            "order_ref": "ORD-503",
            "category": "service",
            "description": "The cashier was slightly rude to me.",
            "wants_followup": True
        },
        "ai_output": {
            "ai_category": "service",
            "key_details": ["rude cashier"],
            "severity": "low",
            "reason": "Minor customer service concern.",
            "reputational_risk": False,
            "confidence": "high"
        },
        "history": []
    },
    {
        "scenario_name": "Scenario 2: Safety Keyword Override (Food Poisoning)",
        "description": "Tests logic_manager overriding low AI severity to HIGH when safety keywords appear.",
        "complaint": {
            "complaint_id": "CMP-1001",
            "name": "Sarah Chen",
            "email": "sarah@example.com",
            "phone": "91234567",
            "outlet_id": "OUT-01",
            "datetime": "2026-10-11T12:00:00",
            "order_ref": "ORD-501",
            "category": "food_quality",
            "description": "I got food poisoning and started to vomit after eating the chicken rice.",
            "wants_followup": True
        },
        "ai_output": {
            "ai_category": "food_quality",
            "key_details": ["food poisoning", "vomit"],
            "severity": "low",  # AI under-evaluates severity
            "reason": "Customer reported feeling unwell.",
            "reputational_risk": True,
            "confidence": "high"
        },
        "history": []
    },
    {
        "scenario_name": "Scenario 3: Short/Ambiguous Complaint Flagged for Review",
        "description": "Tests logic_manager keeping the AI severity and setting the outcome for ambiguous input to FLAG_FOR_REVIEW.",
        "complaint": {
            "complaint_id": "CMP-1002",
            "name": "Alex Tan",
            "email": "alex@example.com",
            "phone": "98765432",
            "outlet_id": "OUT-02",
            "datetime": "2026-10-11T13:30:00",
            "order_ref": "ORD-502",
            "category": "service",
            "description": "bad",
            "wants_followup": False
        },
        "ai_output": {
            "ai_category": "service",
            "key_details": ["bad service"],
            "severity": "low",
            "reason": "Customer gave complete and clear feedback.",
            "reputational_risk": False,
            "confidence": "high" 
        },
        "history": []
    },
    {
        "scenario_name": "Scenario 4: Outlet Pattern Flagging & Score Calculation",
        "description": "Tests history checks flagging outlet and calculating max priority score (High=50 + RepRisk=30 + Outlet=20 -> 100).",
        "complaint": {
            "complaint_id": "CMP-1004",
            "name": "Emily Wong",
            "email": "emily@example.com",
            "phone": "83334444",
            "outlet_id": "OUT-04",
            "datetime": "2026-10-11T15:00:00",
            "order_ref": "ORD-504",
            "category": "food_quality",
            "description": "Found a cockroach inside the soup meal.",
            "wants_followup": True
        },
        "ai_output": {
            "ai_category": "hygiene",
            "key_details": ["pest found in food"],
            "severity": "high",
            "reason": "Severe hygiene violation.",
            "reputational_risk": True,
            "confidence": "high"
        },
        "history": [
            {"category": "hygiene", "datetime": "2026-10-08T10:00:00"},
            {"category": "service", "datetime": "2026-10-09T11:00:00"}
        ]
    }
]

def run_offline_simulation():
    print("=" * 70)
    print("   F&B CUSTOMER COMPLAINT TRIAGE SYSTEM - AUTOMATED TEST SCRIPT   ")
    print("=" * 70)

    for idx, test_case in enumerate(TEST_SCENARIOS, 1):
        print(f"\n{'=' * 75}")
        print(f"▶ [{idx}/{len(TEST_SCENARIOS)}] {test_case['scenario_name']}")
        print(f"   Purpose: {test_case['description']}")
        print(f"{'=' * 75}")

        complaint = test_case["complaint"]
        ai_output = test_case["ai_output"]
        history = test_case["history"]

        # 1. SAMPLE INPUT COMPLAINT
        print("\n  ┌── 1. SAMPLE INPUT COMPLAINT ──────────────────────────────────────────┐")
        print(f"  │ Complaint ID : {complaint['complaint_id']}")
        print(f"  │ Outlet ID    : {complaint['outlet_id']}")
        print(f"  │ Category     : {complaint['category']}")
        print(f"  │ Description  : \"{complaint['description']}\"")
        print("  └───────────────────────────────────────────────────────────────────────┘")

        # 2. AI RESPONSE
        print("\n  ┌── 2. INITIAL AI RESPONSE ─────────────────────────────────────────────┐")
        print(f"  │ AI Category  : {ai_output['ai_category']}")
        print(f"  │ AI Severity  : {ai_output['severity'].upper()}")
        print(f"  │ Confidence   : {ai_output['confidence'].upper()}")
        print(f"  │ Rep Risk     : {ai_output['reputational_risk']}")
        print(f"  │ Key Details  : {', '.join(ai_output['key_details'])}")
        print(f"  │ Reason       : {ai_output['reason']}")
        print("  └───────────────────────────────────────────────────────────────────────┘")

        try:
            # Evaluate via business logic
            eval_result = logic_manager.evaluate_complaint(complaint, ai_output, history)
            priority_score = logic_manager.calculate_score(
                final_severity=eval_result["final_severity"],
                reputational_risk=ai_output.get("reputational_risk", False),
                outlet_flagged=eval_result["outlet_flagged"]
            )

            # 3. FINAL TRIAGE RESULTS
            print("\n  ┌── 3. FINAL TRIAGE & OVERRIDE RESULTS ─────────────────────────────────┐")
            print(f"  │ Final Severity   : {str(eval_result['final_severity']).upper()}")
            print(f"  │ Override Applied : {eval_result['override_applied']}")
            if eval_result["override_applied"]:
                print(f"  │ Override Reason  : {eval_result['override_reason']}")
            print(f"  │ Outlet Flagged   : {eval_result['outlet_flagged']}")
            print(f"  │ Action Outcome   : {eval_result['outcome']}")
            print(f"  │ Priority Score   : {priority_score}/100")
            print("  └───────────────────────────────────────────────────────────────────────┘")
            print("\n   Status: ✅ PASSED SIMULATION")

        except Exception as e:
            print(f"\n   Status: ❌ ERROR - {e}")


if __name__ == "__main__":
    run_offline_simulation()