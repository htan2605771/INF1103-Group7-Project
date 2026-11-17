from __future__ import annotations
from typing import Callable
import logging # used to record API errors
import json
from .ai_client import AIClient # imports the parent class for AI clients
from .response_validator import ResponseValidator # imports the class that validates the AI output


class AIManager:
    def __init__(self, client: AIClient) -> None:
        self.__client = client
        self.__response_validator = ResponseValidator()
        self.__logger = logging.getLogger(__name__) # creates a logger for this file


    def _build_prompt(self, complaint: dict) -> str: # build the prompt to send to the AI API
        prompt = f"""
        
        You are an AI assistant for an F&B customer complaint triage system.
        Analyse the following customer complaint.
        Customer-selected category: {complaint["category"]}
        Complaint description: {complaint["description"]}

        Your tasks are to:
        1. Classify the complaint into exactly one of the following categories:
        food_quality, service, hygiene, billing, other
        2. Extract the key details or issues mentioned in the complaint.
        3. Assess the severity of the complaint as exactly one of: 
        low, medium, high
        4. Provide a short reason for the classification and severity.
        5. Determine whether the complaint indicates a reputational risk.
        Return true or false.
        6. Assess your confidence in the analysis as exactly one of:
        low, medium, high

        Return only valid JSON in exactly this structure:

        {{
            "ai_category": "food_quality",
            "key_details": ["detail 1", "detail 2"],
            "severity": "low",
            "reason": "short explanation",
            "reputational_risk": false,
            "confidence": "high"
        }}

        Do not include markdown, code fences, or any additional text outside the JSON.
        """

        return prompt



    def _parse_ai_response(self, response: str | None) -> dict | None: # parse the AI response into JSON
        if not response: # checks whether the response is empty or None
            self.__logger.error("AI response is empty, there is no response to parse.")
            return None

        else:
            #for markdown fences
            text = response.strip().strip("`") # removes leading and trailing whitespace and backticks from the response
            if text.lower().startswith("json"): # removes the json prefix if it exists, as some AI responses may include it
                text = text[4:]

            try:
                data = json.loads(text) # attempts to parse the response from JSON to a dictionary object

                if not isinstance(data, dict): # checks whether the parsed object is a dictionary
                    self.__logger.error("Parsed AI response is not a dictionary object.")
                    return None
                
                return data
            
            except json.JSONDecodeError as error:
                self.__logger.error(f"Failed to parse AI response as JSON: {error}")
                return None


    def _fallback_ai_output(self, complaint: dict) -> dict: # returns a default ai_output when the AI fails, flagged for manual review
        fallback = {
            "ai_category": complaint["category"], # uses customer-selected category as a fallback for ai_category
            "key_details": [],
            "severity": "medium",
            "reason": "AI analysis unavailable, using customer-selected category, flagged for manual review",
            "reputational_risk": False,
            "confidence": "low"
        }
        return fallback


    def get_ai_output(self, complaint: dict, on_retry: Callable[[int, int, int], None] | None = None) -> dict: # run a complaint through the complete AI processing flow
        prompt = self._build_prompt(complaint)
        response = self.__client.call_ai_api(prompt, on_retry=on_retry)
        ai_output = self._parse_ai_response(response)
        if self.__response_validator.validate_ai_response(ai_output): # if validate is successful return the ai_output
            return ai_output
        self.__logger.error("AI output validation failed, using fallback ai_output.")
        return self._fallback_ai_output(complaint) # returns the fallback ai_output
