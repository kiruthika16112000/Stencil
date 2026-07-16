import os
import sys

import customtkinter as ctk
from PIL import Image

if getattr(sys, "frozen", False):
    # PyInstaller onefile: bundled data files are extracted to _MEIPASS at
    # launch (not next to the exe, which is reserved for persistent user data).
    _BUNDLE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    _BUNDLE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ASSETS_DIR = os.path.join(_BUNDLE_DIR, "data")

# Matches ADAPTIVE_TEXT_COLOR in app.ui.common ("gray10", "gray90").
LOGO_DARK_MODE_COLOR = (229, 229, 229)


def _alpha_from_darkness(image):
    """Derive an alpha mask from how dark each pixel is - dark ink becomes
    opaque, a white/light background becomes transparent."""
    return image.convert("L").point(lambda luminance: 255 - luminance)


def _cutout(image):
    """Keep the original colors but drop the background: transparent where
    the source was light, fully opaque (in its original color) where dark."""
    result = image.convert("RGBA")
    result.putalpha(_alpha_from_darkness(image))
    return result


def _silhouette(image, rgb):
    """Recolor every pixel to a solid rgb, using how dark the original pixel
    was as the new alpha - so black ink becomes opaque and a white/light
    background becomes transparent, regardless of the source's own colors."""
    solid = Image.new("RGB", image.size, rgb).convert("RGBA")
    solid.putalpha(_alpha_from_darkness(image))
    return solid


def load_fixed_logo(filename, height=28, rgb=(255, 255, 255)):
    """Like load_adaptive_logo, but always renders as a solid-color
    silhouette regardless of the app's light/dark appearance mode - for a
    panel whose own background doesn't follow that mode (the Login screen's
    always-dark hero panel)."""
    path = os.path.join(ASSETS_DIR, filename)
    original = Image.open(path).convert("RGB")

    width = max(1, round(original.width * (height / original.height)))
    original = original.resize((width, height), Image.LANCZOS)

    silhouette = _silhouette(original, rgb)
    return ctk.CTkImage(light_image=silhouette, dark_image=silhouette, size=(width, height))


def load_adaptive_logo(filename, height=28):
    """Loads a logo file as a CTkImage with the background removed: the
    original full-color artwork (background dropped) in light mode, and a
    light-gray silhouette (background dropped) in dark mode."""
    path = os.path.join(ASSETS_DIR, filename)
    original = Image.open(path).convert("RGB")

    width = max(1, round(original.width * (height / original.height)))
    original = original.resize((width, height), Image.LANCZOS)

    light_mode_version = _cutout(original)
    dark_mode_version = _silhouette(original, LOGO_DARK_MODE_COLOR)

    return ctk.CTkImage(light_image=light_mode_version, dark_image=dark_mode_version, size=(width, height))
