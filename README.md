# PaperForge

Convert research papers from **any common format** (Word, PDF, LaTeX, Markdown,
plain text) into **IEEE**, **Springer (LNCS)**, or **Elsevier** publication
format — as an editable **Word `.docx`** and/or **LaTeX `.tex` → PDF**.

Useful for PhD students and researchers submitting the same manuscript to
different publishers, each of which mandates its own layout.

---

## What it does

```
                 ┌─────────────┐        ┌──────────────────┐
 .docx           │             │        │  IEEE            │
 .pdf    ──►     │  Parsers    │  ──►   │  Springer (LNCS) │  ──►  .docx
 .tex            │  ↓          │        │  Elsevier        │       .tex
 .txt / .md      │  Paper model│        │  (templates)     │       .pdf
                 └─────────────┘        └──────────────────┘
```

The tool extracts your paper's **structure** (title, authors, affiliation,
abstract, keywords, sections/subsections, references) into a single internal
model, then re-renders that model into the publisher format you choose. Adding a
new input format or a new publisher only means adding one parser or one renderer
— not rewriting everything.

## Important: this is an assistant, not magic

Automatic extraction is **best-effort**, especially for PDFs (which store layout,
not structure) and scanned documents. The tool does the tedious 90% and flags
what to review. **Always proofread the output** before submitting — check
headings, math, figures, tables, and references. LaTeX output for these three
publishers relies on their official document classes (`IEEEtran`, `llncs`,
`elsarticle`), which gives the most faithful result.

---

## Installation

Requires **Python 3.9+**.

```bash
pip install -r requirements.txt
```

For **PDF output** you additionally need a LaTeX engine installed:

- **Windows:** [MiKTeX](https://miktex.org) or TeX Live
- **macOS:** MacTeX
- **Linux:** TeX Live (`sudo apt install texlive-full`)

`.docx`, `.tex`, and parsing all work **without** LaTeX.

---

## Usage

### Desktop app (GUI)

```bash
python -m paperforge
```

Pick a file, choose a publisher and output formats, click **Convert**.

### Command line

```bash
# Word draft -> IEEE Word document
python -m paperforge draft.docx --publisher ieee --format docx

# PDF -> Springer LaTeX + compiled PDF, into ./out
python -m paperforge paper.pdf -p springer -f tex pdf -o out/

# Markdown notes -> Elsevier Word + LaTeX
python -m paperforge notes.md -p elsevier -f docx tex
```

| Option | Values | Default |
|--------|--------|---------|
| `-p`, `--publisher` | `ieee`, `springer`, `elsevier` | `ieee` |
| `-f`, `--format` | `docx`, `tex`, `pdf` (one or more) | `docx` |
| `-o`, `--outdir` | output folder | `.` |

Output files are named `<inputname>_<publisher>.<ext>`.

### As a library

```python
from paperforge import convert

result = convert("draft.docx", publisher="ieee",
                 out_formats=["docx", "tex"], outdir="out")
print(result.outputs)    # list of generated file paths
print(result.warnings)   # things to double-check
```

---

## Supported formats

**Input:** `.docx`, `.pdf`, `.tex` / `.latex`, `.txt`, `.md` / `.markdown`
*(legacy `.doc` is not supported — save as `.docx` first).*

**Output:** `.docx` (Word), `.tex` (LaTeX), `.pdf` (compiled from LaTeX).

**Publishers:** IEEE (`IEEEtran`, two-column conference style), Springer LNCS
(`llncs`), Elsevier (`elsarticle`).

---

## Project layout

```
paperforge/
  model.py            # the intermediate Paper representation
  parsers/            # input  -> Paper   (docx, pdf, latex, text + heuristics)
  renderers/          # Paper  -> output  (latex_render, docx_render)
  compile_pdf.py      # LaTeX -> PDF (auto-detects latexmk/pdflatex/tectonic)
  convert.py          # orchestration
  cli.py / gui.py     # interfaces
samples/              # an example paper to try
```

## Roadmap / known limitations

- Figures and equations are not yet carried through from PDF/Word inputs.
- Two-column PDF extraction can interleave text; prefer the Word source when available.
- Reference parsing keeps entries verbatim (no per-field BibTeX yet).
- More publisher templates (ACM, IET, MDPI) can be added as new renderers.

Contributions welcome.

## License

MIT
