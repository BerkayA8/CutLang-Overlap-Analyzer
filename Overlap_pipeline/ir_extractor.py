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
from typing import Any, ClassVar, Dict, List, Optional, Set, Tuple
import math

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

def _is_var(node) -> bool:  # variable
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
              accessor: list = None, type: str = "",
              src_object: str = "") -> dict:
    """``src_object``, when set, is the name of the user-defined ADL
    object this ID node was substituted from (see ``_resolve_expr``'s
    object-reference branch). It is NOT part of the raw C++ parser
    schema — it's metadata added during resolution so that two
    DIFFERENT objects sharing the same canonical root (e.g. ``jets``
    and ``nonbjets``, both rooted at JET) don't collapse into an
    indistinguishable placeholder once substituted. See
    ``expr_node.IdNode.src_object`` for how it's consumed."""
    return {"tok": "ID", "id": id, "alias": alias, "dotop": dotop,
            "accessor": accessor or [], "type": type,
            "src_object": src_object}

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


# ─────────────────────────────────────────────────────────────────────────────
# CutDependency subclasses
# ─────────────────────────────────────────────────────────────────────────────
# Real subclasses per node kind, so consumers can dispatch on
# ``isinstance(node, ObjectDependency)`` instead of ``node.kind == "object"``.
#
# ``kind`` stays a plain string on every instance (set in ``__post_init__``,
# below), so nothing that reads ``node.kind`` — ``struct_sig``,
# ``full_dep_sig``, ``pretty``, the ``_PRETTY_KIND_*`` lookups, or any
# external code (report.py, catalogue.py) — needs to change. Each subclass
# additionally carries the SAME string as a class-level attribute (e.g.
# ``ObjectDependency.kind == "object"``, readable with no instance at all),
# matching the design's intent of a "class-level string constant" while
# still allowing ``CutDependency`` itself to be constructed directly with
# an arbitrary ``kind=...`` — the base class is unchanged and stays fully
# backwards compatible with any code (or test) that builds plain
# ``CutDependency(kind="object", ...)`` instances by hand.
#
# Only ``ObjectDependency`` and ``BuiltinDependency`` get ``roots()`` /
# ``cumulative_constraint_expr()`` — a cut or define node's children can be
# independent, non-ANDable axes, so those methods don't belong on the base
# class or on ``CutRootDependency`` / ``DefineDependency``.


@dataclass
class CutRootDependency(CutDependency):
    """The root node of one resolved SELECT/REJECT cut's dependency tree."""
    kind = "cut"

    def __post_init__(self):
        self.kind = "cut"


@dataclass
class DefineDependency(CutDependency):
    """A ``define`` substituted into a cut's dependency tree. Carries no
    constraints of its own — it's a pure symbolic substitution node."""
    kind = "define"

    def __post_init__(self):
        self.kind = "define"


@dataclass
class BuiltinDependency(CutDependency):
    """A terminal built-in physics object (ELE, MUO, JET, ...). Leaf of
    every object inheritance chain."""
    kind = "builtin"

    def __post_init__(self):
        self.kind = "builtin"

    def roots(self) -> Set[str]:
        # Only a NAME ACTUALLY RECOGNISED as a built-in physics object
        # counts as a root. _build_object_dep also creates a
        # BuiltinDependency as a fallback label for a ``take`` target
        # that isn't a builtin AND isn't a known object (an undeclared /
        # typo'd name) — that fallback must NOT contribute a root, or an
        # object with a genuinely unresolvable parent would misreport a
        # made-up "root" instead of leaving it unknown (matching the old
        # ObjectInheritanceChain._build_chain's ``is_builtin`` rule,
        # which only ever set ``is_builtin=True`` for a real BUILTIN_OBJECTS
        # match).
        if self.name and self.name.upper() in BUILTIN_OBJECTS:
            return {canonicalise(self.name)}
        return set()

    def cumulative_constraint_expr(self) -> ConstraintExpr:
        # Builtins never carry own_constraint_exprs in practice, but stay
        # defensive so a hand-built BuiltinDependency with constraints
        # (e.g. in a unit test) still behaves sensibly.
        if not self.own_constraint_exprs:
            return ConstraintAnd(())
        if len(self.own_constraint_exprs) == 1:
            return self.own_constraint_exprs[0]
        return ConstraintAnd(tuple(self.own_constraint_exprs))


