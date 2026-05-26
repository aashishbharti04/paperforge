"""Parse LaTeX source into a Paper.

This is a pragmatic regex-based reader, not a full TeX engine. It understands
the common article macros (\\title, \\author, sectioning, abstract,
\\bibitem) which is enough to round-trip typical paper sources.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..model import Paper, Author, Section, Reference


def _strip_comments(src: str) -> str:
    # Remove % comments (but keep escaped \%).
    return re.sub(r"(?<!\\)%.*", "", src)


def _clean(s: str) -> str:
    s = re.sub(r"\\(textbf|textit|emph|texttt|underline)\{([^}]*)\}", r"\2", s)
    s = re.sub(r"\\,|\\ |~", " ", s)
    s = re.sub(r"\\\\", " ", s)
    s = re.sub(r"\{|\}", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _brace_arg(src: str, start: int):
    """Return the balanced {...} argument beginning at index ``start``."""
    assert src[start] == "{"
    depth = 0
    for i in range(start, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[start + 1:i], i + 1
    return src[start + 1:], len(src)


def parse_latex(path: str) -> Paper:
    src = _strip_comments(Path(path).read_text(encoding="utf-8", errors="replace"))
    paper = Paper()

    m = re.search(r"\\title\s*\{", src)
    if m:
        title, _ = _brace_arg(src, m.end() - 1)
        paper.title = _clean(title)

    if "\\IEEEauthorblockN" in src:
        # IEEEtran: names live in \IEEEauthorblockN{...}, affiliations in
        # \IEEEauthorblockA{...} that immediately follow.
        for bm in re.finditer(r"\\IEEEauthorblockN\s*\{", src):
            name, after = _brace_arg(src, bm.end() - 1)
            affil = ""
            am2 = re.match(r"\s*\\IEEEauthorblockA\s*\{", src[after:])
            if am2:
                affil, _ = _brace_arg(src, after + am2.end() - 1)
            paper.authors.append(Author(name=_clean(name),
                                        affiliation=_clean(affil)))
    else:
        for am in re.finditer(r"\\author\s*\{", src):
            arg, _ = _brace_arg(src, am.end() - 1)
            # Strip institute/thanks macros, then split on \and (or commas).
            arg = re.sub(r"\\(inst|thanks|institute)\s*\{[^}]*\}", "", arg)
            parts = re.split(r"\\and", arg) if "\\and" in arg else re.split(r",", arg)
            for nm in (_clean(x) for x in parts):
                if nm:
                    paper.authors.append(Author(name=nm))

    am = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", src, re.DOTALL)
    if am:
        paper.abstract = _clean(am.group(1))

    km = re.search(r"\\(keywords|IEEEkeywords)\s*\{", src)
    if km:
        arg, _ = _brace_arg(src, km.end() - 1)
        paper.keywords = [k.strip() for k in re.split(r"[,;]", _clean(arg)) if k.strip()]

    # Body: take text between \begin{document} ... \end{document} if present.
    dm = re.search(r"\\begin\{document\}(.*)\\end\{document\}", src, re.DOTALL)
    body = dm.group(1) if dm else src

    # Walk sectioning commands in order.
    level_map = {"section": 1, "subsection": 2, "subsubsection": 3}
    pattern = re.compile(r"\\(section|subsection|subsubsection)\*?\s*\{")
    parent_stack = []
    pos = 0
    last_sec = None
    for sm in pattern.finditer(body):
        # Text before this heading belongs to the previous section.
        gap = body[pos:sm.start()]
        if last_sec is not None:
            _append_paragraphs(last_sec, gap)
        title, after = _brace_arg(body, sm.end() - 1)
        level = level_map[sm.group(1)]
        sec = Section(title=_clean(title), level=level)
        if level == 1 or not parent_stack:
            paper.sections.append(sec)
            parent_stack = [sec]
        else:
            while parent_stack and parent_stack[-1].level >= level:
                parent_stack.pop()
            (parent_stack[-1].children if parent_stack else paper.sections).append(sec)
            parent_stack.append(sec)
        last_sec = sec
        pos = after
    if last_sec is not None:
        _append_paragraphs(last_sec, body[pos:])

    for bm in re.finditer(r"\\bibitem(?:\[[^\]]*\])?\s*\{([^}]*)\}(.*?)(?=\\bibitem|\\end\{thebibliography\}|$)", src, re.DOTALL):
        raw = _clean(bm.group(2))
        if raw:
            paper.references.append(Reference(raw=raw, key=bm.group(1)))

    if not paper.title:
        paper.title = Path(path).stem
    return paper


def _append_paragraphs(section: Section, text: str) -> None:
    # Drop common non-text environments before splitting into paragraphs.
    text = re.sub(r"\\begin\{(figure|table|equation|align|thebibliography)\*?\}.*?\\end\{\1\*?\}",
                  " ", text, flags=re.DOTALL)
    for para in re.split(r"\n\s*\n", text):
        cleaned = _clean(para)
        if cleaned:
            section.paragraphs.append(cleaned)
