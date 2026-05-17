#!/usr/bin/env python3
"""
adl_overlap_check.py
====================
Command-line tool to check overlap between two or more ADL analysis files.

Requires the C++ parser binary (adl_to_json) built from the CutLang
Bison/Flex grammar.  The Python fallback parser (adl_parser.py) has been
removed; this tool now uses only the authoritative C++ parser.

Usage
-----
  python adl_overlap_check.py  analysis1.adl  analysis2.adl  [analysis3.adl ...]
  python adl_overlap_check.py  *.adl  --html report.html
  python adl_overlap_check.py  a.adl b.adl  --verbose  --catalogue

Options
  --html FILE      write an HTML report (includes catalogue if --catalogue given)
  -v, --verbose    show per-variable cut details in terminal output
  --catalogue      print the OverlapObject catalogue for each analysis

Exit codes
  0  no overlap detected
  1  overlap detected
"""

import argparse, sys, os
sys.path.insert(0, os.path.dirname(__file__))

from cpp_parser_bridge import is_cpp_parser_available, load_adl_file_cpp
from overlap_checker import compare_many
from catalogue import build_catalogue, render_catalogue_terminal
from report import render_terminal, save_html


def main():
    ap = argparse.ArgumentParser(
        description="Check overlap between CutLang ADL analysis files."
    )
    ap.add_argument("files", nargs="+", metavar="FILE",
                    help="Two or more ADL files to compare")
    ap.add_argument("--html", metavar="OUTPUT_HTML",
                    help="Save an HTML report (with embedded catalogue)")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="Show per-variable cut details in terminal output")
    ap.add_argument("--catalogue", action="store_true",
                    help="Print the OverlapObject catalogue for each analysis")
    args = ap.parse_args()

    if len(args.files) < 2:
        ap.error("At least two ADL files are required.")

    # Verify C++ parser is available (no Python fallback)
    if not is_cpp_parser_available():
        print("ERROR: C++ parser binary (adl_to_json) not found.", file=sys.stderr)
        print("Build it with:", file=sys.stderr)
        print("  bison parser.y && flex scanner.l", file=sys.stderr)
        print("  g++ -std=c++17 main_json.cpp driver.cpp Scanner.cpp Parser.cpp \\",
              file=sys.stderr)
        print("      external_functions.cpp semantic_checks.cpp "
              "cutlang_declares.cpp -o adl_to_json", file=sys.stderr)
        sys.exit(2)

    print("  Parser: C++ (adl_to_json)")

    analyses = []
    catalogues = []
    for path in args.files:
        print(f"  Loading: {path}")
        try:
            ir = load_adl_file_cpp(path)
            analyses.append(ir)
            cat = build_catalogue(ir)
            catalogues.append(cat)
            print(f"    objects: {list(ir.objects.keys())}")
            print(f"    defines: {list(ir.defines_raw.keys())}")
            print(f"    regions: {list(ir.regions.keys())}")
        except Exception as e:
            print(f"    ERROR: {e}", file=sys.stderr)
            import traceback; traceback.print_exc()
            sys.exit(1)

    # Print catalogues
    if args.catalogue:
        for cat in catalogues:
            print(render_catalogue_terminal(cat))

    # Run comparisons
    reports = compare_many(analyses)

    # Terminal output
    print(render_terminal(reports, verbose=args.verbose))

    # HTML output
    if args.html:
        save_html(reports, args.html, catalogues=catalogues)


if __name__ == "__main__":
    main()
