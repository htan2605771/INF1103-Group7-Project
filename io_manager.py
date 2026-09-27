def display_result(complaint: dict, ai_output: dict, result: dict) -> None:
    """Print the final triage outcome to the terminal in a readable format."""
    print("\n" + "=" * 60)
    print(f"          TRIAGE RESULT FOR COMPLAINT: {complaint.get('complaint_id', 'N/A')}")
    print("=" * 60)

    # Core details
    print("[COMPLAINT DETAILS]\n")
    print(f"Outlet ID         : {complaint.get('outlet_id')}")
    print(f"Customer Name     : {complaint.get('name')}")
    print(f"Category          : {complaint.get('category')}")
    print(f"Description       : {complaint.get("description")}")
    print("=" * 60)

    # AI output details
    print("[AI ANALYSIS]\n")
    print(f"Category          : {ai_output.get('ai_category')}")
    print(f"Key Details       : {', '.join(ai_output.get('key_details', []))}")
    print(f"AI Severity       : {ai_output.get('severity').upper()}")
    print(f"Reason            : {ai_output.get('reason')}")
    print(f"Reputational Risk : {'YES' if ai_output.get('reputational_risk') else 'No'}")
    print(f"Confidence        : {ai_output.get('confidence').upper()}")
    print("-" * 60)

    # Final result (logic manager check, business logic)
    print("[FINAL TRIAGE DECISION]\n")
    print(f"Final Severity   : {result.get('final_severity').upper()}")
    print(f"Action Outcome   : {result.get('outcome').upper()}")
    print(f"Pattern Flagged  : {'YES (Multiple complaints detected)' if result.get('outlet_flagged') else 'No'}")

    if result.get("override_applied"):
        print(f"Override Notice  : APPLIED -> {result.get('override_reason')}")

    print("=" * 60 + "\n")

# Test 
if __name__ == "__main__":
    print("--- Running io_manager standalone test ---")

    complaint = collect_complaint()

    #sample
    dummy_ai = {
    "ai_category": sample_complaint["category"],
    "key_details": ["Bug", "Not clean"],
    "severity": "medium",
    "reason": "Soup contained a bug.",
    "reputational_risk": True,
    "confidence": "high",
    }

    #sample
    dummy_result = { # ai_output
        "final_severity": "high",
        "outcome": "route_to_manager",
        "outlet_flagged": True,
        "override_applied": True,
        "override_reason": "Hygiene issue auto-promoted.",
    }

    
    display_result(complaint, dummy_ai, dummy_result)