"""complaint_storage.py - Abstract contract for storing complaints."""

import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta


class ComplaintStorage(ABC):
    """Abstract contract for storing complaints.

    Subclasses only decide HOW records are read and written (JSON file, database, ...).
    The shared behaviour (ID generation, merging a record, filtering) lives here once,
    so every storage backend behaves the same way.
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)  # protected: for this class and subclasses

    # ---- the two operations each backend must implement ----
    @abstractmethod
    def load_complaints(self) -> list[dict]:
        """Return all stored records. Must return [] (never raise) if storage is missing or unreadable."""

    @abstractmethod
    def _write_all(self, records: list[dict]) -> None:
        """Persist the full list of records. May raise OSError if storage is unavailable."""

    # ---- shared behaviour ----
    def generate_complaint_id(self, records: list[dict]) -> str:
        """Return the next complaint ID (CMP-0001, CMP-0002, ...) based on stored records."""
        highest = 0
        for r in records:
            match = re.fullmatch(r"CMP-(\d+)", str(r.get("complaint_id", "")))
            if match:
                highest = max(highest, int(match.group(1)))
        return f"CMP-{highest + 1:04d}"

    def save_complaint(self, complaint: dict, ai_output: dict, result: dict) -> bool:
        """Merge complaint + ai_output + result into one record and append to storage.
        If the complaint has no ID yet, one is generated and written back onto the
        complaint dict so later steps (e.g. display_result) can show it.
        Returns True if saved, False if storage could not be written (the error is logged, not raised)."""
        records = self.load_complaints()

        if not complaint.get("complaint_id"):
            complaint["complaint_id"] = self.generate_complaint_id(records)

        records.append({**complaint, **ai_output, **result})

        try:
            self._write_all(records)
        except OSError as error:
            self._logger.error("Could not save complaint %s: %s", complaint["complaint_id"], error)
            return False
        return True

    def filter_by_outlet_and_date(self, outlet_id: str, days: int) -> list[dict]:
        """Return all complaint records for a given outlet within the last `days` days."""
        cutoff = datetime.now() - timedelta(days=days)
        filtered = []

        for r in self.load_complaints():
            if r.get("outlet_id") != outlet_id:
                continue
            
            dt_str = r.get("datetime", "")
            if not dt_str:
                continue
                
            record_dt = None
            # Tries minute-level first, then seconds/space-separated variants as fallbacks
            for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    clean_str = dt_str.replace('Z', '').split('+')[0]
                    record_dt = datetime.strptime(clean_str, fmt)
                    break
                except (ValueError, TypeError):
                    continue
            
            if record_dt and record_dt >= cutoff:
                filtered.append(r)

        return filtered