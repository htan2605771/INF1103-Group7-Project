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
        full_history = history + [complaint]
        outlet_id = complaint.get("outlet_id")

        outlet_flagged, outlet_flag_reason = self.check_outlet_pattern(full_history, outlet_id, complaint)
        
        description_lower = complaint.get("description", "").lower()
        has_safety_keyword = any(keyword in description_lower for keyword in self.SAFETY_KEYWORDS)

        ai_severity = ai_output.get("severity", "medium")
        final_severity = ai_severity
        override_applied = False
        override_reason = ""

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
            "outlet_flagged": outlet_flagged,
            "outlet_flag_reason": outlet_flag_reason
        }

    def calculate_score(self, final_severity: str, reputational_risk: bool, outlet_flagged: bool) -> int:
        """Computes a numerical priority score based on severity, reputational risk, and repeat issues."""
        score = self.SEVERITY_WEIGHTS.get(final_severity, 10)

        if reputational_risk:
            score += 30
        if outlet_flagged:
            score += 20

        return score

    def _is_insufficient_or_spam(self, record: dict) -> bool:
        """Helper to detect if a record contains spam, gibberish, or insufficient information."""
        desc = str(record.get("description", "")).strip().lower()
        key_details = str(record.get("key_details", "")).lower()
        reason = str(record.get("reason", "")).lower()
        
        if len(desc) <= 3:
            return True
        if "insufficient information" in key_details or "insufficient information" in reason:
            return True
        if "nonsensical" in reason or "lacks sufficient context" in reason:
            return True
        return False

    def check_outlet_pattern(self, history: list[dict], current_outlet_id: str = None, current_complaint: dict = None) -> tuple[bool, str]:
        """
        Flags an outlet if within a rolling 7-day window:
        1. ANY genuine hygiene-related complaint is detected.
        2. OR there are 3 or more total valid complaints.
        """
        if not current_outlet_id:
            return False, ""

        outlet_records = [r for r in history if r.get("outlet_id") == current_outlet_id]
        if not outlet_records:
            return False, ""
            
        latest_dt_str = current_complaint.get("datetime") if current_complaint else None
        try:
            latest_dt = datetime.fromisoformat(latest_dt_str) if latest_dt_str else datetime.now()
        except (TypeError, ValueError):
            latest_dt = datetime.now()

        window_start = latest_dt - timedelta(days=7)

        recent_records = []
        for r in outlet_records:
            try:
                r_dt = datetime.fromisoformat(r.get("datetime", ""))
                if r_dt >= window_start:
                    recent_records.append(r)
            except (TypeError, ValueError):
                recent_records.append(r)

        valid_hygiene_records = []
        for r in recent_records:
            cat = str(r.get("category", "")).lower()
            ai_cat = str(r.get("ai_category", "")).lower()
            is_hygiene_category = ("hygiene" in cat or "hygiene" in ai_cat)
            
            if is_hygiene_category and not self._is_insufficient_or_spam(r):
                valid_hygiene_records.append(r)

        if valid_hygiene_records:
            return True, "Hygiene-related complaint detected within the rolling 7-day window."

        valid_volume_records = [r for r in recent_records if not self._is_insufficient_or_spam(r)]
        if len(valid_volume_records) >= 3:
            return True, f"High complaint volume ({len(valid_volume_records)} complaints) recorded within the rolling 7-day window."
            
        return False, ""

    def determine_outcome(self, final_severity: str, ai_output: dict, outlet_flagged: bool, description: str) -> str:
        """Decides the outcome of the complaint based on business rules."""
        if ai_output["reputational_risk"]:
            return "route_to_manager"
        
        if outlet_flagged:
            return "route_to_manager"

        if final_severity == "high":
            return "escalate"
        
        word_count = len(description.split())
        if ai_output["confidence"] == "low" or len(description.strip()) < 10 or word_count < 3:
            return "flag_for_review"
        
        return "log"