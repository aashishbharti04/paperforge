"""High-level conversion orchestrator tying parsers and renderers together."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .model import Paper
from .parsers import parse
from .renderers import render_latex, render_docx

PUBLISHERS = ["ieee", "springer", "elsevier"]
OUTPUT_FORMATS = ["docx", "tex", "pdf"]


@dataclass
class ConversionResult:
    paper: Paper
    outputs: List[str] = field(default_factory=list)   # produced file paths
    warnings: List[str] = field(default_factory=list)


def convert(input_path: str, publisher: str, out_formats=("docx",),
            outdir: str = ".") -> ConversionResult:
    """Convert ``input_path`` to ``publisher`` style in the given formats.

    out_formats may include 'docx', 'tex', and/or 'pdf'. 'pdf' implies 'tex'.
    """
    publisher = publisher.lower()
    if publisher not in PUBLISHERS:
        raise ValueError(f"publisher must be one of {PUBLISHERS}")
    out_formats = [f.lower() for f in out_formats]
    for f in out_formats:
        if f not in OUTPUT_FORMATS:
            raise ValueError(f"output format '{f}' must be one of {OUTPUT_FORMATS}")

    out_dir = Path(outdir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(input_path).stem
    base = out_dir / f"{stem}_{publisher}"

    paper = parse(input_path)
    result = ConversionResult(paper=paper, warnings=list(paper.warnings))

    if "docx" in out_formats:
        path = str(base.with_suffix(".docx"))
        render_docx(paper, publisher, path)
        result.outputs.append(path)

    need_tex = "tex" in out_formats or "pdf" in out_formats
    tex_path = None
    if need_tex:
        tex_path = str(base.with_suffix(".tex"))
        Path(tex_path).write_text(render_latex(paper, publisher), encoding="utf-8")
        if "tex" in out_formats:
            result.outputs.append(tex_path)

    if "pdf" in out_formats:
        from .compile_pdf import compile_pdf
        try:
            pdf_path = compile_pdf(tex_path)
            result.outputs.append(pdf_path)
        except RuntimeError as e:
            result.warnings.append(str(e))

    return result
