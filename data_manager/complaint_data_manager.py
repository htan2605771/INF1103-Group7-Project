"""complaint_data_manager.py - JSON-file implementation of ComplaintStorage."""

import json

from .complaint_storage import ComplaintStorage


class ComplaintDataManager(ComplaintStorage):
    """Stores complaints in a single JSON file (a JSON array of records)."""

    def __init__(self, data_file: str = "complaints_data.json"):
        super().__init__()
        self._data_file = data_file

    @property
    def data_file(self) -> str:
        """Path of the JSON file (read-only)."""
        return self._data_file

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

    def _write_all(self, records: list[dict]) -> None:
        with open(self._data_file, "w") as f:
            json.dump(records, f, indent=2)