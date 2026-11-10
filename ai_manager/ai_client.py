from __future__ import annotations
from abc import ABC, abstractmethod
import logging
import time


class AIClient(ABC):
    # Parent class for AI clients. This class handles retries while child classes implement the send function.
    def __init__(self, max_retries: int = 3, base_delays: int = 2):
        self.__max_retries = max_retries
        self.__base_delays = base_delays
        self.__logger = logging.getLogger(__name__)


    def call_ai_api(self, prompt: str, on_retry=None) -> str | None: # sends the prompt to the AI API and handle API failures

        for attempt in range(1, self.__max_retries + 1):
            try:
                return self._send(prompt)

            except Exception as error:
                self.__logger.error(
                    f"AI API attempt {attempt}/{self.__max_retries} failed: "
                    f"{type(error).__name__}: {error}"
                )

                if attempt < self.__max_retries:
                    sleep_time = self.__base_delays * attempt

                    if on_retry:
                        on_retry(sleep_time, attempt, self.__max_retries)

                    time.sleep(sleep_time)
                else:
                    self.__logger.error("AI API failed after all retry attempts.")

        return None

    @abstractmethod
    def _send(self, prompt: str) -> str:
        # This is a protected method. It sends one request to the AI and the Child classes must implement this function.
        # Only used by call_ai_api() inside this class. Do not call it directly.
        pass

