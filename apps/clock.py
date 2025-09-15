#!/usr/bin/env python3
# PiGames/apps/clock.py
import time
import curses
from datetime import datetime

from ..lib.curses_util import mainloop
from ..lib.colors import get_color

# ================== Tunables ==================
USE_24H = True
SHOW_SECONDS = True
BLINK_COLON = True
DATE_BELOW = True

DIGIT_FG = ("white", "base")     # number color
DIGIT_BG = None                  # keep terminal bg (we won't paint background blocks)
COLON_FG = ("gold", "base")
DATE_FG  = ("gray", "light")

PADDING_X = 2
PADDING_Y = 1

PIX = "█"  # glyph pixel

# Big 7x7 font
DIGITS = {
    "0": ["0111110","1100011","1100111","1111011","1110011","1100011","0111110"],
    "1": ["0011000","0111000","0011000","0011000","0011000","0011000","1111111"],
    "2": ["0111110","1100001","0000001","0001110","0011000","0110000","1111111"],
    "3": ["1111110","0000011","0000011","0011110","0000011","0000011","1111110"],
    "4": ["0001110","0011110","0110110","1100110","1111111","0000110","0000110"],
    "5": ["1111111","1100000","1111110","0000011","0000011","1100011","0111110"],
    "6": ["0011110","0110000","1100000","1111110","1100011","1100011","0111110"],
    "7": ["1111111","0000011","0000110","0001100","0011000","0011000","0011000"],
    "8": ["0111110","1100011","1100011","0111110","1100011","1100011","0111110"],
    "9": ["0111110","1100011","1100011","0111111","0000011","0000110","0111100"],
}
COLON = ["0000000","0011000","0011000","0000000","0011000","0011000","0000000"]

DIGIT_H = len(next(iter(DIGITS.values())))
DIGIT_W = len(next(iter(DIGITS.values())))

# lazy-initialized attrs (after curses starts)
_ATTRS_READY = False
_ATTR_DIGIT = 0
_ATTR_COLON = 0
_ATTR_DATE  = 0

def _init_attrs():
    global _ATTRS_READY, _ATTR_DIGIT, _ATTR_COLON, _ATTR_DATE
    if _ATTRS_READY:
        return
    # Build color pairs now that curses is initialized (mainloop did initscr/start_color)
    def _attr_for(fg_cfg, bg_cfg):
        # We won’t fill backgrounds; we only draw PIX chars where the glyph has “1”.
        # Using a real bg is fine too because we don’t print spaces for background.
        if bg_cfg is None:
            # fallback: readable fg on a neutral bg; won’t show unless we print spaces
            return get_color(bg=("black", "base"), fg=fg_cfg)
        return get_color(bg=bg_cfg, fg=fg_cfg)

    _ATTR_DIGIT = _attr_for(DIGIT_FG, DIGIT_BG)
    _ATTR_COLON = _attr_for(COLON_FG, DIGIT_BG)
    _ATTR_DATE  = _attr_for(DATE_FG,  None)
    _ATTRS_READY = True

def render_big_text(stdscr, top, left, text, colon_on=True):
    gap = 2
    for r in range(DIGIT_H):
        x = left
        for i, ch in enumerate(text):
            glyph = (COLON if ch == ":" else DIGITS[ch])
            row = glyph[r]
            attr = _ATTR_COLON if ch == ":" else _ATTR_DIGIT
            if ch == ":" and not colon_on:
                attr = _ATTR_DIGIT
            for c, bit in enumerate(row):
                if bit == "1":
                    try:
                        stdscr.addstr(top + r, x + c, PIX, attr)
                    except curses.error:
                        pass
            x += DIGIT_W + gap

def update_draw(stdscr, dt):
    if not _ATTRS_READY:
        _init_attrs()

    stdscr.erase()
    h, w = stdscr.getmaxyx()

    now = datetime.now()
    hour = now.hour if USE_24H else (now.hour % 12 or 12)
    hh = f"{hour:02d}"
    mm = f"{now.minute:02d}"
    ss = f"{now.second:02d}"
    tstr = f"{hh}:{mm}:{ss}" if SHOW_SECONDS else f"{hh}:{mm}"
    colon_on = (now.second % 2 == 0) if BLINK_COLON else True

    glyphs = len(tstr)
    gap = 2
    clock_w = glyphs * DIGIT_W + (glyphs - 1) * gap
    clock_h = DIGIT_H

    area_w = clock_w + 2 * PADDING_X
    area_h = clock_h + 2 * PADDING_Y + (1 if DATE_BELOW else 0)

    top = max(0, (h - area_h) // 2) + PADDING_Y
    left = max(0, (w - area_w) // 2) + PADDING_X

    render_big_text(stdscr, top, left, tstr, colon_on=colon_on)

    if DATE_BELOW:
        datestr = now.strftime("%a %Y-%m-%d")
        y = top + DIGIT_H
        x = max(0, (w - len(datestr)) // 2)
        try:
            stdscr.addstr(y, x, datestr, _ATTR_DATE)
        except curses.error:
            pass

    stdscr.refresh()

def handle_key(stdscr, ch):
    global USE_24H, SHOW_SECONDS, BLINK_COLON
    if ch in (ord('s'),):
        SHOW_SECONDS = not SHOW_SECONDS
    elif ch in (ord('b'),):
        BLINK_COLON = not BLINK_COLON
    elif ch in (ord('t'),):
        USE_24H = not USE_24H
    # 'q'/ESC handled by mainloop

if __name__ == "__main__":
    mainloop(update_draw, handle_key, fps=10)
