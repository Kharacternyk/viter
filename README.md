# viter
Viter is a terminal emulator written and expandable in Python. It features vim-like modes, keybindings and a status line. Viter is mainly inspired by [Termite](https://github.com/thestinger/termite) and uses GTK+ VTE widget as the backend (like Termite) though it doesn't require any patches to VTE ([unlike Termite](https://github.com/thestinger/termite#dependencies)).

# Installation
Viter requires GTK, VTE and Python with bindings for GTK. On Arch you may want to run this:
```bash
sudo pacman -Syu --needed python-gobject gtk3 vte3
```
Clone this repository. Run `viter.py` script to start Viter.
```bash
git clone https://github.com/Kharacternyk/viter
cd viter
python3 viter.py
```
You may want either to give `viter.py` executable rights and link it from somewhere in your PATH or create a .desktop file for it.

# Usage
Viter starts up in **NORMAL** mode where it behaves just like any other terminal emulator. Press `Ctrl+Shift+Space` to switch to **DETACHED** mode and then either:
- Press `j` or `k` to access the scrollback.
- Look at the bar at the bottom of window (you may configure it to show anything you want).
- Press `:` to access the one-line Python interpreter and interact with Viter.
- Press `y` or `Y` to copy some text.
- Use any of the other awesome features of Viter.
- Press `Escape` to switch back to **NORMAL** mode.

You got the spirit, right? Vim users should feel at home.

# Keybindings
- Navigating the scrollback
    - `j`: one line down
    - `k`: one line up
    - `J`: one page down
    - `K`: one page up
    - `g`: to the beginning
    - `G`: to the end
- Search
    - `/`+_pattern_+`Enter`: search for the first occurrence of _pattern_
    - `n`: to the next occurrence of previously set _pattern_
    - `N`: to the previous occurrence of previously set _pattern_
- Clipboard
    - `y`+_characters_+`Enter`: yank the last line that starts with the _characters_ (not counting whitespace)
    - `Y`: yank the top line
    - `Ctrl+Shift+C`/`Ctrl+Shift+V`: copy/paste in **NORMAL** mode
- Command line
    - `:`+_command_+`Enter`: execute the _command_ in the Python environment that executes the code of Viter (change the configuration of Viter on the fly)
    - `e`+_expression_+`Enter`: evaluate the Python _expression_ and print it in the bar

# Command interpreter
The bar at the bottom of the screen is shown when the user is in **DETACHED** mode. It shows some information, such as the total amount of the scrollback, while being unfocused.

After the user had typed some text into it and then pressed `Enter`, the entered text is executed by Viter using `exec` (a Python built-in).

To interact with the window one should use the `win` global variable. Actually, the only thing that some keybindings do is inserting the call to one of the methods of `win` in the bar, for example:
- `/` inserts `win.search("")` and places the cursor between "".
- `y` inserts `win.yank_line("")` and places the cursor between "".
- `e` inserts `win.echo()` and places the cursor between ().

`win` is an instance of `Window` class that inherits `Gtk.Window`. The calls to the inherited methods are also perfectly valid, for example:
- `win.set_title("Terminal")` to set the title of the window to _Terminal_.
- `win.close()` to close the window.
- `win.fullscreen()` to make the window fullscreen.

`win` has `term` field that returns an instance of `Vte.Terminal`. See the Gtk documentation on the `Gtk.Window` and `Vte.Terminal` to see what is possible to do with them. See the source of Viter to see what methods are additionally provided to that of `Gtk.Window`.

# Configuration
Viter looks for the configuration file in the following order:
- `$VITER_CONFIG`
- `$XDG_CONFIG_HOME/viter/viterrc.py`
- `$HOME/.config/viter/viterrc.py`

The first path that exists is read and then passed to `exec` function just before Viter enters the main loop. The configuration file must be a valid script that is executable by the same Python version that runs Viter.

An example of a valid configuration file is in this repository and is named `viterrc.py`. It is the configuration file that the author (@Kharacternyk) uses.
