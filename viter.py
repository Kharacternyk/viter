#!/bin/python3

import sys
import os
import gi
import enum

gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")

# We import more than we actually use so that more things are exposed to user configs.
from gi.repository import Gtk, Vte, GLib, Pango, Gdk  # noqa E402

Mode = enum.Enum("Mode", ["NORMAL", "DETACHED"])


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
    def __init__(self, terminal_shell_argv):
        Gtk.Window.__init__(self, title="viter")
        self.connect("delete_event", Gtk.main_quit)
        self.connect("key_press_event", self.key_press_handler)

        self.term = Terminal(terminal_shell_argv)
        self.term.connect("cursor_moved", lambda a: self.update_bar())

        self.box = Gtk.VBox()
        self.add(self.box)
        self.box.pack_start(self.term, True, True, 0)

        self.bar = Gtk.Entry()
        self.bar.connect("activate", self.command_handler)
        self.bar.connect("key_press_event", self.bar_key_press_handler)
        self.bar.connect("focus_out_event", self.bar_focus_out_handler)
        self.bar.connect("focus_in_event", self.bar_focus_in_handler)
        self.bar.set_alignment(1)

        self.box.pack_start(self.bar, False, True, 0)

        self.derive_bar_appearance()

        self.show_all()

        self.bar.hide()
        self.mode = Mode.NORMAL
        self.last_error_msg = ""
        self.key_queue = []
        self.set_default_key_map()

    def bar_focus_in_handler(self, widget, event):
        self.bar.set_alignment(0)
        self.last_error_msg = ""

    def bar_focus_out_handler(self, widget, event):
        self.bar.set_alignment(1)
        self.bar.set_text("")
        self.update_bar()

    def bar_key_press_handler(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.term.grab_focus()
            return True

    def command_handler(self, widget):
        command = self.bar.get_text()
        if command[0] == ":":
            try:
                eval(command[1:])
            except Exception as err:
                self.last_error_msg = str(err)
            finally:
                self.term.grab_focus()
        elif command[0] == "/":
            # TODO search.
            pass

    def key_press_handler(self, widget, event):
        if (
            event.keyval == Gdk.KEY_space
            and event.state & Gdk.ModifierType.CONTROL_MASK > 0
        ):
            if self.bar.is_visible():
                self.bar.hide()
                self.mode = Mode.NORMAL
            else:
                self.bar.show()
                self.mode = Mode.DETACHED
            return True

        if self.mode == Mode.DETACHED:
            if not self.bar.has_focus():
                self.handle_detached_key_press(event)
                return True

    def handle_detached_key_press(self, event):
        if event.keyval in self.key_map:
            self.key_map[event.keyval]()

    def set_default_key_map(self):
        def prepare_bar(text):
            self.bar.grab_focus()
            Gtk.Entry.do_insert_at_cursor(self.bar, text)

        self.key_map = {
            Gdk.KEY_colon: (lambda: prepare_bar(":")),
            Gdk.KEY_slash: (lambda: prepare_bar("/")),
            Gdk.KEY_j: (lambda: self.scroll_terminal(1)),
            Gdk.KEY_k: (lambda: self.scroll_terminal(-1)),
            Gdk.KEY_J: (lambda: self.scroll_terminal(0, 1)),
            Gdk.KEY_K: (lambda: self.scroll_terminal(0, -1)),
            Gdk.KEY_g: (lambda: self.scroll_terminal_to_top()),
            Gdk.KEY_G: (lambda: self.scroll_terminal_to_bottom()),
        }

    def scroll_terminal(self, line_count, page_count=0):
        vadjustment = self.term.get_vadjustment()
        current = vadjustment.get_value()
        desired = current + line_count + page_count * vadjustment.get_page_size()
        vadjustment.set_value(desired)
        self.update_bar()

    def scroll_terminal_to_top(self):
        vadjustment = self.term.get_vadjustment()
        vadjustment.set_value(vadjustment.get_lower())
        self.update_bar()

    def scroll_terminal_to_bottom(self):
        vadjustment = self.term.get_vadjustment()
        vadjustment.set_value(vadjustment.get_upper())
        self.update_bar()

    def get_status_string(self):
        vadjustment = self.term.get_vadjustment()
        terminal_top = int(vadjustment.get_value())
        terminal_bottom = terminal_top + int(vadjustment.get_page_size())
        emsg = self.last_error_msg
        if emsg != "":
            emsg = "ERROR (" + emsg + ") "
        return (
            f"{emsg}[{terminal_top}-{terminal_bottom}] ({int(vadjustment.get_upper())})"
        )

    def update_bar(self):
        self.bar.set_placeholder_text(self.get_status_string())

    def derive_bar_appearance(self):
        # `override_font` is deprecated.
        # Nothing like it is exposed instead though.
        self.bar.override_font(self.term.get_font())


def read_config():
    if "XDG_CONFIG_HOME" in os.environ:
        config_dir = os.environ["XDG_CONFIG_HOME"]
    else:
        config_dir = os.environ["HOME"] + "/.config"

    path = config_dir + "/viter/viterrc.py"
    if os.path.isfile(path):
        config_file = open(path, "r")
        exec(config_file.read())
        config_file.close()


if __name__ == "__main__":
    child_argv = sys.argv[1:]
    if child_argv == []:
        child_argv = [os.environ["SHELL"]]
    win = Window(child_argv)
    read_config()
    Gtk.main()
