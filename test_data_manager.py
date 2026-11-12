"""Offline tests for data_manager (no API, no real data file: every test uses a temp folder)."""

import json
import logging
import os
import tempfile
import unittest
from datetime import datetime, timedelta

from data_manager import ComplaintDataManager, ComplaintStorage

FMT = "%Y-%m-%dT%H:%M:%S"


def sample_complaint(**overrides) -> dict:
    complaint = {
        "complaint_id": "",
        "name": "Ann Lee",
        "email": "ann@example.com",
        "phone": "91234567",
        "outlet_id": "OUT-01",
        "datetime": (datetime.now() - timedelta(days=1)).strftime(FMT),
        "order_ref": "",
        "category": "hygiene",
        "description": "There was a hair in my soup.",
        "wants_followup": True,
    }
    complaint.update(overrides)
    return complaint


AI_OUTPUT = {
    "ai_category": "hygiene",
    "key_details": ["hair in soup"],
    "severity": "medium",
    "reason": "Foreign object in food.",
    "reputational_risk": False,
    "confidence": "high",
}

RESULT = {
    "final_severity": "medium",
    "outcome": "log",
    "outlet_flagged": False,
    "override_applied": False,
    "override_reason": "",
    "score": 25,
}


class DataManagerTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = os.path.join(self._tmp.name, "complaints.json")
        self.dm = ComplaintDataManager(self.path)

    def write_raw(self, text: str) -> None:
        with open(self.path, "w") as f:
            f.write(text)


class TestLoadFailures(DataManagerTestCase):
    """Missing / corrupt persistence files must never crash the app."""

    def test_missing_file_returns_empty_list(self):
        self.assertEqual(self.dm.load_complaints(), [])

    def test_empty_file_returns_empty_list(self):
        self.write_raw("")
        with self.assertLogs("data_manager", level="WARNING"):
            self.assertEqual(self.dm.load_complaints(), [])

    def test_corrupt_json_returns_empty_list_and_logs_warning(self):
        self.write_raw("{ this is not json")
        with self.assertLogs("data_manager", level="WARNING") as logs:
            self.assertEqual(self.dm.load_complaints(), [])
        self.assertIn("corrupt", logs.output[0])

    def test_valid_json_but_not_a_list_returns_empty_list(self):
        self.write_raw('{"complaint_id": "CMP-0001"}')
        with self.assertLogs("data_manager", level="WARNING"):
            self.assertEqual(self.dm.load_complaints(), [])

    def test_list_of_non_records_returns_empty_list(self):
        self.write_raw("[1, 2, 3]")
        with self.assertLogs("data_manager", level="WARNING"):
            self.assertEqual(self.dm.load_complaints(), [])

    def test_unreadable_path_returns_empty_list(self):
        # a directory where the file should be -> open() raises an OSError
        os.mkdir(self.path)
        with self.assertLogs("data_manager", level="WARNING"):
            self.assertEqual(self.dm.load_complaints(), [])

    def test_save_after_corrupt_file_starts_fresh(self):
        self.write_raw("garbage")
        with self.assertLogs("data_manager", level="WARNING"):
            self.assertTrue(self.dm.save_complaint(sample_complaint(), AI_OUTPUT, RESULT))
        self.assertEqual(len(self.dm.load_complaints()), 1)


class TestSaveFailures(DataManagerTestCase):
    def test_save_to_unwritable_location_returns_false_and_does_not_raise(self):
        bad = ComplaintDataManager(os.path.join(self._tmp.name, "no_such_folder", "x.json"))
        with self.assertLogs("data_manager", level="ERROR"):
            self.assertFalse(bad.save_complaint(sample_complaint(), AI_OUTPUT, RESULT))


