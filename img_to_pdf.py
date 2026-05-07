#!/usr/bin/env python3
"""
Image → PDF Converter

Drag image files directly into the window, or click "Browse".
Converts each JPG/PNG to a multi-page letter-size PDF (8.5" wide).
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog

from PIL import Image

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    _DND = True
except Exception:
    _DND = False

# ── Conversion ────────────────────────────────────────────────────────────────

DPI        = 150
PAGE_W_IN  = 8.5
PAGE_H_IN  = 11.0
MARGIN_IN  = 0.25
EXTS       = {".jpg", ".jpeg", ".png"}


def convert(input_path: str) -> tuple[str, int]:
    pw = int(PAGE_W_IN * DPI)
    ph = int(PAGE_H_IN * DPI)
    m  = int(MARGIN_IN  * DPI)
    cw, ch = pw - 2 * m, ph - 2 * m

    img = Image.open(input_path).convert("RGB")
    img = img.resize((cw, int(img.height * cw / img.width)), Image.LANCZOS)

    pages, y = [], 0
    while y < img.height:
        page = Image.new("RGB", (pw, ph), (255, 255, 255))
        page.paste(img.crop((0, y, cw, min(y + ch, img.height))), (m, m))
        pages.append(page)
        y += ch

    out = os.path.splitext(input_path)[0] + ".pdf"
    pages[0].save(out, save_all=True, append_images=pages[1:])
    return out, len(pages)


# ── GUI ───────────────────────────────────────────────────────────────────────

BG    = "#f0f0f0"
BLUE  = "#2563eb"
BLUE2 = "#1d4ed8"
GREEN = "#16a34a"
RED   = "#dc2626"
GRAY  = "#6b7280"

_BaseClass = TkinterDnD.Tk if _DND else tk.Tk


class App(_BaseClass):

    def __init__(self, preloaded: list[str]):
        super().__init__()
        self.title("Image → PDF Converter")
        self.geometry("560x520")
        self.minsize(480, 420)
        self.configure(bg=BG)
        self._files: list[str] = []
        self._build_ui()
        if preloaded:
            self._add_paths(preloaded)

    # ── layout ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        zone_top = ("Drop images here  •  or click to Browse"
                    if _DND else "Click to Browse for images")

        zone = tk.Frame(self, bg="#dbeafe", relief="groove", bd=2,
                        cursor="hand2", height=120)
        zone.pack(fill="x", padx=18, pady=(18, 6))
        zone.pack_propagate(False)
        tk.Label(zone, text=zone_top, bg="#dbeafe", fg=BLUE,
                 font=("Helvetica", 13, "bold")).pack(expand=True, pady=(20, 2))
        tk.Label(zone, text="JPG / PNG  •  multiple files OK",
                 bg="#dbeafe", fg=GRAY,
                 font=("Helvetica", 10), justify="center").pack()

        for w in (zone, *zone.winfo_children()):
            w.bind("<Button-1>", lambda _e: self._browse())
            if _DND:
                w.drop_target_register(DND_FILES)
                w.dnd_bind("<<Drop>>", self._on_drop)

        # Header row
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=18, pady=(6, 0))
        self._count_lbl = tk.Label(hdr, text="No files added", bg=BG, fg=GRAY,
                                   font=("Helvetica", 10))
        self._count_lbl.pack(side="left")
        for label, cmd in (("Clear all", self._clear),
                           ("Remove selected", self._remove_selected)):
            tk.Button(hdr, text=label, font=("Helvetica", 9), relief="flat",
                      bg=BG, fg=GRAY, cursor="hand2",
                      command=cmd).pack(side="right", padx=(0, 6))

        # File list
        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=18, pady=4)
        sb = tk.Scrollbar(frame)
        sb.pack(side="right", fill="y")
        self._lb = tk.Listbox(frame, yscrollcommand=sb.set,
                              selectmode="extended",
                              font=("Courier", 10), bg="white",
                              relief="groove", bd=1, activestyle="none")
        self._lb.pack(fill="both", expand=True)
        sb.config(command=self._lb.yview)

        # Bottom bar
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=18, pady=(4, 16))
        self._status = tk.StringVar(value="Ready — add images above.")
        tk.Label(bar, textvariable=self._status, bg=BG, fg=GRAY,
                 font=("Helvetica", 10), anchor="w").pack(side="left",
                                                           fill="x", expand=True)
        self._btn = tk.Button(bar, text="Convert All  →  PDF",
                              bg=BLUE, fg="white", relief="flat",
                              font=("Helvetica", 12, "bold"),
                              padx=14, pady=6, cursor="hand2",
                              command=self._start_conversion,
                              activebackground=BLUE2, activeforeground="white")
        self._btn.pack(side="right")

    # ── file management ──────────────────────────────────────────────────────

    def _add_paths(self, paths: list[str]):
        existing = set(self._files)
        added = 0
        for p in paths:
            p = p.strip().strip("{}")
            if p and os.path.splitext(p)[1].lower() in EXTS and p not in existing:
                self._files.append(p)
                self._lb.insert("end", os.path.basename(p))
                existing.add(p)
                added += 1
        self._refresh_count()
        if added:
            self._status.set(f"Added {added} file(s).")

    def _on_drop(self, event):
        self._add_paths(self.tk.splitlist(event.data))

    def _browse(self):
        paths = filedialog.askopenfilenames(
            title="Select images",
            filetypes=[("Images", "*.jpg *.jpeg *.png"), ("All files", "*.*")],
        )
        self._add_paths(list(paths))

    def _remove_selected(self):
        for i in reversed(self._lb.curselection()):
            self._files.pop(i)
            self._lb.delete(i)
        self._refresh_count()

    def _clear(self):
        self._files.clear()
        self._lb.delete(0, "end")
        self._refresh_count()
        self._status.set("Ready — add images above.")

    def _refresh_count(self):
        n = len(self._files)
        self._count_lbl.config(
            text=f"{n} file(s) queued" if n else "No files added")

    # ── conversion ───────────────────────────────────────────────────────────

    def _start_conversion(self):
        if not self._files:
            self._status.set("Add some images first.")
            return
        self._btn.config(state="disabled")
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        total, errors = len(self._files), []
        for i, path in enumerate(self._files):
            self._status.set(
                f"Converting {i + 1} / {total}  —  {os.path.basename(path)}")
            try:
                _out, pages = convert(path)
                self._lb.itemconfig(
                    i, fg=GREEN, selectforeground=GREEN,
                    text=f"✓  {os.path.basename(path)}  ({pages} pages)")
            except Exception as exc:
                errors.append(os.path.basename(path))
                self._lb.itemconfig(
                    i, fg=RED, selectforeground=RED,
                    text=f"✗  {os.path.basename(path)}  — {exc}")

        if errors:
            self._status.set(
                f"Done — {len(errors)} error(s): {', '.join(errors)}")
        else:
            self._status.set(
                f"All {total} PDF(s) saved next to the original images.")
        self._btn.config(state="normal")


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    preloaded = [p for p in sys.argv[1:]
                 if os.path.splitext(p)[1].lower() in EXTS]
    App(preloaded).mainloop()