@dataclass
class ObjectDependency(CutDependency):
    """An ``object`` node. Absorbs what ``ObjectInheritanceChain`` /
    ``InheritanceLevel`` / ``InheritanceChainBuilder`` used to do:

      * ``roots()`` — the set of built-in root types reachable through
        every ``take`` branch (plural, unlike the old scalar
        ``ObjectInheritanceChain.root`` — a ``take Union(a, b, ...)``
        object can genuinely have more than one root).
      * ``cumulative_constraint_expr()`` — this object's own cuts ANDed
        with the OR of every parent branch's cumulative constraints.
        ORing across *all* branches (not just the first) is the fix for
        the inheritance-chain Union bug, where only the first ``take``
        target's cuts used to survive into the cumulative view.
    """
    kind = "object"

    def __post_init__(self):
        self.kind = "object"

    def roots(self) -> Set[str]:
        out: Set[str] = set()
        for ch in self.children:
            if isinstance(ch, (ObjectDependency, BuiltinDependency)):
                out |= ch.roots()
        return out

    def cumulative_constraint_expr(self) -> ConstraintExpr:
        own = ConstraintAnd(tuple(self.own_constraint_exprs)) if self.own_constraint_exprs else None

        parent_nodes = [ch for ch in self.children
                        if isinstance(ch, (ObjectDependency, BuiltinDependency))]
        parent_exprs = [p.cumulative_constraint_expr() for p in parent_nodes]

        if not parent_exprs:
            parent_combined = None
        elif len(parent_exprs) == 1:
            parent_combined = parent_exprs[0]
        else:
            # The fix: OR across every parent branch (Union(a, b, ...)),
            # not just the first one.
            parent_combined = ConstraintOr(tuple(parent_exprs))

        parts = [p for p in (own, parent_combined) if p is not None]
        if not parts:
            return ConstraintAnd(())
        if len(parts) == 1:
            return parts[0]
        return ConstraintAnd(tuple(parts))


def _collect_tree_roots(node: CutDependency, out: Set[str],
                        _seen: Optional[Set[int]] = None) -> None:
    """Add the built-in roots of every object/builtin node reachable from
    ``node`` (through define and nested-region wrappers) to ``out``."""
    if _seen is None:
        _seen = set()
    if id(node) in _seen:
        return
    _seen.add(id(node))
    for ch in node.children:
        if isinstance(ch, (ObjectDependency, BuiltinDependency)):
            out |= ch.roots()
        elif isinstance(ch, (DefineDependency, CutRootDependency)):
            _collect_tree_roots(ch, out, _seen)


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
    # Per-cut external chain mapping: {id(leaf CutStructure) -> chain}.
    # Replaces the old approach of mutating ``leaf.define_chain`` in
    # place. Once object/define dependency nodes are cached and shared
    # by reference across every cut that references them (see
    # DefineResolver's caches), the SAME CutStructure leaf can appear in
    # many different cuts' trees, each at a different path from that
    # cut's own root — so the outer chain cannot be stored on the shared
    # leaf itself without one cut's stamp corrupting another's. This
    # dict holds the outer chain scoped to THIS ResolvedCutIR only; see
    # DefineResolver._compute_leaf_chains.
    leaf_chains: Dict[int, List[str]] = field(default_factory=dict)

    # Region-inheritance role of this line (only set for region cuts;
    # empty for object cuts). See ``_classify_region_line``:
    #   "own"     — an ordinary cut belonging to this region
    #   "inherit" — ``select R`` / bare ``R``: inherit region R's cuts
    #               (``region_ref`` holds R's canonical name)
    #   "all"     — ``select ALL``: no constraint, marks a root region
    #   "opaque"  — a region reference the comparator cannot model
    #               (``reject R``, R inside a compound condition, a
    #               cycle, an unknown name). Contributes OVERLAP, never
    #               a false DISJOINT/EQUAL. ``region_note`` says why.
    region_role: str = ""
    region_ref: str = ""
    region_note: str = ""

    @property
    def constraints(self) -> List[CutStructure]:
        """Flat-leaf view of ``constraint_expr``. Recomputed on access."""
        return constraint_expr_leaves(self.constraint_expr)


