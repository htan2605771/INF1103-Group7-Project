"""data_manager.py - Handles persistent storage of complaint records."""

import json
import os
from datetime import datetime, timedelta

DATA_FILE = "complaints_data.json"


def save_complaint(complaint: dict, ai_output: dict, result: dict) -> None:
    pass


def load_complaints() -> list[dict]:
    """Load all stored complaint records on startup.
    Return empty list if file is missing or corrupt."""
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        print("[!] Warning: complaints_data.json is corrupt. Starting fresh.")
        return []


def filter_by_outlet_and_date(outlet_id: str, days: int) -> list[dict]:
    return []