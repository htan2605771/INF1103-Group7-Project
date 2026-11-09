from io_manager import ComplaintCollector, IOManager

# Test complaint collection and validation
collector = ComplaintCollector()
complaint = collector.collect_complaint()

# Sample AI output (without calling Gemini API)
dummy_ai = {
    "ai_category": complaint["category"],
    "key_details": ["Bug", "Not clean"],
    "severity": "medium",
    "reason": "Soup contained a bug.",
    "reputational_risk": True,
    "confidence": "high"
}

# Sample final result (without calling logic_manager)
dummy_result = {
    "final_severity": "high",
    "outcome": "route_to_manager",
    "outlet_flagged": True,
    "override_applied": True,
    "override_reason": "Hygiene issue auto-promoted."
}

# Test display functions
IOManager.display_result(complaint, dummy_ai, dummy_result)
IOManager.display_summary([complaint])

# Test AI retry message
IOManager.display_ai_retry(2, 1, 3)