class TestSaveAndIds(DataManagerTestCase):
    def test_first_id_is_cmp_0001(self):
        self.assertEqual(self.dm.generate_complaint_id([]), "CMP-0001")

    def test_id_is_one_more_than_highest_and_ignores_bad_ids(self):
        records = [{"complaint_id": "CMP-0003"}, {"complaint_id": "CMP-0010"}, {"complaint_id": "oops"}, {}]
        self.assertEqual(self.dm.generate_complaint_id(records), "CMP-0011")

    def test_save_assigns_id_and_writes_it_back_onto_the_complaint(self):
        complaint = sample_complaint()
        self.assertTrue(self.dm.save_complaint(complaint, AI_OUTPUT, RESULT))
        self.assertEqual(complaint["complaint_id"], "CMP-0001")

    def test_save_keeps_an_existing_id(self):
        complaint = sample_complaint(complaint_id="CMP-0042")
        self.dm.save_complaint(complaint, AI_OUTPUT, RESULT)
        self.assertEqual(self.dm.load_complaints()[0]["complaint_id"], "CMP-0042")

    def test_saved_record_merges_all_three_dicts(self):
        self.dm.save_complaint(sample_complaint(), AI_OUTPUT, RESULT)
        record = self.dm.load_complaints()[0]
        self.assertEqual(record["name"], "Ann Lee")           # from complaint
        self.assertEqual(record["ai_category"], "hygiene")     # from ai_output
        self.assertEqual(record["outcome"], "log")             # from result
        self.assertEqual(record["score"], 25)                  # from result

    def test_ids_are_sequential_and_records_survive_a_restart(self):
        self.dm.save_complaint(sample_complaint(), AI_OUTPUT, RESULT)
        self.dm.save_complaint(sample_complaint(), AI_OUTPUT, RESULT)
        reopened = ComplaintDataManager(self.path)  # simulates a new run of the program
        self.assertEqual([r["complaint_id"] for r in reopened.load_complaints()], ["CMP-0001", "CMP-0002"])


class TestFilter(DataManagerTestCase):
    def add(self, **overrides):
        self.dm.save_complaint(sample_complaint(**overrides), AI_OUTPUT, RESULT)

    def test_filters_by_outlet(self):
        self.add(outlet_id="OUT-01")
        self.add(outlet_id="OUT-02")
        found = self.dm.filter_by_outlet_and_date("OUT-01", days=7)
        self.assertEqual([r["outlet_id"] for r in found], ["OUT-01"])

    def test_filters_by_date_window(self):
        recent = (datetime.now() - timedelta(days=2)).strftime(FMT)
        old = (datetime.now() - timedelta(days=30)).strftime(FMT)
        self.add(datetime=recent)
        self.add(datetime=old)
        found = self.dm.filter_by_outlet_and_date("OUT-01", days=7)
        self.assertEqual([r["datetime"] for r in found], [recent])

    def test_skips_records_with_bad_or_missing_datetime(self):
        self.add(datetime="not a date")
        self.add(datetime=None)
        self.write_raw(json.dumps(
            self.dm.load_complaints() + [{"complaint_id": "CMP-0099", "outlet_id": "OUT-01"}]
        ))
        self.assertEqual(self.dm.filter_by_outlet_and_date("OUT-01", days=7), [])

    def test_no_records_returns_empty_list(self):
        self.assertEqual(self.dm.filter_by_outlet_and_date("OUT-01", days=7), [])


class TestClassBehaviour(DataManagerTestCase):
    def test_abstract_base_class_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            ComplaintStorage()

    def test_json_manager_is_a_complaint_storage(self):
        self.assertIsInstance(self.dm, ComplaintStorage)

    def test_a_different_backend_can_replace_it_without_changing_callers(self):
        """Liskov / polymorphism: an in-memory backend gets ID generation, saving and filtering for free."""

        class InMemoryStorage(ComplaintStorage):
            def __init__(self):
                super().__init__()
                self._records = []

            def load_complaints(self):
                return list(self._records)

            def _write_all(self, records):
                self._records = list(records)

        def submit(storage: ComplaintStorage):
            complaint = sample_complaint()
            storage.save_complaint(complaint, AI_OUTPUT, RESULT)
            return complaint["complaint_id"], storage.filter_by_outlet_and_date("OUT-01", 7)

        for storage in (self.dm, InMemoryStorage()):
            complaint_id, found = submit(storage)
            self.assertEqual(complaint_id, "CMP-0001")
            self.assertEqual(len(found), 1)

    def test_data_file_is_read_only(self):
        self.assertEqual(self.dm.data_file, self.path)
        with self.assertRaises(AttributeError):
            self.dm.data_file = "other.json"


if __name__ == "__main__":
    logging.disable(logging.NOTSET)
    unittest.main()