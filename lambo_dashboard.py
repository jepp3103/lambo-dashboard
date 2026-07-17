#!/usr/bin/env python3
"""
Lamborghini dashboard for the Lian Li O11D EVO RGB Lamborghini Edition rear panel,
streamed live from a Linux host instead of playing pre-baked video off the panel.

Install:  pip install pyserial pillow psutil numpy

This does NOT touch the panel's onboard storage. It renders each frame on the
host and pushes it over serial with DisplayPILImage(), the same primitive the
project's own basic system monitor uses.

This code is open source and contains none of Lamborghini/Lian Li's original
assets. It looks for YOUR copy of the background art + fonts (see README for
how to extract your own) in, in order of priority:
  1. $LAMBO_DASHBOARD_RES environment variable
  2. ~/.config/lambo-dashboard/res/
  3. a "res/" folder next to this script (convenient for local development)

`library/` is a small vendored subset of
https://github.com/mathoudebine/turing-smart-screen-python (GPL-3.0-or-later),
just the pieces needed to talk to the panel -- no external clone required.
"""

import os
import sys
import time
import psutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from serial.tools.list_ports import comports

sys.path.insert(0, str(Path(__file__).resolve().parent))

from library.lcd.lcd_comm import Orientation           # noqa: E402
from library.lcd.lcd_comm_rev_c import LcdCommRevC     # noqa: E402

# ============================== CONFIGURATION ==============================

PANEL_SERIAL = "CT50INCH"  # identifies this exact panel model, used for auto-detect
DISPLAY_W, DISPLAY_H = 480, 800   # native panel orientation (portrait)
ORIENTATION = Orientation.LANDSCAPE  # dashboard art is 800x480, so rotate to landscape
COLOR_VARIANT = os.environ.get("LAMBO_DASHBOARD_COLOR", "c1")  # c1..c8
REFRESH_SECONDS = 1.0      # how often to redraw+push a frame (bandwidth vs. liveliness)

GOLD = (240, 190, 40)
WHITE = (230, 230, 230)
BG_FILL = (8, 9, 6)  # approx. gauge-interior black, used to paint over old digits

# Text regions (x0, y0, x1, y1) in 800x480 source-art space.
REGIONS = {
    "left_big":    (90, 165, 300, 260),
    "left_small":  (110, 110, 280, 155),
    "left_unit":   (130, 260, 260, 300),
    "right_big":   (500, 165, 710, 260),
    "right_small": (530, 110, 690, 155),
    "right_unit":  (570, 260, 700, 300),
}

# ============================================================================


def find_res_dir():
    """Look for assets in order: explicit override, user config dir, then
    whatever's bundled into this script/binary (via PyInstaller --add-data
    when frozen, or the local res/ folder when run from source)."""
    if getattr(sys, "frozen", False):
        bundled_dir = Path(sys._MEIPASS) / "res"    # noqa: SLF001
    else:
        bundled_dir = Path(__file__).resolve().parent / "res"

    candidates = []
    if os.environ.get("LAMBO_DASHBOARD_RES"):
        candidates.append(Path(os.environ["LAMBO_DASHBOARD_RES"]))
    candidates.append(Path.home() / ".config" / "lambo-dashboard" / "res")
    candidates.append(bundled_dir)

    for c in candidates:
        fonts_ok = (c / "fonts" / "Numeri_Lamborghini_version_2.ttf").exists()
        bg_ok = (c / "backgrounds" / "cpu_c1.png").exists()
        if fonts_ok and bg_ok:
            return c

    print("Could not find dashboard assets (fonts + background art).")
    print("They should be bundled with this project in res/ -- checked:")
    for c in candidates:
        print(f"  - {c}")
    print("If you're running from source, make sure res/fonts and")
    print("res/backgrounds are present next to lambo_dashboard.py.")
    sys.exit(1)


def find_panel_port(timeout=15):
    """Scan connected serial devices for the panel's known serial number.
    Makes the script portable across machines/reboots instead of a fixed path."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for port in comports():
            if port.serial_number and PANEL_SERIAL in port.serial_number:
                return port.device
        time.sleep(1)
    return None


def load_fonts(res_dir):
    return {
        "big": ImageFont.truetype(str(res_dir / "fonts" / "Numeri_Lamborghini_version_2.ttf"), 90),
        "small": ImageFont.truetype(str(res_dir / "fonts" / "Lamborghini_CCY_V10.ttf"), 28),
    }


def draw_field(draw, box, text, font, fill):
    draw.rectangle(box, fill=BG_FILL)
    cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
    draw.text((cx, cy), text, font=font, fill=fill, anchor="mm")


def read_cpu_stats():
    load = psutil.cpu_percent(interval=None)
    freq = psutil.cpu_freq()
    ghz = (freq.current / 1000.0) if freq else 0.0
    temp_c = None
    temps = psutil.sensors_temperatures() if hasattr(psutil, "sensors_temperatures") else {}
    for key in ("coretemp", "k10temp", "cpu_thermal"):
        if key in temps and temps[key]:
            temp_c = temps[key][0].current
            break
    if temp_c is None:
        temp_c = 0.0
    return temp_c, ghz, load


def c_to_f(c):
    return c * 9 / 5 + 32


def build_frame(res_dir, fonts, variant):
    bg_path = res_dir / "backgrounds" / f"cpu_{variant}.png"
    frame = Image.open(bg_path).convert("RGB")
    draw = ImageDraw.Draw(frame)

    temp_c, ghz, load = read_cpu_stats()

    draw_field(draw, REGIONS["left_big"], f"{temp_c:.0f}", fonts["big"], GOLD)
    draw_field(draw, REGIONS["left_small"], f"{c_to_f(temp_c):.0f} °F", fonts["small"], WHITE)
    draw_field(draw, REGIONS["left_unit"], "°C", fonts["small"], WHITE)

    draw_field(draw, REGIONS["right_big"], f"{ghz:.2f}", fonts["big"], GOLD)
    draw_field(draw, REGIONS["right_small"], f"{load:.0f} %", fonts["small"], WHITE)
    draw_field(draw, REGIONS["right_unit"], "GHz", fonts["small"], WHITE)

    return frame


def main():
    res_dir = find_res_dir()
    print(f"Using assets from: {res_dir}")

    print("Looking for panel...")
    port = find_panel_port()
    if not port:
        print(f"Could not find a serial device with serial number containing "
              f"'{PANEL_SERIAL}'. Is the panel connected?")
        sys.exit(1)
    print(f"Found panel on {port}")

    lcd = LcdCommRevC(com_port=port, display_width=DISPLAY_W, display_height=DISPLAY_H)
    lcd.Reset()
    lcd.InitializeComm()
    lcd.SetOrientation(ORIENTATION)
    lcd.SetBrightness(80)

    fonts = load_fonts(res_dir)

    try:
        while True:
            frame = build_frame(res_dir, fonts, COLOR_VARIANT)
            lcd.DisplayPILImage(frame)
            time.sleep(REFRESH_SECONDS)
    except KeyboardInterrupt:
        pass
    finally:
        lcd.closeSerial()


if __name__ == "__main__":
    main()
