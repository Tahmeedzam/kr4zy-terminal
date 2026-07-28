"""
icon_generator_k_animation.py
------------------------------
Wireframe-style "K" reveal/erase animation, in the spirit of vector
plotter art (like the cyan wireframe spiral you showed me) rather than
a flat rotating logo.

Design decision:
    Instead of rotating a bitmap, we define the K as literal line
    segments (a vertical bar + two diagonals), then clip each segment
    to a moving Y-band. Sliding that band top->bottom "draws" the K in;
    sliding it again top->bottom "erases" it. This keeps the coding/
    plotter aesthetic (visible strokes + nodes) instead of looking like
    a logo spinning in place.

    All frames are precomputed once at startup, same sprite-animation
    approach as the rest of sidepanel.py - no per-frame drawing cost
    while the app is running.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter

# Muted yellow - saturated enough to read clearly against a dark
# panel, but pulled back from a raw/neon "255,255,0" so it doesn't glare.
_YELLOW = (222, 196, 70)

Point = tuple[float, float]
Segment = tuple[Point, Point]


def _k_segments(size: float) -> list[Segment]:
    """Define the K as three strokes inside a size x size box."""
    pad = size * 0.20
    top = pad
    bottom = size - pad
    mid = size / 2
    left = pad
    right = size - pad * 0.55

    return [
        ((left, top), (left, bottom)),      # vertical bar
        ((left, mid), (right, top)),        # upper diagonal
        ((left, mid), (right, bottom)),     # lower diagonal
    ]


def _clip_segment_by_y(
    p1: Point, p2: Point, y_min: float, y_max: float
) -> tuple[Point, Point] | None:
    """
    Analytically clip the straight line p1->p2 to the Y band
    [y_min, y_max] and return just its two resulting endpoints.

    This is deliberately NOT sampled into many intermediate points -
    drawing a thick line through dozens of sampled points introduces
    a visible "bend" at each joint once stroke_width goes up. Two
    endpoints -> one true straight segment -> no kinks at any width.
    """
    (x1, y1), (x2, y2) = p1, p2
    if y1 == y2:
        # horizontal segment (not used by the K, but handle it safely)
        if y_min <= y1 <= y_max:
            return (x1, y1), (x2, y2)
        return None

    # t=0 at p1, t=1 at p2; find the t-range where y is in band
    t_at_ymin = (y_min - y1) / (y2 - y1)
    t_at_ymax = (y_max - y1) / (y2 - y1)
    t_lo, t_hi = sorted((t_at_ymin, t_at_ymax))
    t_lo = max(0.0, t_lo)
    t_hi = min(1.0, t_hi)

    if t_lo >= t_hi:
        return None

    def _point_at(t: float) -> Point:
        return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)

    return _point_at(t_lo), _point_at(t_hi)


def generate_k_frame(
    size: int,
    progress: float,
    mode: str,
    glow: bool = True,
    stroke_width: int = 8,
) -> Image.Image:
    """
    Render a single frame of the K reveal/erase animation.

    progress: 0.0 -> 1.0
    mode: "appear"    -> K is drawn top-down as progress increases
          "disappear" -> K is erased top-down as progress increases
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if mode == "appear":
        y_min, y_max = 0.0, size * progress
    elif mode == "disappear":
        y_min, y_max = size * progress, float(size)
    else:
        raise ValueError(f"unknown mode: {mode!r}")

    r = stroke_width / 2
    for p1, p2 in _k_segments(size):
        clipped = _clip_segment_by_y(p1, p2, y_min, y_max)
        if not clipped:
            continue
        a, b = clipped
        draw.line([a, b], fill=_YELLOW + (255,), width=stroke_width)
        # round caps at both ends so a thick straight line doesn't
        # look chopped-off square at each clip boundary
        for x, y in (a, b):
            draw.ellipse([x - r, y - r, x + r, y + r], fill=_YELLOW + (255,))

    if not glow:
        return img

    glow_img = img.filter(ImageFilter.GaussianBlur(4))
    return Image.alpha_composite(glow_img, img)


def generate_k_animation_frames(
    size: int = 110,
    appear_frames: int = 26,
    hold_frames: int = 12,
    disappear_frames: int = 26,
) -> list[Image.Image]:
    """
    Build the full loop as a flat list of PIL frames:
        appear (top -> bottom) -> hold (fully formed) -> disappear (top -> bottom)
    Loop it and you get: form -> pause -> erase -> (repeat).
    """
    frames: list[Image.Image] = []

    for i in range(appear_frames):
        progress = (i + 1) / appear_frames
        frames.append(generate_k_frame(size, progress, "appear"))

    for _ in range(hold_frames):
        frames.append(generate_k_frame(size, 1.0, "appear"))

    for i in range(disappear_frames):
        progress = (i + 1) / disappear_frames
        frames.append(generate_k_frame(size, progress, "disappear"))

    return frames


if __name__ == "__main__":
    # Quick visual sanity check: dump a handful of frames to disk.
    frames = generate_k_animation_frames(size=220)
    for idx in (0, 10, 25, 38, 45, 60):
        bg = Image.new("RGB", frames[idx].size, (10, 10, 14))
        bg.paste(frames[idx], (0, 0), frames[idx])
        bg.save(f"/tmp/k_frame_{idx}.png")
    print(f"generated {len(frames)} frames total; previews in /tmp/k_frame_*.png")