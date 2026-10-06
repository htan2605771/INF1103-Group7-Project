SAFETY_KEYWORDS = [
    "food poisoning", "hospital", "allergy", "allergic", "vomit", 
    "diarrhea", "rat", "cockroach", "glass", "metal", "insect", "bug"
]


def get_final_result(complaint: dict, ai_output: dict, history: list[dict]) -> dict:
    """Temporary stub returning default business result."""

    # 1. Handle Short or Ambiguous Text Submissions
    if complaint.get("is_ambiguous", False):
        return {
            "final_severity": "manual_review",
            "outcome": "route_to_manual_queue",
            "outlet_flagged": False,
            "override_applied": True,
            "override_reason": "Short or ambiguous text detected. Flagged for Manual Review."
        }

    # 2. Check for Pattern Flags (e.g., 3 or more past complaints at same outlet)
    outlet_flagged = len(history) >= 3
    
    # 3. Rule-Based AI Misclassification Override (Food Safety Keyword Scan)
    description_lower = complaint.get("description", "").lower()
    has_safety_keyword = any(keyword in description_lower for keyword in SAFETY_KEYWORDS)

    ai_severity = ai_output.get("severity", "medium")
    final_severity = ai_severity
    override_applied = False
    override_reason = ""

    # Force severity to High if critical safety terms are present
    if has_safety_keyword and ai_severity != "high":
        final_severity = "high"
        override_applied = True
        override_reason = "High-priority safety keyword detected (Auto-overridden to High)."
        print("\n[!] High-priority food safety issue detected - Routing to Manager.")

    # 4. Determine Action Outcome based on severity or reputational risk or pattern flag
    if final_severity == "high" or ai_output.get("reputational_risk") or outlet_flagged:
        outcome = "route_to_manager"
    else:
        outcome = "standard_queue"
    
    return {
        "final_severity": final_severity,
        "outcome": outcome,
        "outlet_flagged": outlet_flagged,
        "override_applied": override_applied,
        "override_reason": override_reason,
    }

def evaluate_complaint(complaint: dict, ai_output: dict, history: list[dict]) -> dict:
    """
    Evaluates incoming complaint against business rules, overriding AI misclassifications
    for safety risks or ambiguous input.
    """
    # 1. Handle Short or Ambiguous Text Submissions
    if complaint.get("is_ambiguous", False):
        return {
            "final_severity": "manual_review",
            "override_applied": True,
            "override_reason": "Short or ambiguous text detected. Flagged for Manual Review.",
            "outlet_flagged": False
        }

    # 2. Check for Pattern Flags (e.g., 3 or more past complaints at same outlet)
    outlet_flagged = check_outlet_pattern(complaint["outlet_id"], history + [complaint])
    
    # 3. Rule-Based AI Misclassification Override (Food Safety Keyword Scan)
    description_lower = complaint.get("description", "").lower()
    has_safety_keyword = any(keyword in description_lower for keyword in SAFETY_KEYWORDS)

    ai_severity = ai_output.get("severity", "medium")
    final_severity = ai_severity
    override_applied = False
    override_reason = ""

    # Force severity to High if critical safety terms are present
    if has_safety_keyword and ai_severity != "high":
        final_severity = "high"
        override_applied = True
        override_reason = "High-priority safety keyword detected (Auto-overridden to High)."
        print("\n[!] High-priority food safety issue detected - Routing to Manager.")

    return {
        "final_severity": final_severity,
        "override_applied": override_applied,
        "override_reason": override_reason,
        "outlet_flagged": outlet_flagged
    }

SEVERITY_WEIGHTS = {
    "low": 10,
    "medium": 25,
    "high": 50,
    "manual_review": 15
}

def calculate_score(final_severity: str, reputational_risk: bool, outlet_flagged: bool) -> int:
    """Computes a numerical priority score based on severity, reputational risk, and repeat issues."""
    score = SEVERITY_WEIGHTS.get(final_severity, 10)

    if reputational_risk:
        score += 30  # Add weight for reputational risk
    if outlet_flagged:
        score += 20  # Add weight for repeat outlet issues

    return score


def check_outlet_pattern(outlet_id: str, history: list[dict], days: int = 7) -> bool: # check if outlet has 2 or more complaints in the last 7 days and at least one complaint is hygiene
    # history is already filtered with the filter function which comes before this business rule checking in the main.py flow
    # includes current complaint, passed in as history + [complaint] when function is called
    if len(history) < 2:
        return False
    for record in history:
        if record["category"] == "hygiene" or record.get("ai_category") == "hygiene":
            return True
    return False

if __name__ == "__main__":
    print("--- check outlet patten tests ---")
    print(check_outlet_pattern("B12", [])) # False, no complaints
    print(check_outlet_pattern("B12", [{"category": "hygiene"}])) # False, only one complaint
    print(check_outlet_pattern("B12", [{"category": "service"}, {"category": "hygiene"}])) # True
    print(check_outlet_pattern("B12", [{"category": "service"}, {"category": "billing"}])) # False, no hygiene
    print(check_outlet_pattern("B12", [{"category": "service", "ai_category": "hygiene"}, {"category": "billing"}])) # True, ai category says hygiene
    print(check_outlet_pattern("B12", [{"category": "service", "ai_category": "service"}, {"category": "billing"}])) # False
