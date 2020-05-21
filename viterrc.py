from gi.repository import Pango
from datetime import datetime

# Set font.
win.set_font(Pango.FontDescription("Monospace 12.5"))

# Bigger scrollback.
win.term.set_scrollback_lines(20000)

# Visual bell.
win.term.set_audible_bell(False)
win.last_bell = None

def bell_handler(_):
    win.last_bell = datetime.now()
win.term.connect("bell", bell_handler)

def display_bell():
    if win.last_bell is not None:
        delta = datetime.now() - win.last_bell
        delta_seconds = int(delta.total_seconds())
        if delta_seconds <= 10:
            return '*' * (10 - delta_seconds)
    return ""

win.bar_segments.insert(1, display_bell)

# Add the current time to the bar.
win.bar_segments.append(lambda: datetime.now().time().strftime("{%H:%M}"))

# Map space to exit DETACHED mode.
win.detached_mode_key_map[Gdk.KEY_space] = lambda: win.enter_normal_mode()

# Map `h` to search for shell prompt.
win.prompt = '\|>'
win.detached_mode_key_map[Gdk.KEY_h] = lambda: win.search(win.prompt)

# Map Shift+Space to Ctrl+U ((neo)vi(m)).
win.shift_space_remap = Gdk.ModifierType.CONTROL_MASK, Gdk.KEY_u

if 'VITER_USE_PYWAL' in os.environ:
    # Set pywal color scheme.
    def c(string):
        color = Gdk.RGBA()
        color.parse(string)
        return color

    with open("/home/nazar/.cache/wal/sequences", 'rb') as f:
        win.term.feed(f.read())
else:
    # Set a **LIGHT** color scheme.
    def c(string):
        color = Gdk.RGBA()
        color.parse("#" + string)
        return color

    win.term.set_colors(
        c("000000"),
        c("FFFFFF"),
        [
            c("000000"),
            c("8b0000"),
            c("006400"),
            c("808000"),
            c("00008b"),
            c("8b008b"),
            c("008b8b"),
            c("FFFFFF"),
            c("000000"),
            c("8b0000"),
            c("006400"),
            c("808000"),
            c("00008b"),
            c("8b008b"),
            c("008b8b"),
            c("FFFFFF"),
        ],
    )
