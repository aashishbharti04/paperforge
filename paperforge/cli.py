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


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--gui" in argv or not argv:
        from .gui import launch
        launch()
        return 0

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
