# Bigger scrollback.
win.term.set_scrollback_lines(20000)

# Visual bell.
win.term.set_audible_bell(False)
def visual_bell(_):
    win.echo('BELL')
win.term.connect("bell", visual_bell)

# Set font.
from gi.repository import Pango
win.set_font(Pango.FontDescription("Monospace 12.5"))

# Add the current time to the bar.
from datetime import datetime
win.bar_segments.append(lambda: datetime.now().time().strftime("{%H:%M}"))

# Map space to exit DETACHED mode.
win.detached_mode_key_map[Gdk.KEY_space] = lambda: win.enter_normal_mode()

# Map `h` to search for shell prompt.
win.prompt = '|>'
win.detached_mode_key_map[Gdk.KEY_h] = lambda: win.search(win.prompt)

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
