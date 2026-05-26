"""Compile a .tex file to .pdf using whatever TeX engine is installed.

PDF output is optional: if no LaTeX engine is found we skip it gracefully and
tell the user how to install one. We try latexmk first (handles reruns for
references), then fall back to pdflatex run twice.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def tex_engine_available() -> str | None:
    for engine in ("latexmk", "pdflatex", "tectonic"):
        if shutil.which(engine):
            return engine
    return None


def compile_pdf(tex_path: str) -> str:
    """Compile ``tex_path`` to PDF. Returns the .pdf path, or raises."""
    tex = Path(tex_path)
    workdir = tex.parent
    engine = tex_engine_available()
    if not engine:
        raise RuntimeError(
            "No LaTeX engine found. Install one to enable PDF output:\n"
            "  Windows : MiKTeX (https://miktex.org) or TeX Live\n"
            "  Then re-run. The .tex file has already been generated."
        )

    if engine == "latexmk":
        cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", tex.name]
        runs = [cmd]
    elif engine == "tectonic":
        runs = [["tectonic", tex.name]]
    else:  # pdflatex needs two passes to resolve references
        cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name]
        runs = [cmd, cmd]

    last = None
    for cmd in runs:
        last = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True)

    pdf = tex.with_suffix(".pdf")
    if not pdf.exists():
        tail = (last.stdout or "")[-1500:] if last else ""
        raise RuntimeError(
            "LaTeX compilation failed (the document class may be missing from "
            "your TeX install, e.g. IEEEtran/llncs/elsarticle).\n"
            "Install the missing class via your TeX package manager.\n\n"
            f"--- compiler output (tail) ---\n{tail}"
        )
    return str(pdf)