# ─────────────────────────────────────────────────────────────────────────────
# ObjectIR / RegionIR / AnalysisIR
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ObjectIR:
    name: str
    takes: List[str] = field(default_factory=list)
    own_cuts: List[ResolvedCutIR] = field(default_factory=list)
    # This object's own dependency-tree node. Used to be a separate
    # ``ObjectInheritanceChain``; ``ObjectDependency`` now absorbs that
    # role (see the class docstring). ``None`` only before extraction
    # has run (or in the deep-recursion edge case documented on
    # ``DefineResolver._build_object_dep``).
    chain: Optional["ObjectDependency"] = None

    def all_constraints(self) -> List[CutStructure]:
        if self.chain is None:
            return []
        return constraint_expr_leaves(self.chain.cumulative_constraint_expr())

    def root_type(self) -> str:
        """A single representative built-in root, for callers that only
        need a scalar (e.g. ``_resolve_expr``'s object substitution, or
        grouping cuts by root for report display). A ``take
        Union(a, b, ...)`` object genuinely has more than one root —
        use ``self.chain.roots()`` directly when the full set matters,
        such as when deciding whether two objects' root coverage
        actually intersects.
        """
        if self.chain is None:
            return "UNKNOWN"
        roots = self.chain.roots()
        if not roots:
            return "UNKNOWN"
        return sorted(roots)[0]


