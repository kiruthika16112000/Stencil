"""Small icons drawn with PIL instead of Unicode glyphs.

Font-rendered symbols (gear "⚙", eye "👁", ...) look inconsistent across
Windows font/DPI combinations - a gear can render like a flower, an eye
icon can sit off-center in its button. Drawing simple vector-style shapes
ourselves (supersampled then downscaled for anti-aliasing) is slower to
write but renders identically everywhere.
"""

import math

import customtkinter as ctk
from PIL import Image, ImageDraw

SUPERSAMPLE = 4


def _canvas(size):
    big = size * SUPERSAMPLE
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    return image, ImageDraw.Draw(image), big


def _finish(image, size):
    return image.resize((size, size), Image.LANCZOS)


def _tooth_polygon(cx, cy, angle, r_in, r_out, half_w):
    dx, dy = math.cos(angle), math.sin(angle)
    px, py = -dy, dx
    return [
        (cx + dx * r_in - px * half_w, cy + dy * r_in - py * half_w),
        (cx + dx * r_in + px * half_w, cy + dy * r_in + py * half_w),
        (cx + dx * r_out + px * half_w, cy + dy * r_out + py * half_w),
        (cx + dx * r_out - px * half_w, cy + dy * r_out - py * half_w),
    ]


def _draw_gear(draw, big, color):
    cx = cy = big / 2
    r_in = big * 0.24
    r_out = big * 0.34
    half_w = big * 0.055
    hole_r = big * 0.11
    teeth = 8

    draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=color)
    for i in range(teeth):
        angle = (2 * math.pi / teeth) * i
        draw.polygon(_tooth_polygon(cx, cy, angle, r_in * 0.9, r_out, half_w), fill=color)

    draw.ellipse([cx - hole_r, cy - hole_r, cx + hole_r, cy + hole_r], fill=(0, 0, 0, 0))


def _draw_person(draw, big, color, offset_x=0.0, scale=1.0):
    cx, cy = big / 2 + offset_x, big / 2
    head_r = big * 0.15 * scale
    head_cy = cy - big * 0.22 * scale
    draw.ellipse(
        [cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r], fill=color
    )

    shoulder_w = big * 0.22 * scale
    shoulder_top = cy + big * 0.14 * scale
    shoulder_bottom = cy + big * 0.34 * scale
    draw.pieslice(
        [cx - shoulder_w, shoulder_top - shoulder_w, cx + shoulder_w, shoulder_top + shoulder_w],
        start=180,
        end=360,
        fill=color,
    )
    draw.rectangle([cx - shoulder_w, shoulder_top, cx + shoulder_w, shoulder_bottom], fill=color)


def _draw_person_plus(draw, big, color):
    """A smaller person (shifted left) with a "+" badge - for "create a new
    account", distinct from the plain person_icon used for "manage my
    existing account"."""
    _draw_person(draw, big, color, offset_x=-big * 0.12, scale=0.85)

    badge_cx, badge_cy = big * 0.72, big * 0.68
    arm = big * 0.11
    width = max(1, int(big * 0.07))
    draw.line([badge_cx - arm, badge_cy, badge_cx + arm, badge_cy], fill=color, width=width)
    draw.line([badge_cx, badge_cy - arm, badge_cx, badge_cy + arm], fill=color, width=width)


def _draw_key(draw, big, color):
    cx, cy = big * 0.38, big * 0.38
    r_out = big * 0.16
    r_in = big * 0.08
    draw.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], outline=color, width=max(1, int(big * 0.06)))
    draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=color)

    shaft_end = big * 0.86
    width = max(1, int(big * 0.07))
    dx = dy = (shaft_end - cx) / (2**0.5)
    ex, ey = cx + dx, cy + dy
    draw.line([cx + r_out * 0.7, cy + r_out * 0.7, ex, ey], fill=color, width=width)

    tooth_dx, tooth_dy = dy, -dx
    tooth_len = big * 0.09
    tx, ty = ex - dx * 0.28, ey - dy * 0.28
    draw.line(
        [tx, ty, tx + tooth_dx / (2**0.5) * tooth_len, ty + tooth_dy / (2**0.5) * tooth_len],
        fill=color,
        width=width,
    )


