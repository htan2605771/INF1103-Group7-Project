"""merchant_config_manager.py - Manages merchant configuration and store reference data."""

import json
from pathlib import Path


class MerchantConfigManager:
    """Loads merchant profile and outlet reference data from JSON."""

    def __init__(self, config_file: str = "merchant_config.json"):
        self._config_file = Path(config_file)

    def load_config(self) -> dict:
        """Load the merchant configuration data safely."""
        try:
            with open(self._config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {"business_name": "", "outlets": []}

        return data

    def get_store_name(self, outlet_id: str) -> str:
        """Looks up and returns the store name matching the outlet_id."""
        config = self.load_config()
        for outlet in config.get("outlets", []):
            if outlet.get("outlet_id") == outlet_id:
                return outlet.get("store_name", outlet_id)
        return outlet_id