"""The Login screen's left-panel hero image: a stencil photo dimmed under a
dark, accent-tinted scrim so the brand wordmark reads clearly on top of it.
Built once (not regenerated on resize like the old background gradient)
since the login window is now a fixed size.

The wordmark is drawn directly onto this image with PIL rather than laid
out as a separate CTkLabel widget on top of it. CTkLabel's
fg_color="transparent" is a simulated transparency - it just matches
whatever flat color it thinks its parent is, not the actual pixels of a
sibling image widget sitting behind it - so a text label placed over this
photo showed up as a visible gray box instead of blending in. Baking the
text into the photo itself sidesteps that entirely.
"""

import os
import random

import customtkinter as ctk
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.ui.assets import ASSETS_DIR

HERO_IMAGE_PATH = os.path.join(ASSETS_DIR, "laser-cut-stencil.jpg")
LOGO_PATH = os.path.join(ASSETS_DIR, "demeter_logo.png")

# Login's hero panel picks a different photo from this folder each time the
# screen is shown (see LoginFrame.on_show), instead of always the same fixed
# image - drop more images in here to add them to the rotation.
HERO_IMAGE_DIR = os.path.join(ASSETS_DIR, "UI Reference")
_HERO_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


def _random_hero_photo_path():
    """Falls back to the single bundled default photo if HERO_IMAGE_DIR is
    missing or empty (e.g. a packaged build where it wasn't copied)."""
    try:
        candidates = [
            os.path.join(HERO_IMAGE_DIR, name)
            for name in os.listdir(HERO_IMAGE_DIR)
            if name.lower().endswith(_HERO_IMAGE_EXTENSIONS)
        ]
    except OSError:
        candidates = []

    return random.choice(candidates) if candidates else HERO_IMAGE_PATH

_FONTS_DIR = os.path.join(os.path.dirname(ctk.__file__), "assets", "fonts", "Roboto")
_HEADING_FONT_PATH = os.path.join(_FONTS_DIR, "Roboto-Medium.ttf")


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _cover_resize(image, width, height):
    """Resize+crop to exactly fill width x height without distorting the
    photo's aspect ratio (like CSS background-size: cover)."""
    src_w, src_h = image.size
    scale = max(width / src_w, height / src_h)
    new_w, new_h = max(1, round(src_w * scale)), max(1, round(src_h * scale))
    image = image.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - width) // 2
    top = (new_h - height) // 2
    return image.crop((left, top, left + width, top + height))


def make_login_hero_image(width, height, accent_dark_hex):
    width = max(1, int(width))
    height = max(1, int(height))

    photo = Image.open(_random_hero_photo_path()).convert("RGB")
    photo = _cover_resize(photo, width, height)
    photo_arr = np.asarray(photo, dtype=np.float32)

    base = np.array((10, 12, 20), dtype=np.float32)
    accent = np.array(_hex_to_rgb(accent_dark_hex), dtype=np.float32)

    # A soft accent glow anchored top-right ties the panel back to the app's
    # own accent color instead of a flat black scrim - kept away from the
    # middle, where the wordmark sits, so it never competes with the white
    # text for contrast.
    xs = np.linspace(0.0, 1.0, width, dtype=np.float32)
    ys = np.linspace(0.0, 1.0, height, dtype=np.float32)
    xx, yy = np.meshgrid(xs, ys)
    distance = np.sqrt((xx - 0.88) ** 2 + (yy - 0.1) ** 2)
    glow = np.clip(1.0 - distance * 1.1, 0.0, 1.0) ** 2
    glow = glow[..., None]

    scrim = base[None, None, :] * (1 - glow * 0.3) + accent[None, None, :] * (glow * 0.3)

    # Scrim over the photo, but not so opaque that the photo itself
    # disappears - just enough that white text on top stays legible.
    scrim_strength = 0.6
    rgb = photo_arr * (1 - scrim_strength) + scrim * scrim_strength
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)

    hero_image = Image.fromarray(rgb, mode="RGB")
    _draw_logo(hero_image, width, height)
    _draw_wordmark(hero_image, width, height)
    return ctk.CTkImage(light_image=hero_image, dark_image=hero_image, size=(width, height))


def _draw_logo(image, width, height, logo_height=34):
    """Pastes the Demeter mark as a white silhouette directly onto the hero
    photo - like the wordmark, this needs true alpha compositing (PIL's own
    paste with the silhouette's own alpha as the mask), not a CTkLabel
    overlay, since CTk's fg_color="transparent" just resolves to a flat
    ancestor color and shows up as a visible box against a busy photo. A
    white silhouette (rather than the mark's own colors) is what actually
    stays legible against this dark, busy photo - the original's black text
    all but disappeared here."""
    # Height fractions, not fixed pixel offsets - stays proportionally
    # placed whether this is the default 560px-tall panel or a much taller
    # maximized one.
    top_margin = max(24, round(height * 0.06))
    left_margin = max(24, round(width * 0.07))

    original = Image.open(LOGO_PATH).convert("L")
    logo_width = max(1, round(original.width * (logo_height / original.height)))
    original = original.resize((logo_width, logo_height), Image.LANCZOS)

    # Dark ink -> opaque white; light background -> transparent, same
    # darkness-based mask assets.py uses for the adaptive-mode logo.
    alpha = original.point(lambda luminance: 255 - luminance)
    silhouette = Image.new("RGBA", original.size, (255, 255, 255, 255))
    silhouette.putalpha(alpha)

    image.paste(silhouette, (left_margin, top_margin), silhouette)


def _draw_wordmark(image, width, height):
    draw = ImageDraw.Draw(image)
    center_x = width / 2

    heading_font = ImageFont.truetype(_HEADING_FONT_PATH, 34)
    draw.multiline_text(
        (center_x, height * 0.5),
        "STENCIL\nINSPECTION",
        font=heading_font,
        fill=(255, 255, 255, 255),
        anchor="mm",
        align="center",
        spacing=6,
    )
