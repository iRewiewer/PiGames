#!/usr/bin/env python3
# utils/colors.py
"""
Named colors with dark/base/light variants mapped to nearest xterm-256 indices,
plus helper to build cached curses color attributes.

Usage (inside a curses app):

    from utils.colors import get_color

    tile_attr = get_color(bg=("blue", "dark"))            # auto fg contrast
    bold_attr = get_color(bg=("gold", "base"), bold=True) # bold number
    gap_attr  = get_color(bg=("gray", "dark"))
"""

import curses
from typing import Dict, Tuple

# --------------------------------
# 1) Named palette (hex values)
# --------------------------------
COLOR_HEX: Dict[str, Dict[str, str]] = {
    "red":     {"dark": "#8B0000", "base": "#FF0000", "light": "#FF7F7F"},
    "blue":    {"dark": "#0033AA", "base": "#1E90FF", "light": "#87CEFA"},
    "green":   {"dark": "#006400", "base": "#00A000", "light": "#7CFC00"},
    "yellow":  {"dark": "#8B8000", "base": "#FFD400", "light": "#FFF27A"},
    "gold":    {"dark": "#B8860B", "base": "#DAA520", "light": "#FFD24D"},
    "brown":   {"dark": "#5A3A1A", "base": "#8B5A2B", "light": "#C6975B"},
    "purple":  {"dark": "#4B0082", "base": "#7A43B6", "light": "#B19CD9"},
    "magenta": {"dark": "#8B008B", "base": "#FF00FF", "light": "#FF77FF"},
    "pink":    {"dark": "#C71585", "base": "#FF69B4", "light": "#FFB6C1"},
    "cyan":    {"dark": "#007777", "base": "#00B7B7", "light": "#7FFFD4"},
    "orange":  {"dark": "#CC5500", "base": "#FF8C00", "light": "#FFB347"},
    "lime":    {"dark": "#2E8B57", "base": "#32CD32", "light": "#98FB98"},
    "gray":    {"dark": "#505050", "base": "#808080", "light": "#BDBDBD"},
    "black":   {"base": "#000000"},
    "white":   {"base": "#FFFFFF"},
}

# --------------------------------
# 2) Build xterm-256 palette
# --------------------------------
def _cube_level(n: int) -> int:
    return [0, 95, 135, 175, 215, 255][n]

def _build_xterm256() -> list[Tuple[int, int, int]]:
    pal = []
    # 0..15 standard
    pal += [
        (0,0,0),(205,0,0),(0,205,0),(205,205,0),
        (0,0,238),(205,0,205),(0,205,205),(229,229,229),
        (127,127,127),(255,0,0),(0,255,0),(255,255,0),
        (92,92,255),(255,0,255),(0,255,255),(255,255,255)
    ]
    # 16..231 cube
    for r in range(6):
        for g in range(6):
            for b in range(6):
                pal.append((_cube_level(r), _cube_level(g), _cube_level(b)))
    # 232..255 grayscale
    for i in range(24):
        v = 8 + i * 10
        pal.append((v,v,v))
    return pal

_XTERM256 = _build_xterm256()

def _hex_to_rgb(h: str) -> Tuple[int,int,int]:
    h = h.lstrip("#")
    return int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)

def _nearest_index(r:int,g:int,b:int) -> int:
    best_i, best_d = 0, 1e18
    for i,(rr,gg,bb) in enumerate(_XTERM256):
        d = (r-rr)*(r-rr)+(g-gg)*(g-gg)+(b-bb)*(b-bb)
        if d < best_d:
            best_d, best_i = d, i
    return best_i

# Precompute indices for all named colors
COLOR_IDX: Dict[str, Dict[str, int]] = {}
for name, variants in COLOR_HEX.items():
    COLOR_IDX[name] = {}
    for vname, hexv in variants.items():
        COLOR_IDX[name][vname] = _nearest_index(*_hex_to_rgb(hexv))

# --------------------------------
# 3) curses helpers
# --------------------------------
def _luminance(r:int,g:int,b:int)->float:
    return 0.2126*r + 0.7152*g + 0.0722*b

def _auto_contrast_fg(bg_idx:int)->int:
    r,g,b = _XTERM256[bg_idx]
    return 0 if _luminance(r,g,b) > 140 else 15  # 0=black, 15=white

_PAIR_CACHE: Dict[Tuple[int,int], int] = {}
_NEXT_PAIR_ID = 1

def _pair_for_indices(fg_idx:int,bg_idx:int)->int:
    global _NEXT_PAIR_ID
    key=(fg_idx,bg_idx)
    if key in _PAIR_CACHE:
        return _PAIR_CACHE[key]
    curses.init_pair(_NEXT_PAIR_ID, fg_idx, bg_idx)
    _PAIR_CACHE[key]=_NEXT_PAIR_ID
    _NEXT_PAIR_ID+=1
    return _PAIR_CACHE[key]

def get_color(
    *,
    bg: Tuple[str,str],          # e.g. ("blue","dark")
    fg: Tuple[str,str]|None=None,
    bold: bool=False,
    underline: bool=False
) -> int:
    """Return curses attribute for named bg/fg colors."""
    bg_name,bg_var = bg
    bg_idx = COLOR_IDX[bg_name][bg_var]

    if fg is None:
        fg_idx = _auto_contrast_fg(bg_idx)
    else:
        fg_name,fg_var = fg
        fg_idx = COLOR_IDX[fg_name][fg_var]

    pid = _pair_for_indices(fg_idx,bg_idx)
    a = curses.color_pair(pid)
    if bold: a |= curses.A_BOLD
    if underline: a |= curses.A_UNDERLINE
    return a
