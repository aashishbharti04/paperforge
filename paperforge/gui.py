"""Tkinter desktop GUI for PaperForge.

A single window: pick a file, choose a publisher and output formats, click
Convert. Conversion runs on a worker thread so the window stays responsive,
and results/warnings are shown in a log box.
"""

from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .convert import convert, PUBLISHERS, OUTPUT_FORMATS


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PaperForge — Paper to IEEE / Springer / Elsevier")
        self.geometry("680x560")
        self.minsize(620, 520)

        self.input_var = tk.StringVar()
        self.outdir_var = tk.StringVar(value=os.path.abspath("output"))
        self.publisher_var = tk.StringVar(value="ieee")
        self.fmt_vars = {f: tk.BooleanVar(value=(f == "docx")) for f in OUTPUT_FORMATS}

        self._build()

    def _build(self):
        pad = {"padx": 10, "pady": 6}

        frm_in = ttk.LabelFrame(self, text="1. Input paper")
        frm_in.pack(fill="x", **pad)
        ttk.Entry(frm_in, textvariable=self.input_var).pack(
            side="left", fill="x", expand=True, padx=8, pady=8)
        ttk.Button(frm_in, text="Browse…", command=self._browse_input).pack(
            side="left", padx=8)

        frm_pub = ttk.LabelFrame(self, text="2. Target publisher")
        frm_pub.pack(fill="x", **pad)
        for pub in PUBLISHERS:
            ttk.Radiobutton(frm_pub, text=pub.capitalize(),
                            variable=self.publisher_var, value=pub).pack(
                side="left", padx=12, pady=8)

        frm_fmt = ttk.LabelFrame(self, text="3. Output formats")
        frm_fmt.pack(fill="x", **pad)
        labels = {"docx": "Word (.docx)", "tex": "LaTeX (.tex)", "pdf": "PDF (needs LaTeX)"}
        for f in OUTPUT_FORMATS:
            ttk.Checkbutton(frm_fmt, text=labels[f],
                            variable=self.fmt_vars[f]).pack(
                side="left", padx=12, pady=8)

        frm_out = ttk.LabelFrame(self, text="4. Output folder")
        frm_out.pack(fill="x", **pad)
        ttk.Entry(frm_out, textvariable=self.outdir_var).pack(
            side="left", fill="x", expand=True, padx=8, pady=8)
        ttk.Button(frm_out, text="Browse…", command=self._browse_outdir).pack(
            side="left", padx=8)

        self.convert_btn = ttk.Button(self, text="Convert", command=self._convert)
        self.convert_btn.pack(pady=8)

        frm_log = ttk.LabelFrame(self, text="Result")
        frm_log.pack(fill="both", expand=True, **pad)
        self.log = tk.Text(frm_log, height=12, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True, padx=8, pady=8)

    def _browse_input(self):
        path = filedialog.askopenfilename(
            title="Select a paper",
            filetypes=[("Papers", "*.docx *.pdf *.tex *.txt *.md *.markdown"),
                       ("All files", "*.*")])
        if path:
            self.input_var.set(path)

    def _browse_outdir(self):
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.outdir_var.set(path)

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _convert(self):
        inp = self.input_var.get().strip()
        if not inp:
            messagebox.showwarning("Missing input", "Please choose an input file.")
            return
        formats = [f for f in OUTPUT_FORMATS if self.fmt_vars[f].get()]
        if not formats:
            messagebox.showwarning("No output", "Select at least one output format.")
            return
        self.convert_btn.configure(state="disabled")
        self._log(f"Converting {os.path.basename(inp)} → {self.publisher_var.get()} "
                  f"({', '.join(formats)}) …")
        threading.Thread(
            target=self._worker,
            args=(inp, self.publisher_var.get(), formats, self.outdir_var.get()),
            daemon=True).start()

    def _worker(self, inp, publisher, formats, outdir):
        try:
            result = convert(inp, publisher, formats, outdir)
        except Exception as e:  # surface any parser/renderer error to the user
            self.after(0, lambda: self._finish_error(str(e)))
            return
        self.after(0, lambda: self._finish_ok(result))

    def _finish_ok(self, result):
        self._log(f"Title: {result.paper.title}")
        self._log(f"Authors: {len(result.paper.authors)}  "
                  f"Sections: {len(result.paper.sections)}  "
                  f"References: {len(result.paper.references)}")
        self._log("Generated files:")
        for o in result.outputs:
            self._log(f"   • {o}")
        for w in result.warnings:
            self._log(f"   ! {w.splitlines()[0]}")
        self._log("Done.\n")
        self.convert_btn.configure(state="normal")
        try:
            if result.outputs and sys.platform == "win32":
                os.startfile(os.path.dirname(os.path.abspath(result.outputs[0])))
        except Exception:
            pass

    def _finish_error(self, msg):
        self._log(f"ERROR: {msg}")
        messagebox.showerror("Conversion failed", msg)
        self.convert_btn.configure(state="normal")


def launch():
    App().mainloop()


if __name__ == "__main__":
    launch()