def _draw_lock(draw, big, color):
    # A narrower, taller body (not a flat wide bar) and a shackle radius
    # that actually matches its width - the previous proportions (a body
    # nearly twice as wide as tall) read as a squashed blob at icon sizes.
    cx, cy = big / 2, big / 2 + big * 0.08
    body_half_w, body_h = big * 0.17, big * 0.27
    body_top = cy - body_h * 0.5
    line_width = max(1, int(big * 0.09))

    # A proper circle bbox (equal on all sides), not a stretched oval - its
    # top half ("∩") sits with both ends landing right at the body's top
    # edge, so the shackle actually reads as attached to the body.
    shackle_r = big * 0.145
    draw.arc(
        [cx - shackle_r, body_top - shackle_r, cx + shackle_r, body_top + shackle_r],
        start=180,
        end=360,
        fill=color,
        width=line_width,
    )

    draw.rounded_rectangle(
        [cx - body_half_w, body_top, cx + body_half_w, body_top + body_h],
        radius=big * 0.04,
        fill=color,
    )

    keyhole_r = big * 0.04
    keyhole_cy = body_top + body_h * 0.4
    draw.ellipse(
        [cx - keyhole_r, keyhole_cy - keyhole_r, cx + keyhole_r, keyhole_cy + keyhole_r],
        fill=(0, 0, 0, 0),
    )
    draw.rectangle(
        [cx - keyhole_r * 0.45, keyhole_cy, cx + keyhole_r * 0.45, body_top + body_h * 0.8],
        fill=(0, 0, 0, 0),
    )


def _draw_eye(draw, big, color, slashed):
    cx, cy = big / 2, big / 2
    w, h = big * 0.4, big * 0.22
    outline_width = max(1, int(big * 0.045))

    draw.ellipse([cx - w, cy - h, cx + w, cy + h], outline=color, width=outline_width)

    pupil_r = big * 0.1
    draw.ellipse([cx - pupil_r, cy - pupil_r, cx + pupil_r, cy + pupil_r], fill=color)

    if slashed:
        line_width = max(1, int(big * 0.05))
        draw.line(
            [cx - w * 1.05, cy - h * 1.5, cx + w * 1.05, cy + h * 1.5], fill=color, width=line_width
        )


def _dual_image(draw_fn, size, light_color, dark_color):
    light_image, light_draw, big = _canvas(size)
    draw_fn(light_draw, big, light_color)

    dark_image, dark_draw, _ = _canvas(size)
    draw_fn(dark_draw, big, dark_color)

    return ctk.CTkImage(
        light_image=_finish(light_image, size), dark_image=_finish(dark_image, size), size=(size, size)
    )


def gear_icon(size=20, light_color=(40, 40, 40, 255), dark_color=(225, 225, 225, 255)):
    return _dual_image(_draw_gear, size, light_color, dark_color)


def person_icon(size=20, light_color=(40, 40, 40, 255), dark_color=(225, 225, 225, 255)):
    return _dual_image(_draw_person, size, light_color, dark_color)


def person_plus_icon(size=20, light_color=(40, 40, 40, 255), dark_color=(225, 225, 225, 255)):
    return _dual_image(_draw_person_plus, size, light_color, dark_color)


def key_icon(size=20, light_color=(40, 40, 40, 255), dark_color=(225, 225, 225, 255)):
    return _dual_image(_draw_key, size, light_color, dark_color)


def lock_icon(size=20, light_color=(40, 40, 40, 255), dark_color=(225, 225, 225, 255)):
    return _dual_image(_draw_lock, size, light_color, dark_color)


def eye_icon(size=18, slashed=False, light_color=(120, 120, 120, 255), dark_color=(150, 150, 150, 255)):
    return _dual_image(lambda d, b, c: _draw_eye(d, b, c, slashed), size, light_color, dark_color)
