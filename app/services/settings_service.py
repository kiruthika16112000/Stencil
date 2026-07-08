class SettingsService:
    """Holds the currently loaded variant's settings in memory; save() is
    what persists it, mirroring VariantService's working-copy pattern."""

    def __init__(self, settings_repository):
        self._repository = settings_repository
        self._current = None

    def load(self, variant_name):
        self._current = self._repository.load(variant_name)
        return self._current

    @property
    def current(self):
        return self._current

    def update(self, settings):
        self._current = settings

    def save(self):
        if self._current is None:
            raise ValueError("No settings loaded to save.")

        self._repository.save(self._current)
