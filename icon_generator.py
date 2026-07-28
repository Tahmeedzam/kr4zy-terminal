"""
icon_generator.py

Creates every Kr4zy Terminal logo.

Functions
---------
generate_k_logo(size)
generate_rotating_logo(size, angle)
ensure_ico_file()

The rotating logo is used for the side panel.

The flat logo is used for:
- tray
- taskbar
- window icon
- exe icon
"""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw
import math


# -----------------------------
# Colors
# -----------------------------

BACKGROUND = (17, 24, 39, 255)

BLUE = (59, 130, 246, 255)

LIGHT_BLUE = (120, 180, 255, 255)

WHITE = (240, 245, 255, 255)


# -----------------------------
# Utilities
# -----------------------------

def _rounded(draw, xy, radius, fill):
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def _draw_k(draw, center_x, center_y, scale=1.0, color=WHITE):

    w = 18 * scale

    # vertical
    draw.rounded_rectangle(
        (
            center_x - 38 * scale,
            center_y - 60 * scale,
            center_x - 20 * scale,
            center_y + 60 * scale,
        ),
        radius=8,
        fill=color,
    )

    # upper
    draw.polygon(
        [
            (center_x - 10 * scale, center_y),
            (center_x + 45 * scale, center_y - 60 * scale),
            (center_x + 60 * scale, center_y - 45 * scale),
            (center_x + 5 * scale, center_y + 8 * scale),
        ],
        fill=color,
    )

    # lower
    draw.polygon(
        [
            (center_x - 10 * scale, center_y),
            (center_x + 60 * scale, center_y + 45 * scale),
            (center_x + 45 * scale, center_y + 60 * scale),
            (center_x + 5 * scale, center_y - 8 * scale),
        ],
        fill=color,
    )


# -----------------------------
# Flat Logo
# -----------------------------

def generate_k_logo(size=256):

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    draw = ImageDraw.Draw(img)

    margin = size * 0.08

    _rounded(
        draw,
        (margin, margin, size - margin, size - margin),
        radius=int(size * 0.18),
        fill=BLUE,
    )

    _draw_k(
        draw,
        size / 2,
        size / 2,
        scale=size / 170,
        color=WHITE,
    )

    return img


# -----------------------------
# Rotating Logo
# -----------------------------

def generate_rotating_logo(size=220, angle=0):

    base = generate_k_logo(size)

    angle = math.radians(angle)

    width = abs(math.cos(angle))

    width = max(width, 0.15)

    new_width = int(size * width)

    logo = base.resize(
        (new_width, size),
        Image.Resampling.LANCZOS,
    )

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    x = (size - new_width) // 2

    canvas.paste(logo, (x, 0), logo)

    return canvas


# -----------------------------
# ICO
# -----------------------------

def ensure_ico_file():

    assets = Path("assets")

    assets.mkdir(exist_ok=True)

    path = assets / "icon.ico"

    if path.exists():
        return

    img = generate_k_logo(256)

    img.save(
        path,
        format="ICO",
        sizes=[
            (16, 16),
            (24, 24),
            (32, 32),
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256),
        ],
    )