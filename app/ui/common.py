import customtkinter as ctk

from app.services.password_policy import password_strength
from app.ui.icons import eye_icon

PASSWORD_HINT = "At least 8 characters, with uppercase, lowercase and a digit."

# First value applies in light mode, second in dark mode (CustomTkinter convention).
ADAPTIVE_TEXT_COLOR = ("gray10", "gray90")
ICON_TEXT_COLOR = ADAPTIVE_TEXT_COLOR
HINT_TEXT_COLOR = ("gray40", "gray65")
ERROR_TEXT_COLOR = ("#c0392b", "#ff6347")
SUCCESS_TEXT_COLOR = ("#2e7d32", "#4caf50")

# Shared "Berry"-style visual language: an accent color plus elevated
# rounded cards, applied consistently instead of the flat/plain default
# look. Used across screens for primary buttons, section accents, and (via
# BaseFrame below) every simple screen's card container.
#
# The accent is user-selectable (Settings popup "PRESET COLOR" swatches),
# so it's kept as mutable state read through primary_color()/
# primary_hover_color() at *widget-creation* time rather than baked in as
# fixed constants - changing it and rebuilding the UI (App._build_ui)
# picks up the new color everywhere these are called from.
ACCENT_PRESETS = {
    "Indigo": {"base": ("#5B4FE0", "#8477F0"), "hover": ("#4A3FCC", "#6C5FE0")},
    "Blue": {"base": ("#1F6AA5", "#3B8ED0"), "hover": ("#175680", "#2F7DB8")},
    "Green": {"base": ("#2FA572", "#3FC98A"), "hover": ("#24855C", "#33AD75")},
    "Rose": {"base": ("#D6336C", "#F06595"), "hover": ("#B02352", "#D9457D")},
    "Amber": {"base": ("#C77B0A", "#E8A33D"), "hover": ("#A6650A", "#CC8F2E")},
}

_current_accent = "Indigo"

CARD_COLOR = ("white", "gray14")
CARD_BORDER_COLOR = ("gray87", "gray24")


def set_accent(name):
    global _current_accent
    if name in ACCENT_PRESETS:
        _current_accent = name


def get_accent_name():
    return _current_accent


def accent_names():
    return list(ACCENT_PRESETS.keys())


def accent_swatch_color(name):
    """The light-mode base color, for drawing a preset swatch chip."""
    return ACCENT_PRESETS[name]["base"][0]


def primary_color():
    return ACCENT_PRESETS[_current_accent]["base"]


def primary_hover_color():
    return ACCENT_PRESETS[_current_accent]["hover"]


def primary_button(master, text, command, width=260, **kwargs):
    """The one emphasized action on a screen (Login, Continue, Save, ...)."""
    return ctk.CTkButton(
        master,
        text=text,
        width=width,
        corner_radius=10,
        fg_color=primary_color(),
        hover_color=primary_hover_color(),
        font=ctk.CTkFont(size=13, weight="bold"),
        command=command,
        **kwargs,
    )


def secondary_button(master, text, command, width=260, **kwargs):
    """A lower-emphasis action - outlined instead of filled."""
    return ctk.CTkButton(
        master,
        text=text,
        width=width,
        corner_radius=10,
        fg_color="transparent",
        border_width=1,
        border_color=CARD_BORDER_COLOR,
        text_color=ADAPTIVE_TEXT_COLOR,
        hover_color=("gray92", "gray20"),
        command=command,
        **kwargs,
    )


def link_button(master, text, command, width=260, font=None, **kwargs):
    """A minimal text-link action (no fill, no border) - for tertiary
    actions like "Forgot password?" or "Create an account", so a screen
    isn't just a stack of boxy buttons."""
    return ctk.CTkButton(
        master,
        text=text,
        width=width,
        corner_radius=8,
        fg_color="transparent",
        hover_color=("gray93", "gray19"),
        text_color=primary_color(),
        font=font or ctk.CTkFont(size=12, weight="bold"),
        command=command,
        **kwargs,
    )


