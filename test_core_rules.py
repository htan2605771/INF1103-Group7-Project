"""Offline tests for the core business rules in logic_manager, using hardcoded sample AI responses.

These add edge cases on top of test_logic_manager.py (they do not replace it).
No API key, network or real data file is needed.
"""

import unittest

from logic_manager import ComplaintEvaluator

# Hardcoded sample AI responses (what ai_manager would return after validation)
CALM_AI = {
    "ai_category": "service", "key_details": ["slow"], "severity": "low",
    "reason": "Minor delay.", "reputational_risk": False, "confidence": "high",
}
RISKY_AI = {**CALM_AI, "reputational_risk": True}
UNSURE_AI = {**CALM_AI, "confidence": "low"}
HIGH_AI = {**CALM_AI, "severity": "high"}

LONG_TEXT = "The staff were rude and the food took forty minutes"


def complaint(description=LONG_TEXT, category="service"):
    return {"description": description, "category": category}


class TestDetermineOutcome(unittest.TestCase):
    def setUp(self):
        self.ev = ComplaintEvaluator()

    def test_reputational_risk_routes_to_manager(self):
        self.assertEqual(self.ev.determine_outcome("low", RISKY_AI, False, LONG_TEXT), "route_to_manager")

    def test_flagged_outlet_routes_to_manager(self):
        self.assertEqual(self.ev.determine_outcome("low", CALM_AI, True, LONG_TEXT), "route_to_manager")

    def test_reputational_risk_beats_high_severity(self):
        self.assertEqual(self.ev.determine_outcome("high", RISKY_AI, False, LONG_TEXT), "route_to_manager")

    def test_high_severity_escalates_even_for_short_description(self):
        self.assertEqual(self.ev.determine_outcome("high", CALM_AI, False, "food poisoning!!"), "escalate")

    def test_low_confidence_flags_for_review(self):
        self.assertEqual(self.ev.determine_outcome("medium", UNSURE_AI, False, LONG_TEXT), "flag_for_review")

    def test_short_description_flags_for_review(self):
        self.assertEqual(self.ev.determine_outcome("medium", CALM_AI, False, "not good"), "flag_for_review")

    def test_two_word_description_flags_for_review_even_if_long_characters(self):
        self.assertEqual(self.ev.determine_outcome("medium", CALM_AI, False, "extraordinarily terrible"), "flag_for_review")

    def test_whitespace_padding_does_not_hide_a_short_description(self):
        self.assertEqual(self.ev.determine_outcome("medium", CALM_AI, False, "   bad   "), "flag_for_review")

    def test_normal_complaint_is_logged(self):
        self.assertEqual(self.ev.determine_outcome("medium", CALM_AI, False, LONG_TEXT), "log")


class TestOutletPattern(unittest.TestCase):
    def setUp(self):
        self.ev = ComplaintEvaluator()

    def test_empty_and_single_complaint_do_not_flag(self):
        self.assertFalse(self.ev.check_outlet_pattern([]))
        self.assertFalse(self.ev.check_outlet_pattern([{"category": "hygiene"}]))

    def test_two_complaints_without_hygiene_do_not_flag(self):
        self.assertFalse(self.ev.check_outlet_pattern([{"category": "service"}, {"category": "billing"}]))

    def test_two_complaints_with_customer_hygiene_flag(self):
        self.assertTrue(self.ev.check_outlet_pattern([{"category": "service"}, {"category": "hygiene"}]))

    def test_ai_category_hygiene_also_counts(self):
        self.assertTrue(self.ev.check_outlet_pattern(
            [{"category": "service", "ai_category": "hygiene"}, {"category": "billing"}]))


class TestScore(unittest.TestCase):
    def setUp(self):
        self.ev = ComplaintEvaluator()

    def test_base_scores_by_severity(self):
        self.assertEqual(self.ev.calculate_score("low", False, False), 10)
        self.assertEqual(self.ev.calculate_score("medium", False, False), 25)
        self.assertEqual(self.ev.calculate_score("high", False, False), 50)

    def test_reputational_risk_adds_30_and_flagged_outlet_adds_20(self):
        self.assertEqual(self.ev.calculate_score("low", True, False), 40)
        self.assertEqual(self.ev.calculate_score("low", False, True), 30)
        self.assertEqual(self.ev.calculate_score("high", True, True), 100)

    def test_unknown_severity_falls_back_to_lowest_score(self):
        self.assertEqual(self.ev.calculate_score("unknown", False, False), 10)


class TestEvaluateComplaint(unittest.TestCase):
    def setUp(self):
        self.ev = ComplaintEvaluator()

    def test_safety_keyword_overrides_low_severity_and_escalates(self):
        result = self.ev.evaluate_complaint(complaint("I got food poisoning after the meal"), CALM_AI, [])
        self.assertEqual(result["final_severity"], "high")
        self.assertTrue(result["override_applied"])
        self.assertEqual(result["outcome"], "escalate")

    def test_safety_keyword_is_not_an_override_when_ai_already_says_high(self):
        result = self.ev.evaluate_complaint(complaint("I got food poisoning after the meal"), HIGH_AI, [])
        self.assertFalse(result["override_applied"])
        self.assertEqual(result["override_reason"], "")

    def test_safety_keyword_scan_is_case_insensitive(self):
        result = self.ev.evaluate_complaint(complaint("A COCKROACH was on my plate today"), CALM_AI, [])
        self.assertEqual(result["final_severity"], "high")

    def test_multi_condition_rule_uses_history_and_hygiene_category(self):
        """Repeat complaints at an outlet AND a hygiene complaint -> outlet flagged and routed to the manager."""
        history = [{"category": "service"}]
        result = self.ev.evaluate_complaint(complaint(category="hygiene"), CALM_AI, history)
        self.assertTrue(result["outlet_flagged"])
        self.assertEqual(result["outcome"], "route_to_manager")

    def test_repeat_complaints_without_hygiene_are_not_flagged(self):
        history = [{"category": "service"}]
        result = self.ev.evaluate_complaint(complaint(category="billing"), CALM_AI, history)
        self.assertFalse(result["outlet_flagged"])
        self.assertEqual(result["outcome"], "log")

    def test_result_has_every_field_the_data_layer_stores(self):
        result = self.ev.evaluate_complaint(complaint(), CALM_AI, [])
        self.assertEqual(
            set(result),
            {"final_severity", "outcome", "override_applied", "override_reason", "outlet_flagged"},
        )


if __name__ == "__main__":
    unittest.main()