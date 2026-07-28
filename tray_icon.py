"""
tray_icon.py
------------
Provides the image pystray displays in the system tray.

Prefers a real assets/icon.ico if the user has added one; otherwise
generates the "K" logo via icon_generator so the tray never looks
broken/missing out of the box.
"""

from PIL import Image

from utils import resource_path
from icon_generator import ensure_ico_file


def get_tray_icon_image():

    ensure_ico_file()

    icon = resource_path("assets/icon.ico")

    return Image.open(icon)