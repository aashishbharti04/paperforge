"""Command-line interface for PaperForge.

Examples:
    py -m paperforge draft.docx --publisher ieee --format docx
    py -m paperforge paper.pdf -p springer -f tex pdf -o out/
    py -m paperforge notes.md -p elsevier -f docx tex
"""

from __future__ import annotations

import argparse
import sys

from .convert import convert, PUBLISHERS, OUTPUT_FORMATS
from . import humanizer


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="paperforge",
        description="Convert papers (docx/pdf/tex/txt/md) into IEEE, Springer, "
                    "or Elsevier format as .docx and/or LaTeX/PDF.",
    )
    p.add_argument("input", help="Path to the source paper file.")
    p.add_argument("-p", "--publisher", choices=PUBLISHERS, default="ieee",
                   help="Target publisher format (default: ieee).")
    p.add_argument("-f", "--format", nargs="+", choices=OUTPUT_FORMATS,
                   default=["docx"], dest="formats",
                   help="One or more output formats (default: docx). "
                        "'pdf' requires a LaTeX install.")
    p.add_argument("-o", "--outdir", default=".",
                   help="Output directory (default: current directory).")
    p.add_argument("--gui", action="store_true",
                   help="Launch the desktop GUI instead of converting.")
    return p


def build_humanize_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="paperforge humanize",
        description="Rewrite stiff / AI-sounding text into plainer language. "
                    "Works on a file (all paragraphs or one), or literal --text.",
    )
    p.add_argument("input", nargs="?", help="File to humanize (omit if using --text).")
    p.add_argument("--text", help="Humanize this literal text instead of a file.")
    p.add_argument("-l", "--level", choices=humanizer.LEVELS, default="medium")
    p.add_argument("--scope", default="all",
                   help="'all' (default) or a 1-based paragraph number.")
    p.add_argument("-o", "--outdir", default=".",
                   help="Output folder for file mode (default: current dir).")
    # Fine-grained overrides (otherwise derived from --level).
    p.add_argument("--no-vocab", action="store_true", help="Don't simplify words.")
    p.add_argument("--filler", action="store_true", help="Remove filler words.")
    p.add_argument("--contractions", action="store_true", help="Use contractions.")
    p.add_argument("--split", action="store_true", help="Split long sentences.")
    return p


def _options_from_args(args):
    base = humanizer.Options.for_level(args.level)
    if args.no_vocab:
        base.simplify_vocab = False
    if args.filler:
        base.remove_filler = True
    if args.contractions:
        base.use_contractions = True
    if args.split:
        base.split_sentences = True
    return base


def humanize_main(argv) -> int:
    args = build_humanize_parser().parse_args(argv)
    opts = _options_from_args(args)

    if args.text is not None:
        result = humanizer.humanize_text(args.text, args.level, opts)
        print(result.text)
        if result.changes >= 0:
            print(f"\n[{result.changes} change(s)]", file=sys.stderr)
        return 0

    if not args.input:
        print("Error: provide a file path or --text.", file=sys.stderr)
        return 1

    scope = "all"
    if args.scope != "all":
        try:
            scope = int(args.scope) - 1  # 1-based -> 0-based
        except ValueError:
            print("Error: --scope must be 'all' or a paragraph number.",
                  file=sys.stderr)
            return 1
    try:
        outputs, results = humanizer.humanize_file(
            args.input, scope=scope, level=args.level, outdir=args.outdir,
            options=opts)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    total = sum(r.changes for r in results if r.changes > 0)
    print(f"Humanized {len(results)} paragraph(s), {total} total edit(s).")
    print("Wrote:")
    for o in outputs:
        print(f"  - {o}")
    print("\nReview the output before using it.")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--gui" in argv or not argv:
        from .gui import launch
        launch()
        return 0

    if argv[0] == "humanize":
        return humanize_main(argv[1:])
    if argv[0] == "convert":   # explicit subcommand is optional
        argv = argv[1:]

    args = build_parser().parse_args(argv)
    try:
        result = convert(args.input, args.publisher, args.formats, args.outdir)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Parsed: {result.paper.title!r}")
    print(f"  authors:    {len(result.paper.authors)}")
    print(f"  sections:   {len(result.paper.sections)}")
    print(f"  references: {len(result.paper.references)}")
    print(f"\nGenerated {len(result.outputs)} file(s) for '{args.publisher}':")
    for o in result.outputs:
        print(f"  - {o}")
    if result.warnings:
        print("\nNotes / warnings:")
        for w in result.warnings:
            print(f"  ! {w.splitlines()[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
