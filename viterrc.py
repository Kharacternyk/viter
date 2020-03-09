# Set some random options.
win.term.set_audible_bell(False)
win.term.set_scrollback_lines(2000)

from gi.repository import Pango
win.set_font(Pango.FontDescription("Monospace 12.5"))

# Add the current time to the bar.
default_status_string_func = Window.get_status_string

from datetime import datetime

def get_custom_status_string(window):
    now = datetime.now().time().strftime("%H:%M")
    return f"{default_status_string_func(window)} |{now}|"

Window.get_status_string = get_custom_status_string

# Map space to exit DETACHED mode.
win.detached_mode_key_map[Gdk.KEY_space] = lambda: win.enter_normal_mode()

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
