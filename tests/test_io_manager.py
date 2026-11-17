"""Offline tests for io_manager: no one needs to type anything and no API is called.

input() is replaced with a scripted list of answers, and print() output is captured.
"""

import io
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from unittest.mock import patch

from io_manager import ComplaintCollector, IOManager
from io_manager.complaint_validator import IOComplaintValidator

FMT = "%Y-%m-%dT%H:%M:%S"
PAST = (datetime.now() - timedelta(days=1)).strftime(FMT)
FUTURE = (datetime.now() + timedelta(days=1)).strftime(FMT)

# answers in the order collect_complaint() asks for them
GOOD_ANSWERS = [
    "Ann Lee",             # name
    "ann@example.com",     # email
    "91234567",            # phone
    "OUT-01",              # outlet
    PAST,                  # incident datetime
    "",                    # order ref (optional)
    "Food Quality",        # category
    "The soup was cold.",  # description
    "Yes",                 # follow-up
]


def collect(answers):
    """Run collect_complaint() with scripted answers; return (complaint, printed_text)."""
    out = io.StringIO()
    with patch("builtins.input", side_effect=answers), redirect_stdout(out):
        complaint = ComplaintCollector().collect_complaint()
    return complaint, out.getvalue()


def show(func, *args):
    out = io.StringIO()
    with redirect_stdout(out):
        func(*args)
    return out.getvalue()


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.v = IOComplaintValidator()

    def test_name_and_outlet_must_not_be_blank(self):
        self.assertTrue(self.v.validate_name("Ann"))
        self.assertFalse(self.v.validate_name("   "))
        self.assertFalse(self.v.validate_outlet_id(""))

    def test_email_format(self):
        self.assertTrue(self.v.validate_email("a.b@site.com"))
        self.assertFalse(self.v.validate_email("not-an-email"))
        self.assertFalse(self.v.validate_email("a@b"))

    def test_phone_must_be_exactly_8_digits(self):
        self.assertTrue(self.v.validate_phone_number("91234567"))
        self.assertFalse(self.v.validate_phone_number("9123456"))
        self.assertFalse(self.v.validate_phone_number("9123456a"))

    def test_incident_datetime_results(self):
        self.assertEqual(self.v.validate_incident_datetime(PAST), "valid")
        self.assertEqual(self.v.validate_incident_datetime(FUTURE), "future")
        self.assertEqual(self.v.validate_incident_datetime("18/09/2026"), "invalid_format")

    def test_category_and_normalisation(self):
        self.assertTrue(self.v.validate_complaint_category("food quality"))
        self.assertFalse(self.v.validate_complaint_category("rude"))
        self.assertEqual(self.v.normalise_complaint_category("food quality"), "food_quality")
        self.assertEqual(self.v.normalise_complaint_category("service"), "service")

    def test_follow_up(self):
        self.assertTrue(self.v.validate_follow_up_preference("yes"))
        self.assertFalse(self.v.validate_follow_up_preference("maybe"))
        self.assertTrue(self.v.normalise_follow_up_preference("yes"))
        self.assertFalse(self.v.normalise_follow_up_preference("no"))


class TestCollectComplaint(unittest.TestCase):
    def test_valid_answers_build_the_complaint_dict(self):
        complaint, _ = collect(GOOD_ANSWERS)
        self.assertEqual(complaint["complaint_id"], "")  # assigned later by data_manager
        self.assertEqual(complaint["name"], "Ann Lee")
        self.assertEqual(complaint["phone"], "91234567")
        self.assertEqual(complaint["category"], "food_quality")  # "Food Quality" is normalised
        self.assertIs(complaint["wants_followup"], True)
        self.assertEqual(complaint["order_ref"], "")

    def test_invalid_input_is_rejected_and_reprompted(self):
        answers = [
            "", "Ann Lee",                          # blank name, then valid
            "not-an-email", "ann@example.com",     # bad email, then valid
            "12345", "91234567",                   # bad phone, then valid
            "OUT-01",                              # outlet
            "18/09/2026", FUTURE, PAST,            # bad format, future, then valid datetime
            "",                                    # order ref (optional)
            "rude", "Food Quality",                # bad category, then valid
            "The soup was cold.",                  # description
            "maybe", "No",                         # bad follow-up, then valid
        ]
        complaint, printed = collect(answers)
        self.assertEqual(complaint["name"], "Ann Lee")
        self.assertIs(complaint["wants_followup"], False)
        for message in ("Name cannot be empty", "Invalid email", "Invalid phone",
                        "Invalid date/time", "cannot be in the future",
                        "Invalid complaint category", "Please enter Yes or No"):
            self.assertIn(message, printed)


class TestDisplays(unittest.TestCase):
    complaint = {"complaint_id": "CMP-0001", "outlet_id": "OUT-01", "name": "Ann Lee",
                 "category": "hygiene", "description": "A bug in my soup."}
    ai_output = {"ai_category": "hygiene", "key_details": ["bug", "soup"], "severity": "medium",
                 "reason": "Insect in food.", "reputational_risk": True, "confidence": "high"}
    result = {"final_severity": "high", "outcome": "escalate", "outlet_flagged": True,
              "override_applied": True, "override_reason": "Safety keyword detected."}

    def test_display_result_shows_complaint_ai_and_decision(self):
        text = show(IOManager.display_result, self.complaint, self.ai_output, self.result)
        for expected in ("CMP-0001", "OUT-01", "bug, soup", "MEDIUM", "YES",
                         "HIGH", "ESCALATE", "Safety keyword detected."):
            self.assertIn(expected, text)

    def test_display_result_hides_override_notice_when_no_override(self):
        text = show(IOManager.display_result, self.complaint, self.ai_output,
                    {**self.result, "override_applied": False})
        self.assertNotIn("Override Notice", text)

    def test_display_summary_lists_records_and_total(self):
        text = show(IOManager.display_summary, [self.complaint, {**self.complaint, "complaint_id": "CMP-0002"}])
        self.assertIn("CMP-0001", text)
        self.assertIn("CMP-0002", text)
        self.assertIn("Total Records: 2", text)

    def test_display_summary_handles_no_records(self):
        self.assertIn("No complaint records found", show(IOManager.display_summary, []))

    def test_display_ai_retry_message(self):
        text = show(IOManager.display_ai_retry, 2, 1, 3)
        self.assertIn("Retrying in 2s", text)
        self.assertIn("Attempt 1/3", text)


if __name__ == "__main__":
    unittest.main()