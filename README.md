# PaperForge

Convert research papers from **any common format** (Word, PDF, LaTeX, Markdown,
plain text) into **IEEE**, **Springer (LNCS)**, or **Elsevier** publication
format — as an editable **Word `.docx`** and/or **LaTeX `.tex` → PDF**.

Useful for PhD students and researchers submitting the same manuscript to
different publishers, each of which mandates its own layout.

It also includes an **AI → Human** text rewriter that turns stiff, robotic
prose into plainer, more natural language — on pasted text, a single
paragraph, or a whole file. (See [Humanize text](#humanize-text-ai--human).)

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

## Humanize text (AI → Human)

Rewrites inflated, "AI-sounding" writing into plainer language by swapping
puffed-up vocabulary (`utilize` → `use`, `a plethora of` → `many`), dropping
empty filler phrases (`it is important to note that …`), and — at stronger
settings — using contractions and splitting overlong sentences.

**Honest scope:** this is a *writing-improvement* aid for polishing your **own**
drafts. It is **not** an "AI-detector bypass," uses no hidden-character tricks,
and makes no guarantee about evading detectors. Always read the result before
using it.

Three strength levels: **light** (vocabulary only), **medium** (+ filler
removal, sentence splitting), **strong** (+ contractions). Every option can also
be toggled individually.

### In the GUI

Open the app and switch to the **AI → Human** tab. Paste text *or* load a file
and pick **All paragraphs** or a single paragraph from the dropdown, choose a
strength, click **Humanize**, then **Save result…**.

### On the command line

```bash
# Rewrite a snippet directly
python -m paperforge humanize --text "It is important to note that we utilize numerous methods." -l medium

# Whole file -> writes <name>_humanized.txt and .docx
python -m paperforge humanize draft.docx -l strong -o out/

# Just the 3rd paragraph of a file
python -m paperforge humanize draft.docx --scope 3
```

| Option | Meaning |
|--------|---------|
| `--text "…"` | Humanize literal text and print it (instead of a file). |
| `-l`, `--level` | `light`, `medium` (default), or `strong`. |
| `--scope` | `all` (default) or a 1-based paragraph number. |
| `--contractions`, `--filler`, `--split`, `--no-vocab` | Override individual options. |

### Higher quality with an LLM (optional)

The rule engine is deterministic and offline. For stronger rewriting you can
plug in a model:

```python
from paperforge import humanizer
humanizer.set_llm_backend(lambda text, level: my_model_rewrite(text))
# now humanize_text / the GUI / the CLI use your backend
```

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
  humanizer.py        # AI -> human text rewriter (offline rule engine + LLM hook)
  convert.py          # orchestration
  cli.py / gui.py     # interfaces (gui.py has Converter + AI->Human tabs)
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
