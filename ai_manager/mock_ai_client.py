from __future__ import annotations
import json
from .ai_client import AIClient

class MockAIClient(AIClient):
    # Fake AI client for testing purposes. It simulates the behavior of an AI API without making actual network calls.
    # it returns a valid JSON sample response by default.
    def __init__(self, max_retries: int = 3, base_delays: int = 2, response: str | None = None):
        super().__init__(max_retries, base_delays)
        self.__response = response

    def _send(self, prompt: str) -> str:
        # Mock response for testing purposes
        if self.__response is not None:
            return self.__response
        # Default mock response if none provided
        mock_response = {
                "ai_category": "service",
                "key_details": ["Staff was rude", "Order was delayed"],
                "severity": "medium",
                "reason": "Poor staff attitude and delayed service can affect customer experience.",
                "reputational_risk": False,
                "confidence": "high"
            }
        return json.dumps(mock_response)