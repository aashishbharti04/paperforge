"""Output renderers: Paper model -> publisher-formatted document."""

from .latex_render import render_latex
from .docx_render import render_docx

__all__ = ["render_latex", "render_docx"]
