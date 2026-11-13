import pytest
from ai_manager.ai_manager import AIManager
from ai_manager.mock_ai_client import MockAIClient
from ai_manager.response_validator import ResponseValidator

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


def valid_ai_output():
    # Return a valid AI response for use in validation tests.
    return {
        "ai_category": "service",
        "key_details": ["Delayed order", "Rude staff"],
        "severity": "medium",
        "reason": "The customer experienced poor service.",
        "reputational_risk": False,
        "confidence": "high"
    }


def test_validate_complete_ai_response():
    # Test that a response containing all valid fields is accepted.
    validator = ResponseValidator()

    assert validator.validate_ai_response(valid_ai_output()) is True


@pytest.mark.parametrize(
    "missing_field",
    [
        "ai_category",
        "key_details",
        "severity",
        "reason",
        "reputational_risk",
        "confidence",
    ]
)
def test_validate_missing_fields(missing_field):
    # Test that every required field must be present.
    validator = ResponseValidator()
    response = valid_ai_output()
    del response[missing_field]

    assert validator.validate_ai_response(response) is False


@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("ai_category", 123),
        ("key_details", "Delayed order"),
        ("severity", 3),
        ("reason", None),
        ("reputational_risk", "False"),
        ("confidence", 0.9),
    ]
)
def test_validate_incorrect_field_types(field, invalid_value):
    # Test that fields with incorrect data types are rejected.
    validator = ResponseValidator()
    response = valid_ai_output()
    response[field] = invalid_value

    assert validator.validate_ai_response(response) is False


@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("ai_category", "delivery"),
        ("severity", "critical"),
        ("confidence", "certain"),
    ]
)
def test_validate_invalid_field_values(field, invalid_value):
    # Test that values outside the permitted options are rejected.
    validator = ResponseValidator()
    response = valid_ai_output()
    response[field] = invalid_value

    assert validator.validate_ai_response(response) is False


@pytest.mark.parametrize(
    "invalid_details",
    [
        [123],
        ["Delayed order", None],
        ["Rude staff", True],
    ]
)
def test_validate_invalid_key_details(invalid_details):
    # Test that every item in key_details must be a string.
    validator = ResponseValidator()
    response = valid_ai_output()
    response["key_details"] = invalid_details

    assert validator.validate_ai_response(response) is False


@pytest.mark.parametrize(
    "invalid_reason",
    [
        "",
        " ",
        "\n\t",
    ]
)
def test_validate_empty_reason(invalid_reason):
    # Test that empty or whitespace-only reasons are rejected.
    validator = ResponseValidator()
    response = valid_ai_output()
    response["reason"] = invalid_reason

    assert validator.validate_ai_response(response) is False


@pytest.mark.parametrize(
    "invalid_response",
    [
        None,
        [],
        "Invalid response",
        123,
    ]
)
def test_validate_non_dictionary_response(invalid_response):
    # Test that responses which are not dictionaries are rejected.
    validator = ResponseValidator()

    assert validator.validate_ai_response(invalid_response) is False


@pytest.mark.parametrize(
    "category",
    [
        "food_quality",
        "service",
        "hygiene",
        "billing",
        "other",
    ]
)
def test_validate_allowed_categories(category):
    # Test that all permitted complaint categories are accepted.
    validator = ResponseValidator()
    response = valid_ai_output()
    response["ai_category"] = category

    assert validator.validate_ai_response(response) is True


@pytest.mark.parametrize(
    "severity",
    ["low", "medium", "high"]
)
def test_validate_allowed_severity(severity):
    # Test that all permitted severity levels are accepted.
    validator = ResponseValidator()
    response = valid_ai_output()
    response["severity"] = severity

    assert validator.validate_ai_response(response) is True


@pytest.mark.parametrize(
    "confidence",
    ["low", "medium", "high"]
)
def test_validate_allowed_confidence(confidence):
    # Test that all permitted confidence levels are accepted.
    validator = ResponseValidator()
    response = valid_ai_output()
    response["confidence"] = confidence

    assert validator.validate_ai_response(response) is True


@pytest.mark.parametrize(
    "risk",
    [True, False]
)
def test_validate_allowed_reputational_risk(risk):
    # Test that both Boolean values are accepted.
    validator = ResponseValidator()
    response = valid_ai_output()
    response["reputational_risk"] = risk

    assert validator.validate_ai_response(response) is True


@pytest.mark.parametrize(
    "details",
    [
        [],
        ["Delayed order"],
        ["Delayed order", "Rude staff"],
    ]
)
def test_validate_allowed_key_details(details):
    # Test that valid lists of key details are accepted.
    validator = ResponseValidator()
    response = valid_ai_output()
    response["key_details"] = details

    assert validator.validate_ai_response(response) is True


@pytest.mark.parametrize(
    "category, description",
    [
        ("service", "The staff was rude."),
        ("hygiene", "There was a hair in my food."),
        ("food quality", "The chicken was undercooked."),
        ("billing", "I was charged twice."),
        ("other", "The restaurant was too noisy."),
    ]
)
def test_build_prompt_includes_complaint_details(category, description):
    # Test that the prompt includes the customer's category and description.
    manager = AIManager(MockAIClient())
    complaint = {
        "category": category,
        "description": description
    }

    prompt = manager._build_prompt(complaint)

    assert category in prompt
    assert description in prompt
    assert isinstance(prompt, str)


def test_build_prompt_includes_required_instructions():
    # Test that the prompt specifies the required AI output format.
    manager = AIManager(MockAIClient())
    complaint = {
        "category": "service",
        "description": "The staff was rude."
    }

    prompt = manager._build_prompt(complaint)

    assert "food_quality, service, hygiene, billing, other" in prompt
    assert "low, medium, high" in prompt
    assert "ai_category" in prompt
    assert "key_details" in prompt
    assert "severity" in prompt
    assert "reason" in prompt
    assert "reputational_risk" in prompt
    assert "confidence" in prompt
    assert "Return only valid JSON" in prompt
    assert "Do not include markdown" in prompt