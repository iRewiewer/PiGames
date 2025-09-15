import curses
from time import time, sleep

def init():
    stdscr = curses.initscr()        # start curses, get main screen
    curses.noecho()                  # don't echo typed keys to the terminal
    curses.cbreak()                  # keys are sent immediately (no Enter needed)
    curses.curs_set(0)               # hide the cursor
    stdscr.keypad(True)              # let us use arrow keys, F1, etc.
    curses.start_color()             # enable colors
    curses.use_default_colors()      # let terminal default background show through
    return stdscr                    # return the main window object

def teardown(stdscr):
    try:
        stdscr.keypad(False)
        curses.nocbreak()
        curses.echo()
        curses.curs_set(1)           # show cursor again
    finally:
        curses.endwin()              # exit curses cleanly

def mainloop(update_draw, handle_key, fps=30):
    stdscr = init()
    stdscr.nodelay(True)  # non-blocking getch()
    delta_time_target = 1.0 / fps
    last = time()
    try:
        while True:
            # --- TIMING ---
            now = time()
            delta_time = now - last
            if delta_time < delta_time_target:
                sleep(delta_time_target - delta_time)   # wait if running too fast
                now = time()
                delta_time = now - last
            last = now

            # --- INPUT ---
            while True:
                ch = stdscr.getch()
                if ch == -1:         # no more keys in buffer
                    break
                if ch in (ord('q'), 27):  # quit if 'q' or ESC
                    return
                handle_key(stdscr, ch)    # pass key to game logic

            # --- UPDATE & DRAW ---
            update_draw(stdscr, delta_time)
    finally:
        teardown(stdscr)
