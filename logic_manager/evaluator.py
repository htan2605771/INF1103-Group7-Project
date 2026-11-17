from datetime import datetime, timedelta
import re
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

    def _has_safety_keyword(self, text: str) -> bool:
        """True if any safety keyword appears as a whole word (or its plural), so 'rat' matches
        'a rat in the kitchen' and 'rats', but not 'frustrated' or 'rather'."""
        text = str(text).lower()
        return any(
            re.search(r"\b" + re.escape(keyword) + r"(?:s|es)?\b", text)
            for keyword in self.SAFETY_KEYWORDS
        )

    def evaluate_complaint(self, complaint: dict, ai_output: dict, history: list[dict]) -> dict:
        """
        Evaluates incoming complaint against business rules, overriding AI misclassifications
        for safety risks and flagging short or ambiguous input for review.
        """
        full_history = history + [complaint]
        outlet_id = complaint.get("outlet_id")

        outlet_flagged, _ = self.check_outlet_pattern(full_history, outlet_id, complaint)
        
        description_lower = complaint.get("description", "").lower()
        has_safety_keyword = self._has_safety_keyword(description_lower)

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
        if "description" not in record:
            return False
            
        desc = str(record.get("description", "")).strip().lower()
        key_details = str(record.get("key_details", "")).lower()
        reason = str(record.get("reason", "")).lower()
        
        if desc and len(desc) <= 3:
            return True
        if "insufficient information" in key_details or "insufficient information" in reason:
            return True
        if "nonsensical" in reason or "lacks sufficient context" in reason:
            return True
        return False

    def check_outlet_pattern(self, history: list[dict], current_outlet_id: str = None, current_complaint: dict = None) -> tuple[bool, list[str]]:
            """
            Flags an outlet if within a rolling 7-day window:
            1. 2 or more complaints with at least 1 hygiene issue.
            2. 3 or more active valid complaints.
            3. 1 or more active high-severity issues.
            """
            all_records = list(history) if history else []
            if current_complaint and current_complaint not in all_records:
                all_records.append(current_complaint)

            if not all_records:
                return (False, [])

            if current_outlet_id:
                outlet_records = [r for r in all_records if r.get("outlet_id") == current_outlet_id or not r.get("outlet_id")]
            else:
                outlet_records = all_records

            if not outlet_records:
                return (False, [])

            latest_dt_str = current_complaint.get("datetime") if current_complaint else None
            if not latest_dt_str and outlet_records:
                for r in reversed(outlet_records):
                    if r.get("datetime"):
                        latest_dt_str = r.get("datetime")
                        break

            try:
                latest_dt = datetime.fromisoformat(latest_dt_str) if latest_dt_str else datetime.now()
            except (TypeError, ValueError):
                latest_dt = datetime.now()

            window_start = latest_dt - timedelta(days=7)

            def is_in_window(r):
                dt_str = r.get("datetime")
                if not dt_str:
                    return True
                try:
                    r_dt = datetime.fromisoformat(dt_str)
                    return window_start <= r_dt <= latest_dt
                except (TypeError, ValueError):
                    return True

            recent_all_records = [r for r in outlet_records if is_in_window(r)]

            recent_active_records = [
                r for r in recent_all_records 
                if not r.get("is_addressed", False) and not r.get("resolved", False)
            ]
            valid_active_records = [r for r in recent_active_records if not self._is_insufficient_or_spam(r)]

            reasons = []

            # Rule 1: Hygiene threshold (2+ complaints total with at least 1 hygiene/safety issue)
            valid_hygiene_records = [
                r for r in valid_active_records 
                if (
                    str(r.get("category", "")).lower() == "hygiene" 
                    or str(r.get("ai_category", "")).lower() == "hygiene"
                    or self._has_safety_keyword(r.get("description", ""))                )
            ]
            if len(valid_active_records) >= 2 and len(valid_hygiene_records) >= 1:
                reasons.append("Hygiene-related complaint detected within the rolling 7-day window.")

            # Rule 2: Volume threshold (3 or more active valid complaints)
            if len(valid_active_records) >= 3:
                reasons.append("High complaint volume recorded within the rolling 7-day window.")

            # Rule 3: High-severity threshold (1 or more active high-severity complaints)
            high_severity_records = [
                r for r in valid_active_records 
                if str(r.get("final_severity", "")).lower() in ["high", "critical"]
            ]
            if len(high_severity_records) >= 1:
                reasons.append("High-severity issue requires immediate escalation review.")

            is_flagged = len(reasons) > 0
            return (is_flagged, reasons)

    def determine_outcome(self, final_severity: str, ai_output: dict, outlet_flagged: bool, description: str) -> str:
        """Decides the outcome of the complaint based on business rules."""
        # 1. Reputational risk takes highest priority
        if ai_output.get("reputational_risk"):
            return "route_to_manager"
        
        # 2. Flagged outlet takes next priority
        if outlet_flagged:
            return "route_to_manager"

        # 3. High severity escalates
        if final_severity == "high":
            return "escalate"
        
        # 4. Low confidence or short description flags for review
        word_count = len(description.split())
        if ai_output.get("confidence") == "low" or len(description.strip()) < 10 or word_count < 3:
            return "flag_for_review"
        
        return "log"