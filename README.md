# viter
Viter is a terminal emulator written and expandable in Python. It features vim-like modes, keybindings and a status line. Viter is mainly inspired by [Termite](https://github.com/thestinger/termite) and uses GTK+ VTE widget as the backend (like Termite) though it doesn't require any patches to VTE ([unlike Termite](https://github.com/thestinger/termite#dependencies)).

# Usage
Viter starts up in **NORMAL** mode where it behaves just like any other terminal emulator. Press Ctrl+Space to switch to **DETACHED** mode and then either:
- Press `j` or `k` to access the scrollback.
- Look at the bar at the bottom of window (you may configure it to show anything you want).
- Press `:` to access the one-line Python interpreter and interact with Viter.
- Press `y` or `Y` to copy some text.
- Use any of the other awesome features of Viter.
- Press Ctrl+Space to switch back to **NORMAL** mode.

You got the spirit, right? Vim users should feel themselves like at home.
