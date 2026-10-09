#!/usr/bin/env python3
"""Dual-date waybar tooltip (Jalali + Gregorian), no month grids.

Outputs JSON for a waybar `custom/jalali` module:
  - "text":     HH:MM, or the Persian date (Persian digits) when toggled
  - "tooltip":  Pango markup — today's date in both calendars, two
                centered rows

Usage (handy while configuring):
  python3 jalali.py            # today
  python3 jalali.py 2026 9 17  # explicit Gregorian date
"""

import json
import os
import sys
from datetime import date, datetime

MODE_FILE = os.path.join(
    os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "waybar-jalali-mode"
)

MONTHS_FA = [
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
]

MONTHS_EN = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

WEEKDAYS_FA_FULL = {
    5: "شنبه",
    6: "یک\u200cشنبه",
    0: "دوشنبه",
    1: "سه\u200cشنبه",
    2: "چهارشنبه",
    3: "پنج\u200cشنبه",
    4: "جمعه",
}

WEEKDAYS_EN_FULL = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

ACCENT = "#3689e6"
DIM = "#a6a6a6"

RLM = "\u200f"  # pins the paragraph direction to RTL

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

TOOLTIP_W = 38  # monospace width of the tooltip block


def div(a, b):
    return a // b


def fa_num(value):
    """Latin digits -> Persian digits."""
    return str(value).translate(FA_DIGITS)


def span(text, fg=None, bold=False):
    """Wrap text in a Pango span, ignoring empty attributes."""
    attrs = ""
    if fg:
        attrs += f' foreground="{fg}"'
    if bold:
        text = f"<b>{text}</b>"
    return f"<span{attrs}>{text}</span>" if attrs else text


def center(text, width):
    """Pad with spaces so the text sits in the middle of a width block.

    Padding is symmetric, which keeps it correct under the RTL paragraph
    direction (the whole line reverses, the padding stays balanced).
    """
    pad = max(width - len(text.replace("\u200c", "")), 0)
    left = pad // 2
    return " " * left + text + " " * (pad - left)


def gregorian_to_jalali(gy, gm, gd):
    """Standard jalaali-js algorithm."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621

    gy2 = gy + 1 if gm > 2 else gy
    days = (
        365 * gy
        + div(gy2 + 3, 4)
        - div(gy2 + 99, 100)
        + div(gy2 + 399, 400)
        - 80
        + gd
        + g_d_m[gm - 1]
    )

    jy += 33 * div(days, 12053)
    days %= 12053
    jy += 4 * div(days, 1461)
    days %= 1461

    if days > 365:
        jy += div(days - 1, 365)
        days = (days - 1) % 365

    if days < 186:
        jm = 1 + div(days, 31)
        jd = 1 + days % 31
    else:
        jm = 7 + div(days - 186, 30)
        jd = 1 + (days - 186) % 30

    return jy, jm, jd


def build_calendar_markup(gy, gm, gd, jy, jm, jd):
    """Pango markup: today's date in both calendars, two centered rows."""
    weekday = date(gy, gm, gd).weekday()

    fa_title = f"{WEEKDAYS_FA_FULL[weekday]} {fa_num(jd)} {MONTHS_FA[jm - 1]} {fa_num(jy)}"
    en_title = f"{WEEKDAYS_EN_FULL[weekday]}, {gd} {MONTHS_EN[gm - 1]} {gy}"

    # Both rows share the same size so they center against the same width;
    # hierarchy comes from color and weight instead.
    fa_line = f'<span size="large">{span(center(fa_title, TOOLTIP_W), fg=ACCENT, bold=True)}</span>'
    en_line = f'<span size="large">{span(center(en_title, TOOLTIP_W), fg=DIM)}</span>'

    return RLM + "\n".join([f"<tt>{fa_line}</tt>", f"<tt>{en_line}</tt>"])


def build_text(jy, jm, jd):
    """Bar text when toggled: ۲۹ شهریور ۱۴۰۵ (reads RTL)."""
    return f"{fa_num(jd)} {MONTHS_FA[jm - 1]} {fa_num(jy)}"


def main():
    if len(sys.argv) == 4:
        gy, gm, gd = (int(part) for part in sys.argv[1:4])
        today = date(gy, gm, gd)
        current_time = None
    else:
        now = datetime.now()
        today = now.date()
        current_time = now.strftime("%H:%M")

    gy, gm, gd = today.year, today.month, today.day
    jy, jm, jd = gregorian_to_jalali(gy, gm, gd)

    jalali_mode = os.path.exists(MODE_FILE)

    if jalali_mode or current_time is None:
        text = build_text(jy, jm, jd)
    else:
        text = current_time

    print(
        json.dumps(
            {
                "text": text,
                "tooltip": build_calendar_markup(gy, gm, gd, jy, jm, jd),
                "class": "jalali-date" if jalali_mode else "",
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
