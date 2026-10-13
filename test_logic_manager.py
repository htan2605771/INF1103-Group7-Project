from logic_manager import evaluate_complaint, calculate_score


def test_01_ambiguous_complaint():
    """Ambiguous complaints should yield manual_review and override_applied=True."""
    print("\n--- Ambiguous Output Test ---")
    complaint = {
        "description": "bad", 
        "is_ambiguous": True, 
        "category": "service"
    }
    ai_output = {
        "severity": "low", 
        "reputational_risk": False, 
        "confidence": "high"
    }
    history = []

    result = evaluate_complaint(complaint, ai_output, history)

    assert result["final_severity"] == "manual_review"
    assert result["override_applied"] is True
    assert "ambiguous" in result["override_reason"].lower()
    print("PASS")


def test_02_safety_keyword_override():
    """Food poisoning keyword should override low AI severity to high."""
    print("\n--- Safety Keyword Override Test ---")
    complaint = {
        "description": "I got food poisoning and started to vomit.",
        "is_ambiguous": False,
        "category": "service"
    }
    ai_output = {
        "severity": "low", 
        "reputational_risk": False, 
        "confidence": "high"
    }
    history = []

    result = evaluate_complaint(complaint, ai_output, history)

    assert result["final_severity"] == "high"
    assert result["override_applied"] is True
    assert "safety keyword" in result["override_reason"].lower()
    print("PASS")


def test_03_no_override_needed():
    """Standard complaint without safety keywords or ambiguity should retain AI severity."""
    print("\n--- Standard Input Test (No Override) ---")
    complaint = {
        "description": "The cashier was slightly rude to me during my visit.",
        "is_ambiguous": False,
        "category": "service"
    }
    ai_output = {
        "severity": "low", 
        "reputational_risk": False, 
        "confidence": "high"
    }
    history = []

    result = evaluate_complaint(complaint, ai_output, history)

    assert result["final_severity"] == "low"
    assert result["override_applied"] is False
    assert result["override_reason"] == ""
    print("PASS")


def test_04_outlet_flagging():
    """2 or more complaints with at least 1 hygiene issue should flag outlet_flagged = True."""
    print("\n--- Outlet Pattern Flagging Test ---")
    complaint = {
        "description": "The cashier was slightly rude to me during my visit.",
        "is_ambiguous": False,
        "category": "hygiene"
    }
    ai_output = {
        "severity": "low", 
        "reputational_risk": False, 
        "confidence": "high"
    }
    # history + [complaint] length will be 2, with at least one 'hygiene' category
    history = [{"category": "service"}]

    result = evaluate_complaint(complaint, ai_output, history)

    assert result["outlet_flagged"] is True
    print("PASS")


def test_05_score_calculation():
    """Test score calculation: High severity (50) + Reputational Risk (30) + Outlet Flag (20)."""
    print("\n--- Score Calculation Test ---")
    final_severity = "high"
    reputational_risk = True
    outlet_flagged = True

    score = calculate_score(final_severity, reputational_risk, outlet_flagged)

    assert score == 100
    print("PASS")


def run_all_tests():
    print("-------------------------------------------------------------------------")
    print("1. Tests for evaluate_complaint()")
    print("-------------------------------------------------------------------------")
    test_01_ambiguous_complaint()
    test_02_safety_keyword_override()
    test_03_no_override_needed()
    test_04_outlet_flagging()

    print("\n-------------------------------------------------------------------------")
    print("2. Test for calculate_score()")
    print("-------------------------------------------------------------------------")
    test_05_score_calculation()


if __name__ == "__main__":
    run_all_tests()