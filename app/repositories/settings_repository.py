import json
import os

from app.models.settings import Settings


def _safe_filename(variant_name):
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in variant_name) + ".json"


class SettingsRepository:
    """Each variant gets its own settings JSON file, so switching variants
    never mixes up their configuration."""

    def __init__(self, settings_dir):
        self._settings_dir = settings_dir

    def _path_for(self, variant_name):
        return os.path.join(self._settings_dir, _safe_filename(variant_name))

    def load(self, variant_name):
        path = self._path_for(variant_name)

        if not os.path.exists(path):
            return Settings(variant_name)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return Settings.from_dict(variant_name, data)

    def save(self, settings):
        os.makedirs(self._settings_dir, exist_ok=True)
        path = self._path_for(settings.variant_name)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings.to_dict(), f, indent=2)
