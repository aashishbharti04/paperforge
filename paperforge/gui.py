"""Tkinter desktop GUI for PaperForge.

Two tabs:
  * Format Converter — file -> IEEE / Springer / Elsevier (.docx/.tex/.pdf)
  * AI -> Human       — rewrite stiff/AI-sounding text into plainer language,
                        on pasted text, one paragraph, or a whole file.
"""

from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .convert import convert, PUBLISHERS, OUTPUT_FORMATS
from . import humanizer


class ConverterTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.input_var = tk.StringVar()
        self.outdir_var = tk.StringVar(value=os.path.abspath("output"))
        self.publisher_var = tk.StringVar(value="ieee")
        self.fmt_vars = {f: tk.BooleanVar(value=(f == "docx")) for f in OUTPUT_FORMATS}
        self._build()

    def _build(self):
        pad = {"padx": 10, "pady": 6}

        frm_in = ttk.LabelFrame(self, text="1. Input paper (docx / pdf / tex / txt / md)")
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
        self.log = tk.Text(frm_log, height=10, wrap="word", state="disabled")
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
        except Exception as e:
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


class HumanizerTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.mode_var = tk.StringVar(value="paste")     # paste | file
        self.file_var = tk.StringVar()
        self.level_var = tk.StringVar(value="medium")
        self.para_var = tk.StringVar(value="All paragraphs")
        self.opt_vars = {
            "simplify_vocab": tk.BooleanVar(value=True),
            "remove_filler": tk.BooleanVar(value=True),
            "use_contractions": tk.BooleanVar(value=False),
            "split_sentences": tk.BooleanVar(value=True),
        }
        self._paragraphs = []
        self._build()

    def _build(self):
        pad = {"padx": 10, "pady": 6}

        frm_mode = ttk.LabelFrame(self, text="1. What to humanize")
        frm_mode.pack(fill="x", **pad)
        ttk.Radiobutton(frm_mode, text="Paste text", variable=self.mode_var,
                        value="paste", command=self._sync_mode).pack(
            side="left", padx=12, pady=6)
        ttk.Radiobutton(frm_mode, text="From a file", variable=self.mode_var,
                        value="file", command=self._sync_mode).pack(
            side="left", padx=12, pady=6)

        # File row
        self.frm_file = ttk.Frame(self)
        self.frm_file.pack(fill="x", padx=10)
        ttk.Entry(self.frm_file, textvariable=self.file_var).pack(
            side="left", fill="x", expand=True, padx=2, pady=4)
        ttk.Button(self.frm_file, text="Browse…", command=self._browse_file).pack(
            side="left", padx=2)
        ttk.Button(self.frm_file, text="Load paragraphs",
                   command=self._load_paragraphs).pack(side="left", padx=2)
        self.para_combo = ttk.Combobox(self.frm_file, textvariable=self.para_var,
                                       state="readonly", width=30,
                                       values=["All paragraphs"])
        self.para_combo.pack(side="left", padx=2)
        self.para_combo.bind("<<ComboboxSelected>>", lambda e: self._show_selected())

        # Input text
        frm_in = ttk.LabelFrame(self, text="Input text")
        frm_in.pack(fill="both", expand=True, **pad)
        self.input_text = tk.Text(frm_in, height=7, wrap="word")
        self.input_text.pack(fill="both", expand=True, padx=8, pady=8)

        # Options
        frm_lvl = ttk.LabelFrame(self, text="2. Strength & options")
        frm_lvl.pack(fill="x", **pad)
        for lvl in humanizer.LEVELS:
            ttk.Radiobutton(frm_lvl, text=lvl.capitalize(), variable=self.level_var,
                            value=lvl, command=self._apply_level).pack(
                side="left", padx=10, pady=4)
        labels = {"simplify_vocab": "Simplify words", "remove_filler": "Remove filler",
                  "use_contractions": "Contractions", "split_sentences": "Split long sentences"}
        for key, lab in labels.items():
            ttk.Checkbutton(frm_lvl, text=lab, variable=self.opt_vars[key]).pack(
                side="left", padx=8, pady=4)

        ttk.Button(self, text="Humanize", command=self._humanize).pack(pady=6)

        # Output
        frm_out = ttk.LabelFrame(self, text="Result (review before using)")
        frm_out.pack(fill="both", expand=True, **pad)
        self.output_text = tk.Text(frm_out, height=8, wrap="word")
        self.output_text.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        bar = ttk.Frame(frm_out)
        bar.pack(fill="x", padx=8, pady=(0, 8))
        self.status_lbl = ttk.Label(bar, text="")
        self.status_lbl.pack(side="left")
        ttk.Button(bar, text="Save result…", command=self._save).pack(side="right")

        self._sync_mode()

    # --- option helpers ---
    def _apply_level(self):
        opts = humanizer.Options.for_level(self.level_var.get())
        self.opt_vars["simplify_vocab"].set(opts.simplify_vocab)
        self.opt_vars["remove_filler"].set(opts.remove_filler)
        self.opt_vars["use_contractions"].set(opts.use_contractions)
        self.opt_vars["split_sentences"].set(opts.split_sentences)

    def _current_options(self):
        return humanizer.Options(
            simplify_vocab=self.opt_vars["simplify_vocab"].get(),
            remove_filler=self.opt_vars["remove_filler"].get(),
            use_contractions=self.opt_vars["use_contractions"].get(),
            split_sentences=self.opt_vars["split_sentences"].get(),
        )

    def _sync_mode(self):
        state = "normal" if self.mode_var.get() == "file" else "disabled"
        for child in self.frm_file.winfo_children():
            try:
                child.configure(state=state)
            except tk.TclError:
                pass

    # --- file handling ---
    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Select a file",
            filetypes=[("Documents", "*.docx *.pdf *.tex *.txt *.md *.markdown"),
                       ("All files", "*.*")])
        if path:
            self.file_var.set(path)

    def _load_paragraphs(self):
        path = self.file_var.get().strip()
        if not path:
            messagebox.showwarning("No file", "Choose a file first.")
            return
        try:
            self._paragraphs = humanizer.extract_paragraphs(path)
        except Exception as e:
            messagebox.showerror("Could not read file", str(e))
            return
        previews = ["All paragraphs"] + [
            f"Para {i+1}: {p[:50]}…" for i, p in enumerate(self._paragraphs)]
        self.para_combo.configure(values=previews)
        self.para_var.set("All paragraphs")
        self._show_selected()

    def _show_selected(self):
        if self.para_var.get() == "All paragraphs":
            text = "\n\n".join(self._paragraphs)
        else:
            idx = self.para_combo.current() - 1
            text = self._paragraphs[idx] if 0 <= idx < len(self._paragraphs) else ""
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", text)

    # --- run ---
    def _humanize(self):
        if self.mode_var.get() == "file" and self._paragraphs:
            self._show_selected()
        text = self.input_text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("No text", "Enter or load some text first.")
            return
        result = humanizer.humanize_text(text, self.level_var.get(),
                                         self._current_options())
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", result.text)
        n = result.changes
        self.status_lbl.configure(
            text=("LLM backend used." if n < 0 else f"{n} change(s) made."))

    def _save(self):
        text = self.output_text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Nothing to save", "Run Humanize first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("Word", "*.docx")])
        if not path:
            return
        if path.lower().endswith(".docx"):
            from docx import Document
            doc = Document()
            for para in text.split("\n\n"):
                doc.add_paragraph(para)
            doc.save(path)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        messagebox.showinfo("Saved", f"Saved to:\n{path}")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PaperForge")
        self.geometry("720x680")
        self.minsize(660, 600)
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        nb.add(ConverterTab(nb), text="Format Converter")
        nb.add(HumanizerTab(nb), text="AI → Human")


def launch():
    App().mainloop()


if __name__ == "__main__":
    launch()
