"""A soft, accent-colored backdrop gradient behind the app's cards.

Regenerated (not just recolored) whenever the window resizes or the user
picks a different accent color, since it's sized to exactly fill the
window. Built with numpy for speed - a naive per-pixel Python loop would be
far too slow to redo on every resize of a large, maximized window.
"""

import customtkinter as ctk
import numpy as np
from PIL import Image


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _light_gradient_array(width, height, accent_hex):
    """A simple top-to-bottom wash: accent tint at the top, fading down into
    a near-white base by the bottom."""
    accent = np.array(_hex_to_rgb(accent_hex), dtype=np.float32)
    base = np.array((250, 250, 252), dtype=np.float32)

    ys = np.linspace(0.0, 1.0, height, dtype=np.float32)
    strength = np.clip(1.0 - ys * 1.15, 0.0, 1.0) * 0.55

    column = base[None, :] * (1 - strength[:, None]) + accent[None, :] * strength[:, None]
    rgb = np.empty((height, width, 3), dtype=np.float32)
    rgb[:, :, :] = column[:, None, :]
    return rgb.astype(np.uint8)


def _dark_gradient_array(width, height, accent_hex):
    """A soft glow band sitting a little below center, fading to near-black
    toward the top, bottom, and sides - a spotlight rather than a flat
    corner wash."""
    accent = np.array(_hex_to_rgb(accent_hex), dtype=np.float32)
    base = np.array((10, 8, 16), dtype=np.float32)

    xs = np.linspace(0.0, 1.0, width, dtype=np.float32)
    ys = np.linspace(0.0, 1.0, height, dtype=np.float32)
    xx, yy = np.meshgrid(xs, ys)

    vertical = np.exp(-((yy - 0.6) ** 2) / (2 * 0.22**2))
    horizontal = np.exp(-((xx - 0.5) ** 2) / (2 * 0.55**2))
    strength = np.clip(vertical * horizontal, 0.0, 1.0) * 0.85
    strength = strength[..., None]

    rgb = base[None, None, :] * (1 - strength) + accent[None, None, :] * strength
    return rgb.astype(np.uint8)


def make_background_image(width, height, accent_light_hex, accent_dark_hex):
    width = max(1, int(width))
    height = max(1, int(height))

    light_image = Image.fromarray(_light_gradient_array(width, height, accent_light_hex), mode="RGB")
    dark_image = Image.fromarray(_dark_gradient_array(width, height, accent_dark_hex), mode="RGB")

    return ctk.CTkImage(light_image=light_image, dark_image=dark_image, size=(width, height))
