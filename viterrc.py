win.term.set_audible_bell(False)
win.term.set_font(Pango.FontDescription("Monospace 12.5"))
win.derive_bar_appearance()


# We may define an utility fuction.
# This one avoids some boilerplate involved with color definition in hex.
# Viter doesn't use itself names that begin with an underscore.
def _c(string):
    color = Gdk.RGBA()
    color.parse("#" + string)
    return color


# Attention!
# This is a **light** palette that I use myself.
# Do not accidentally burn your eyes at night.
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
