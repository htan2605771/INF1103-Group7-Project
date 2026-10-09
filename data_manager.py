"""data_manager.py - Handles persistent storage of complaint records."""

import json
import logging
import os
import re
from datetime import datetime, timedelta

DATA_FILE = "complaints_data.json"

logger = logging.getLogger(__name__)  # logger for this file (no print() calls outside io_manager)


def generate_complaint_id(records: list[dict]) -> str:
    """Return the next complaint ID (CMP-0001, CMP-0002, ...) based on stored records."""
    highest = 0
    for r in records:
        match = re.fullmatch(r"CMP-(\d+)", str(r.get("complaint_id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"CMP-{highest + 1:04d}"


def save_complaint(complaint: dict, ai_output: dict, result: dict) -> None:
    """Merge complaint + ai_output + result into one record and append to storage.
    If the complaint has no ID yet, one is generated and written back onto the
    complaint dict so later steps (e.g. display_result) can show it."""
    records = load_complaints()

    if not complaint.get("complaint_id"):
        complaint["complaint_id"] = generate_complaint_id(records)

    record = {**complaint, **ai_output, **result}
    records.append(record)

    with open(DATA_FILE, "w") as f:
        json.dump(records, f, indent=2)


def load_complaints() -> list[dict]:
    """Load all stored complaint records on startup.
    Return empty list if file is missing or corrupt."""
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        logger.warning("%s is corrupt. Starting fresh.", DATA_FILE)
        return []


def filter_by_outlet_and_date(outlet_id: str, days: int) -> list[dict]:
    """Return all complaint records for a given outlet within the last `days` days."""
    records = load_complaints()
    cutoff = datetime.now() - timedelta(days=days)
    filtered = []

    for r in records:
        if r.get("outlet_id") != outlet_id:
            continue
        try:
            record_dt = datetime.strptime(r.get("datetime", ""), "%Y-%m-%dT%H:%M:%S")
            if record_dt >= cutoff:
                filtered.append(r)
        except ValueError:
            continue

    return filtered