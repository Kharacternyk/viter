#!/bin/python3

import sys
import os
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")

# We import more than we actually use so that more things are exposed to user configs.
from gi.repository import Gtk, Vte, GLib, Pango, Gdk  # noqa E402


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


class Window(Gtk.Window):
    def key_press_handler(self, widget, event):
        if (
            event.keyval == Gdk.KEY_space
            and event.state & Gdk.ModifierType.CONTROL_MASK > 0
        ):
            if self.command_line.is_visible():
                self.command_line.hide()
            else:
                self.command_line.show()
                self.command_line.grab_focus()

    def command_handler(self, command_line):
        command = command_line.get_text()
        try:
            eval(command)
        except Exception as err:
            command_line.set_text(str(err))

    def __init__(self, terminal_shell_argv):
        Gtk.Window.__init__(self, title="viter")
        self.connect("delete_event", Gtk.main_quit)
        self.connect("key_press_event", self.key_press_handler)

        self.terminal = Terminal(terminal_shell_argv)

        self.box = Gtk.VBox()
        self.add(self.box)
        self.box.pack_start(self.terminal, True, True, 0)

        self.command_line = Gtk.Entry(placeholder_text="sample text")
        self.command_line.connect("activate", self.command_handler)
        # `override_font` is deprecated.
        # Nothing like it is exposed instead though.
        self.command_line.override_font(self.terminal.get_font())
        self.box.pack_start(self.command_line, False, True, 0)

        self.show_all()


def read_config():
    if "XDG_CONFIG_HOME" in os.environ:
        config_dir = os.environ["XDG_CONFIG_HOME"]
    else:
        config_dir = os.environ["HOME"] + "/.config"

    path = config_dir + "/viter/viterrc.py"
    if os.path.isfile(path):
        config_file = open(path, "r")
        eval(config_file.read())


if __name__ == "__main__":
    child_argv = sys.argv[1:]
    if child_argv == []:
        child_argv = [os.environ["SHELL"]]
    window = Window(child_argv)
    read_config()
    Gtk.main()
