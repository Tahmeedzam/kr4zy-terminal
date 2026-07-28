"""
sidepanel.py
------------
A vertical side panel showing a "K" that draws itself in from the top,
holds, then erases itself from the top - looping slowly and calmly.

Design decision:
    Animating a live vector draw every frame would be expensive and
    janky. Instead we precompute every frame of the reveal/erase cycle
    ONCE at startup (see icon_generator_k_animation.py, which clips
    literal line segments to a moving Y-band), convert them to
    PhotoImage, and then just flip between pre-rendered frames on a
    timer via `self.after()`. Same sprite-animation approach as before,
    just with a different frame generator underneath.

    The animation loop uses `after()` (Tkinter's own scheduler) rather
    than a background thread, since it only touches a Tkinter widget
    and must run on the main thread anyway - no threading complexity
    needed here, unlike launcher.py or windows_integration.py.
"""

from __future__ import annotations

import customtkinter as ctk
from PIL import Image, ImageTk

from icon_generator_k_animation import generate_k_animation_frames
from config import get_config

# Timing knobs for the reveal/erase cycle. Frame *counts* control how
# many discrete steps the draw/erase takes (more = smoother sweep),
# while the interval below controls overall pacing. Keep this slow and
# deliberate - this isn't a spinner, it's a "the machine is thinking"
# beat.
_APPEAR_FRAMES = 26
_HOLD_FRAMES = 14
_DISAPPEAR_FRAMES = 26
_FRAME_INTERVAL_MS = 55  # slow, paced - raise this further to slow it more


class SidePanel(ctk.CTkFrame):
    """A fixed-width vertical panel containing a forming/erasing K."""

    def __init__(self, master, width: int = 140) -> None:
        super().__init__(master, width=width, fg_color="transparent")
        self.pack_propagate(False)  # keep fixed width regardless of content

        self.config = get_config()
        self._frames: list[ImageTk.PhotoImage] = []
        self._frame_index = 0
        self._running = False
        self._after_id: str | None = None

        self._logo_label = ctk.CTkLabel(self, text="")
        self._logo_label.pack(expand=True)

        self._build_frames()
        self._show_frame(0)

    def _build_frames(self) -> None:
        """Precompute every frame of the reveal/erase cycle once, up front."""
        pil_frames = generate_k_animation_frames(
            size=110,
            appear_frames=_APPEAR_FRAMES,
            hold_frames=_HOLD_FRAMES,
            disappear_frames=_DISAPPEAR_FRAMES,
        )

        # Composite onto the panel's actual background so we don't get
        # a visible box around the glow. Falls back to a plain dark
        # background if the theme lookup fails.
        bg_color = self.config.get("theme.panel_bg_color", default="#0d0d0e")
        bg_rgb = self.winfo_rgb(bg_color)
        bg = tuple(c // 256 for c in bg_rgb)

        for frame in pil_frames:
            canvas = Image.new("RGB", frame.size, bg)
            canvas.paste(frame, (0, 0), frame)
            self._frames.append(ImageTk.PhotoImage(canvas))

    def _show_frame(self, index: int) -> None:
        self._logo_label.configure(image=self._frames[index])

    def start(self) -> None:
        """Begin the reveal/erase animation loop."""
        if self._running:
            return
        self._running = True
        self._tick()

    def stop(self) -> None:
        """Stop the animation loop (e.g. window is hidden to tray)."""
        self._running = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None

    def _tick(self) -> None:
        if not self._running:
            return
        self._frame_index = (self._frame_index + 1) % len(self._frames)
        self._show_frame(self._frame_index)
        self._after_id = self.after(_FRAME_INTERVAL_MS, self._tick)