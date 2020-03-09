#!/bin/python3

import sys
import os
import enum
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")

from gi.repository import Gtk, Vte, GLib, Gdk  # noqa E402

Mode = enum.Enum("Mode", ["NORMAL", "DETACHED"])


class Window(Gtk.Window):
    def __init__(self, shell_argv):
        Gtk.Window.__init__(self, title="viter")
        self.connect("delete_event", Gtk.main_quit)
        self.connect("key_press_event", self.key_press_handler)

        self.init_term()
        self.init_bar()
        self.init_layout()

        self.show_all()

        self.bar.hide()
        self.set_default_key_map()

        self.mode = Mode.NORMAL
        self.message = ""
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        self.spawn(shell_argv)

    def init_term(self):
        self.term = Vte.Terminal()

        self.term.search_set_wrap_around(True)
        self.term.connect("eof", lambda a: self.close())

        self.adjustment = self.term.get_vadjustment()
        self.adjustment.connect("changed", lambda a: self.update_bar())
        self.adjustment.connect("value_changed", lambda a: self.update_bar())

    def init_bar(self):
        self.bar = Gtk.Entry()
        self.bar.connect("activate", self.command_handler)
        self.bar.connect("key_press_event", self.bar_key_press_handler)
        self.bar.connect("focus_out_event", self.bar_focus_out_handler)
        self.bar.connect("focus_in_event", self.bar_focus_in_handler)
        self.bar.set_alignment(1)

        self.bar.override_font(self.term.get_font())

    def init_layout(self):
        self.box = Gtk.VBox()
        self.add(self.box)
        self.box.pack_start(self.term, True, True, 0)
        self.box.pack_start(self.bar, False, True, 0)

    def spawn(self, argv):
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
                    self.update_bar()
                return True
        else:
            if (
                event.state & Gdk.ModifierType.CONTROL_MASK > 0
                and event.state & Gdk.ModifierType.SHIFT_MASK > 0
                and event.keyval in self.normal_mode_key_map
            ):
                self.normal_mode_key_map[event.keyval]()
                return True

    def prepare_bar(self, text_left, text_right=""):
        self.bar.grab_focus()
        Gtk.Entry.do_insert_at_cursor(self.bar, text_left + text_right)
        Gtk.Entry.do_move_cursor(
            self.bar, Gtk.MovementStep.LOGICAL_POSITIONS, -len(text_right), False
        )

    def set_default_key_map(self):
        self.detached_mode_key_map = {
            Gdk.KEY_colon: (lambda: self.bar.grab_focus()),
            Gdk.KEY_slash: (lambda: self.prepare_bar('win.search("', '")')),
            Gdk.KEY_j: (lambda: self.scroll_term(1)),
            Gdk.KEY_k: (lambda: self.scroll_term(-1)),
            Gdk.KEY_J: (lambda: self.scroll_term(0, 1)),
            Gdk.KEY_K: (lambda: self.scroll_term(0, -1)),
            Gdk.KEY_g: (lambda: self.scroll_term_to_top()),
            Gdk.KEY_G: (lambda: self.scroll_term_to_bottom()),
            Gdk.KEY_y: (lambda: self.prepare_bar('win.yank_line("', '")')),
            Gdk.KEY_Y: (lambda: self.yank_message()),
            Gdk.KEY_Escape: (lambda: self.enter_normal_mode()),
            Gdk.KEY_n: (lambda: self.search_next()),
            Gdk.KEY_N: (lambda: self.search_previous()),
            Gdk.KEY_e: (lambda: self.prepare_bar("win.echo(", ")")),
            Gdk.KEY_plus: (lambda: self.zoom(0.25)),
            Gdk.KEY_equal: (lambda: self.zoom(0.25)),
            Gdk.KEY_minus: (lambda: self.zoom(-0.25)),
        }

        self.normal_mode_key_map = {
            Gdk.KEY_space: (lambda: self.enter_detached_mode()),
            Gdk.KEY_C: (lambda: self.term.copy_clipboard_format(Vte.Format.TEXT)),
            Gdk.KEY_V: (lambda: self.term.paste_clipboard()),
        }

    def enter_normal_mode(self):
        self.bar.hide()
        self.mode = Mode.NORMAL

    def enter_detached_mode(self):
        self.update_bar()
        self.bar.show()
        self.mode = Mode.DETACHED

    def scroll_term(self, line_count, page_count=0):
        current = self.adjustment.get_value()
        desired = current + line_count + page_count * self.adjustment.get_page_size()
        self.adjustment.set_value(desired)

    def scroll_term_to_top(self):
        self.adjustment.set_value(self.adjustment.get_lower())

    def scroll_term_to_bottom(self):
        self.adjustment.set_value(self.adjustment.get_upper())

    def set_font(self, font):
        self.term.set_font(font)
        self.bar.override_font(font)

    def zoom(self, delta):
        current = self.term.get_font_scale()
        self.term.set_font_scale(current + delta)

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

    def search_previous(self):
        self.term.search_find_previous()

    def get_status_string(self):
        term_top = int(self.adjustment.get_value())
        term_bottom = term_top + int(self.adjustment.get_page_size())
        term_upper = int(self.adjustment.get_upper())
        term_zoom = int(self.term.get_font_scale() * 100)
        return (
            f"{self.message} <{term_zoom}%> [{term_top}-{term_bottom}] ({term_upper})"
        )

    def update_bar(self):
        self.bar.set_placeholder_text(self.get_status_string())

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
