"""Shared heuristics for turning a flat list of text blocks into a Paper.

PDF and plain-text inputs carry no reliable structure, so we guess the
document's anatomy (title, abstract, keywords, sections, references) from
common academic conventions. DOCX uses its own style-aware path but still
reuses the reference/abstract splitting helpers here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from ..model import Paper, Author, Section, Reference


@dataclass
class Block:
    """A paragraph of source text plus an optional known heading level.

    ``level`` is None when the source could not tell us whether this block is a
    heading (the typical case for PDF/text); in that role-guessing falls to the
    regex heuristics below.
    """

    text: str
    level: Optional[int] = None  # 1/2/3 = heading; None = unknown; 0 = body


# Headings we treat as structural landmarks regardless of numbering.
ABSTRACT_RE = re.compile(r"^\s*abstract\b[\s:.\-—]*", re.IGNORECASE)
KEYWORDS_RE = re.compile(r"^\s*(keywords|key words|index terms)\b[\s:.\-—]*", re.IGNORECASE)
# A line that *is* the references heading on its own.
REFERENCES_RE = re.compile(r"^\s*(references|bibliography)\s*$", re.IGNORECASE)
# A line that *starts* the references section (heading may be glued to entries,
# e.g. "References [1] ..." when blank lines were lost during extraction).
REFERENCES_START_RE = re.compile(r"^\s*(references|bibliography)\b[\s:.\-—]*", re.IGNORECASE)

# Words that mark an affiliation rather than an author name.
AFFIL_KEYWORDS_RE = re.compile(
    r"\b(university|department|dept\.?|institute|laborator|school|college|"
    r"faculty|centre|center|academy|hospital|corporation|company|inc\.?|ltd\.?)",
    re.IGNORECASE,
)

# Numbered headings: "1.", "1.2", "I.", "II.", "A." etc. followed by a title.
NUM_HEADING_RE = re.compile(
    r"^\s*(?:"
    r"(?P<arabic>\d+(?:\.\d+)*)\.?|"          # 1  1.2  1.2.3
    r"(?P<roman>[IVXLC]+)\.|"                  # I.  II.
    r"(?P<alpha>[A-Z])\."                      # A.  B.
    r")\s+(?P<title>\S.*)$"
)

# A reference line usually starts with [n] or n. — used to split a refs blob.
REF_ITEM_RE = re.compile(r"^\s*(?:\[(\d+)\]|(\d+)\.)\s+")


def _heading_level_from_number(m: re.Match) -> int:
    if m.group("arabic"):
        return m.group("arabic").count(".") + 1
    return 1  # roman / alpha treated as top-level sections


def looks_like_heading(text: str) -> Optional[int]:
    """Return a guessed heading level for a line, or None if it's body text."""
    t = text.strip()
    if not t or len(t) > 120:
        return None
    m = NUM_HEADING_RE.match(t)
    if m:
        return _heading_level_from_number(m)
    # Short, title-cased or all-caps line with no terminal punctuation.
    if len(t.split()) <= 10 and not t.endswith((".", ",", ";", ":")):
        letters = [c for c in t if c.isalpha()]
        if letters and (t.isupper() or t.istitle()):
            return 1
    return None


def strip_heading_number(text: str) -> str:
    m = NUM_HEADING_RE.match(text.strip())
    if m:
        return m.group("title").strip()
    return text.strip()


def split_references(blob: str) -> List[Reference]:
    """Split a references section (one big string) into individual entries."""
    refs: List[Reference] = []
    # Prefer splitting on [n] markers if present.
    if re.search(r"\[\d+\]", blob):
        parts = re.split(r"(?=\[\d+\])", blob)
    else:
        parts = re.split(r"(?=^\s*\d+\.\s)", blob, flags=re.MULTILINE)
    for i, part in enumerate(p.strip() for p in parts if p.strip()):
        clean = REF_ITEM_RE.sub("", part).strip()
        refs.append(Reference(raw=clean, key=f"ref{i + 1}"))
    return refs


def _normalize_levels(sections, depth: int) -> None:
    for sec in sections:
        sec.level = depth
        _normalize_levels(sec.children, depth + 1)


