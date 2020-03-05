# viter
Viter is a terminal emulator written and expandable in Python. It features vim-like modes, keybindings and a status line. Viter is mainly inspired by [Termite](https://github.com/thestinger/termite) and uses GTK+ VTE widget as the backend (like Termite) though it doesn't require any patches to VTE ([unlike Termite](https://github.com/thestinger/termite#dependencies)).

# Usage
Viter starts up in **NORMAL** mode where it behaves just like any other terminal emulator. Press `Ctrl+Shift+Space` to switch to **DETACHED** mode and then either:
- Press `j` or `k` to access the scrollback.
- Look at the bar at the bottom of window (you may configure it to show anything you want).
- Press `:` to access the one-line Python interpreter and interact with Viter.
- Press `y` or `Y` to copy some text.
- Use any of the other awesome features of Viter.
- Press `Escape` to switch back to **NORMAL** mode.

You got the spirit, right? Vim users should feel at home.

# Features
- [x] Navigating the scrollback
    - `j`: one line down
    - `k`: one line up
    - `J`: one page down
    - `K`: one page up
    - `g`: to the beginning
    - `G`: to the end
- [x] Search
    - `/`+_pattern_+`Enter`: search for the first occurrence of _pattern_
    - `n`: to the next occurrence of previously set _pattern_
    - `N`: to the previous occurrence of previously set _pattern_
- [ ] Clipboard
    - [x] `y`: yank the line that starts with the given characters (not counting whitespace)
    - [x] `Y`: yank the top line
    - [ ] yank the search result
    - [ ] copy/paste in **NORMAL** mode
- [x] Command line
    - `:` + _command_ + `Enter`: execute the _command_ in the Python environment that executes the code of Viter (change the configuration of Viter on the fly)
