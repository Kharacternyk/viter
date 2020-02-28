#!/bin/python3

import sys
import os
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")

from gi.repository import Gtk, Vte, GLib, Pango  # noqa E402


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
    def command_handler(self, command_line):
        command = command_line.get_text()
        eval(command)

    def __init__(self, terminal):
        Gtk.Window.__init__(self, title="viter")
        self.connect("delete_event", Gtk.main_quit)

        self.terminal = terminal
        self.box = Gtk.VBox()
        self.add(self.box)
        self.box.pack_start(self.terminal, True, True, 0)

        self.command_line = Gtk.Entry(placeholder_text="sample text")
        self.command_line.connect("activate", self.command_handler)
        # `override_font` is deprecated.
        # Nothing like it is exposed instead though.
        self.command_line.override_font(Pango.FontDescription("Monospace 12.5"))
        self.box.pack_start(self.command_line, False, True, 0)

        self.show_all()


if __name__ == "__main__":
    child_argv = sys.argv[1:]
    if child_argv == []:
        child_argv = [os.environ["SHELL"]]
    window = Window(Terminal(child_argv))
    Gtk.main()