def styled_option_menu(master, **kwargs):
    """A dropdown using the app's own accent color instead of CTk's default
    blue theme, so it doesn't clash with primary buttons and headings
    elsewhere on the same screen."""
    return ctk.CTkOptionMenu(
        master,
        fg_color=primary_color(),
        button_color=primary_hover_color(),
        button_hover_color=primary_hover_color(),
        dropdown_fg_color=CARD_COLOR,
        dropdown_hover_color=("gray85", "gray25"),
        dropdown_text_color=ADAPTIVE_TEXT_COLOR,
        text_color="white",
        **kwargs,
    )


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


# Lazily built and cached on first use (after a Tk root exists), then
# reused by every PasswordEntry instance rather than redrawing per field.
_EYE_ICON_CACHE = {}


def _get_eye_icon(slashed):
    if slashed not in _EYE_ICON_CACHE:
        _EYE_ICON_CACHE[slashed] = eye_icon(size=18, slashed=slashed)
    return _EYE_ICON_CACHE[slashed]


class PasswordEntry(ctk.CTkFrame):
    """An entry with an eye-icon show/hide toggle sitting inside its right
    edge (not a separate button beside it), usable anywhere a plain
    CTkEntry is. Same overall width as a plain CTkEntry of the same width,
    so username/password fields on a form line up exactly."""

    def __init__(self, master, placeholder_text="", width=260, height=28, **kwargs):
        super().__init__(master, fg_color="transparent", width=width, height=height)
        self.pack_propagate(False)

        self._visible = False

        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder_text, show="*", height=height, **kwargs)
        self.entry.place(x=0, y=0, relwidth=1, relheight=1)

        # A plain CTkButton with an image still applies its own internal
        # padding around the image, so its rendered size doesn't match the
        # width/height passed in - it came out visibly taller than the
        # entry itself. A fixed-size frame (pack_propagate off) with a
        # centered label inside is guaranteed to be exactly this size.
        #
        # fg_color="transparent" here would resolve to *this frame's own*
        # parent background (the surrounding card), not the entry sitting
        # underneath it, since they're just two separate siblings placed on
        # top of each other rather than truly nested - that mismatch is
        # exactly what showed up as a visible seam/box around the icon.
        # Matching the entry's own fill color directly is what actually
        # makes it blend in as part of the field.
        entry_bg = self.entry.cget("fg_color")
        toggle_size = max(18, height - 12)
        self.toggle_button = ctk.CTkFrame(
            self, width=toggle_size, height=toggle_size, corner_radius=6, fg_color=entry_bg
        )
        self.toggle_button.pack_propagate(False)
        self.toggle_button.place(relx=1.0, rely=0.5, anchor="e", x=-10)

        self.toggle_icon = ctk.CTkLabel(self.toggle_button, text="", image=_get_eye_icon(False))
        self.toggle_icon.pack(expand=True, fill="both")

        self.toggle_button.bind("<Button-1>", lambda _e: self._toggle())
        self.toggle_icon.bind("<Button-1>", lambda _e: self._toggle())

    def _toggle(self):
        self._visible = not self._visible
        self.entry.configure(show="" if self._visible else "*")
        self.toggle_icon.configure(image=_get_eye_icon(self._visible))

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
    """Every screen's widgets live in self.content, kept centered no matter the window
    size. self.content sits inside self.card, a rounded/bordered "elevated" panel that
    gives every simple screen a consistent card look for free - screens that build
    directly on self instead (SettingsFrame, MainFrame, ActuatorDebugFrame) opt out of
    this since they're dense, full-page layouts with their own section styling."""

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app

        self.card = ctk.CTkFrame(
            self, fg_color=CARD_COLOR, corner_radius=18, border_width=1, border_color=CARD_BORDER_COLOR
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")

        self.content = ctk.CTkFrame(self.card, fg_color="transparent")
        self.content.pack(padx=32, pady=28)
