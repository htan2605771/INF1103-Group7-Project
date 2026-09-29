def get_ai_output(complaint: dict) -> dict:
    """Temporary stub returning mock AI data."""
    return {
        "ai_category": complaint.get("category", "other"),
        "key_details": ["mock detail"],
        "severity": "medium",
        "reason": "Temporary stub response",
        "reputational_risk": False,
        "confidence": "high",
    }