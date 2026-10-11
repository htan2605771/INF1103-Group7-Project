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
        "scenario_name": "Scenario 1: Safety Keyword Override (Food Poisoning)",
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
            "is_ambiguous": False,
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
        "scenario_name": "Scenario 2: Ambiguous Complaint Manual Review Override",
        "description": "Tests logic_manager redirecting ambiguous input to MANUAL_REVIEW.",
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
            "is_ambiguous": True,  # Triggers ambiguity early return
            "wants_followup": False
        },
        "ai_output": {
            "ai_category": "service",
            "key_details": ["unclear input"],
            "severity": "low",
            "reason": "Feedback is too brief.",
            "reputational_risk": False,
            "confidence": "low"
        },
        "history": []
    },
    {
        "scenario_name": "Scenario 3: Standard Input (No Override)",
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
            "is_ambiguous": False,
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
            "is_ambiguous": False,
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