@dataclass
class RegionIR:
    """One region block.

    Region inheritance
    ------------------
    A line ``select R`` — or a bare ``R``, which the grammar desugars to
    the same ``SELECT ID(R)`` — makes this region inherit every cut of
    region R. Inheritance is a plain AND: ``SR = presel ∩ own cuts``.
    ``select ALL`` is a no-op constraint that marks a root region.

    ``resolved_cuts`` keeps every line in source order (including the
    inheritance/ALL lines) for backward compatibility. After
    ``extract_ir`` runs:

      parents         — canonical names of directly-inherited regions
      effective_cuts  — the flattened cut set the comparator uses:
                        ancestors' cuts first (each ancestor once, even
                        through a diamond), then this region's own cuts.
                        Inheritance and ALL lines are excluded.
      cut_origins     — {id(rc): path} provenance for inherited cuts,
                        e.g. ``("init", "presel")`` = owned by init,
                        reached via presel. Own cuts map to ``()``.
      warnings        — problems found on this region's own lines
                        (cycles, unknown names, unsupported uses).

    ``effective_cuts`` stays ``None`` for a RegionIR built by hand
    (tests); consumers then fall back to ``resolved_cuts``.
    """
    name: str
    resolved_cuts: List[ResolvedCutIR] = field(default_factory=list)
    parents: List[str] = field(default_factory=list)
    has_all_marker: bool = False
    effective_cuts: Optional[List[ResolvedCutIR]] = None
    cut_origins: Dict[int, Tuple[str, ...]] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_root(self) -> bool:
        return not self.parents

    @property
    def own_cuts(self) -> List[ResolvedCutIR]:
        return [rc for rc in self.resolved_cuts
                if rc.region_role not in ("inherit", "all")]

    def comparison_cuts(self) -> List[ResolvedCutIR]:
        return self.effective_cuts if self.effective_cuts is not None else self.resolved_cuts

    def all_builtin_objects(self) -> Set[str]:
        # Uses the flattened cut set, so a region whose own cuts touch
        # no built-in collection still shares its parents' collections
        # (otherwise Rule 1 would wrongly call it DISJOINT).
        obs: Set[str] = set()
        for rc in self.comparison_cuts():
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
        # Caches keyed by lowercased name. Built once per name, shared by
        # reference from every cut/object/define that references it — the
        # fix for the redundant subtree-rebuilding that used to happen on
        # every reference site. See _build_object_dep / _get_define_dep /
        # _get_builtin_dep / _get_region_ref_dep.
        self._object_dep_cache: Dict[str, ObjectDependency] = {}
        self._define_dep_cache: Dict[str, DefineDependency] = {}
        self._builtin_dep_cache: Dict[str, BuiltinDependency] = {}
        self._region_dep_cache: Dict[str, DefineDependency] = {}
        # Guards the lazy own_cuts resolution in _build_object_dep against
        # re-entrancy: an object's own SELECT/REJECT can reference the
        # object itself by name (e.g. "object jets: select pt(jets) > 25",
        # a common, legal ADL pattern meaning "this object's own pT").
        # Resolving that select re-enters _build_object_dep("jets") before
        # the outer resolution has finished — this set makes the inner
        # call see (still-empty) own_cuts as-is instead of trying to
        # resolve them again, which would recurse forever.
        self._resolving_own_cuts: Set[str] = set()

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
        root_dep = CutRootDependency(
            name=cut_label,
            own_constraint_exprs=root_exprs,
        )
        self._build_children(condition, root_dep, [], 0)
        rc.dependency_tree = root_dep

        # ``_resolve_expr`` substitutes an object reference with ONE
        # representative root (``ObjectIR.root_type()``), so for a
        # ``take Union(a, b)`` object spanning several roots (e.g. ELE and
        # MUO) only the alphabetically-first root reached
        # ``builtin_objects`` above. Rule 1 ("no shared built-in
        # collections → DISJOINT") then saw a lepton-union cut as
        # electron-only and could report a false DISJOINT against a
        # muon-only region. Add every root of every object the cut
        # depends on.
        _collect_tree_roots(root_dep, rc.builtin_objects)

        # Compute this cut's own outer chain for every leaf reachable from
        # its root — WITHOUT mutating any leaf. See ResolvedCutIR.leaf_chains.
        rc.leaf_chains = self._compute_leaf_chains(root_dep, path=[])

        # Resolve collection names in constraints
        self._resolve_collections_in_tree(root_dep)

        return rc

    # ── chain computation ────────────────────────────────────────────────────

    def _compute_leaf_chains(
        self, node: CutDependency, path: List[str],
        out: Optional[Dict[int, List[str]]] = None,
    ) -> Dict[int, List[str]]:
        """Compute, without mutating any ``CutStructure``, the outer
        define/object substitution chain for every leaf reachable from
        ``node``, scoped to ONE cut's own tree.

        Object and define dependency nodes are now cached and shared by
        reference across every cut that references them (see
        ``_object_dep_cache`` / ``_define_dep_cache``), so the *same*
        leaf ``CutStructure`` can appear in many different cuts' trees,
        each at a different path from that cut's own root. The chain is
        therefore not a property of the leaf itself — it depends on
        which cut is asking — so it lives in this external, per-cut map
        (``ResolvedCutIR.leaf_chains``) instead of being stamped onto
        the shared leaf (which is exactly what the old
        ``_stamp_chains_from_tree`` did, and why it's unsafe once nodes
        are shared: the second cut to stamp a shared leaf would silently
        overwrite the first cut's chain).

        Compare ``leaf.define_chain`` — the LOCAL chain set once, at
        cache-build time, in ``_build_object_dep`` — which reports only
        the leaf's own owning object's name (e.g. ``["jets"]``), not the
        outer path through whichever cut currently references it.
        """
        if out is None:
            out = {}
        current_chain = [] if isinstance(node, CutRootDependency) else path + [node.name]
        for ce in node.own_constraint_exprs:
            for leaf in constraint_expr_leaves(ce):
                out[id(leaf)] = list(current_chain)
        for child in node.children:
            self._compute_leaf_chains(child, current_chain, out)
        return out

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
                dep = self._get_define_dep(name_lc, dn["body"], new_visited, depth)
                parent.children.append(dep)
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
                dep = self._get_region_ref_dep(expr["id"], reg)
                parent.children.append(dep)

        elif tok == "FUNCTION":
            func_lc = expr["id"].lower()
            if func_lc not in visited:
                dn = self.ir.get_define(func_lc)
                if dn is not None:
                    dep = self._get_define_dep(func_lc, dn["body"], visited+[func_lc], depth)
                    parent.children.append(dep)
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

    # ── cached node construction ─────────────────────────────────────────────

    def _get_define_dep(self, name_lc: str, body: dict,
                        visited_for_body: List[str], depth: int) -> DefineDependency:
        """Build (once) and cache the DefineDependency subtree for a
        define, shared by reference across every reference site."""
        cached = self._define_dep_cache.get(name_lc)
        if cached is not None:
            return cached
        dep = DefineDependency(name=name_lc)
        self._build_children(body, dep, visited_for_body, depth+1)
        self._define_dep_cache[name_lc] = dep
        return dep

    def _get_builtin_dep(self, name: str) -> BuiltinDependency:
        """Builtins are stateless terminal leaves — one shared instance
        per canonical name is always safe."""
        cached = self._builtin_dep_cache.get(name)
        if cached is not None:
            return cached
        dep = BuiltinDependency(name=name)
        self._builtin_dep_cache[name] = dep
        return dep

    def _get_region_ref_dep(self, region_id: str, reg: RegionIR) -> DefineDependency:
        """Build (once) and cache the wrapper node for a nested-region
        reference. The nested cuts' own dependency trees are grafted by
        reference regardless (as before) — only the wrapper node itself
        is now shared rather than rebuilt per reference site."""
        key = region_id.lower()
        cached = self._region_dep_cache.get(key)
        if cached is not None:
            return cached
        dep = DefineDependency(name=f"region:{region_id}")
        for nested_rc in reg.resolved_cuts:
            if nested_rc.dependency_tree is not None:
                dep.children.append(nested_rc.dependency_tree)
        # Only cache a populated stub. A region referenced before its own
        # cuts are resolved (only possible now through a cycle, since
        # extract_ir resolves regions parents-first) would otherwise be
        # cached EMPTY and every later reference would get the empty one.
        if reg.resolved_cuts:
            self._region_dep_cache[key] = dep
        return dep

    def _build_object_dep(self, obj: ObjectIR, visited: List[str],
                          depth: int) -> Optional[ObjectDependency]:
        """Build (once) and cache this object's ObjectDependency subtree.

        Cached by lowercased object name: every reference site (another
        object's ``take``, a region cut, another define) that reaches
        the same object gets back the SAME node by reference, instead of
        a freshly-rebuilt, structurally-equal copy. This is the fix for
        the redundant subtree rebuilding (and repeated
        ``retag_constraint_expr`` calls) that used to happen once per
        reference site.

        ``obj.own_cuts`` is resolved lazily, on first build, mirroring
        what the old (now-removed) ``InheritanceChainBuilder._build_chain``
        did — this method is now the single place that both resolves an
        object's own SELECT/REJECT cuts and builds its dependency
        subtree, replacing the two separate, parallel mechanisms
        (``_build_object_dep`` and ``InheritanceChainBuilder``) that used
        to compute overlapping information independently. See
        ``_resolving_own_cuts`` for the re-entrancy guard this requires.
        """
        key = obj.name.lower()
        cached = self._object_dep_cache.get(key)
        if cached is not None:
            return cached
        if depth > self.MAX_DEPTH:
            return None

        if not obj.own_cuts and key not in self._resolving_own_cuts:
            raw_cmds: List[dict] = getattr(obj, "_raw_cmds_store", [])
            if raw_cmds:
                self._resolving_own_cuts.add(key)
                try:
                    obj.own_cuts = self.resolve_cuts(raw_cmds)
                finally:
                    self._resolving_own_cuts.discard(key)

        # Aggregate the structured forms of every cut in this object,
        # retagged with object provenance. Preserving the boolean shape
        # (AND/OR) is required for the IntervalSet evaluator to compute
        # correct per-axis acceptance — losing it would reintroduce the
        # union-as-intersection bug for object-level cuts inherited via
        # the dependency tree.
        #
        # Each retagged leaf's LOCAL ``define_chain`` is stamped exactly
        # once, right here, to just this object's own name (e.g.
        # ["jets"]) — never touched again afterwards. This is safe
        # because these are brand-new CutStructure copies produced by
        # ``retag_constraint_expr`` a few lines above, not yet observed
        # or shared anywhere; it is a one-time local write, not a later
        # re-stamp of an already-shared leaf (which is what made the old
        # ``_stamp_chains_from_tree`` unsafe once nodes are cached). The
        # OUTER chain — this object's position within any particular
        # cut's own tree — is computed separately, per cut, without
        # mutation, by ``_compute_leaf_chains``.
        own_exprs: List[ConstraintExpr] = []
        for rc in obj.own_cuts:
            if constraint_expr_leaves(rc.constraint_expr):
                retagged = retag_constraint_expr(
                    rc.constraint_expr, "object", obj.name,
                )
                for leaf in constraint_expr_leaves(retagged):
                    leaf.define_chain = [obj.name]
                own_exprs.append(retagged)

        dep = ObjectDependency(
            name=obj.name,
            own_constraint_exprs=own_exprs,
        )
        for parent_name in obj.takes:
            new_vis = visited + [obj.name.lower()]
            if parent_name.upper() in BUILTIN_OBJECTS:
                dep.children.append(self._get_builtin_dep(canonicalise(parent_name)))
            else:
                parent_obj = self.ir.get_object(parent_name)
                if parent_obj is not None and parent_name.lower() not in visited:
                    child = self._build_object_dep(parent_obj, new_vis, depth+1)
                    if child:
                        dep.children.append(child)
                else:
                    dep.children.append(self._get_builtin_dep(parent_name.upper()))

        self._object_dep_cache[key] = dep
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
                        src_object=sub.get("src_object", ""),
                    )
                return sub
            obj = self.ir.get_object(expr["id"])
            if obj is not None:
                root = obj.root_type()
                if root != "UNKNOWN":
                    acc = expr.get("accessor", [])
                    # Keep ``id`` as the canonical builtin root (existing
                    # code — builtin detection, roots(), display fallback
                    # — depends on it being e.g. "JET"), but stamp
                    # ``src_object`` with the ACTUAL referenced object's
                    # own name. Two different objects sharing a root
                    # (``jets`` and ``nonbjets``, both rooted at JET) must
                    # stay distinguishable once substituted, or a cut like
                    # ``dR(ELE, nonbjets)`` and another like
                    # ``dR(ELE, jets)`` collapse onto the identical
                    # signature ``dr(ELE, JET)`` and get wrongly treated
                    # as constraints on the SAME axis (see IdNode.signature
                    # in expr_node.py for where this is consumed).
                    return _make_var(id=root, dotop=expr.get("dotop", ""),
                                     accessor=acc, src_object=obj.name)
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
# Main extraction
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Region inheritance
# ─────────────────────────────────────────────────────────────────────────────
# Grammar fact (parser.y, ``criterion : id``): a bare ``presel`` line in a
# region is desugared by the C++ parser into ``SELECT ID(presel)`` — so it
# reaches Python indistinguishable from ``select presel``, and one rule
# covers both spellings. ``select ALL`` arrives as ``SELECT ID(ALL)``.
#
# Name priority mirrors DefineResolver._build_children: a define or object
# with the same name shadows a region.

