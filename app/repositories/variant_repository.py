import json
import os

from app.models.variant import Variant


class VariantRepository:
    def __init__(self, storage_path):
        self._storage_path = storage_path

    def load(self):
        if not os.path.exists(self._storage_path):
            return []

        with open(self._storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        names = data if isinstance(data, list) else data.get("variants", [])
        return [Variant(name) for name in names]

    def save(self, variants):
        os.makedirs(os.path.dirname(self._storage_path) or ".", exist_ok=True)

        with open(self._storage_path, "w", encoding="utf-8") as f:
            json.dump([variant.name for variant in variants], f, indent=2)
