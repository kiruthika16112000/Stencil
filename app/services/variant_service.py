from app.models.variant import Variant


class VariantError(Exception):
    pass


class VariantService:
    """Holds a working copy of variants in memory. Add/rename/delete only
    change the working copy; save() is what persists it to the repository."""

    def __init__(self, variant_repository):
        self._repository = variant_repository
        self._working_set = []

    def load(self):
        self._working_set = self._repository.load()
        return self.list_variants()

    def list_variants(self):
        return list(self._working_set)

    def add(self, name):
        name = name.strip()

        if not name:
            raise VariantError("Variant name is required.")

        if any(variant.name == name for variant in self._working_set):
            raise VariantError(f"'{name}' already exists.")

        self._working_set.append(Variant(name))

    def rename(self, old_name, new_name):
        new_name = new_name.strip()

        if not new_name:
            raise VariantError("Variant name is required.")

        if new_name != old_name and any(variant.name == new_name for variant in self._working_set):
            raise VariantError(f"'{new_name}' already exists.")

        for variant in self._working_set:
            if variant.name == old_name:
                variant.rename(new_name)
                return

        raise VariantError(f"'{old_name}' not found.")

    def delete(self, name):
        self._working_set = [variant for variant in self._working_set if variant.name != name]

    def save(self):
        self._repository.save(self._working_set)
