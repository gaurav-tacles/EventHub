"""ui.py - small helpers for colours, boxes and tables.
Keeping all the 'looks' here makes the other modules easy to read."""
import os
import sys

# Make sure Unicode box characters print correctly (e.g. on Windows)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


def _colors_supported():
    """Use colours only when printing to a real terminal."""
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return False
    if os.name == "nt":
        os.system("")  # turns on ANSI colour support in Windows 10+
    return True


USE_COLOR = _colors_supported()
RESET, BOLD = "\033[0m", "\033[1m"
RED, GREEN, YELLOW, CYAN = "\033[91m", "\033[92m", "\033[93m", "\033[96m"


def paint(text, color):
    """Wrap text in a colour code (or return it unchanged if no colour)."""
    return f"{color}{text}{RESET}" if USE_COLOR else text


def success(msg):
    print(paint("✔ " + msg, GREEN))


def error(msg):
    print(paint("✘ " + msg, RED))


def warning(msg):
    print(paint("⚠ " + msg, YELLOW))


def info(msg):
    print(paint("ℹ " + msg, CYAN))


def banner(title, subtitle="", width=40):
    """Draw a boxed title using Unicode box characters."""
    print()
    print(paint("╔" + "═" * width + "╗", CYAN))
    print(paint("║" + title.center(width) + "║", CYAN + BOLD if USE_COLOR else ""))
    if subtitle:
        print(paint("║" + subtitle.center(width) + "║", CYAN))
    print(paint("╚" + "═" * width + "╝", CYAN))


def heading(title, width=40):
    print()
    print(paint("─" * width, CYAN))
    print(paint(title.center(width), BOLD))
    print(paint("─" * width, CYAN))


def show_menu(options):
    """Print a numbered menu from a list of strings."""
    print()
    for number, text in enumerate(options, start=1):
        print(f"  {number}. {text}")
    print()


def truncate(text, max_width):
    """Shorten long text so tables do not become too wide."""
    return text if len(text) <= max_width else text[:max_width - 1] + "…"


def table(headers, rows, max_width=22):
    """Print a simple ASCII table. rows is a list of lists."""
    rows = [[truncate(str(cell), max_width) for cell in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    print(border)
    print("| " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)) + " |")
    print(border)
    for row in rows:
        print("| " + " | ".join(c.ljust(w) for c, w in zip(row, widths)) + " |")
    print(border)
