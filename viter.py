#!/bin/python3 -W ignore

import sys
import os
import enum
import fileinput
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")

from gi.repository import Gtk, Vte, GLib, Gdk  # noqa E402

Mode = enum.Enum("Mode", ["NORMAL", "DETACHED"])


class Window(Gtk.Window):
    def __init__(self, argv, is_pager=False):
        Gtk.Window.__init__(self, title="viter")
        self.connect("delete_event", Gtk.main_quit)
        self.connect("key_press_event", self.key_press_handler)

        self.init_term()
        self.init_bar()
        self.init_layout()

        self.show_all()

        self.bar.hide()
        self.set_default_key_map()
        self.set_default_bar_segments()

        self.mode = Mode.NORMAL
        self.message = ""
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.connect("size_allocate", lambda a, b: self.update_bar())

        if is_pager:
            self.is_pager = True
            self.page(argv)
        else:
            self.is_pager = False
            self.spawn(argv)

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

    def page(self, argv):
        # The terminal doesn't report its scroll position until it's drawn.
        # We connect an one-time handler.
        def scroll_to_top(*args):
            self.scroll_term_to_top()
            self.term.disconnect_by_func(scroll_to_top)

        self.term.feed("\r".join(fileinput.input()).encode("utf-8"))
        self.enter_detached_mode()
        self.enter_normal_mode = lambda: None
        self.term.set_cursor_blink_mode(Vte.CursorBlinkMode.OFF)
        self.term.connect("draw", scroll_to_top)

    def spawn(self, argv):
        try:
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
        except AttributeError:
            # See issue #1.
            self.term.spawn_sync(
                Vte.PtyFlags.DEFAULT,
                None,
                argv,
                None,
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,
                None,
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
            self.try_autocomplete()
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
            if event.state & Gdk.ModifierType.SHIFT_MASK > 0:
                if (
                    event.state & Gdk.ModifierType.CONTROL_MASK > 0
                    and event.keyval in self.normal_mode_key_map
                ):
                    self.normal_mode_key_map[event.keyval]()
                    return True
                elif (
                    event.keyval == Gdk.KEY_space and self.shift_space_remap is not None
                ):
                    event.state, event.keyval = self.shift_space_remap

    def try_autocomplete(self):
        command = self.bar.get_text()

        try:
            last_dot_index = command.rindex(".")
        except ValueError:
            return

        obj = command[:last_dot_index]
        part = command[last_dot_index + 1 :]

        try:
            attributes = dir(eval(obj))
        except NameError:
            return
        except SyntaxError:
            return

        possible_matches = [
            attribute for attribute in attributes if attribute.startswith(part)
        ]

        if len(possible_matches) == 1:
            self.bar.set_text("")
            Gtk.Entry.do_insert_at_cursor(self.bar, obj + "." + possible_matches[-1])

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
            Gdk.KEY_V: (lambda: self.yank_all()),
            Gdk.KEY_v: (lambda: self.prepare_bar('win.yank_block("', ")")),
            Gdk.KEY_y: (lambda: self.prepare_bar('win.yank_line("', '")')),
            Gdk.KEY_Y: (lambda: self.yank_message()),
            Gdk.KEY_c: (lambda: self.term.copy_clipboard_format(Vte.Format.TEXT)),
            Gdk.KEY_p: (lambda: self.term.paste_clipboard()),
            Gdk.KEY_Escape: (lambda: self.enter_normal_mode()),
            Gdk.KEY_n: (lambda: self.term.search_find_next()),
            Gdk.KEY_N: (lambda: self.term.search_find_previous()),
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

        self.shift_space_remap = None

    def enter_normal_mode(self):
        self.bar.hide()
        self.scroll_term_to_bottom()
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

    def yank_all(self):
        text, attributes = self.term.get_text()
        self.clipboard.set_text(text, -1)

    def yank_block(self, trait, count, preserve_identation=True):
        text, attributes = self.term.get_text()
        search_text = trait.strip()
        lines = text.splitlines()

        if not preserve_identation:
            lines = [line.strip() for line in lines]
            first_line_candidates = [
                num for num, line in enumerate(lines) if line.startswith(search_text)
            ]
        else:
            first_line_candidates = [
                num
                for num, line in enumerate(lines)
                if line.strip().startswith(search_text)
            ]

        if first_line_candidates != []:
            first_line_num = first_line_candidates[0]
            block = "\n".join(lines[first_line_num : first_line_num + count])
            self.clipboard.set_text(block, -1)
        else:
            self.message = "no such lines: " + search_text

    def yank_line(self, trait):
        self.yank_block(trait, 1, False)

    def yank_message(self):
        self.clipboard.set_text(self.message, -1)

    def search(self, pattern, caseless=True):
        PCRE2_MULTILINE = 0x00000400
        PCRE2_CASELESS = 0x00000008

        if caseless:
            flags = PCRE2_MULTILINE | PCRE2_CASELESS
        else:
            flags = PCRE2_MULTILINE

        regex = Vte.Regex.new_for_search(pattern, len(pattern), flags)
        self.term.search_set_regex(regex, 0)
        self.term.search_find_next()

    def set_default_bar_segments(self):
        def get_top():
            return int(self.adjustment.get_value())

        def get_bottom():
            return get_top() + int(self.adjustment.get_page_size())

        def get_rows():
            return self.term.get_row_count()

        def get_columns():
            return self.term.get_column_count()

        self.bar_segments = [
            (lambda: f"{self.message}"),
            (lambda: f"<{self.term.get_font_scale():.0%}>"),
            (lambda: f"[{get_top()}-{get_bottom()}]"),
            (lambda: f"({int(self.adjustment.get_upper())})"),
            (lambda: f"|{get_rows()}x{get_columns()}|"),
        ]

    def update_bar(self):
        status_string = " ".join([f() for f in self.bar_segments])
        self.bar.set_placeholder_text(status_string)

    def echo(self, obj):
        self.message = str(obj)


if __name__ == "__main__":
    is_pager = os.path.basename(sys.argv[0]) == "viter-pager"
    child_argv = sys.argv[1:]
    if child_argv == []:
        child_argv = [os.environ["SHELL"]]
    else:
        child_argv.insert(0, "/usr/bin/env")
    win = Window(child_argv, is_pager)

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
