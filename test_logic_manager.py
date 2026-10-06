import unittest
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
        complaint = {"description": "bad", "is_ambiguous": True}
        ai_output = {"severity": "low"}
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
            "is_ambiguous": False
        }
        ai_output = {"severity": "low"}
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
            "is_ambiguous": False
        }
        ai_output = {"severity": "low"}
        history = []

        result = evaluate_complaint(complaint, ai_output, history)

        self.assertEqual(result["final_severity"], "low")
        self.assertFalse(result["override_applied"])
        self.assertEqual(result["override_reason"], "")

    def test_04_outlet_flagging(self):
        """3 or more past complaints in history should flag outlet_flagged = True."""
        print("\n--- Outlet Pattern Flagging Test ---")
        complaint = {"description": "Cold food.", "is_ambiguous": False}
        ai_output = {"severity": "low"}
        history = [{"id": 1}, {"id": 2}, {"id": 3}]

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


if __name__ == "__main__":
    unittest.main(testRunner=PassTestRunner)