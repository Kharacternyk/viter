#!/bin/python3

from gi.repository import Gtk, Gdk, Vte, GLib, Pango


class Terminal(Vte.Terminal):
    def __init__(self, argv):
        Vte.Terminal.__init__(self)
        self.spawn_async(
            Vte.PtyFlags.DEFAULT,
            None,
            argv,
            None,
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,
            None,
            -1,
        )
        self.set_font(Pango.FontDescription("Monospace 12.5"))

class Window(Gtk.Window):
    def __init__(self, terminal):
        Gtk.Window.__init__(self, title="viter")
        self.connect("delete_event", Gtk.main_quit)
        self.add(terminal)
        self.show_all()


if __name__ == "__main__":
    Window(Terminal(["/bin/bash"]))
    Gtk.main()
