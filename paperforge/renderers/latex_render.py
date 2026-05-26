"""Render a Paper to LaTeX for IEEE, Springer (LNCS), or Elsevier.

Each publisher provides an official document class:
  - IEEE     -> IEEEtran
  - Springer -> llncs  (Lecture Notes in Computer Science)
  - Elsevier -> elsarticle
The user must have these installed in their TeX distribution to compile. The
generated .tex is standard and self-contained otherwise.
"""

from __future__ import annotations

from ..model import Paper, Section

# Characters that must be escaped in LaTeX body text.
_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def esc(text: str) -> str:
    if not text:
        return ""
    out = []
    for ch in text:
        out.append(_ESCAPES.get(ch, ch))
    return "".join(out)


def _sections_tex(sections, lines):
    cmd = {1: "section", 2: "subsection", 3: "subsubsection"}
    for sec in sections:
        lines.append("\\%s{%s}" % (cmd.get(sec.level, "section"), esc(sec.title)))
        for p in sec.paragraphs:
            lines.append(esc(p))
            lines.append("")
        if sec.children:
            _sections_tex(sec.children, lines)


def _bibliography_tex(paper: Paper, lines, width="9"):
    if not paper.references:
        return
    lines.append("\\begin{thebibliography}{%s}" % width)
    for i, ref in enumerate(paper.references, 1):
        key = ref.key or f"ref{i}"
        lines.append("\\bibitem{%s} %s" % (key, esc(ref.raw)))
    lines.append("\\end{thebibliography}")


def _render_ieee(paper: Paper) -> str:
    L = []
    L.append("\\documentclass[conference]{IEEEtran}")
    L.append("\\IEEEoverridecommandlockouts")
    L.append("\\usepackage{cite,amsmath,amssymb,amsfonts,graphicx,textcomp,xcolor}")
    L.append("\\begin{document}")
    L.append("\\title{%s}" % esc(paper.title))
    if paper.authors:
        blocks = []
        for a in paper.authors:
            b = "\\IEEEauthorblockN{%s}" % esc(a.name)
            extra = []
            if a.affiliation:
                extra.append(esc(a.affiliation))
            if a.email:
                extra.append("\\\\ \\texttt{%s}" % esc(a.email))
            if extra:
                b += "\n\\IEEEauthorblockA{%s}" % " ".join(extra)
            blocks.append(b)
        L.append("\\author{%s}" % "\n\\and\n".join(blocks))
    L.append("\\maketitle")
    if paper.abstract:
        L.append("\\begin{abstract}\n%s\n\\end{abstract}" % esc(paper.abstract))
    if paper.keywords:
        L.append("\\begin{IEEEkeywords}\n%s\n\\end{IEEEkeywords}" %
                 esc(", ".join(paper.keywords)))
    _sections_tex(paper.sections, L)
    _bibliography_tex(paper, L)
    L.append("\\end{document}")
    return "\n".join(L) + "\n"


def _render_springer(paper: Paper) -> str:
    L = []
    L.append("\\documentclass[runningheads]{llncs}")
    L.append("\\usepackage{graphicx,amsmath,amssymb}")
    L.append("\\begin{document}")
    L.append("\\title{%s}" % esc(paper.title))
    if paper.authors:
        names = " \\and ".join(esc(a.name) for a in paper.authors)
        L.append("\\author{%s}" % names)
        affils = [a.affiliation for a in paper.authors if a.affiliation]
        inst = "\\and ".join(esc(x) for x in dict.fromkeys(affils)) or "Affiliation"
        L.append("\\institute{%s}" % inst)
    L.append("\\maketitle")
    if paper.abstract:
        kw = ""
        if paper.keywords:
            kw = "\n\\keywords{%s}" % (" \\and ".join(esc(k) for k in paper.keywords))
        L.append("\\begin{abstract}\n%s%s\n\\end{abstract}" % (esc(paper.abstract), kw))
    _sections_tex(paper.sections, L)
    if paper.references:
        L.append("\\begin{thebibliography}{8}")
        for i, ref in enumerate(paper.references, 1):
            L.append("\\bibitem{%s} %s" % (ref.key or f"ref{i}", esc(ref.raw)))
        L.append("\\end{thebibliography}")
    L.append("\\end{document}")
    return "\n".join(L) + "\n"


def _render_elsevier(paper: Paper) -> str:
    L = []
    L.append("\\documentclass[preprint,12pt]{elsarticle}")
    L.append("\\usepackage{graphicx,amsmath,amssymb,lineno}")
    L.append("\\journal{Journal Name}")
    L.append("\\begin{document}")
    L.append("\\begin{frontmatter}")
    L.append("\\title{%s}" % esc(paper.title))
    for idx, a in enumerate(paper.authors, 1):
        L.append("\\author{%s}" % esc(a.name))
        if a.affiliation:
            L.append("\\address{%s}" % esc(a.affiliation))
    if paper.abstract:
        L.append("\\begin{abstract}\n%s\n\\end{abstract}" % esc(paper.abstract))
    if paper.keywords:
        kw = " \\sep ".join(esc(k) for k in paper.keywords)
        L.append("\\begin{keyword}\n%s\n\\end{keyword}" % kw)
    L.append("\\end{frontmatter}")
    L.append("\\linenumbers")
    _sections_tex(paper.sections, L)
    if paper.references:
        L.append("\\begin{thebibliography}{00}")
        for i, ref in enumerate(paper.references, 1):
            L.append("\\bibitem{%s} %s" % (ref.key or f"ref{i}", esc(ref.raw)))
        L.append("\\end{thebibliography}")
    L.append("\\end{document}")
    return "\n".join(L) + "\n"


_RENDERERS = {
    "ieee": _render_ieee,
    "springer": _render_springer,
    "elsevier": _render_elsevier,
}


def render_latex(paper: Paper, publisher: str) -> str:
    publisher = publisher.lower()
    if publisher not in _RENDERERS:
        raise ValueError(f"Unknown publisher '{publisher}'. "
                         f"Choose from {sorted(_RENDERERS)}.")
    return _RENDERERS[publisher](paper)
