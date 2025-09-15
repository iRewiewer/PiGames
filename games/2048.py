#!/usr/bin/env python3
# Imports
import curses
import random
from ..lib.curses_util import mainloop
from ..lib.colors import get_color

# =======================
# Tunables / “theme” bits
# =======================
SIZE = 4                 # board is SIZE x SIZE

# Tile geometry (compensate terminal aspect ratio)
TILE_W = 8              # characters per tile width
TILE_H = 3              # terminal rows per tile height
H_GAP  = 2              # horizontal gap (chars) between tiles
V_GAP  = 1              # vertical gap (rows) between tiles

# Board frame (border) around the grid (NOT the whole screen)
BORDER_SIZE = 1         # thickness in terminal rows/cols
BORDER_BG   = ("gray", "dark")  # background color of border area
BORDER_FG   = ("white", "base") # text color if we print characters there (we fill with spaces)

# Gap color (the “grid lines” between tiles)
GAP_BG      = ("gray", "dark")
GAP_FG      = ("gray", "dark")  # irrelevant; we draw spaces

# Menu panel (title + how-to + score)
MENU_BG     = ("gray", "base")
MENU_FG     = ("black", "base")
MENU_PADDING_X = 2
MENU_PADDING_Y = 1

# =====================
# Number formatting util
# =====================
def fmt_tile(v: int) -> str:
    if v == 0:
        return "."
    units = [(1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")]
    for base, suffix in units:
        if v >= base:
            n = v // base
            s = f"{n}{suffix}"
            return s[:4]
    return str(v)[:4]

# =================
# Board mechanics
# =================
def new_board():
    b = [[0] * SIZE for _ in range(SIZE)]
    spawn(b); spawn(b)
    return b

def spawn(b):
    empties = [(r, c) for r in range(SIZE) for c in range(SIZE) if b[r][c] == 0]
    if not empties:
        return
    r, c = random.choice(empties)
    b[r][c] = 4 if random.random() < 0.1 else 2

def compress_line(line):
    """Left-compress + merge once per pair; returns (new_line, moved, gained_score)."""
    xs = [x for x in line if x]
    out, i, gained = [], 0, 0
    while i < len(xs):
        if i + 1 < len(xs) and xs[i] == xs[i + 1]:
            v = xs[i] * 2
            out.append(v)
            gained += v
            i += 2
        else:
            out.append(xs[i])
            i += 1
    out += [0] * (len(line) - len(out))
    moved = out != line
    return out, moved, gained

def move_left(b):
    moved = False
    gained = 0
    for r in range(SIZE):
        new, ch, sc = compress_line(b[r])
        b[r] = new
        moved = moved or ch
        gained += sc
    return moved, gained

def move_right(b):
    moved = False
    gained = 0
    for r in range(SIZE):
        rev = list(reversed(b[r]))
        new, ch, sc = compress_line(rev)
        b[r] = list(reversed(new))
        moved = moved or ch
        gained += sc
    return moved, gained

def transpose(b):
    return [list(row) for row in zip(*b)]

def move_up(b):
    t = transpose(b)
    ch, sc = move_left(t)
    nb = transpose(t)
    for r in range(SIZE):
        b[r] = nb[r]
    return ch, sc

def move_down(b):
    t = transpose(b)
    ch, sc = move_right(t)
    nb = transpose(t)
    for r in range(SIZE):
        b[r] = nb[r]
    return ch, sc

def has_moves(b):
    if any(0 in row for row in b):
        return True
    for r in range(SIZE):
        for c in range(SIZE):
            v = b[r][c]
            if r + 1 < SIZE and b[r + 1][c] == v:
                return True
            if c + 1 < SIZE and b[r][c + 1] == v:
                return True
    return False

def max_tile(b):
    return max(max(row) for row in b)

# ===========
# Game state
# ===========
board = new_board()
score = 0
won = False

# ===============
# Small draw utils
# ===============
def draw_rect(stdscr, y, x, h, w, attr):
    """Fill rectangle [y..y+h-1] x [x..x+w-1] with spaces in attr."""
    for yy in range(h):
        try:
            stdscr.addstr(y + yy, x, " " * max(0, w), attr)
        except curses.error:
            pass

def draw_text_center(stdscr, y, x, w, text, attr):
    try:
        stdscr.addstr(y, x + max(0, (w - len(text)) // 2), text, attr)
    except curses.error:
        pass

# ===============
# Input & drawing
# ===============
def handle_key(stdscr, ch):
    global board, score, won
    moved = False
    gained = 0

    if ch in (curses.KEY_LEFT, ord('a'), ord('h')):
        moved, gained = move_left(board)
    elif ch in (curses.KEY_RIGHT, ord('d'), ord('l')):
        moved, gained = move_right(board)
    elif ch in (curses.KEY_UP, ord('w'), ord('k')):
        moved, gained = move_up(board)
    elif ch in (curses.KEY_DOWN, ord('s'), ord('j')):
        moved, gained = move_down(board)
    elif ch in (ord('r'),):
        board[:] = new_board()
        score = 0
        won = False
        return

    if moved:
        score += gained
        spawn(board)
        if not won and max_tile(board) >= 2048:
            won = True

def update_draw(stdscr, dt):
    stdscr.erase()  # clears to terminal's own background; we don't force a global bg

    h, w = stdscr.getmaxyx()

    # ---------- MENU PANEL ----------
    # Content lines
    title = "2048 — arrows/WASD (HJKL) | r: reset | q/ESC: quit"
    help1 = "Combine tiles to reach 2048. One merge per tile per move."
    score_line = f"Score: {score}"
    lines = [title, help1, score_line]

    # Menu geometry
    menu_width = max(len(s) for s in lines) + 2 * MENU_PADDING_X
    menu_height = len(lines) + 2 * MENU_PADDING_Y
    menu_x = max(0, (w - menu_width) // 2)
    menu_y = 0  # top of screen

    menu_attr_bg = get_color(bg=MENU_BG, fg=MENU_FG)    # bg+fg set
    draw_rect(stdscr, menu_y, menu_x, menu_height, menu_width, menu_attr_bg)
    # Write lines centered inside
    for i, s in enumerate(lines):
        try:
            stdscr.addstr(menu_y + MENU_PADDING_Y + i,
                          menu_x + MENU_PADDING_X,
                          s.ljust(menu_width - 2 * MENU_PADDING_X),
                          menu_attr_bg)
        except curses.error:
            pass

    # ---------- BOARD AREA ----------
    # Grid (inner area) dimensions
    gridw = SIZE * TILE_W + (SIZE - 1) * H_GAP
    gridh = SIZE * TILE_H + (SIZE - 1) * V_GAP

    # Outer (bordered) box dimensions
    bs = BORDER_SIZE
    outer_w = gridw + 2 * bs + 2
    outer_h = gridh + 2 * bs

    # Place the outer box below the menu with a blank line spacing
    starty = menu_y + menu_height + 1
    startx = max(0, (w - outer_w) // 2)

    # Too small?
    if h < starty + outer_h + 1 or w < outer_w:
        warn = "Terminal too small — enlarge window"
        draw_text_center(stdscr, starty, 0, w, warn, curses.A_BOLD)
        stdscr.refresh()
        return

    # Border rectangle
    border_attr = get_color(bg=BORDER_BG, fg=BORDER_FG)
    draw_rect(stdscr, starty, startx, outer_h, outer_w, border_attr)

    # Inner area origin (top-left corner of the grid)
    inner_y = starty + bs
    inner_x = startx + bs + 1

    # Fill inner area with “gap” background first (solid board background)
    gap_attr = get_color(bg=GAP_BG, fg=GAP_FG)
    draw_rect(stdscr, inner_y, inner_x, gridh, gridw, gap_attr)

    # Draw each tile (colored blocks) over the gap background
    for r in range(SIZE):
        for c in range(SIZE):
            v = board[r][c]
            s = fmt_tile(v)
            # choose tile color based on value
            # simple cyclic palette: bump lightness with value
            # map by exponent to a few named backgrounds for better looks
            if v == 0:
                tile_bg = ("gray", "base")
            else:
                exp = v.bit_length() - 1
                # a small cycle through named colors
                palette = [
                    ("blue", "light"),
                    ("cyan", "base"),
                    ("green", "base"),
                    ("yellow", "base"),
                    ("orange", "base"),
                    ("magenta", "base"),
                    ("red", "base"),
                    ("purple", "base"),
                    ("gold", "base"),
                    ("pink", "base"),
                    ("lime", "base"),
                    ("blue", "base"),
                    ("cyan", "light"),
                    ("green", "light"),
                    ("yellow", "light"),
                    ("orange", "light"),
                ]
                tile_bg = palette[(exp - 1) % len(palette)]
            tile_attr = get_color(bg=tile_bg)  # auto-contrast fg

            # Tile top-left
            x = inner_x + c * (TILE_W + H_GAP)
            y = inner_y + r * (TILE_H + V_GAP)

            # Fill tile rectangle
            for dy in range(TILE_H):
                try:
                    stdscr.addstr(y + dy, x, " " * TILE_W, tile_attr)
                except curses.error:
                    pass

            # Number centered on the middle row
            text_y = y + TILE_H // 2
            text_x = x + (TILE_W - len(s)) // 2
            try:
                stdscr.addstr(text_y, text_x, s, tile_attr | curses.A_BOLD if v >= 1024 else tile_attr)
            except curses.error:
                pass

    # Win/lose messages (draw under the board area)
    msg = None
    if not has_moves(board):
        msg = "Game Over — press r to restart or q to quit"
    elif won:
        msg = "You made 2048! Keep going… (r to reset)"

    if msg:
        draw_text_center(stdscr, inner_y + gridh + 1, 0, w, msg, curses.A_BOLD)

    stdscr.refresh()

# -----------
# Entry point
# -----------
if __name__ == "__main__":
    mainloop(update_draw, handle_key, fps=60)
