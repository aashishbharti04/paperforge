"""Intermediate representation of a research paper.

Every input parser converts a source file into a ``Paper`` object, and every
output renderer turns a ``Paper`` object into a publisher-formatted document.
Keeping this model in the middle means we never write an N x M matrix of
"format A -> format B" converters: N parsers + M renderers is enough.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Author:
    name: str
    affiliation: str = ""
    email: str = ""
    orcid: str = ""


@dataclass
class Section:
    """A section or subsection of the paper.

    ``level`` 1 = section, 2 = subsection, 3 = subsubsection. ``paragraphs`` is
    a list of plain-text paragraphs belonging directly to this heading.
    ``children`` holds nested subsections.
    """

    title: str
    level: int = 1
    paragraphs: List[str] = field(default_factory=list)
    children: List["Section"] = field(default_factory=list)


@dataclass
class Figure:
    caption: str = ""
    path: str = ""          # image file on disk, if extracted
    label: str = ""


@dataclass
class Table:
    caption: str = ""
    rows: List[List[str]] = field(default_factory=list)
    label: str = ""


@dataclass
class Reference:
    """A single bibliography entry.

    We keep the raw string (always) plus optional parsed fields. Renderers fall
    back to ``raw`` when structured fields are missing.
    """

    raw: str
    key: str = ""           # citation key for LaTeX (\bibitem)


@dataclass
class Paper:
    title: str = ""
    authors: List[Author] = field(default_factory=list)
    abstract: str = ""
    keywords: List[str] = field(default_factory=list)
    sections: List[Section] = field(default_factory=list)
    references: List[Reference] = field(default_factory=list)
    figures: List[Figure] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)

    # Free-form notes about parsing quality, shown to the user so they know
    # what to double-check after an automated conversion.
    warnings: List[str] = field(default_factory=list)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def author_names(self) -> str:
        return ", ".join(a.name for a in self.authors)

    def is_empty(self) -> bool:
        return not (self.title or self.abstract or self.sections)
