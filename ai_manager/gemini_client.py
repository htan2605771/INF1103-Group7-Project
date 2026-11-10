from __future__ import annotations
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from .ai_client import AIClient


class GeminiClient(AIClient):
    # child class of the AIClient class. This class sends requests to the gemini api.
    def __init__(self, max_retries: int = 3, base_delays: int = 2, model: str = "gemini-3.1-flash-lite"):
        super().__init__(max_retries, base_delays)
        load_dotenv()  # Load environment variables from .env file
        self.__api_key = os.getenv("GEMINI_API_KEY")
        self.__model = model

    def _send(self, prompt: str) -> str:
        if not self.__api_key:
            raise ValueError("Gemini API key is missing.")
        client = genai.Client(api_key=self.__api_key)
        try:
            response = client.models.generate_content(
                model=self.__model,
                contents=prompt, # sends the prompt to Gemini
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )

            return response.text

        finally: 
            client.close()