def build_paper(blocks: List[Block]) -> Paper:
    """Assemble a Paper from ordered text blocks using academic conventions."""
    paper = Paper()
    blocks = [b for b in blocks if b.text and b.text.strip()]
    if not blocks:
        paper.warn("No readable text found in the source file.")
        return paper

    i = 0
    n = len(blocks)

    # --- Title: first substantial block -------------------------------------
    paper.title = blocks[0].text.strip()
    i = 1

    # --- Authors: blocks before the abstract that look like a name line ------
    # Author names are often title-cased and would be mistaken for a heading,
    # so we grab the first line after the title unconditionally; only an
    # explicit numbered/landmark heading stops collection.
    author_lines: List[str] = []
    while i < n and not ABSTRACT_RE.match(blocks[i].text):
        t = blocks[i].text.strip()
        if REFERENCES_RE.match(t) or NUM_HEADING_RE.match(t):
            break
        if author_lines and looks_like_heading(t):
            break
        author_lines.append(t)
        i += 1
        if len(author_lines) >= 4:  # don't swallow the whole intro if no abstract
            break
    if author_lines:
        # The first line holds the names, but an affiliation may be glued on
        # (e.g. "Jane Doe, John Roe Department of CS, Example University").
        first = author_lines[0]
        name_part, glued_affil = first, ""
        m_affil = AFFIL_KEYWORDS_RE.search(first)
        if m_affil:
            name_part = first[:m_affil.start()].rstrip(" ,;")
            glued_affil = first[m_affil.start():].strip()
        for nm in (x.strip() for x in re.split(r",| and ", name_part) if x.strip()):
            paper.authors.append(Author(name=nm))
        affil = " ".join([glued_affil] + author_lines[1:]).strip()
        if affil:
            for a in paper.authors:
                a.affiliation = affil

    # --- Abstract -----------------------------------------------------------
    if i < n and ABSTRACT_RE.match(blocks[i].text):
        abstract_text = ABSTRACT_RE.sub("", blocks[i].text).strip()
        i += 1
        # Continuation paragraphs until keywords or first section.
        while i < n:
            t = blocks[i].text.strip()
            if KEYWORDS_RE.match(t) or looks_like_heading(t) or REFERENCES_RE.match(t):
                break
            abstract_text += ("\n\n" if abstract_text else "") + t
            i += 1
        paper.abstract = abstract_text.strip()

    # --- Keywords -----------------------------------------------------------
    if i < n and KEYWORDS_RE.match(blocks[i].text):
        kw = KEYWORDS_RE.sub("", blocks[i].text).strip().rstrip(".")
        paper.keywords = [k.strip() for k in re.split(r"[,;]", kw) if k.strip()]
        i += 1

    # --- Body sections + references -----------------------------------------
    current: Optional[Section] = None
    parent_stack: List[Section] = []
    ref_mode = False
    ref_blob: List[str] = []

    while i < n:
        b = blocks[i]
        t = b.text.strip()
        i += 1

        if not ref_mode and REFERENCES_START_RE.match(t):
            ref_mode = True
            remainder = REFERENCES_START_RE.sub("", t).strip()
            if remainder:               # entries glued onto the heading line
                ref_blob.append(remainder)
            continue
        if ref_mode:
            ref_blob.append(t)
            continue

        level = b.level if (b.level and b.level > 0) else looks_like_heading(t)
        if level:
            sec = Section(title=strip_heading_number(t), level=level)
            if level == 1 or not parent_stack:
                paper.sections.append(sec)
                parent_stack = [sec]
            else:
                while parent_stack and parent_stack[-1].level >= level:
                    parent_stack.pop()
                if parent_stack:
                    parent_stack[-1].children.append(sec)
                else:
                    paper.sections.append(sec)
                parent_stack.append(sec)
            current = sec
        else:
            if current is None:
                # Body text before any heading -> synthetic Introduction.
                current = Section(title="Introduction", level=1)
                paper.sections.append(current)
                parent_stack = [current]
            current.paragraphs.append(t)

    if ref_blob:
        paper.references = split_references("\n".join(ref_blob))

    # Normalize heading levels to tree depth: whatever the source numbering was
    # (e.g. Markdown '##' for top sections), the outermost sections become 1.
    _normalize_levels(paper.sections, 1)

    if not paper.abstract:
        paper.warn("No abstract detected — check the output and add one if needed.")
    if not paper.sections:
        paper.warn("No sections detected — the body may need manual structuring.")
    if not paper.references:
        paper.warn("No references detected.")

    return paper
