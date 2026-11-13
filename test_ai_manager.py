import pytest
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


@pytest.mark.parametrize(
    "response, expected",
    [
        ('{"ai_category": "service"}', {"ai_category": "service"}),
        ('  {"ai_category": "hygiene"}  ', {"ai_category": "hygiene"}),
        ('```json\n{"ai_category": "billing"}\n```', {"ai_category": "billing"}),
        ('```\n{"ai_category": "other"}\n```', {"ai_category": "other"}),
        ("{}", {}),
    ]
)
def test_parse_valid_json_response(response, expected):
    # Test parsing of valid JSON objects in different formats.
    manager = AIManager(MockAIClient())

    result = manager._parse_ai_response(response)

    assert result == expected


@pytest.mark.parametrize(
    "response",
    [
        None,
        "",
        "   ",
        "Invalid JSON",
        '{"ai_category": "service"',
        '[1, 2, 3]',
        '"service"',
        "123",
        "null",
    ]
)
def test_parse_invalid_json_response(response):
    # Test that invalid or non-dictionary responses return None.
    manager = AIManager(MockAIClient())

    result = manager._parse_ai_response(response)

    assert result is None