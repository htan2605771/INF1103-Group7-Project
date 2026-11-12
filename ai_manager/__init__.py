""" AI Manager Module package for handling AI-related tasks in the complaint triage system. Builds prompts, calls the AI model, and parses and validates the output. """

# This file tells Python that this folder is a package. It can be left empty, but it can also contain package-level docstrings or initialization code if needed.
# It allows imports and tests (e.g. unittest) to recognise this folder as a package for it to work properly. 
# For example, you can import modules from this package using `from ai_manager import module_name`.
# Please keep this file even if it has no code.
from .ai_manager import AIManager
from .ai_client import AIClient
from .gemini_client import GeminiClient
from .mock_ai_client import MockAIClient