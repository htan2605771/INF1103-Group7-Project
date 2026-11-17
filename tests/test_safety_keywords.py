"""Regression tests: safety keywords must match whole words, not parts of other words."""

import pytest

from logic_manager import ComplaintEvaluator

AI_OUTPUT = {
    "ai_category": "service", "key_details": ["slow"], "severity": "low",
    "reason": "Minor delay.", "reputational_risk": False, "confidence": "high",
}


def severity_for(description):
    complaint = {"description": description, "category": "service", "outlet_id": "OUT-001"}
    return ComplaintEvaluator().evaluate_complaint(complaint, AI_OUTPUT, [])["final_severity"]


@pytest.mark.parametrize("description", [
    "I was so frustrated with how long the wait was",
    "I would rather not come back to this outlet again",
    "The rate they charged me was wrong on the bill",
])
def test_words_that_only_contain_a_keyword_are_not_safety_issues(description):
    assert severity_for(description) == "low"


@pytest.mark.parametrize("description", [
    "A rat ran past our table during dinner",
    "We saw rats near the kitchen door at lunch",
    "I think I got food poisoning after the meal",
    "There was a piece of glass in my drink today",
])
def test_real_safety_issues_are_still_escalated(description):
    assert severity_for(description) == "high"