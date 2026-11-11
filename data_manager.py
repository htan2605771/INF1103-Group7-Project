"""data_manager.py - Handles persistent storage of complaint records."""

import json
import logging
import re
from datetime import datetime, timedelta

class ComplaintDataManager:
    """Manages persistent storage, loading, filtering, and ID generation for complaints."""

    def __init__(self, data_file: str = "complaints_data.json"):
        self.data_file = data_file
        self.logger = logging.getLogger(__name__)

    def generate_complaint_id(self, records: list[dict]) -> str:
        """Return the next complaint ID (CMP-0001, CMP-0002, ...) based on stored records."""
        highest = 0
        for r in records:
            match = re.fullmatch(r"CMP-(\d+)", str(r.get("complaint_id", "")))
            if match:
                highest = max(highest, int(match.group(1)))
        return f"CMP-{highest + 1:04d}"

    def save_complaint(self, complaint: dict, ai_output: dict, result: dict) -> None:
        """Merge complaint + ai_output + result into one record and append to storage.
        If the complaint has no ID yet, one is generated and written back onto the
        complaint dict so later steps (e.g. display_result) can show it."""
        records = self.load_complaints()

        if not complaint.get("complaint_id"):
            complaint["complaint_id"] = self.generate_complaint_id(records)

        record = {**complaint, **ai_output, **result}
        records.append(record)

        with open(self.data_file, "w") as f:
            json.dump(records, f, indent=2)

    def load_complaints(self) -> list[dict]:
        """Load all stored complaint records.
        Returns an empty list if the file is missing, unreadable, corrupt or not a list of records."""
        try:
            with open(self._data_file, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            return []
        except (json.JSONDecodeError, ValueError):
            self._logger.warning("%s is corrupt. Starting fresh.", self._data_file)
            return []
        except OSError as error:
            self._logger.warning("Could not read %s: %s. Starting fresh.", self._data_file, error)
            return []
 
        if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
            self._logger.warning("%s does not contain a list of records. Starting fresh.", self._data_file)
            return []
 
        return data


    def filter_by_outlet_and_date(self, outlet_id: str, days: int) -> list[dict]:
        """Return all complaint records for a given outlet within the last `days` days."""
        cutoff = datetime.now() - timedelta(days=days)
        filtered = []
 
        for r in self.load_complaints():
            if r.get("outlet_id") != outlet_id:
                continue
            try:
                record_dt = datetime.strptime(r.get("datetime", ""), "%Y-%m-%dT%H:%M:%S")
            except (ValueError, TypeError):
                continue  # missing or badly formatted datetime: skip this record
            if record_dt >= cutoff:
                filtered.append(r)
 
        return filtered
 