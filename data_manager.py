"""data_manager.py - Handles persistent storage of complaint records."""

import json
import os
from datetime import datetime, timedelta

DATA_FILE = "complaints_data.json"


def save_complaint(complaint: dict, ai_output: dict, result: dict) -> None:
    """Merge complaint + ai_output + result into one record and append to storage."""
    record = {**complaint, **ai_output, **result}
    records = load_complaints()
    records.append(record)

    with open(DATA_FILE, "w") as f:
        json.dump(records, f, indent=2)


def load_complaints() -> list[dict]:
    """Load all stored complaint records on startup.
    Return empty list if file is missing or corrupt."""
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        print("[!] Warning: complaints_data.json is corrupt. Starting fresh.")
        return []


def filter_by_outlet_and_date(outlet_id: str, days: int) -> list[dict]:
    """Return all complaint records for a given outlet within the last `days` days."""
    records = load_complaints()
    cutoff = datetime.now() - timedelta(days=days)
    filtered = []

    for r in records:
        if r.get("outlet_id") != outlet_id:
            continue
        try:
            record_dt = datetime.strptime(r.get("datetime", ""), "%Y-%m-%dT%H:%M:%S")
            if record_dt >= cutoff:
                filtered.append(r)
        except ValueError:
            continue

    return filtered

# if __name__ == "__main__":
#     print("--- Running data_manager standalone test ---")

#     dummy_complaint = {
#         "complaint_id": "CMP-0001",
#         "name": "Test User",
#         "email": "test@test.com",
#         "phone": "91234567",
#         "outlet_id": "OUT01",
#         "datetime": "2026-09-30T10:00:00",
#         "order_ref": "",
#         "category": "hygiene",
#         "description": "Found a bug in my soup",
#         "wants_followup": True
#     }

#     dummy_ai = {
#         "ai_category": "hygiene",
#         "key_details": ["bug in food"],
#         "severity": "high",
#         "reason": "Hygiene issue mentioned",
#         "reputational_risk": True,
#         "confidence": "high"
#     }

#     dummy_result = {
#         "final_severity": "high",
#         "outcome": "route_to_manager",
#         "outlet_flagged": False,
#         "override_applied": True,
#         "override_reason": "Hygiene keyword detected"
#     }

#     save_complaint(dummy_complaint, dummy_ai, dummy_result)
#     print("Loaded:", load_complaints())
#     print("Filtered (OUT01, 7 days):", filter_by_outlet_and_date("OUT01", 7))