def _region_key(ir: AnalysisIR, name: str) -> Optional[str]:
    """Canonical (as-declared) region name for ``name``, case-insensitive."""
    if name in ir.regions:
        return name
    nl = name.lower()
    return next((k for k in ir.regions if k.lower() == nl), None)


def _shadowed_by_define_or_object(ir: AnalysisIR, name: str) -> bool:
    return ir.get_define(name.lower()) is not None or ir.get_object(name) is not None


def _region_refs_in(ir: AnalysisIR, expr: Optional[dict]) -> List[str]:
    """Every region named anywhere inside an expression (canonical names)."""
    out: List[str] = []
    if not isinstance(expr, dict):
        return out
    tok = _tok(expr)
    if tok == "ID":
        nm = expr.get("id", "")
        if nm and not _shadowed_by_define_or_object(ir, nm):
            key = _region_key(ir, nm)
            if key is not None:
                out.append(key)
        return out
    for k in ("lhs", "rhs", "condition", "then", "else"):
        out += _region_refs_in(ir, expr.get(k))
    for p in expr.get("params", []) or []:
        out += _region_refs_in(ir, p)
    return out


def _classify_region_line(ir: AnalysisIR, cmd: dict) -> Tuple[str, str, str]:
    """Return ``(role, ref, note)`` for one raw region command.

    role ∈ {"own", "inherit", "all", "opaque"} — see ResolvedCutIR.region_role.
    """
    tok = (cmd.get("tok") or "").upper()
    cond = cmd.get("condition")
    bare = _is_var(cond) and not cond.get("accessor") and not cond.get("dotop")

    if bare:
        nm = cond.get("id", "")
        if nm and not _shadowed_by_define_or_object(ir, nm):
            key = _region_key(ir, nm)
            if key is not None:
                if tok == "SELECT":
                    return ("inherit", key, "")
                return ("opaque", key,
                        f"`{tok.lower()} {key}` (negated region reference) is not "
                        f"modelled; this line contributes OVERLAP.")
            if nm.upper() == "ALL":
                if tok == "SELECT":
                    return ("all", "", "")
                return ("opaque", "",
                        f"`{tok.lower()} ALL` rejects every event; not modelled, "
                        f"this line contributes OVERLAP.")
            if nm.upper() not in BUILTIN_OBJECTS:
                return ("opaque", nm,
                        f"`{nm}` is not a known region, object or define "
                        f"(possible typo?); this line contributes OVERLAP.")

    refs = _region_refs_in(ir, cond)
    if refs:
        return ("opaque", refs[0],
                f"Region `{refs[0]}` is used inside a compound condition; only a "
                f"plain `select {refs[0]}` / bare `{refs[0]}` line is inherited. "
                f"This line contributes OVERLAP.")
    return ("own", "", "")


