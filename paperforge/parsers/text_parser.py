"""Parse plain text and Markdown into a Paper."""

from __future__ import annotations

import re
from pathlib import Path

from ..model import Paper
from .heuristics import Block, build_paper


def _markdown_level(line: str):
    m = re.match(r"^(#{1,6})\s+(.*)$", line)
    if m:
        return len(m.group(1)), m.group(2).strip()
    return None, None


def parse_text(path: str) -> Paper:
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    blocks = []

    # Split on blank lines into paragraphs, but treat Markdown headings as
    # their own single-line blocks with a known level.
    for chunk in re.split(r"\n\s*\n", raw):
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        lvl, title = _markdown_level(chunk.strip())
        if lvl is not None and "\n" not in chunk.strip():
            blocks.append(Block(text=title, level=lvl))
        else:
            # A chunk may itself contain a leading markdown heading line.
            lines = chunk.split("\n")
            head_lvl, head_title = _markdown_level(lines[0].strip())
            if head_lvl is not None:
                blocks.append(Block(text=head_title, level=head_lvl))
                body = "\n".join(lines[1:]).strip()
                if body:
                    blocks.append(Block(text=body, level=0))
            else:
                blocks.append(Block(text=chunk.replace("\n", " ").strip(), level=0))

    paper = build_paper(blocks)
    if not paper.title:
        paper.title = Path(path).stem
    return paper
