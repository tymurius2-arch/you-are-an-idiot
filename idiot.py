"""YOU ARE AN IDIOT! - harmless prank, inspired by the old 2000s meme.

Opens a pile of flashing windows. The STOP IT button does nothing.
After a few seconds everything closes by itself and an "error" says you are free.

Emergency exit (just in case): press Ctrl+Shift+Q in any window.
Custom music: put a file named music.wav next to this script (Windows).
"""
import math
import os
import random
import struct
import sys
import tempfile
import tkinter as tk
import wave
from tkinter import messagebox

TEXT = "YOU ARE AN IDIOT!"
BUTTON = "STOP IT"
FREE_MSG = "you are free this time...."
MAX_WINDOWS = 24          # hard cap, never more than this
SPAWN_EVERY_MS = 350      # delay between new windows
TOTAL_MS = 120000         # 2 minutes, then everything ends
FLASH_MS = 120
SHAKE_MS = 60
WIN_W, WIN_H = 360, 200

COLORS = [
    ("#ff0000", "#ffff00"), ("#0000ff", "#ffffff"), ("#00ff00", "#ff00ff"),
    ("#000000", "#ff0000"), ("#ffff00", "#0000ff"), ("#ff00ff", "#00ffff"),
    ("#ffffff", "#000000"), ("#ff8800", "#003366"),
]

try:
    import winsound
except ImportError:  # not Windows: no sound, everything else works
    winsound = None


def make_music(path):
    """Generate a short, annoying 8-bit loop (original melody)."""
    rate = 22050
    notes = [523, 659, 784, 659, 523, 659, 784, 1047,
             988, 784, 659, 784, 988, 784, 659, 523]
    frames = bytearray()
    for i, f in enumerate(notes):
        dur = 0.11
        n = int(rate * dur)
        for t in range(n):
            # square wave with fade-out so notes are distinct
            env = 1 - t / n
            v = 1 if math.sin(2 * math.pi * f * t / rate) > 0 else -1
            frames += struct.pack("<h", int(v * env * 9000))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))


def start_music():
    if winsound is None:
        return None
    custom = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music.wav")
    path = custom
    if not os.path.exists(custom):
        path = os.path.join(tempfile.gettempdir(), "idiot_loop.wav")
        make_music(path)
    try:
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
    except Exception:
        return None
    return path


def stop_music():
    if winsound is not None:
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass


class IdiotWindow:
    def __init__(self, root, index):
        self.win = tk.Toplevel(root)
        self.win.title(TEXT)
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)
        self.win.protocol("WM_DELETE_WINDOW", lambda: None)  # X does nothing

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        self.x = random.randint(0, max(0, sw - WIN_W))
        self.y = random.randint(0, max(0, sh - WIN_H - 40))
        self.win.geometry(f"{WIN_W}x{WIN_H}+{self.x}+{self.y}")

        self.bg, self.fg = random.choice(COLORS)
        self.label = tk.Label(
            self.win, text=TEXT, font=("Impact", 30, "bold"),
            bg=self.bg, fg=self.fg, wraplength=WIN_W - 20,
        )
        self.label.pack(expand=True, fill="both")
        # STOP IT button: clicking does absolutely nothing
        self.btn = tk.Button(
            self.win, text=BUTTON, font=("Arial", 14, "bold"),
            command=lambda: None, bg="#dddddd",
        )
        self.btn.pack(side="bottom", pady=8, ipadx=20)
        self.win.bind("<Control-Shift-Q>", lambda e: root.event_generate("<<Emergency>>"))
        self.win.configure(bg=self.bg)

        self.alive = True
        self.flash()
        self.shake()

    def flash(self):
        if not self.alive:
            return
        self.bg, self.fg = random.choice(COLORS)
        self.label.configure(bg=self.bg, fg=self.fg)
        self.win.configure(bg=self.bg)
        self.win.after(FLASH_MS, self.flash)

    def shake(self):
        if not self.alive:
            return
        dx, dy = random.randint(-8, 8), random.randint(-8, 8)
        self.win.geometry(f"{WIN_W}x{WIN_H}+{self.x + dx}+{self.y + dy}")
        self.win.after(SHAKE_MS, self.shake)

    def close(self):
        self.alive = False
        try:
            self.win.destroy()
        except tk.TclError:
            pass


def main():
    root = tk.Tk()
    root.withdraw()
    windows = []
    finished = {"done": False}

    def finish(_event=None):
        if finished["done"]:
            return
        finished["done"] = True
        stop_music()
        for w in windows:
            w.close()
        root.bell()
        messagebox.showerror("ERROR", FREE_MSG, parent=root)
        root.destroy()

    def spawn():
        if finished["done"]:
            return
        if len(windows) < MAX_WINDOWS:
            windows.append(IdiotWindow(root, len(windows)))
            root.after(SPAWN_EVERY_MS, spawn)

    root.bind("<<Emergency>>", finish)
    start_music()
    spawn()
    root.after(TOTAL_MS, finish)
    root.mainloop()


if __name__ == "__main__":
    if "--help" in sys.argv:
        print(__doc__)
    else:
        main()
