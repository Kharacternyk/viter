#!/bin/python3

import sys
import os
import gi
import enum

gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")

from gi.repository import Gtk, Vte, GLib, Gdk  # noqa E402

Mode = enum.Enum("Mode", ["NORMAL", "DETACHED"])


class Window(Gtk.Window):
    def __init__(self, shell_argv):
        Gtk.Window.__init__(self, title="viter")
        self.connect("delete_event", Gtk.main_quit)
        self.connect("key_press_event", self.key_press_handler)

        self.init_term(shell_argv)
        self.init_bar()
        self.init_layout()

        self.show_all()

        self.bar.hide()
        self.set_default_key_map()

        self.mode = Mode.NORMAL
        self.message = ""
        self.key_queue = []
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    def init_term(self, argv):
        self.term = Vte.Terminal()
        self.term.spawn_async(
            Vte.PtyFlags.DEFAULT,
            None,
            argv,
            None,
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,
            None,
            -1,
        )
        self.term.search_set_wrap_around(True)
        self.term.connect("cursor_moved", lambda a: self.update_bar())
        self.term.connect("eof", lambda a: self.close())

    def init_bar(self):
        self.bar = Gtk.Entry()
        self.bar.connect("activate", self.command_handler)
        self.bar.connect("key_press_event", self.bar_key_press_handler)
        self.bar.connect("focus_out_event", self.bar_focus_out_handler)
        self.bar.connect("focus_in_event", self.bar_focus_in_handler)
        self.bar.set_alignment(1)
        self.derive_bar_appearance()

    def init_layout(self):
        self.box = Gtk.VBox()
        self.add(self.box)
        self.box.pack_start(self.term, True, True, 0)
        self.box.pack_start(self.bar, False, True, 0)

    def bar_focus_in_handler(self, widget, event):
        self.bar.set_alignment(0)
        self.message = ""

    def bar_focus_out_handler(self, widget, event):
        self.bar.set_alignment(1)
        self.bar.set_text("")
        self.update_bar()

    def bar_key_press_handler(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.term.grab_focus()
            return True
        if event.keyval == Gdk.KEY_Tab:
            # This would be the place for the tab completion, if it existed.
            return True

    def command_handler(self, widget):
        command = self.bar.get_text()
        try:
            exec(command)
        except Exception as err:
            self.message = str(err)
        finally:
            self.term.grab_focus()

    def key_press_handler(self, widget, event):
        if self.mode == Mode.DETACHED:
            if not self.bar.has_focus():
                if event.keyval in self.detached_mode_key_map:
                    self.detached_mode_key_map[event.keyval]()
                return True
        else:
            if (
                event.state & Gdk.ModifierType.CONTROL_MASK > 0
                and event.state & Gdk.ModifierType.SHIFT_MASK > 0
                and event.keyval in self.normal_mode_key_map
            ):
                self.normal_mode_key_map[event.keyval]()
                return True

    def enter_normal_mode(self):
        self.bar.hide()
        self.mode = Mode.NORMAL

    def enter_detached_mode(self):
        self.bar.show()
        self.mode = Mode.DETACHED

    def set_default_key_map(self):
        def prepare_bar(text_left, text_right=""):
            self.bar.grab_focus()
            Gtk.Entry.do_insert_at_cursor(self.bar, text_left + text_right)
            Gtk.Entry.do_move_cursor(
                self.bar, Gtk.MovementStep.LOGICAL_POSITIONS, -len(text_right), False
            )

        self.detached_mode_key_map = {
            Gdk.KEY_colon: (lambda: self.bar.grab_focus()),
            Gdk.KEY_slash: (lambda: prepare_bar('win.search("', '")')),
            Gdk.KEY_j: (lambda: self.scroll_term(1)),
            Gdk.KEY_k: (lambda: self.scroll_term(-1)),
            Gdk.KEY_J: (lambda: self.scroll_term(0, 1)),
            Gdk.KEY_K: (lambda: self.scroll_term(0, -1)),
            Gdk.KEY_g: (lambda: self.scroll_term_to_top()),
            Gdk.KEY_G: (lambda: self.scroll_term_to_bottom()),
            Gdk.KEY_y: (lambda: prepare_bar('win.yank_line("', '")')),
            Gdk.KEY_Y: (lambda: self.yank_message()),
            Gdk.KEY_Escape: (lambda: self.enter_normal_mode()),
            Gdk.KEY_n: (lambda: self.search_next()),
            Gdk.KEY_N: (lambda: self.search_previous()),
            Gdk.KEY_e: (lambda: prepare_bar("win.echo(", ")")),
        }

        self.normal_mode_key_map = {
            Gdk.KEY_space: (lambda: self.enter_detached_mode()),
            Gdk.KEY_C: (lambda: self.term.copy_clipboard_format(Vte.Format.TEXT)),
            Gdk.KEY_V: (lambda: self.term.paste_clipboard()),
        }

    def scroll_term(self, line_count, page_count=0):
        vadjustment = self.term.get_vadjustment()
        current = vadjustment.get_value()
        desired = current + line_count + page_count * vadjustment.get_page_size()
        vadjustment.set_value(desired)
        self.update_bar()

    def scroll_term_to_top(self):
        vadjustment = self.term.get_vadjustment()
        vadjustment.set_value(vadjustment.get_lower())
        self.update_bar()

    def scroll_term_to_bottom(self):
        vadjustment = self.term.get_vadjustment()
        vadjustment.set_value(vadjustment.get_upper())
        self.update_bar()

    def yank_line(self, trait):
        text, attributes = self.term.get_text()
        if isinstance(trait, int):
            line_number = trait
            line = text.splitlines()[line_number].strip()
            self.clipboard.set_text(line, -1)
        elif isinstance(trait, str):
            search_text = trait.strip()
            lines = [
                line
                for line in text.splitlines()
                if line.strip().startswith(search_text)
            ]
            if lines != []:
                self.clipboard.set_text(lines[-1].strip(), -1)
            else:
                self.message = "no such lines: " + search_text

    def yank_message(self):
        self.clipboard.set_text(self.message, -1)

    def search(self, pattern):
        PCRE2_MULTILINE = 0x00000400
        regex = Vte.Regex.new_for_search(pattern, len(pattern), PCRE2_MULTILINE)
        self.term.search_set_regex(regex, 0)
        self.search_next()

    def search_next(self):
        self.term.search_find_next()
        self.update_bar()

    def search_previous(self):
        self.term.search_find_previous()
        self.update_bar()

    def get_status_string(self):
        vadjustment = self.term.get_vadjustment()
        term_top = int(vadjustment.get_value())
        term_bottom = term_top + int(vadjustment.get_page_size())
        term_upper = int(vadjustment.get_upper())
        return f"{self.message} [{term_top}-{term_bottom}] ({term_upper})"

    def update_bar(self):
        self.bar.set_placeholder_text(self.get_status_string())

    def derive_bar_appearance(self):
        # `override_font` is deprecated.
        # Nothing like it is exposed instead though.
        self.bar.override_font(self.term.get_font())

    def echo(self, obj):
        self.message = str(obj)


if __name__ == "__main__":
    child_argv = sys.argv[1:]
    if child_argv == []:
        child_argv = [os.environ["SHELL"]]
    win = Window(child_argv)

    if "VITER_CONFIG" in os.environ:
        config_path = os.environ["VITER_CONFIG"]
    else:
        if "XDG_CONFIG_HOME" in os.environ:
            config_dir = os.environ["XDG_CONFIG_HOME"]
        else:
            config_dir = os.environ["HOME"] + "/.config"
        config_path = config_dir + "/viter/viterrc.py"

    if os.path.isfile(config_path):
        config_file = open(config_path, "r")
        exec(config_file.read())
        config_file.close()

    Gtk.main()
