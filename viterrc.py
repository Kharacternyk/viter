# Set some random options.
win.term.set_audible_bell(False)
win.term.set_scrollback_lines(2000)

from gi.repository import Pango as _pango
win.set_font(_pango.FontDescription("Monospace 12.5"))

# Add the current time to the bar.
_default_status_string_func = Window.get_status_string

from datetime import datetime as _dt

def _custom_status_string(window):
    now = _dt.now().time().strftime("%H:%M")
    return f"{_default_status_string_func(window)} |{now}|"

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
