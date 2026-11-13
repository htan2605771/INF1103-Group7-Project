from ai_manager.ai_manager import AIManager
from ai_manager.mock_ai_client import MockAIClient

def test_valid_ai_response():
    # Test AI response handling using a mock client without a live API.
    complaint = {
        "category": "service",
        "description": "The staff was rude and my order was delayed."
    }

    manager = AIManager(MockAIClient())
    result = manager.get_ai_output(complaint)

    assert result["ai_category"] == "service"
    assert result["severity"] == "medium"
    assert result["confidence"] == "high"
    assert result["reputational_risk"] is False
    assert isinstance(result["key_details"], list)

def test_invalid_ai_response():
    # Test fallback handling when the AI returns invalid JSON.
    complaint = {
        "category": "hygiene",
        "description": "There was a hair in my food."
    }

    manager = AIManager(MockAIClient(response="Invalid JSON"))
    result = manager.get_ai_output(complaint)

    assert result["ai_category"] == "hygiene"
    assert result["severity"] == "medium"
    assert result["confidence"] == "low"
    assert result["reputational_risk"] is False
    assert result["key_details"] == []
    assert "manual review" in result["reason"]