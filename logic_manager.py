from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ComplaintEvaluator:
    """Evaluates customer complaints against business rules and calculates priority scores."""

    SAFETY_KEYWORDS = [
        "food poisoning", "hospital", "allergy", "allergic", "vomit", 
        "diarrhea", "rat", "cockroach", "glass", "metal", "insect", "bug"
    ]

    SEVERITY_WEIGHTS = {
        "low": 10,
        "medium": 25,
        "high": 50,
    }

    def evaluate_complaint(self, complaint: dict, ai_output: dict, history: list[dict]) -> dict:
        """
        Evaluates incoming complaint against business rules, overriding AI misclassifications
        for safety risks and flagging short or ambiguous input for review.
        """
        # 1. Check for Pattern Flags (e.g., 2 or more complaints at same outlet in the last 7 days and at least 1 hygiene complaint)
        full_history = history + [complaint]
        outlet_id = complaint.get("outlet_id")

        outlet_flagged = self.check_outlet_pattern(full_history, outlet_id)
        
        # 2. Rule-Based AI Misclassification Override (Food Safety Keyword Scan)
        description_lower = complaint.get("description", "").lower()
        has_safety_keyword = any(keyword in description_lower for keyword in self.SAFETY_KEYWORDS)

        ai_severity = ai_output.get("severity", "medium")
        final_severity = ai_severity
        override_applied = False
        override_reason = ""

        # Force severity to High if critical safety terms are present
        if has_safety_keyword and ai_severity != "high":
            final_severity = "high"
            override_applied = True
            override_reason = "High-priority safety keyword detected (Auto-overridden to High)."
            logger.warning("[!] High-priority food safety issue detected - Routing to Manager.")

        outcome = self.determine_outcome(final_severity, ai_output, outlet_flagged, complaint["description"])

        return {
            "final_severity": final_severity,
            "outcome": outcome,
            "override_applied": override_applied,
            "override_reason": override_reason,
            "outlet_flagged": outlet_flagged
        }

    def calculate_score(self, final_severity: str, reputational_risk: bool, outlet_flagged: bool) -> int:
        """Computes a numerical priority score based on severity, reputational risk, and repeat issues."""
        score = self.SEVERITY_WEIGHTS.get(final_severity, 10)

        if reputational_risk:
            score += 30  # Add weight for reputational risk
        if outlet_flagged:
            score += 20  # Add weight for repeat outlet issues

        return score

    def check_outlet_pattern(self, history: list[dict], current_outlet_id: str = None) -> bool:
        """
        Flags an outlet if within a rolling 7-day window:
        1. ANY complaint is hygiene-related.
        2. OR there are 3 or more total complaints.
        """
        if not current_outlet_id:
            return False

        outlet_records = [r for r in history if r.get("outlet_id") == current_outlet_id]
        if not outlet_records:
            return False
            
        # Get the timestamp of the current incoming complaint (or use current time)
        # Assuming ISO format string like "2026-11-13T20:44:00"
        latest_dt_str = outlet_records[-1].get("datetime")
        try:
            latest_dt = datetime.fromisoformat(latest_dt_str)
        except (TypeError, ValueError):
            latest_dt = datetime.now()

        # Define the time window (e.g., last 7 days)
        window_start = latest_dt - timedelta(days=7)

        # Filter records strictly within the last 7 days
        recent_records = []
        for r in outlet_records:
            try:
                r_dt = datetime.fromisoformat(r.get("datetime", ""))
                if r_dt >= window_start:
                    recent_records.append(r)
            except (TypeError, ValueError):
                # If datetime parsing fails, include it just in case
                recent_records.append(r)

        # Rule 1: Immediate Red Flag for any hygiene issue in the recent window
        has_hygiene = any(
            str(r.get("category", "")).lower() == "hygiene" or str(r.get("ai_category", "")).lower() == "hygiene" 
            for r in recent_records
        )
        if has_hygiene:
            return True

        # Rule 2: Volume Red Flag (3 or more complaints within the 7-day window)
        if len(recent_records) >= 3:
            return True
            
        return False

    def determine_outcome(self, final_severity: str, ai_output: dict, outlet_flagged: bool, description: str) -> str:
        """Decides the outcome of the complaint based on business rules."""
        if ai_output["reputational_risk"]:
            return "route_to_manager"
        
        if outlet_flagged:
            return "route_to_manager"

        # high severity escalates even if the description is short or ambiguous (e.g. "food poisoning!!")
        if final_severity == "high":
            return "escalate"
        
        # description under 3 words or under 10 characters is treated as too short or ambiguous
        word_count = len(description.split())
        if ai_output["confidence"] == "low" or len(description.strip()) < 10 or word_count < 3:
            return "flag_for_review"
        
        return "log"


if __name__ == "__main__":
    evaluator = ComplaintEvaluator()

    print("--- check outlet pattern tests ---")
    print(evaluator.check_outlet_pattern([])) # False, no complaints
    print(evaluator.check_outlet_pattern([{"category": "hygiene"}])) # False, only one complaint
    print(evaluator.check_outlet_pattern([{"category": "service"}, {"category": "hygiene"}])) # True
    print(evaluator.check_outlet_pattern([{"category": "service"}, {"category": "billing"}])) # False, no hygiene
    print(evaluator.check_outlet_pattern([{"category": "service", "ai_category": "hygiene"}, {"category": "billing"}])) # True, ai category says hygiene
    print(evaluator.check_outlet_pattern([{"category": "service", "ai_category": "service"}, {"category": "billing"}])) # False

    print("--- determine outcome tests ---")
    ok_ai = {"reputational_risk": False, "confidence": "high"}
    normal_description = "The staff were rude and the food took forty minutes"
    print(evaluator.determine_outcome("low", {"reputational_risk": True, "confidence": "high"}, False, normal_description)) # route_to_manager
    print(evaluator.determine_outcome("low", ok_ai, True, normal_description)) # route_to_manager
    print(evaluator.determine_outcome("medium", {"reputational_risk": False, "confidence": "low"}, False, normal_description)) # flag_for_review
    print(evaluator.determine_outcome("medium", ok_ai, False, "not good")) # flag_for_review
    print(evaluator.determine_outcome("high", ok_ai, False, normal_description)) # escalate
    print(evaluator.determine_outcome("high", ok_ai, False, "food poisoning!!")) # escalate, high severity overrides short description 
    print(evaluator.determine_outcome("medium", ok_ai, False, normal_description)) # log