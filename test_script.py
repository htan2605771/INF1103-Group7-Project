import json
import unittest
import ai_manager
from logic_manager import evaluate_complaint, calculate_score


class PassTestResult(unittest.TextTestResult):
    """Custom result formatter that prints PASS instead of a dot."""
    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.write("PASS\n")
        self.stream.flush()

class PassTestRunner(unittest.TextTestRunner):
    resultclass = PassTestResult


class Test01EvaluateComplaint(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n-------------------------------------------------------------------------")
        print("1. Tests for evaluate_complaint()")
        print("-------------------------------------------------------------------------")

    def test_01_ambiguous_complaint(self):
        """Ambiguous complaints should yield manual_review and override_applied=True."""
        print("\n--- Ambiguous Output Test ---")
        complaint = {"description": "bad", "is_ambiguous": True, "category": "service"}
        ai_output = {"severity": "low", "reputational_risk": False, "confidence": "high"}
        history = []

        result = evaluate_complaint(complaint, ai_output, history)

        self.assertEqual(result["final_severity"], "manual_review")
        self.assertTrue(result["override_applied"])
        self.assertIn("ambiguous", result["override_reason"].lower())

    def test_02_safety_keyword_override(self):
        """Food poisoning keyword should override low AI severity to high."""
        print("\n--- Safety Keyword Override Test ---")
        complaint = {
            "description": "I got food poisoning and started to vomit.",
            "is_ambiguous": False,
            "category": "food_quality"
        }
        ai_output = {"severity": "low", "reputational_risk": False, "confidence": "high"}
        history = []

        result = evaluate_complaint(complaint, ai_output, history)

        self.assertEqual(result["final_severity"], "high")
        self.assertTrue(result["override_applied"])
        self.assertIn("safety keyword", result["override_reason"].lower())

    def test_03_no_override_needed(self):
        """Standard complaint without safety keywords or ambiguity should retain AI severity."""
        print("\n--- Standard Input Test (No Override) ---")
        complaint = {
            "description": "The cashier was slightly rude to me.",
            "is_ambiguous": False,
            "category": "service"
        }
        ai_output = {"severity": "low", "reputational_risk": False, "confidence": "high"}
        history = []

        result = evaluate_complaint(complaint, ai_output, history)

        self.assertEqual(result["final_severity"], "low")
        self.assertFalse(result["override_applied"])
        self.assertEqual(result["override_reason"], "")

    def test_04_outlet_flagging(self):
        """Past complaints including hygiene should flag outlet_flagged = True."""
        print("\n--- Outlet Pattern Flagging Test ---")
        complaint = {"description": "Cold food.", "is_ambiguous": False, "category": "food_quality"}
        ai_output = {"severity": "low", "reputational_risk": False, "confidence": "high"}
        history = [
            {"category": "hygiene"},
            {"category": "service"},
            {"category": "service"}
        ]

        result = evaluate_complaint(complaint, ai_output, history)

        self.assertTrue(result["outlet_flagged"])


class Test02CalculateScore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n-------------------------------------------------------------------------")
        print("2. Test for calculate_score()")
        print("-------------------------------------------------------------------------")

    def test_01_score_calculation(self):
        """Test score calculation: High severity (50) + Reputational Risk (30) + Outlet Flag (20)."""
        print("\n--- Score Calculation Test ---")
        final_severity = "high"
        reputational_risk = True
        outlet_flagged = True

        score = calculate_score(final_severity, reputational_risk, outlet_flagged)

        self.assertEqual(score, 100)

class Test03AIManagerOffline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n-------------------------------------------------------------------------")
        print("3. Tests for ai_manager (Offline Mock)")
        print("-------------------------------------------------------------------------")

    def test_01_get_ai_output_successful_mock(self):
        """Test get_ai_output with a mocked call_ai_api returning a valid JSON string."""
        print("\n--- AI Successful Mock Test ---")
        original_call_ai_api = getattr(ai_manager, "call_ai_api", None)

        def fake_call_ai_api(prompt, max_retries=3, on_retry=None):
            return json.dumps({
                "ai_category": "service",
                "key_details": ["rude staff"],
                "severity": "medium",
                "reason": "Customer reported rude staff.",
                "reputational_risk": False,
                "confidence": "high"
            })

        try:
            ai_manager.call_ai_api = fake_call_ai_api
            complaint = {
                "complaint_id": "CMP-0003",
                "name": "Alice",
                "email": "alice@example.com",
                "phone": "81112222",
                "outlet_id": "OUT-03",
                "datetime": "2026-10-10T14:00:00",
                "order_ref": "ORD-200",
                "category": "service",
                "description": "The staff were extremely rude.",
                "wants_followup": True
            }
            output = ai_manager.get_ai_output(complaint)

            self.assertEqual(output["ai_category"], "service")
            self.assertEqual(output["confidence"], "high")
        finally:
            if original_call_ai_api is not None:
                ai_manager.call_ai_api = original_call_ai_api

    def test_02_get_ai_output_api_failure_fallback(self):
            """Test get_ai_output offline fallback when call_ai_api returns None."""
            print("\n--- AI Failure Fallback Test ---")
            original_call_ai_api = getattr(ai_manager, "call_ai_api", None)

            def fake_call_ai_api_error(prompt, max_retries=3, on_retry=None):
                return None

            try:
                ai_manager.call_ai_api = fake_call_ai_api_error
                complaint = {
                    "complaint_id": "CMP-0004",
                    "name": "Bob",
                    "email": "bob@example.com",
                    "phone": "83334444",
                    "outlet_id": "OUT-04",
                    "datetime": "2026-10-10T15:00:00",
                    "order_ref": "",
                    "category": "food_quality",
                    "description": "The soup was cold.",
                    "wants_followup": False
                }
                output = ai_manager.get_ai_output(complaint)

                self.assertEqual(output["confidence"], "low")
                self.assertIn("key_details", output)
            finally:
                if original_call_ai_api is not None:
                    ai_manager.call_ai_api = original_call_ai_api


if __name__ == "__main__":
    unittest.main(testRunner=PassTestRunner)