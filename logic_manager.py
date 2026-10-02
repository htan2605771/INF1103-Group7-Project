def get_final_result(complaint: dict, ai_output: dict, history: list[dict]) -> dict:
    """Temporary stub returning default business result."""
    return {
        "final_severity": ai_output.get("severity", "medium"),
        "outcome": "log",
        "outlet_flagged": False,
        "override_applied": False,
        "override_reason": "",
    }