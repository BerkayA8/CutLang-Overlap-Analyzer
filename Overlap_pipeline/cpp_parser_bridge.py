"""
cpp_parser_bridge.py
====================
Bridges the CutLang C++ parser to the Python overlap pipeline.

The C++ binary (adl_to_json) parses an ADL file using the Bison/Flex
grammar and emits the AST as JSON.  This module runs the binary, parses
the JSON, applies a grammar-reversal fix to restore source order of
statements, and returns the AST as plain Python dicts.

The downstream pipeline (ir_extractor.py) works directly on these dicts,
dispatching on the "tok" field — no intermediate Python classes needed.

Build the binary (requires bison, flex, g++, and all CutLang sources):

    bison parser.y && flex scanner.l
    g++ -std=c++17 main_json.cpp driver.cpp Scanner.cpp Parser.cpp \\
        external_functions.cpp semantic_checks.cpp cutlang_declares.cpp \\
        -o adl_to_json

Then either:
  - Place adl_to_json next to this file, OR
  - Set ADL_TO_JSON env var to its full path.

JSON node schema (tok field determines the structure):
------------------------------------------------------
  tok "INT"/"REAL"              → {"tok", "value"}
  tok "ID"                      → {"tok", "id", "alias", "dotop", "accessor", "type"}
  tok "COMPAREOP"/"LOGICOP"/
      "EXPROP"/"FACTOROP"       → {"tok", "op", "lhs", "rhs"}
  tok "FUNCTION"                → {"tok", "id", "params": [...]}
  tok "DEFINE"                  → {"tok", "id", "body"}
  tok "OBJECT"/"TRIGGER"        → {"tok", "id", "statements": [...]}
  tok "REGION"/"HISTOLIST"      → {"tok", "id", "statements": [...]}
  tok "SELECT"/"REJECT"/"TAKE"/
      "BIN"/"WEIGHT"/"TRIGGER"  → {"tok", "condition"}
  tok "ITE"                     → {"tok", "condition", "then", "else"}
  tok "HISTO"                   → {"tok", "id", "desc"}
"""

from __future__ import annotations
import json
import os
import subprocess
import tempfile
from typing import List


# ── Binary location ───────────────────────────────────────────────────────────

def _binary_path() -> str:
    """Return path to adl_to_json binary (env override or default sibling)."""
    env = os.environ.get("ADL_TO_JSON")
    if env:
        return env
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "adl_to_json")


def is_cpp_parser_available() -> bool:
    """True if the compiled C++ parser binary exists and is executable."""
    p = _binary_path()
    return os.path.isfile(p) and os.access(p, os.X_OK)


# ── Grammar reversal fix ─────────────────────────────────────────────────────

def _fix_statement_order(nodes: List[dict]) -> List[dict]:
    """
    Fix reversed statement order caused by the Bison grammar's
    right-recursive rules.

    The C++ parser's "takes" and "criteria" rules are right-recursive,
    which causes statements to be pushed to the shared `lists` vector
    in reverse order relative to their position in the source file.

    For OBJECT/TRIGGER nodes:
      TAKE statements appear first (correct order, usually just one),
      followed by SELECT/REJECT/BIN (reversed).
      Fix: keep TAKEs in place, reverse the rest.

    For REGION/HISTOLIST nodes:
      All statements arrive reversed. A full reversal restores order.
    """
    fixed = []
    for node in nodes:
        if node is None:
            continue
        tok = node.get("tok", "")

        if tok in ("OBJECT", "TRIGGER"):
            stmts = node.get("statements", [])
            takes = [s for s in stmts if s and s.get("tok", "").upper() == "TAKE"]
            others = [s for s in stmts if s and s.get("tok", "").upper() != "TAKE"]
            others.reverse()
            node = dict(node, statements=takes + others)

        elif tok in ("REGION", "HISTOLIST"):
            stmts = list(node.get("statements", []))
            stmts.reverse()
            node = dict(node, statements=stmts)

        fixed.append(node)
    return fixed


# ── Public entry points ───────────────────────────────────────────────────────

def parse_adl_file_cpp(adl_path: str) -> List[dict]:
    """
    Run adl_to_json on adl_path and return a list of AST node dicts.
    Raises FileNotFoundError if the binary is missing.
    Raises RuntimeError if parsing fails.
    """
    binary = _binary_path()
    if not is_cpp_parser_available():
        raise FileNotFoundError(
            f"adl_to_json not found at {binary!r}.\n"
            "Build it with (from the CutLang source directory):\n"
            "  bison parser.y && flex scanner.l\n"
            "  g++ -std=c++17 main_json.cpp driver.cpp Scanner.cpp Parser.cpp \\\n"
            "      external_functions.cpp semantic_checks.cpp cutlang_declares.cpp \\\n"
            "      -o adl_to_json\n"
            "Then place adl_to_json next to cpp_parser_bridge.py, or set "
            "the ADL_TO_JSON environment variable."
        )

    # The C++ Driver constructor searches for an adl/ subdirectory starting
    # from the current working directory.  When parsing temp files (e.g. from
    # parse_adl_text_cpp), the cwd may be unrelated to the binary location.
    # Fix: always run the binary with cwd set to its own directory, and pass
    # the ADL file as an absolute path so it can still be found.
    binary_dir = os.path.dirname(os.path.abspath(binary))
    abs_adl_path = os.path.abspath(adl_path)

    result = subprocess.run(
        [binary, abs_adl_path],
        capture_output=True,
        text=True,
        cwd=binary_dir,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"adl_to_json failed (exit {result.returncode}) on {adl_path!r}.\n"
            "Parser stderr:\n" + result.stderr
        )

    try:
        raw = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"adl_to_json produced invalid JSON for {adl_path!r}: {e}\n"
            "stdout was:\n" + result.stdout[:500]
        )

    return _fix_statement_order(raw)


def parse_adl_text_cpp(text: str, label: str = "<text>") -> List[dict]:
    """
    Write text to a temp file, parse it with the C++ binary, return dict list.
    """
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.adl', delete=False, prefix='adl_tmp_'
    ) as f:
        f.write(text)
        tmp_path = f.name
    try:
        return parse_adl_file_cpp(tmp_path)
    finally:
        os.unlink(tmp_path)


def load_adl_file_cpp(adl_path: str):
    """
    Parse with the C++ binary and return a fully-populated AnalysisIR.
    """
    from ir_extractor import extract_ir
    return extract_ir(parse_adl_file_cpp(adl_path), source_file=adl_path)


def load_adl_text_cpp(text: str, label: str = "<text>"):
    """
    Parse ADL text and return a fully-populated AnalysisIR.
    """
    from ir_extractor import extract_ir
    return extract_ir(parse_adl_text_cpp(text, label), source_file=label)
