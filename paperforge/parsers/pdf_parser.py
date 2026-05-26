"""Parse PDF into a Paper (best-effort).

PDFs encode layout, not structure, so we extract text and reassemble
paragraphs by font/line heuristics. Two-column and scanned PDFs are the
hardest cases; the resulting Paper always carries warnings so the user knows
to review the output.
"""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from ..model import Paper
from .heuristics import (
    Block, build_paper, looks_like_heading,
    ABSTRACT_RE, KEYWORDS_RE, REFERENCES_START_RE,
)


def _starts_new_block(line: str) -> bool:
    """True if a line should begin its own block rather than continue a paragraph.

    PDFs frequently drop the blank lines that separate a heading or landmark
    (Abstract/Keywords/References) from surrounding text, so we detect those
    structurally instead of relying on whitespace.
    """
    s = line.strip()
    return bool(
        ABSTRACT_RE.match(s) or KEYWORDS_RE.match(s)
        or REFERENCES_START_RE.match(s) or looks_like_heading(s)
    )


def _extract_lines(path: str):
    """Yield text lines across all pages, preserving reading order per page."""
    lines = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=1.5, y_tolerance=3) or ""
            for ln in text.split("\n"):
                lines.append(ln.rstrip())
    return lines


def _lines_to_paragraphs(lines):
    """Merge consecutive lines into paragraphs.

    A blank line starts a new paragraph. A line that does not end with
    sentence punctuation is assumed to continue onto the next line (typical of
    justified body text), so we join it with a space.
    """
    paragraphs = []
    buf = ""

    def flush():
        nonlocal buf
        if buf.strip():
            paragraphs.append(buf.strip())
        buf = ""

    for ln in lines:
        s = ln.strip()
        if not s:
            flush()
            continue
        if _starts_new_block(s):
            # Headings/landmarks (and the title, as the first such line) stand
            # alone: end the previous paragraph and emit this line by itself.
            flush()
            paragraphs.append(s)
            continue
        buf = (buf + " " + s) if buf else s
        # Flush when the line clearly ends a paragraph.
        if s.endswith((".", "?", "!")) and len(s) > 40:
            flush()
    flush()
    return paragraphs


def parse_pdf(path: str) -> Paper:
    lines = _extract_lines(path)
    if not any(l.strip() for l in lines):
        paper = Paper(title=Path(path).stem)
        paper.warn(
            "No selectable text found. This may be a scanned PDF — run OCR "
            "first, or supply a Word/text version."
        )
        return paper

    paragraphs = _lines_to_paragraphs(lines)
    blocks = [Block(text=p, level=None) for p in paragraphs]

    paper = build_paper(blocks)
    if not paper.title:
        paper.title = Path(path).stem
    paper.warn(
        "PDF parsing is approximate (layout is reconstructed). Please verify "
        "headings, math, figures, and references in the output."
    )
    return paper
