# Set some random options.
win.term.set_audible_bell(False)
win.term.set_font(Pango.FontDescription("Monospace 12.5"))

# Make the bar (status line) to look consistent with window.
win.derive_bar_appearance()

# Add the current time to the bar.
_default_status_string_func = Window.get_status_string

from datetime import datetime as _dt

def _custom_status_string(window):
    now = _dt.now().time()
    return f"{_default_status_string_func(window)} |{now.hour}:{now.minute}|"

Window.get_status_string = _custom_status_string

# Set a **LIGHT** color scheme.
def _c(string):
    color = Gdk.RGBA()
    color.parse("#" + string)
    return color

win.term.set_colors(
    _c("000000"),
    _c("FFFFFF"),
    [
        _c("000000"),
        _c("8b0000"),
        _c("006400"),
        _c("808000"),
        _c("00008b"),
        _c("8b008b"),
        _c("008b8b"),
        _c("FFFFFF"),
        _c("000000"),
        _c("8b0000"),
        _c("006400"),
        _c("808000"),
        _c("00008b"),
        _c("8b008b"),
        _c("008b8b"),
        _c("FFFFFF"),
    ],
)

# Map `q` to close while being in the detached mode.
win.key_map[Gdk.KEY_q] = (lambda: win.close())
