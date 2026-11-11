"""complaint_storage.py - Abstract contract for storing complaints."""

import logging
import re
from abc import ABC, abstractmethod


class ComplaintStorage(ABC):
    """Abstract contract for storing complaints.

    Subclasses only decide HOW records are read and written (JSON file, database, ...).
    Shared behaviour lives here once, so every storage backend behaves the same way.
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)  # protected: for this class and subclasses

    @abstractmethod
    def load_complaints(self) -> list[dict]:
        """Return all stored records. Must return [] (never raise) if storage is missing or unreadable."""

    @abstractmethod
    def _write_all(self, records: list[dict]) -> None:
        """Persist the full list of records. May raise OSError if storage is unavailable."""

    def generate_complaint_id(self, records: list[dict]) -> str:
        """Return the next complaint ID (CMP-0001, CMP-0002, ...) based on stored records."""
        highest = 0
        for r in records:
            match = re.fullmatch(r"CMP-(\d+)", str(r.get("complaint_id", "")))
            if match:
                highest = max(highest, int(match.group(1)))
        return f"CMP-{highest + 1:04d}"