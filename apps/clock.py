#!/usr/bin/env python3
# PiGames/apps/clock.py
import time
import curses
from datetime import datetime

# relative to package (PiGames.apps.*)
from ..lib.curses_util import mainloop
from ..lib.colors import get_color

# ================== Tunables ==================
USE_24H = True          # 24h vs 12h
SHOW_SECONDS = True
BLINK_COLON = True      # blink once per second
DATE_BELOW = True       # show date under the clock

DIGIT_FG = ("white", "base")       # number color (fg auto-contrasts if bg given)
DIGIT_BG = None                    # keep terminal background; or e.g. ("blue","dark")
COLON_FG = ("gold", "base")
DATE_FG  = ("gray", "light")

PADDING_X = 2     # spaces around the clock
PADDING_Y = 1     # lines around the clock

# Character to paint "on" pixels (full block looks crisp); fallback: '#'
PIX = "█"

# Big-font digits (height=7, width=7) using 0/1 maps
# fmt: off
DIGITS = {
    "0": [
        "0111110",
        "1100011",
        "1100111",
        "1111011",
        "1110011",
        "1100011",
        "0111110",
    ],
    "1": [
        "0011000",
        "0111000",
        "0011000",
        "0011000",
        "0011000",
        "0011000",
        "1111111",
    ],
    "2": [
        "0111110",
        "1100001",
        "0000001",
        "0001110",
        "0011000",
        "0110000",
        "1111111",
    ],
    "3": [
        "1111110",
        "0000011",
        "0000011",
        "0011110",
        "0000011",
        "0000011",
        "1111110",
    ],
    "4": [
        "0001110",
        "0011110",
        "0110110",
        "1100110",
        "1111111",
        "0000110",
        "0000110",
    ],
    "5": [
        "1111111",
        "1100000",
        "1111110",
        "0000011",
        "0000011",
        "1100011",
        "0111110",
    ],
    "6": [
        "0011110",
        "0110000",
        "1100000",
        "1111110",
        "1100011",
        "1100011",
        "0111110",
    ],
    "7": [
        "1111111",
        "0000011",
        "0000110",
        "0001100",
        "0011000",
        "0011000",
        "0011000",
    ],
    "8": [
        "0111110",
        "1100011",
        "1100011",
        "0111110",
        "1100011",
        "1100011",
        "0111110",
    ],
    "9": [
        "0111110",
        "1100011",
        "1100011",
        "0111111",
        "0000011",
        "0000110",
        "0111100",
    ],
}
COLON = [
    "0000000",
    "0011000",
    "0011000",
    "0000000",
    "0011000",
    "0011000",
    "0000000",
]
# fmt: on

DIGIT_H = len(next(iter(DIGITS.values())))
DIGIT_W = len(next(iter(DIGITS.values())))

def _attr_for(fg_cfg, bg_cfg):
    if bg_cfg is None:
        # pure-foreground: emulate by using bg=black(light) vs not painting bg at all
        # Here we just return fg on terminal bg by giving same tuple to bg but relying on get_color’s auto-contrast if needed.
        # Simpler: request attr with only fg by picking a neutral bg and accepting terminal’s bg show-through: curses can’t do “fg only” pairs.
        return get_color(bg=("black", "base"), fg=fg_cfg)
    return get_color(bg=bg_cfg, fg=fg_cfg)

ATTR_DIGIT = _attr_for(DIGIT_FG, DIGIT_BG)
ATTR_COLON = _attr_for(COLON_FG, DIGIT_BG)
ATTR_DATE  = _attr_for(DATE_FG,  None)

def render_big_text(stdscr, top, left, text, attr_digit, attr_colon, colon_on=True):
    """
    Draw HH:MM[:SS] using big font at (top,left).
    """
    # Build sequence of glyph matrices for the given text
    glyphs = []
    for ch in text:
        if ch == ":":
            glyphs.append(COLON if colon_on else ["0"*DIGIT_W]*DIGIT_H)
        else:
            glyphs.append(DIGITS[ch])

    # Spacing between glyphs
    gap = 2

    # Draw row by row
    for r in range(DIGIT_H):
        x = left
        for i, g in enumerate(glyphs):
            row = g[r]
            a = attr_colon if text[i] == ":" else attr_digit
            if text[i] == ":" and not colon_on:
                a = attr_digit
            # paint this glyph row
            for c, bit in enumerate(row):
                if bit == "1":
                    try:
                        stdscr.addstr(top + r, x + c, PIX, a)
                    except curses.error:
                        pass
            x += DIGIT_W + gap

def update_draw(stdscr, dt):
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    now = datetime.now()
    hour = now.hour
    if not USE_24H:
        hour = hour % 12 or 12
    hh = f"{hour:02d}"
    mm = f"{now.minute:02d}"
    ss = f"{now.second:02d}"

    # Construct time string
    tstr = f"{hh}:{mm}:{ss}" if SHOW_SECONDS else f"{hh}:{mm}"
    colon_on = (now.second % 2 == 0) if BLINK_COLON else True

    # Compute rendered width
    glyphs = len(tstr)
    gap = 2
    clock_w = glyphs * DIGIT_W + (glyphs - 1) * gap
    clock_h = DIGIT_H

    # Box around the clock (optional): we just use padding here, no filled rectangle to preserve terminal bg
    area_w = clock_w + 2 * PADDING_X
    area_h = clock_h + 2 * PADDING_Y + (1 if DATE_BELOW else 0)

    top = max(0, (h - area_h) // 2) + PADDING_Y
    left = max(0, (w - area_w) // 2) + PADDING_X

    # Draw the big time
    render_big_text(stdscr, top, left, tstr, ATTR_DIGIT, ATTR_COLON, colon_on=colon_on)

    # Date line (centered under clock)
    if DATE_BELOW:
        datestr = now.strftime("%a %Y-%m-%d")
        y = top + DIGIT_H
        x = max(0, (w - len(datestr)) // 2)
        try:
            stdscr.addstr(y, x, datestr, ATTR_DATE)
        except curses.error:
            pass

    stdscr.refresh()

def handle_key(stdscr, ch):
    global USE_24H, SHOW_SECONDS, BLINK_COLON
    if ch in (ord('q'), 27):   # handled by mainloop too, but safe
        raise SystemExit
    elif ch in (ord('s'),):
        SHOW_SECONDS = not SHOW_SECONDS
    elif ch in (ord('b'),):
        BLINK_COLON = not BLINK_COLON
    elif ch in (ord('t'),):
        USE_24H = not USE_24H

if __name__ == "__main__":
    # 2–10 FPS is plenty; choose 10 so the blink feels responsive and resizing redraws quickly
    mainloop(update_draw, handle_key, fps=10)
