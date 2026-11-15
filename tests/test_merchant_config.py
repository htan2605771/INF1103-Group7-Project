"""Offline tests for MerchantConfigManager (outlet reference data used by the web GUI)."""

import json
import os
import tempfile
import unittest

from data_manager import MerchantConfigManager

CONFIG = {
    "business_name": "Test Group Pte Ltd",
    "outlets": [
        {"outlet_id": "OUT-001", "store_name": "Jewel Changi"},
        {"outlet_id": "OUT-002", "store_name": "Tampines Mall"},
    ],
}
EMPTY = {"business_name": "", "outlets": []}


class TestMerchantConfigManager(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = os.path.join(self._tmp.name, "merchant_config.json")

    def write(self, text):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(text)

    def test_loads_a_valid_config(self):
        self.write(json.dumps(CONFIG))
        self.assertEqual(MerchantConfigManager(self.path).load_config(), CONFIG)

    def test_missing_file_returns_empty_config(self):
        self.assertEqual(MerchantConfigManager(self.path).load_config(), EMPTY)

    def test_corrupt_file_returns_empty_config(self):
        self.write("{ not json")
        self.assertEqual(MerchantConfigManager(self.path).load_config(), EMPTY)

    def test_store_name_lookup(self):
        self.write(json.dumps(CONFIG))
        self.assertEqual(MerchantConfigManager(self.path).get_store_name("OUT-002"), "Tampines Mall")

    def test_unknown_outlet_falls_back_to_its_id(self):
        self.write(json.dumps(CONFIG))
        self.assertEqual(MerchantConfigManager(self.path).get_store_name("OUT-999"), "OUT-999")

    def test_store_name_with_missing_file_falls_back_to_the_id(self):
        self.assertEqual(MerchantConfigManager(self.path).get_store_name("OUT-001"), "OUT-001")


if __name__ == "__main__":
    unittest.main()