def _region_resolution_order(
    ir: AnalysisIR, raw_parents: Dict[str, List[str]],
) -> Tuple[List[str], Set[Tuple[str, str]]]:
    """Parents-first (post-order DFS) order over the region graph, plus
    the set of ``(child, parent)`` edges that close a cycle. Resolving in
    this order means file order no longer matters: a child written above
    its parent still sees the parent's cuts."""
    state: Dict[str, int] = {}          # 0 = on stack, 1 = done
    order: List[str] = []
    back_edges: Set[Tuple[str, str]] = set()

    def visit(n: str):
        state[n] = 0
        for p in raw_parents.get(n, []):
            st = state.get(p)
            if st == 0:
                back_edges.add((n, p))
            elif st is None:
                visit(p)
        state[n] = 1
        order.append(n)

    for n in ir.regions:
        if n not in state:
            visit(n)
    return order, back_edges


def _flatten_region(ir: AnalysisIR, reg: RegionIR) -> None:
    """Fill ``reg.effective_cuts`` / ``reg.cut_origins``: ancestors' cuts
    first (each shared ancestor once), then this region's own cuts."""
    out: List[ResolvedCutIR] = []
    origins: Dict[int, Tuple[str, ...]] = {}
    seen: Set[int] = set()

    def walk(r: RegionIR, path: Tuple[str, ...], stack: Set[str]):
        for p in r.parents:
            if p in stack:              # defensive; cycle edges are pruned already
                continue
            walk(ir.regions[p], (p,) + path, stack | {p})
        for rc in r.own_cuts:
            if id(rc) in seen:
                continue
            seen.add(id(rc))
            out.append(rc)
            origins[id(rc)] = path

    walk(reg, (), {reg.name})
    reg.effective_cuts = out
    reg.cut_origins = origins


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

    # Build (and cache) each object's own dependency tree. This also
    # lazily resolves each object's own SELECT/REJECT cuts on first
    # build (see DefineResolver._build_object_dep) — replacing the old,
    # separate InheritanceChainBuilder pass that used to do both jobs
    # independently of _build_object_dep.
    for name, obj in ir.objects.items():
        obj.chain = resolver._build_object_dep(obj, [], 0)

    # Region inheritance. Classification only needs names, so it runs on
    # the raw commands before anything is resolved — that's what lets us
    # resolve regions parents-first regardless of file order.
    raw_roles: Dict[str, List[Tuple[str, str, str]]] = {}
    raw_parents: Dict[str, List[str]] = {}
    for name, reg in ir.regions.items():
        raw = getattr(reg, "_raw_cmds_store", [])
        roles = [_classify_region_line(ir, cmd) for cmd in raw]
        raw_roles[name] = roles
        raw_parents[name] = [ref for role, ref, _ in roles if role == "inherit"]

    order, back_edges = _region_resolution_order(ir, raw_parents)

    for name in order:
        reg = ir.regions[name]
        raw = getattr(reg, "_raw_cmds_store", [])
        reg.resolved_cuts = resolver.resolve_cuts(raw)
        for rc, (role, ref, note) in zip(reg.resolved_cuts, raw_roles[name]):
            if role == "inherit" and (name, ref) in back_edges:
                role = "opaque"
                note = (f"`select {ref}` closes an inheritance cycle "
                        f"({name} → … → {ref} → {name}); the edge is ignored "
                        f"and this line contributes OVERLAP.")
            rc.region_role, rc.region_ref, rc.region_note = role, ref, note
            if role == "inherit":
                reg.parents.append(ref)
            elif role == "all":
                reg.has_all_marker = True
            elif role == "opaque":
                reg.warnings.append(note)

    for reg in ir.regions.values():
        _flatten_region(ir, reg)

    for name, dn in ir.defines_raw.items():
        resolved_expr = resolver._resolve_expr(dn["body"], [], 0)
        ir.defines_resolved[name] = _expr_repr(resolved_expr)

    return ir


def load_adl_file(path: str) -> AnalysisIR:
    return extract_ir(parse_adl_file(path), source_file=path)


def load_adl_text(text: str, label: str = "<text>") -> AnalysisIR:
    return extract_ir(parse_adl_text(text), source_file=label)
