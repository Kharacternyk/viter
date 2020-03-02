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
    def prepare_command_line(self, text):
        self.command_line.grab_focus()
        Gtk.Entry.do_insert_at_cursor(self.command_line, text)

    def scroll_terminal(self, count):
        vadjustment = self.terminal.get_vadjustment()
        current = vadjustment.get_value()
        desired = current + count
        if desired < vadjustment.get_upper():
            if desired > vadjustment.get_lower():
                vadjustment.set_value(desired)
            else:
                vadjustment.set_value(vadjustment.get_lower())
        else:
            vadjustment.set_value(vadjustment.get_upper())
        self.update_status_line()

    def set_default_key_map(self):
        self.key_map = {
            Gdk.KEY_colon: (lambda: self.prepare_command_line(":")),
            Gdk.KEY_slash: (lambda: self.prepare_command_line("/")),
            Gdk.KEY_j: (lambda: self.scroll_terminal(1)),
            Gdk.KEY_k: (lambda: self.scroll_terminal(-1)),
        }

    def handle_detached_key_press(self, event):
        if event.keyval in self.key_map:
            self.key_map[event.keyval]()

    def key_press_handler(self, widget, event):
        if (
            event.keyval == Gdk.KEY_space
            and event.state & Gdk.ModifierType.CONTROL_MASK > 0
        ):
            if self.command_line.is_visible():
                self.command_line.hide()
                self.mode = Mode.NORMAL
            else:
                self.command_line.show()
                self.mode = Mode.DETACHED
            return True

        if self.mode == Mode.DETACHED:
            if not self.command_line.has_focus():
                self.handle_detached_key_press(event)
                return True

    def command_handler(self, widget):
        command = self.command_line.get_text()
        if command[0] == ":":
            try:
                eval(command[1:])
            except Exception as err:
                self.last_error_msg = str(err)
            finally:
                self.terminal.grab_focus()
        elif command[0] == "/":
            # TODO search.
            pass

    def get_status_line_string(self):
        vadjustment = self.terminal.get_vadjustment()
        terminal_top = int(vadjustment.get_value())
        terminal_bottom = terminal_top + int(vadjustment.get_page_size())
        emsg = self.last_error_msg
        if emsg != "":
            emsg = "ERROR (" + emsg + ") "
        return f"{emsg}[{terminal_top}-{terminal_bottom}]"

    def update_status_line(self):
        self.command_line.set_placeholder_text(self.get_status_line_string())

    def derive_command_line_appearance(self):
        # `override_font` is deprecated.
        # Nothing like it is exposed instead though.
        self.command_line.override_font(self.terminal.get_font())

    def command_line_focus_in_handler(self, widget, event):
        self.command_line.set_alignment(0)
        self.last_error_msg = ""

    def command_line_focus_out_handler(self, widget, event):
        self.command_line.set_alignment(1)
        self.command_line.set_text("")
        self.update_status_line()

    def command_line_key_press_handler(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.terminal.grab_focus()
            return True

    def __init__(self, terminal_shell_argv):
        Gtk.Window.__init__(self, title="viter")
        self.connect("delete_event", Gtk.main_quit)
        self.connect("key_press_event", self.key_press_handler)

        self.terminal = Terminal(terminal_shell_argv)
        self.terminal.connect("cursor_moved", lambda a: self.update_status_line())

        self.box = Gtk.VBox()
        self.add(self.box)
        self.box.pack_start(self.terminal, True, True, 0)

        self.command_line = Gtk.Entry()
        self.command_line.connect("activate", self.command_handler)
        self.command_line.connect(
            "key_press_event", self.command_line_key_press_handler
        )
        self.command_line.connect(
            "focus_out_event", self.command_line_focus_out_handler
        )
        self.command_line.connect("focus_in_event", self.command_line_focus_in_handler)
        self.command_line.set_alignment(1)

        self.box.pack_start(self.command_line, False, True, 0)

        self.derive_command_line_appearance()

        self.show_all()

        self.command_line.hide()
        self.mode = Mode.NORMAL
        self.last_error_msg = ""
        self.set_default_key_map()


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
    window = Window(child_argv)
    read_config()
    Gtk.main()
