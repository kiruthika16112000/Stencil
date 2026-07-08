import customtkinter as ctk

from app.services.password_policy import password_strength

PASSWORD_HINT = "At least 8 characters, with uppercase, lowercase and a digit."

# First value applies in light mode, second in dark mode (CustomTkinter convention).
ADAPTIVE_TEXT_COLOR = ("gray10", "gray90")
ICON_TEXT_COLOR = ADAPTIVE_TEXT_COLOR
HINT_TEXT_COLOR = ("gray40", "gray65")
ERROR_TEXT_COLOR = ("#c0392b", "#ff6347")
SUCCESS_TEXT_COLOR = ("#2e7d32", "#4caf50")

STRENGTH_DISPLAY = {
    "weak": ("Weak", ERROR_TEXT_COLOR),
    "medium": ("Medium", ("#b8860b", "#ffa500")),
    "strong": ("Strong", SUCCESS_TEXT_COLOR),
}


def make_strength_label(master):
    return ctk.CTkLabel(master, text="", font=ctk.CTkFont(size=11))


def update_strength_label(label, password):
    if not password:
        label.configure(text="")
        return

    level = password_strength(password)
    text, color = STRENGTH_DISPLAY[level]
    label.configure(text=f"Password strength: {text}", text_color=color)


class PasswordEntry(ctk.CTkFrame):
    """An entry + Show/Hide toggle button, usable anywhere a plain CTkEntry is."""

    def __init__(self, master, placeholder_text="", width=260, **kwargs):
        super().__init__(master, fg_color="transparent")

        self._visible = False

        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder_text, show="*", width=width - 56, **kwargs)
        self.entry.pack(side="left")

        self.toggle_button = ctk.CTkButton(self, text="Show", width=50, command=self._toggle)
        self.toggle_button.pack(side="left", padx=(6, 0))

    def _toggle(self):
        self._visible = not self._visible
        self.entry.configure(show="" if self._visible else "*")
        self.toggle_button.configure(text="Hide" if self._visible else "Show")

    def get(self):
        return self.entry.get()

    def delete(self, *args):
        self.entry.delete(*args)

    def insert(self, *args):
        self.entry.insert(*args)

    def bind(self, *args, **kwargs):
        self.entry.bind(*args, **kwargs)


class IPAddressEntry(ctk.CTkFrame):
    """Four small octet boxes separated by dots, like the Windows IPv4 field."""

    def __init__(self, master, width=200, **kwargs):
        super().__init__(master, fg_color="transparent")

        self.octets = []
        octet_width = max(30, (width - 3 * 14) // 4)

        for i in range(4):
            entry = ctk.CTkEntry(self, width=octet_width, justify="center", **kwargs)
            entry.pack(side="left")
            entry.bind("<KeyRelease>", lambda event, index=i: self._on_key(index))
            self.octets.append(entry)

            if i < 3:
                ctk.CTkLabel(self, text=".", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=2)

    def _on_key(self, index):
        entry = self.octets[index]
        digits = "".join(c for c in entry.get() if c.isdigit())[:3]

        if digits != entry.get():
            entry.delete(0, "end")
            entry.insert(0, digits)

        if len(digits) >= 3 and index < 3:
            self.octets[index + 1].focus_set()

    def get(self):
        return ".".join(entry.get() for entry in self.octets)

    def delete(self, *_args):
        for entry in self.octets:
            entry.delete(0, "end")

    def insert(self, _index, value):
        parts = (value or "").split(".")

        for i, entry in enumerate(self.octets):
            entry.delete(0, "end")
            if i < len(parts):
                entry.insert(0, parts[i])


class BaseFrame(ctk.CTkFrame):
    """Every screen's widgets live in self.content, kept centered no matter the window size."""

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.place(relx=0.5, rely=0.5, anchor="center")
