"""PaperForge: convert research papers into IEEE / Springer / Elsevier formats.

Public API:
    from paperforge import convert
    convert("draft.docx", publisher="ieee", out_format="docx", outdir="out/")
"""

from .model import Paper, Author, Section, Reference, Figure, Table
from .convert import convert, PUBLISHERS, OUTPUT_FORMATS
from .humanizer import (
    humanize_text, humanize_file, humanize_paragraphs, extract_paragraphs,
    Options as HumanizeOptions, Result as HumanizeResult, LEVELS,
)

__all__ = [
    "Paper",
    "Author",
    "Section",
    "Reference",
    "Figure",
    "Table",
    "convert",
    "PUBLISHERS",
    "OUTPUT_FORMATS",
    "humanize_text",
    "humanize_file",
    "humanize_paragraphs",
    "extract_paragraphs",
    "HumanizeOptions",
    "HumanizeResult",
    "LEVELS",
]

__version__ = "0.1.0"
