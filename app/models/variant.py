class Variant:
    def __init__(self, name):
        self.name = name

    def rename(self, new_name):
        self.name = new_name

    def __eq__(self, other):
        return isinstance(other, Variant) and self.name == other.name

    def __repr__(self):
        return f"Variant({self.name!r})"
