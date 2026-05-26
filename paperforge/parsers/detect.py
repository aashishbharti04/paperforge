"""Detect a source file's format and dispatch to the right parser."""

from __future__ import annotations

from pathlib import Path

from ..model import Paper

EXT_MAP = {
    ".docx": "docx",
    ".pdf": "pdf",
    ".tex": "latex",
    ".latex": "latex",
    ".txt": "text",
    ".md": "text",
    ".markdown": "text",
}


def detect_format(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext in EXT_MAP:
        return EXT_MAP[ext]
    if ext == ".doc":
        raise ValueError(
            "Legacy .doc is not supported. Please save as .docx and try again."
        )
    raise ValueError(f"Unsupported file type '{ext}'. Supported: {sorted(EXT_MAP)}")


def parse(path: str) -> Paper:
    """Parse any supported file into a Paper model."""
    if not Path(path).exists():
        raise FileNotFoundError(path)
    fmt = detect_format(path)
    if fmt == "docx":
        from .docx_parser import parse_docx
        return parse_docx(path)
    if fmt == "pdf":
        from .pdf_parser import parse_pdf
        return parse_pdf(path)
    if fmt == "latex":
        from .latex_parser import parse_latex
        return parse_latex(path)
    from .text_parser import parse_text
    return parse_text(path)
