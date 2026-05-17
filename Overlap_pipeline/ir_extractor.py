"""
ir_extractor.py  (v5 — dict-based)
====================================
Extracts an AnalysisIR from a list of AST node dicts produced by the
C++ parser bridge (cpp_parser_bridge.py).

All AST nodes are plain Python dicts with a "tok" field that determines
the node type.  No intermediate Python AST classes are used.

Node schema (mirrors the C++ ast.hpp / main_json.cpp output):
  {"tok": "INT"|"REAL",  "value": <number>}
  {"tok": "ID",          "id", "alias", "dotop", "accessor": [...], "type"}
  {"tok": "COMPAREOP"|"LOGICOP"|"EXPROP"|"FACTOROP",  "op", "lhs", "rhs"}
  {"tok": "FUNCTION",    "id", "params": [...]}
  {"tok": "DEFINE",      "id", "body"}
  {"tok": "OBJECT"|"TRIGGER",  "id", "statements": [...]}
  {"tok": "REGION", "id", "statements": [...]}
  {"tok": "SELECT"|"REJECT"|"TAKE"|"BIN"|"WEIGHT"|"CMD"|"COMMAND",
                         "condition"}
  {"tok": "ITE",         "condition", "then", "else"}
  {"tok": "HISTO",       "id", "desc"}
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from cpp_parser_bridge import parse_adl_file_cpp as parse_adl_file
from cpp_parser_bridge import parse_adl_text_cpp as parse_adl_text
from expr_node import (
    ExprNode, FuncNode, IdNode,
    build_expr_node,
)

# ── Dict helpers ──────────────────────────────────────────────────────────────
# Convenience accessors for AST node dicts.

def _tok(node) -> str:
    """Return the tok field of a node, or empty string for None/non-dict."""
    if isinstance(node, dict):
        return node.get("tok", "")
    return ""

def _is_num(node) -> bool:
    return _tok(node) in ("INT", "REAL")

def _is_var(node) -> bool:  # variable
    return _tok(node) == "ID"

def _is_bin(node) -> bool:  # binary operator
    return _tok(node) in ("COMPAREOP", "LOGICOP", "EXPROP", "FACTOROP")

def _is_func(node) -> bool:
    return _tok(node) == "FUNCTION"

def _is_ite(node) -> bool:  # if-then-else expression
    return _tok(node) == "ITE"

def _is_define(node) -> bool:
    return _tok(node) == "DEFINE"

def _is_object(node) -> bool:
    return _tok(node) in ("OBJECT", "TRIGGER")

def _is_region(node) -> bool:
    return _tok(node) == "REGION"

def _is_command(node) -> bool:
    return _tok(node) in ("SELECT", "REJECT", "TAKE") ## "BIN", "WEIGHT", "TRIGGER", "CMD", "COMMAND" ???

# Dict constructors for building resolved expression trees
def _make_var(id: str, alias: str = "", dotop: str = "",
              accessor: list = None, type: str = "") -> dict:
    return {"tok": "ID", "id": id, "alias": alias, "dotop": dotop,
            "accessor": accessor or [], "type": type}

def _make_func(id: str, params: list = None) -> dict:
    return {"tok": "FUNCTION", "id": id, "params": params or []}

def _make_bin(tok: str, op: str, lhs: dict, rhs: dict) -> dict:
    return {"tok": tok, "op": op, "lhs": lhs, "rhs": rhs}

def _make_ite(condition: dict, then: dict, else_: dict = None) -> dict:
    return {"tok": "ITE", "condition": condition, "then": then, "else": else_}


# ─────────────────────────────────────────────────────────────────────────────
# Builtin physics object types
# ─────────────────────────────────────────────────────────────────────────────
# Must stay in sync with three sources in the C++ parser:
#   1. driver.cpp  fillTypeTable()       — maps names to particle type enums
#   2. driver.cpp  fillParentObjectsMap() — registers parent particle objects
#   3. ext_objs.txt                       — loaded by loadFromLibraries(),
#                                           uppercased and added as PARENT objects

BUILTIN_OBJECTS: Set[str] = {
    # From fillTypeTable  (all keys, uppercased)
    "ELE", "ELECTRON",
    "MUO", "MUON", "MUOLIKE", "MUONLIKE",
    "TAU",
    "PHO", "PHOTON",
    "JET", "QCJET",
    "FJET",
    "TRUTH",
    "TRACK", "TRK",
    "METLV", "MET", "PUREV",
    "ELELIKE", "ELECTRONLIKE",
    "COMB", "COMBO",
    "CONSTIT",
    # From ext_objs.txt  (uppercased by loadFromLibraries)
    "LEPTON",
    "FATJET",
    "AK4JET", "AK8JET",
    "BJET",
    "MISSINGET",
    "MHT",
    "TAPPIONTRACKS",
}

_CANONICAL: Dict[str, str] = {
    "ELECTRON": "ELE",
    "MUON":     "MUO",
    "PHOTON":   "PHO",
    "TRACK":    "TRK",
    "FATJET":   "FJET",
    "FJET":     "FJET",
    "MISSINGET":"MET",
    "PUREV":    "METLV",
    "MUOLIKE":  "MUO",
    "MUONLIKE": "MUO",
    "ELELIKE":  "ELE",
    "ELECTRONLIKE": "ELE",
    "COMBO":    "COMB",
    "AK4JET":   "JET",
    "AK8JET":   "FJET",
    "BJET":     "JET",
}

def canonicalise(name: str) -> str:
    up = name.upper()
    return _CANONICAL.get(up, up)

# Two distinct operator-rewrite tables. They are NOT interchangeable —
# they encode different transformations and disagree on ``==`` and ``!=``.
#
# SWAP_OP — what the operator becomes when the LHS and RHS are swapped:
#     ``5 > x``  rewritten as  ``x < 5``
# Equality and inequality are symmetric under swap, so they are fixed
# points: ``==`` ↔ ``==``, ``!=`` ↔ ``!=``.
#
# NEGATE_OP — what the operator becomes when the predicate is logically
# negated:
#     NOT (x > 5)  ≡  x <= 5
# Equality flips to inequality and vice versa: ``==`` ↔ ``!=``.
#
# ``~=`` (chi-square minimization) is a special operator that does not
# carry an interval-arithmetic meaning. It is treated as a fixed point
# in both tables: symmetric under LHS/RHS swap, and we keep it as ``~=``
# under negation as well — the overlap pipeline routes ``~=`` cuts
# through a dedicated equality-of-cut decision rather than interval
# logic, so a literal "negation" has no useful interpretation. Keeping
# it as a fixed point ensures ``effective_op()`` round-trips cleanly
# whether or not the cut originated from a REJECT statement.
SWAP_OP: Dict[str, str] = {
    ">=":"<=","<=":">=",">":"<","<":">","==":"==","!=":"!=","~=":"~="
}
NEGATE_OP: Dict[str, str] = {
    ">=":"<", "<=":">", ">":"<=", "<":">=", "==":"!=", "!=":"==", "~=":"~="
}

# ─────────────────────────────────────────────────────────────────────────────
# CutStructure  — the central representation of one cut
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CutStructure:
    """
    Represents one scalar cut extracted from a SELECT/REJECT statement.

    A cut is a predicate of the form ``LHS op THRESHOLD``. Three fields
    capture that directly:

      lhs        – the LHS expression as a structural ``ExprNode`` tree.
                   Built and canonicalised at extraction time so that two
                   cuts with structurally-equivalent LHSes (commutativity,
                   associativity, parenthesisation, integer-vs-float
                   spelling) produce identical trees and compare EQUAL.
      op         – comparison operator (>, >=, <, <=, ==, !=).
      threshold  – numeric RHS literal.

    The remaining fields carry provenance metadata — they describe where
    the cut came from rather than what it says:

      negated      – True when from a REJECT statement; flips ``op`` when
                     read via ``effective_op()``.
      define_chain – ordered define/object substitution trail.
      source_kind  – "cut" | "object" | "inherited".
      source_name  – name of the object/define this cut originated in.

    Backwards-compatibility projections
    -----------------------------------
    The legacy fields ``func_chain``, ``collection``, ``resolved_collection``,
    ``accessor`` are preserved as read-only properties delegating to ``lhs``.
    They return the same values they used to for simple cuts (single
    ``func(collection)`` LHS) and honestly return empty for composite LHSes
    where there is no single primary collection. ``display_name()`` uses
    the LHS's ``pretty()`` for composite cuts and the compact
    ``func_chain(collection)`` form for simple cuts.
    """
    lhs: ExprNode
    op: str
    threshold: float
    negated: bool = False
    define_chain: List[str] = field(default_factory=list)
    source_kind: str = "cut"
    source_name: str = ""
    # ``_resolved_collection`` is set by the post-extraction resolution
    # pass (see DefineResolver._resolve_collections_in_tree). It maps the
    # user-written collection name (which lives on the LHS tree) to its
    # canonical built-in or parent-object name. We keep it as a stored
    # mutable field — separate from the immutable LHS tree — so the
    # resolution pass can fill it in without rebuilding the tree. For
    # composite LHSes it stays empty, since there's no single primary
    # collection to resolve.
    _resolved_collection: str = ""

    # ── Backwards-compatibility projections ──────────────────────────────
    # These properties exist so existing call sites in the catalogue,
    # report renderer, and overlap pipeline keep working without churn.
    # New code should read ``lhs`` directly.

    @property
    def func_chain(self) -> str:
        return self.lhs.outer_func_chain()

    @property
    def collection(self) -> str:
        return self.lhs.primary_collection()

    @property
    def resolved_collection(self) -> str:
        # Returns the post-resolution collection name if the resolution
        # pass set one; otherwise falls back to the LHS-derived name.
        # This preserves the legacy semantics where unresolved cuts read
        # the same as their LHS collection.
        if self._resolved_collection:
            return self._resolved_collection
        return self.lhs.primary_collection()

    @resolved_collection.setter
    def resolved_collection(self, value: str):
        self._resolved_collection = value

    @property
    def accessor(self) -> Tuple[int, ...]:
        return self.lhs.primary_accessor()

    # ── Operator handling ────────────────────────────────────────────────

    def effective_op(self) -> str:
        return NEGATE_OP[self.op] if self.negated else self.op

    def flipped(self) -> "CutStructure":
        # Goal: produce a CutStructure whose ``effective_op()`` equals
        # the original's. We toggle ``negated`` and transform ``op`` via
        # the *same* table that ``effective_op`` uses (NEGATE_OP), so
        # the two transforms cancel: effective_op stays put.
        return CutStructure(
            lhs=self.lhs,             # ExprNode is frozen — share by ref
            op=NEGATE_OP[self.op], threshold=self.threshold,
            negated=not self.negated,
            define_chain=list(self.define_chain),
            source_kind=self.source_kind, source_name=self.source_name,
            _resolved_collection=self._resolved_collection,
        )

    # ── Rendering ────────────────────────────────────────────────────────

    def display_name(self) -> str:
        """Compact for simple cuts, faithful for composite or multi-arg cuts.

        A "simple" cut is one whose LHS is exactly ``func(IdNode)`` with
        a single argument — the legacy shape. For these we emit the
        existing ``func_chain(collection)`` form so the catalogue and
        report look unchanged. Anything else gets the verbatim
        ``lhs.pretty()`` rendering:

        * multi-arg functions (``dR(a, b)``) — pretty shows every arg
          including their accessors, so ``dR(JET[0:1], MET[0])`` and
          ``dR(JET[0:2], MET[0])`` render distinctly;
        * composite LHS (``size(ELE) + size(MUO) == 0``) — pretty shows
          the arithmetic structure;
        * function over composite (``sqrt(2*pT*MET*(1-cos(...)))``) —
          pretty shows the inner expression.
        """
        if (isinstance(self.lhs, FuncNode)
                and len(self.lhs.args) == 1
                and isinstance(self.lhs.args[0], IdNode)):
            inner: IdNode = self.lhs.args[0]
            return f"{self.lhs.func_chain}({inner.collection})"
        if isinstance(self.lhs, IdNode):
            return self.lhs.collection
        return self.lhs.pretty()

    def __repr__(self):
        neg = "NOT " if self.negated else ""
        chain = " → ".join(self.define_chain)
        suffix = f"  [{chain}]" if self.define_chain else ""
        return f"{neg}{self.display_name()} {self.op} {self.threshold}{suffix}"


# ─────────────────────────────────────────────────────────────────────────────
# ConstraintExpr  — boolean structure of a single source-level cut
# ─────────────────────────────────────────────────────────────────────────────
# A SELECT/REJECT statement may decompose into a tree of AND/OR over atomic
# comparisons. Flattening to a list discards that structure and breaks any
# cut whose per-axis acceptance is a union of intervals — for instance
# ``reject abs(eta) [] 1.44 1.56`` which by De Morgan means
# ``abs(eta) < 1.44 OR abs(eta) > 1.56``.
#
# ConstraintExpr captures the structure exactly. Three concrete kinds:
#
#   ConstraintLeaf  — a single CutStructure (atomic comparison).
#   ConstraintAnd   — conjunction of ConstraintExprs.
#   ConstraintOr    — disjunction of ConstraintExprs.
#
# Negation is pushed to the leaves at extraction time (negation-normal
# form), so we never need a Not node — the leaf's CutStructure carries
# its own ``negated`` flag and reads its effective op via effective_op().
# Empty And/Or are well-defined: And([]) ≡ everything, Or([]) ≡ nothing,
# matching set-algebra convention.
#
# The overlap pipeline evaluates per-axis IntervalSets from these
# expressions; see overlap_checker.evaluate_axis_for_expr.

@dataclass(frozen=True)
class ConstraintExpr:
    """Abstract base for the AND/OR/Leaf hierarchy."""
    pass


@dataclass(frozen=True)
class ConstraintLeaf(ConstraintExpr):
    """An atomic comparison. The CutStructure carries the LHS, op,
    threshold, and negation state."""
    cut: CutStructure


@dataclass(frozen=True)
class ConstraintAnd(ConstraintExpr):
    """Conjunction. Empty conjunction is the identity (everything is
    accepted)."""
    children: Tuple[ConstraintExpr, ...]


@dataclass(frozen=True)
class ConstraintOr(ConstraintExpr):
    """Disjunction. Empty disjunction is unsatisfiable (nothing accepted)."""
    children: Tuple[ConstraintExpr, ...]


def constraint_expr_leaves(expr: ConstraintExpr) -> List[CutStructure]:
    """Flatten a ConstraintExpr into a list of leaf CutStructures.

    Used for backwards compatibility with code that pre-dates the
    structured form and only knows about flat constraint lists. The
    returned list discards AND/OR structure, so any code using it for
    interval evaluation will continue to mishandle OR-shaped cuts —
    callers should migrate to the structured evaluator where possible.
    """
    if isinstance(expr, ConstraintLeaf):
        return [expr.cut]
    if isinstance(expr, (ConstraintAnd, ConstraintOr)):
        out: List[CutStructure] = []
        for ch in expr.children:
            out.extend(constraint_expr_leaves(ch))
        return out
    return []


def retag_constraint_expr(
    expr: ConstraintExpr,
    source_kind: str,
    source_name: str,
) -> ConstraintExpr:
    """Rebuild a ConstraintExpr with leaves tagged ``source_kind`` /
    ``source_name``. Used when copying object-level cuts into the
    inheritance dependency tree, where each leaf needs to carry
    provenance pointing at the object it came from rather than the
    original ``"cut"`` source.

    The expression's boolean structure (AND/OR shape) is preserved.
    Only the leaf CutStructures change; ExprNodes, ops, thresholds,
    and negation flags are shared by reference (they're immutable).
    """
    if isinstance(expr, ConstraintLeaf):
        c = expr.cut
        new_cut = CutStructure(
            lhs=c.lhs,
            op=c.op, threshold=c.threshold, negated=c.negated,
            define_chain=list(c.define_chain),
            source_kind=source_kind, source_name=source_name,
            _resolved_collection=c._resolved_collection,
        )
        return ConstraintLeaf(new_cut)
    if isinstance(expr, ConstraintAnd):
        return ConstraintAnd(tuple(
            retag_constraint_expr(ch, source_kind, source_name)
            for ch in expr.children
        ))
    if isinstance(expr, ConstraintOr):
        return ConstraintOr(tuple(
            retag_constraint_expr(ch, source_kind, source_name)
            for ch in expr.children
        ))
    return expr


# ─────────────────────────────────────────────────────────────────────────────
# Raw constraint extraction from AST dicts
# ─────────────────────────────────────────────────────────────────────────────

def _normalise_accessor(acc) -> Tuple[int, ...]:
    """
    Normalise an AST `accessor` list to a canonical tuple.
    `[]`     → ()           (whole collection)
    `[i]`    → (i, i+1)     (single index ≡ one-element slice)
    `[a, b]` → (a, b)       (slice as written)
    Anything else is returned as-is (preserves forward-compatibility).
    """
    if not acc:
        return ()
    if len(acc) == 1:
        i = int(acc[0])
        return (i, i + 1)
    return tuple(int(x) for x in acc)


def _extract_func_chain_and_collection(
    expr: dict,
) -> Optional[Tuple[str, str, Tuple[int, ...]]]:
    """
    Recursively extract (func_chain, collection, accessor) from a function
    expression dict. Accessor is the innermost ID's slice in normalised form.
    Returns None if the expression is not a recognisable function application.
    """
    if _is_func(expr):
        fname = expr["id"].lower()
        params = expr.get("params", [])
        if params:
            inner = params[0]
            inner_result = _extract_func_chain_and_collection(inner)
            if inner_result is not None:
                inner_chain, collection, accessor = inner_result
                chain = f"{fname}∘{inner_chain}" if inner_chain else fname
                return (chain, collection, accessor)
            if _is_var(inner):
                return (fname, inner["id"],
                        _normalise_accessor(inner.get("accessor", [])))
        return (fname, "", ())
    if _is_var(expr):
        return ("", expr["id"],
                _normalise_accessor(expr.get("accessor", [])))
    return None


def _build_constraint_expr(
    expr: dict,
    negated: bool,
    chain: List[str],
) -> Optional[ConstraintExpr]:
    """Build a ConstraintExpr (negation-normal form) from the AST.

    Returns None when the expression has no extractable constraint
    content — caller should treat that as "no constraint", i.e. the
    cut imposes no per-axis restriction (semantically equivalent to
    ``ConstraintAnd([])`` / IntervalSet.everything()).

    De Morgan handling
    ------------------
    The ``negated`` flag represents whether we're currently underneath
    an odd number of negations. At each LOGICOP we apply De Morgan:

      NOT (a AND b) = (NOT a) OR  (NOT b)
      NOT (a OR  b) = (NOT a) AND (NOT b)

    so the *effective* op flips when ``negated`` is True. Negation is
    not stored on AND/OR nodes — it bottoms out at the leaves, which
    set CutStructure.negated.

    Recovering AND/OR semantics
    ---------------------------
    REJECT at the top level seeds ``negated=True``, which by De Morgan
    converts the top-level ``AND`` of a ``[]`` operator into an ``OR``
    of two negated comparisons. This is the fix for the empty-interval
    bug: ``reject abs(eta) [] 1.44 1.56`` produces

      ConstraintOr(
        ConstraintLeaf(abs(eta) >= 1.44, negated=True),
        ConstraintLeaf(abs(eta) <= 1.56, negated=True),
      )

    which evaluates per-axis to
      IntervalSet((-∞, 1.44)) ∪ IntervalSet((1.56, +∞))
    rather than the spurious empty intersection produced by the flat
    extractor.
    """
    if not isinstance(expr, dict):
        return None
    tok = expr.get("tok", "")

    if tok == "LOGICOP":
        op = expr.get("op", "AND").upper()
        # Effective op flips under negation (De Morgan).
        effective_is_and = (op == "AND") ^ negated
        children: List[ConstraintExpr] = []
        for side_key in ("lhs", "rhs"):
            sub = _build_constraint_expr(expr.get(side_key), negated, chain)
            if sub is not None:
                children.append(sub)
        if not children:
            return None
        if len(children) == 1:
            return children[0]
        if effective_is_and:
            return ConstraintAnd(tuple(children))
        return ConstraintOr(tuple(children))

    if tok == "COMPAREOP":
        lhs, rhs = expr.get("lhs"), expr.get("rhs")
        lnum = float(rhs["value"]) if _is_num(rhs) else None
        rnum = float(lhs["value"]) if _is_num(lhs) else None

        if lnum is not None:
            cut = CutStructure(
                lhs=build_expr_node(lhs, _expr_repr),
                op=expr["op"], threshold=lnum, negated=negated,
                define_chain=list(chain), source_kind="cut",
            )
            return ConstraintLeaf(cut)
        if rnum is not None:
            cut = CutStructure(
                lhs=build_expr_node(rhs, _expr_repr),
                op=SWAP_OP[expr["op"]], threshold=rnum, negated=negated,
                define_chain=list(chain), source_kind="cut",
            )
            return ConstraintLeaf(cut)
        # Non-numeric on both sides: no extractable constraint.
        return None

    if tok in ("EXPROP", "FACTOROP"):
        # Arithmetic op as the top-level cut expression — not a
        # comparison, so no constraint. Defensive descent in case the
        # AST nests COMPAREOPs inside (the legacy extractor did).
        sub_l = _build_constraint_expr(expr.get("lhs"), negated, chain)
        sub_r = _build_constraint_expr(expr.get("rhs"), negated, chain)
        kids = [s for s in (sub_l, sub_r) if s is not None]
        if not kids:
            return None
        if len(kids) == 1:
            return kids[0]
        # Conjunction is the safe default when we don't know the boolean
        # combinator — same as the legacy descent which always produced
        # a flat list of constraints (i.e. an AND).
        return ConstraintAnd(tuple(kids)) if not negated else ConstraintOr(tuple(kids))

    return None


# ─────────────────────────────────────────────────────────────────────────────
# CutDependency  — full dependency tree node
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CutDependency:
    """
    One node in the dependency tree of a resolved cut.

    The single stored representation of constraint content is
    ``own_constraint_exprs`` — a list of structured ``ConstraintExpr``
    trees in negation-normal form. All consumers walk this directly;
    there is no separate flat-leaf view.

    Why structured-only:
      * The IntervalSet evaluator in the overlap pipeline needs
        AND/OR shape preserved (e.g. ``reject abs(eta) [] 1.44 1.56``
        is an OR of two half-lines, not an empty intersection).
      * A separate flat view would risk drift: chain-stamping and
        collection-resolution walk ``own_constraint_exprs``, and any
        write site that updated only the flat copy would create a
        silent inconsistency.

    Cardinality of ``own_constraint_exprs``:
      * One entry for ``cut``-kind nodes (the single source-level
        cut at the root).
      * One entry per source-level cut for ``object`` nodes that
        aggregate multiple SELECT/REJECT statements.
      * Empty for ``define`` and ``builtin`` nodes that contribute
        no constraints of their own.
    """
    kind: str = ""       # "cut", "define", "object", "built-in"
    name: str = ""
    own_constraint_exprs: List[ConstraintExpr] = field(default_factory=list)
    children: List["CutDependency"] = field(default_factory=list)

    def struct_sig(self) -> tuple:
        child_sigs = tuple(c.struct_sig() for c in self.children)
        own_sig = tuple(
            sorted((c.func_chain, c.op)
                   for ce in self.own_constraint_exprs
                   for c in constraint_expr_leaves(ce))
        )
        return (self.kind, own_sig, child_sigs)

    def full_dep_sig(self) -> tuple:
        child_sigs = tuple(c.full_dep_sig() for c in self.children)
        own_sig = tuple(
            sorted(
                (c.func_chain, c.resolved_collection.lower(), c.op, c.threshold)
                for ce in self.own_constraint_exprs
                for c in constraint_expr_leaves(ce)
            )
        )
        return (self.kind, own_sig, child_sigs)

    def children_full_dep_sig(self) -> tuple:
        return tuple(c.full_dep_sig() for c in self.children)

    def pretty(self, indent: int = 2, _depth: int = 0) -> str:
        """
        Render this dependency tree as an indented, ANSI-colored text block
        suitable for terminal display.
        """
        pad = " " * (indent * _depth + 6)   # 6-space base to sit under "dep tree:"
        tag_label = _PRETTY_KIND_LABELS.get(self.kind, "?")
        tag_color = _PRETTY_KIND_COLORS.get(self.kind, "")
        tag = f"{tag_color}[{tag_label}]{_ANSI_RESET}"

        own = [c for ce in self.own_constraint_exprs
                  for c in constraint_expr_leaves(ce)]
        if own:
            parts = []
            for c in own:
                eff = c.effective_op()
                try:
                    val = int(c.threshold) if float(c.threshold) == int(c.threshold) else c.threshold
                except (TypeError, ValueError):
                    val = c.threshold
                parts.append(f"{_ANSI_CYAN}{c.display_name()} {eff} {val}{_ANSI_RESET}")
            constraints_str = f" {_ANSI_MUTED}←{_ANSI_RESET} " + ", ".join(parts)
        else:
            constraints_str = ""

        line = f"{pad}{tag} {self.name}{constraints_str}"
        child_lines = [ch.pretty(indent=indent, _depth=_depth + 1) for ch in self.children]
        return "\n".join([line] + child_lines)


# ANSI rendering constants used by ``CutDependency.pretty``. Module-level
# so they're not rebuilt on every call during deep tree rendering.
_PRETTY_KIND_LABELS = {"cut": "cut", "define": "def", "object": "obj", "builtin": "BLT"}
_PRETTY_KIND_COLORS = {
    "cut":     "\033[94m",   # blue
    "define":  "\033[95m",   # purple
    "object":  "\033[33m",   # orange
    "builtin": "\033[32m",   # green
}
_ANSI_RESET = "\033[0m"
_ANSI_CYAN  = "\033[96m"
_ANSI_MUTED = "\033[90m"


# ─────────────────────────────────────────────────────────────────────────────
# ResolvedCutIR  — one fully-resolved cut in a region or object
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ResolvedCutIR:
    """
    One fully-resolved SELECT/REJECT/BIN/WEIGHT command from a region
    or object block.

    Constraint content is stored once, in structured form
    (``constraint_expr``). The flat ``constraints`` view is derived on
    demand from that tree. The default value ``ConstraintAnd(())`` is
    the identity element of conjunction — semantically "no extractable
    constraint", matching the old ``None`` value but without forcing
    callers to write ``Optional`` guards.
    """
    command: str = ""       # SELECT / REJECT / BIN / WEIGHT
    raw_expr: Optional[dict] = None
    surface_vars: Set[str] = field(default_factory=set)
    resolved_vars: Set[str] = field(default_factory=set)
    builtin_objects: Set[str] = field(default_factory=set)
    constraint_expr: ConstraintExpr = field(
        default_factory=lambda: ConstraintAnd(())
    )
    dependency_tree: Optional[CutDependency] = None

    @property
    def constraints(self) -> List[CutStructure]:
        """Flat-leaf view of ``constraint_expr``. Recomputed on access."""
        return constraint_expr_leaves(self.constraint_expr)


# ─────────────────────────────────────────────────────────────────────────────
# InheritanceLevel / ObjectInheritanceChain
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class InheritanceLevel:
    """One step in an object's inheritance chain.

    Constraint content is stored once, in ``constraint_exprs``, the
    list of structured ``ConstraintExpr`` trees at this level. The
    flat ``cuts`` view is derived on demand. ``constraint_exprs`` is
    empty for builtin terminal levels and for inheritance steps that
    add no cuts.
    """
    name: str = ""
    is_builtin: bool = False
    constraint_exprs: List[ConstraintExpr] = field(default_factory=list)

    @property
    def cuts(self) -> List[CutStructure]:
        """Flat-leaf view of ``constraint_exprs``. Recomputed on access."""
        out: List[CutStructure] = []
        for ce in self.constraint_exprs:
            out.extend(constraint_expr_leaves(ce))
        return out


@dataclass
class ObjectInheritanceChain:
    levels: List[InheritanceLevel] = field(default_factory=list)

    @property
    def root(self) -> str:
        if self.levels:
            for lv in reversed(self.levels):
                if lv.is_builtin:
                    return canonicalise(lv.name)
        return "UNKNOWN"

    def cumulative_cuts(self) -> List[CutStructure]:
        nc: List[CutStructure] = []
        for lv in self.levels:
            nc.extend(lv.cuts)
        return nc

    def cumulative_constraint_exprs(self) -> List[ConstraintExpr]:
        """Concatenated structured forms across all inheritance levels.

        Each level's constraint_exprs is a list of ConstraintExprs;
        flattened, this gives the full conjunction of structured cuts
        the chain imposes. Consumers (the IntervalSet evaluator) treat
        the returned list as conjoined.
        """
        out: List[ConstraintExpr] = []
        for lv in self.levels:
            out.extend(lv.constraint_exprs)
        return out

    def struct_sig(self) -> tuple:
        return tuple(
            (lv.is_builtin,
             frozenset((c.func_chain, c.op) for c in lv.cuts))
            for lv in self.levels
        )

    def full_dep_sig(self) -> tuple:
        return tuple(
            (lv.is_builtin,
             tuple(sorted(
                 (c.func_chain, c.resolved_collection.lower(), c.op, c.threshold)
                 for c in lv.cuts)))
            for lv in self.levels
        )

    def __repr__(self):
        if not self.levels:
            return "Chain()"
        names = " → ".join(lv.name for lv in self.levels)
        return f"Chain({names})"


# ─────────────────────────────────────────────────────────────────────────────
# ObjectIR / RegionIR / AnalysisIR
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ObjectIR:
    name: str
    takes: List[str] = field(default_factory=list)
    own_cuts: List[ResolvedCutIR] = field(default_factory=list)
    chain: ObjectInheritanceChain = field(default_factory=ObjectInheritanceChain)

    def all_constraints(self) -> List[CutStructure]:
        return self.chain.cumulative_cuts()

    def root_type(self) -> str:
        return self.chain.root


@dataclass
class RegionIR:
    name: str
    resolved_cuts: List[ResolvedCutIR] = field(default_factory=list)

    def all_builtin_objects(self) -> Set[str]:
        obs: Set[str] = set()
        for rc in self.resolved_cuts:
            obs |= rc.builtin_objects
        return obs


@dataclass
class AnalysisIR:
    source_file: str
    objects: Dict[str, ObjectIR] = field(default_factory=dict)
    regions: Dict[str, RegionIR] = field(default_factory=dict)
    defines_raw: Dict[str, dict] = field(default_factory=dict)
    defines_resolved: Dict[str, str] = field(default_factory=dict)

    def get_object(self, name: str) -> Optional[ObjectIR]:
        direct = self.objects.get(name)
        if direct:
            return direct
        nl = name.lower()
        return next((v for k, v in self.objects.items() if k.lower() == nl), None)

    def get_define(self, name: str) -> Optional[dict]:
        return self.defines_raw.get(name.lower())


# ─────────────────────────────────────────────────────────────────────────────
# AST utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def _expr_repr(expr: dict, depth: int = 0) -> str:
    if expr is None or depth > 12:
        return "…"
    tok = _tok(expr)
    if tok in ("INT", "REAL"):
        v = float(expr["value"])
        return str(int(v) if v == int(v) else v)
    if tok == "ID":
        s = expr.get("id", "")
        dotop = expr.get("dotop", "")
        acc = expr.get("accessor", [])
        if dotop: s += f".{dotop}"
        if acc:
            s += f"[{acc[0]}]" if len(acc)==1 else f"[{acc[0]}:{acc[1]}]"
        return s
    if tok in ("COMPAREOP", "LOGICOP", "EXPROP", "FACTOROP"):
        return f"({_expr_repr(expr['lhs'],depth+1)} {expr['op']} {_expr_repr(expr['rhs'],depth+1)})"
    if tok == "FUNCTION":
        params = ", ".join(_expr_repr(p,depth+1) for p in expr.get("params", []))
        return f"{expr['id']}({params})"
    if _is_ite(expr):
        c = _expr_repr(expr.get("condition"),depth+1)
        t = _expr_repr(expr.get("then"),depth+1)
        e = _expr_repr(expr.get("else"),depth+1) if expr.get("else") else "∅"
        return f"({c} ? {t} : {e})"
    return str(expr)


def _collect_surface_vars(expr: dict, out: Set[str]):
    if expr is None:
        return
    tok = _tok(expr)
    if tok == "ID":
        out.add(expr.get("id", "").lower())
        dotop = expr.get("dotop", "")
        if dotop: out.add(dotop.lower())
    elif tok in ("COMPAREOP", "LOGICOP", "EXPROP", "FACTOROP"):
        _collect_surface_vars(expr.get("lhs"), out)
        _collect_surface_vars(expr.get("rhs"), out)
    elif tok == "FUNCTION":
        out.add(expr.get("id", "").lower())
        for p in expr.get("params", []): _collect_surface_vars(p, out)
    elif _is_ite(expr):
        _collect_surface_vars(expr.get("condition"), out)
        _collect_surface_vars(expr.get("then"), out)
        _collect_surface_vars(expr.get("else"), out)


# ─────────────────────────────────────────────────────────────────────────────
# DefineResolver
# ─────────────────────────────────────────────────────────────────────────────

class DefineResolver:
    MAX_DEPTH = 20

    def __init__(self, ir: AnalysisIR):
        self.ir = ir

    def resolve_cuts(self, cmds: List[dict]) -> List[ResolvedCutIR]:
        return [self._build_resolved_cut(cmd) for cmd in cmds]

    def _build_resolved_cut(self, cmd: dict) -> ResolvedCutIR:
        condition = cmd.get("condition")
        rc = ResolvedCutIR(command=cmd["tok"].upper(), raw_expr=condition)
        _collect_surface_vars(condition, rc.surface_vars)

        # Resolve expression (substitute defines + object refs)
        resolved_expr = self._resolve_expr(condition, [], 0)
        _collect_surface_vars(resolved_expr, rc.resolved_vars)
        self._collect_builtins(resolved_expr, rc.builtin_objects)

        is_reject = (cmd["tok"].upper() == "REJECT")

        # Build the structured ConstraintExpr (negation-normal AND/OR/Leaf
        # tree) — the single stored representation of constraint content.
        # The flat list view is derived on demand via the ``constraints``
        # property. ``ConstraintAnd(())`` is the identity element of
        # conjunction and stands in for "no extractable constraint".
        ce = _build_constraint_expr(
            resolved_expr, negated=is_reject, chain=[],
        )
        rc.constraint_expr = ce if ce is not None else ConstraintAnd(())

        # Build dependency tree. The root carries the cut's structured
        # form when it has any leaves; otherwise an empty list (consumers
        # treat that as "no constraints at this node").
        cut_label = _expr_repr(condition)
        root_exprs: List[ConstraintExpr] = (
            [rc.constraint_expr] if constraint_expr_leaves(rc.constraint_expr) else []
        )
        root_dep = CutDependency(
            kind="cut", name=cut_label,
            own_constraint_exprs=root_exprs,
        )
        self._build_children(condition, root_dep, [], 0)
        rc.dependency_tree = root_dep

        # Stamp define_chain on every constraint from the tree
        self._stamp_chains_from_tree(root_dep, path=[])

        # Resolve collection names in constraints
        self._resolve_collections_in_tree(root_dep)

        return rc

    # ── chain stamping ────────────────────────────────────────────────────────

    def _stamp_chains_from_tree(self, node: CutDependency, path: List[str]):
        """Stamp ``define_chain`` on every leaf cut in the tree.

        Operates on ``own_constraint_exprs`` only — the single stored
        representation. Mutating the leaves here is sufficient; there is
        no separate flat view to keep in sync.
        """
        current_chain = [] if node.kind == "cut" else path + [node.name]
        for ce in node.own_constraint_exprs:
            for leaf in constraint_expr_leaves(ce):
                leaf.define_chain = list(current_chain)
        for child in node.children:
            self._stamp_chains_from_tree(child, current_chain)

    # ── collection resolution ─────────────────────────────────────────────────

    def _resolve_collections_in_tree(self, node: CutDependency):
        """Resolve user-written collection names to their canonical
        builtin/parent-object names. Operates on the leaves of
        ``own_constraint_exprs`` — the single stored representation.
        """
        for ce in node.own_constraint_exprs:
            for leaf in constraint_expr_leaves(ce):
                leaf.resolved_collection = self._resolve_collection_name(
                    leaf.collection,
                )
        for ch in node.children:
            self._resolve_collections_in_tree(ch)

    def _resolve_collection_name(self, name: str, _seen: Optional[Set[str]] = None) -> str:
        if _seen is None:
            _seen = set()
        if name.upper() in BUILTIN_OBJECTS:
            return canonicalise(name)
        if name in _seen:
            return name
        _seen.add(name)
        obj = self.ir.get_object(name)
        if obj is None:
            dn = self.ir.get_define(name.lower())
            if dn is not None:
                resolved = self._resolve_expr(dn["body"], list(_seen), 0)
                result = _extract_func_chain_and_collection(resolved)
                if result:
                    _, col, _acc = result
                    return self._resolve_collection_name(col, _seen)
            return name
        for parent in obj.takes:
            r = self._resolve_collection_name(parent, _seen)
            if r != parent:
                return r
            if parent.upper() in BUILTIN_OBJECTS:
                return canonicalise(parent)
        return name

    # ── dependency tree builder ───────────────────────────────────────────────

    def _build_children(self, expr: dict, parent: CutDependency,
                        visited: List[str], depth: int):
        if expr is None or depth > self.MAX_DEPTH:
            return
        tok = _tok(expr)

        if tok == "ID":
            name_lc = expr["id"].lower()
            if name_lc in visited:
                return
            new_visited = visited + [name_lc]

            # User defines and objects take priority over builtin names.
            # e.g. "define MHT = pT(MHTLV)" shadows the builtin "MHT" object.
            dn = self.ir.get_define(name_lc)
            if dn is not None:
                dep = CutDependency(kind="define", name=name_lc)
                parent.children.append(dep)
                self._build_children(dn["body"], dep, new_visited, depth+1)
                return

            obj = self.ir.get_object(expr["id"])
            if obj is not None:
                dep = self._build_object_dep(obj, new_visited, depth)
                if dep is not None:
                    parent.children.append(dep)
                return

            # Nested region reference
            reg = self.ir.regions.get(expr["id"]) or next(
                (v for k,v in self.ir.regions.items() if k.lower()==name_lc), None)
            if reg is not None:
                dep = CutDependency(
                    kind="define", name=f"region:{expr['id']}",
                )
                parent.children.append(dep)
                for nested_rc in reg.resolved_cuts:
                    if nested_rc.dependency_tree is not None:
                        dep.children.append(nested_rc.dependency_tree)

        elif tok == "FUNCTION":
            func_lc = expr["id"].lower()
            if func_lc not in visited:
                dn = self.ir.get_define(func_lc)
                if dn is not None:
                    dep = CutDependency(kind="define", name=func_lc)
                    parent.children.append(dep)
                    self._build_children(dn["body"], dep, visited+[func_lc], depth+1)
                    return
            for p in expr.get("params", []):
                self._build_children(p, parent, visited, depth+1)

        elif _is_bin(expr):
            self._build_children(expr.get("lhs"), parent, visited, depth+1)
            self._build_children(expr.get("rhs"), parent, visited, depth+1)

        elif _is_ite(expr):
            self._build_children(expr.get("condition"), parent, visited, depth+1)
            self._build_children(expr.get("then"), parent, visited, depth+1)
            if expr.get("else"):
                self._build_children(expr["else"], parent, visited, depth+1)

    def _build_object_dep(self, obj: ObjectIR, visited: List[str],
                          depth: int) -> Optional[CutDependency]:
        if depth > self.MAX_DEPTH:
            return None

        # Aggregate the structured forms of every cut in this object,
        # retagged with object provenance. Preserving the boolean shape
        # (AND/OR) is required for the IntervalSet evaluator to compute
        # correct per-axis acceptance — losing it would reintroduce the
        # union-as-intersection bug for object-level cuts inherited via
        # the dependency tree.
        own_exprs: List[ConstraintExpr] = []
        for rc in obj.own_cuts:
            if constraint_expr_leaves(rc.constraint_expr):
                own_exprs.append(retag_constraint_expr(
                    rc.constraint_expr, "object", obj.name,
                ))

        dep = CutDependency(
            kind="object", name=obj.name,
            own_constraint_exprs=own_exprs,
        )
        for parent_name in obj.takes:
            new_vis = visited + [obj.name.lower()]
            if parent_name.upper() in BUILTIN_OBJECTS:
                dep.children.append(
                    CutDependency(kind="builtin", name=canonicalise(parent_name))
                )
            else:
                parent_obj = self.ir.get_object(parent_name)
                if parent_obj is not None and parent_name.lower() not in visited:
                    child = self._build_object_dep(parent_obj, new_vis, depth+1)
                    if child:
                        dep.children.append(child)
                else:
                    dep.children.append(
                        CutDependency(kind="builtin", name=parent_name.upper())
                    )
        return dep

    # ── expression resolution ─────────────────────────────────────────────────

    def _resolve_expr(self, expr: dict, visited: List[str],
                      depth: int) -> dict:
        """Recursively substitute defines and object references in an
        expression dict. Returns the resolved expression. (An earlier
        version also returned a substitution trace, but it had no
        consumers; the trace is no longer built.)
        """
        if expr is None or depth > self.MAX_DEPTH:
            return expr
        tok = _tok(expr)

        if tok == "ID":
            name_lc = expr["id"].lower()
            if name_lc in visited:
                return expr
            new_vis = visited + [name_lc]
            # User defines and objects take priority over builtin names.
            dn = self.ir.get_define(name_lc)
            if dn is not None:
                sub = self._resolve_expr(dn["body"], new_vis, depth+1)
                dotop = expr.get("dotop", "")
                if dotop and _is_var(sub):
                    sub = _make_var(
                        id=sub["id"], alias=sub.get("alias", ""),
                        dotop=dotop or sub.get("dotop", ""),
                        accessor=sub.get("accessor", []),
                        type=sub.get("type", ""),
                    )
                return sub
            obj = self.ir.get_object(expr["id"])
            if obj is not None:
                root = obj.root_type()
                if root != "UNKNOWN":
                    acc = expr.get("accessor", [])
                    return _make_var(id=root, dotop=expr.get("dotop", ""),
                                     accessor=acc)
            return expr

        if tok == "FUNCTION":
            func_lc = expr["id"].lower()
            new_vis = visited + [func_lc]
            dn = self.ir.get_define(func_lc)
            if dn is not None:
                return self._resolve_expr(dn["body"], new_vis, depth+1)
            new_params = [self._resolve_expr(p, visited, depth+1)
                          for p in expr.get("params", [])]
            return _make_func(id=expr["id"], params=new_params)

        if _is_bin(expr):
            rl = self._resolve_expr(expr["lhs"], visited, depth+1)
            rr = self._resolve_expr(expr["rhs"], visited, depth+1)
            return _make_bin(tok=tok, op=expr["op"], lhs=rl, rhs=rr)

        if _is_ite(expr):
            rc_ = self._resolve_expr(expr.get("condition"), visited, depth+1)
            rt_ = self._resolve_expr(expr.get("then"), visited, depth+1)
            re_ = (self._resolve_expr(expr["else"], visited, depth+1)
                   if expr.get("else") else None)
            return _make_ite(condition=rc_, then=rt_, else_=re_)

        return expr

    def _collect_builtins(self, expr: dict, out: Set[str]):
        if expr is None:
            return
        tok = _tok(expr)
        if tok == "ID":
            if expr["id"].upper() in BUILTIN_OBJECTS:
                out.add(canonicalise(expr["id"]))
        elif tok == "FUNCTION":
            for p in expr.get("params", []): self._collect_builtins(p, out)
        elif _is_bin(expr):
            self._collect_builtins(expr.get("lhs"), out)
            self._collect_builtins(expr.get("rhs"), out)
        elif _is_ite(expr):
            self._collect_builtins(expr.get("condition"), out)
            self._collect_builtins(expr.get("then"), out)
            if expr.get("else"): self._collect_builtins(expr["else"], out)


# ─────────────────────────────────────────────────────────────────────────────
# InheritanceChainBuilder
# ─────────────────────────────────────────────────────────────────────────────

class InheritanceChainBuilder:
    def __init__(self, ir: AnalysisIR, resolver: DefineResolver):
        self.ir = ir
        self.resolver = resolver
        self._cache: Dict[str, ObjectInheritanceChain] = {}

    def build_all(self):
        for name in list(self.ir.objects.keys()):
            self.ir.objects[name].chain = self._build_chain(name, [])

    def _build_chain(self, name: str, visited: List[str]) -> ObjectInheritanceChain:
        if name in self._cache:
            return self._cache[name]
        if name in visited:
            ch = ObjectInheritanceChain()
            ch.levels.append(InheritanceLevel(name=name, is_builtin=False))
            return ch
        if name.upper() in BUILTIN_OBJECTS:
            ch = ObjectInheritanceChain()
            ch.levels.append(InheritanceLevel(name=name.upper(), is_builtin=True))
            self._cache[name] = ch
            return ch
        obj = self.ir.get_object(name)
        if obj is None:
            ch = ObjectInheritanceChain()
            ch.levels.append(InheritanceLevel(name=name, is_builtin=False))
            self._cache[name] = ch
            return ch

        raw_cmds: List[dict] = getattr(obj, "_raw_cmds_store", [])
        own_resolved = self.resolver.resolve_cuts(raw_cmds)
        obj.own_cuts = own_resolved

        # Build this object's level. Only the structured form is stored;
        # the flat-leaf view is derived on demand by InheritanceLevel.cuts.
        # One ConstraintExpr per source-level cut preserves AND/OR shape
        # for the IntervalSet evaluator.
        level = InheritanceLevel(name=obj.name, is_builtin=False)
        for rc in own_resolved:
            if constraint_expr_leaves(rc.constraint_expr):
                level.constraint_exprs.append(rc.constraint_expr)

        chain = ObjectInheritanceChain()
        chain.levels.append(level)

        for parent_name in obj.takes:
            parent_chain = self._build_chain(parent_name, visited+[name])
            chain.levels.extend(parent_chain.levels)
            if len(obj.takes) > 1:
                chain.levels[0] = InheritanceLevel(
                    name=obj.name+"[UNION]", is_builtin=False,
                    constraint_exprs=level.constraint_exprs,
                )
                break

        self._cache[name] = chain
        return chain


# ─────────────────────────────────────────────────────────────────────────────
# Main extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_ir(ast_nodes: list, source_file: str = "<unknown>") -> AnalysisIR:
    ir = AnalysisIR(source_file=source_file)

    for node in ast_nodes:
        if node is None:
            continue

        if _is_define(node):
            ir.defines_raw[node["id"].lower()] = node

        elif _is_object(node):
            obj = ObjectIR(name=node["id"])
            raw_cmds: List[dict] = []
            for stmt in node.get("statements", []):
                if stmt is None or not _is_command(stmt):
                    continue
                if stmt["tok"].upper() == "TAKE":
                    cond = stmt.get("condition")
                    if cond and _is_var(cond):
                        for part in cond["id"].split("|"):
                            obj.takes.append(part.strip())
                else:
                    raw_cmds.append(stmt)
            obj._raw_cmds_store = raw_cmds  # type: ignore
            ir.objects[node["id"]] = obj

        elif _is_region(node):
            reg = RegionIR(name=node["id"])
            raw_cmds_r: List[dict] = []
            for stmt in node.get("statements", []):
                if stmt and _is_command(stmt):
                    raw_cmds_r.append(stmt)
            reg._raw_cmds_store = raw_cmds_r  # type: ignore
            ir.regions[node["id"]] = reg

    resolver = DefineResolver(ir)
    chain_builder = InheritanceChainBuilder(ir, resolver)
    chain_builder.build_all()

    for reg in ir.regions.values():
        raw = getattr(reg, "_raw_cmds_store", [])
        reg.resolved_cuts = resolver.resolve_cuts(raw)

    for name, dn in ir.defines_raw.items():
        resolved_expr = resolver._resolve_expr(dn["body"], [], 0)
        ir.defines_resolved[name] = _expr_repr(resolved_expr)

    return ir


def load_adl_file(path: str) -> AnalysisIR:
    return extract_ir(parse_adl_file(path), source_file=path)


def load_adl_text(text: str, label: str = "<text>") -> AnalysisIR:
    return extract_ir(parse_adl_text(text), source_file=label)
