"""
expr_node.py
============
Structural representation of cut LHS expressions for the overlap pipeline.

A cut written in ADL — anything of the form ``EXPR op NUMBER`` — has its
left-hand side modelled here as an :class:`ExprNode` tree.  Every cut in
the IR carries one such tree, simple or composite.  Two cuts compare
*by structure*, not by string: equivalent expressions written with
different parenthesisation, operand order on commutative operators, or
integer-vs-float spelling produce identical trees and compare EQUAL.

Hierarchy
---------
``ExprNode`` is the abstract base.  The concrete kinds are::

    NumNode      — numeric literal:                   3, 1.5, 0.2
    IdNode       — bare identifier with accessor:     MET, JET, JET[0:3]
    FuncNode     — function chain over an inner expr: pT(JET), abs(eta(JET[0]))
    BinOpNode    — binary +, -, *, /:                 a + b,  pT(j[0]) / pT(j[1])
    OpaqueNode   — unmodelled subtree (escape hatch): kept as a faithful
                   string with the leaf collection refs that appeared in it.

The set is closed: subclassing ``ExprNode`` outside this module is rejected
by ``__init_subclass__``.  Adding a new kind means changing this file *and*
the comparator's ``match`` arms, which is the whole point — a new node
forces the comparator to declare what it does about it.

Canonicalisation
----------------
Trees built via the factory functions (``num``, ``ident``, ``fn``, ``binop``,
``opaque``) are canonical at construction time:

* ``+`` and ``*`` are flattened across nesting and their children sorted
  by signature.  ``a+(b+c)`` and ``(c+a)+b`` become identical n-ary trees.
* ``-`` and ``/`` keep their order; arity is fixed at 2.
* Integer-valued floats compare equal to ints (``2`` and ``2.0`` are
  the same NumNode).

What is *not* normalised: distributivity, factoring, sign-flipping
across multiplication, even-function symmetries (``cos(a-b) = cos(b-a)``).
Those would be algebraic equivalences and are deliberately out of scope.

Comparison
----------
``compare_expr(a, b)`` is the single entry point.  It returns one of the
five-value verdicts (DISJOINT, EQUAL, SUBSET, SUPERSET, OVERLAP).  The
soundness invariant is::

    compare_expr(a, b) == EQUAL  ⇒  a and b evaluate to the same value
                                    on every event.

Anything weaker than EQUAL means "not provably equal"; the outer cut-level
comparator then conservatively returns OVERLAP unless the cut intervals
themselves are disjoint.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from itertools import permutations
from typing import List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Verdict lattice (mirrors overlap_checker.py — kept here to avoid circular
# imports).  A future refactor could move both to a shared verdict module.
# ─────────────────────────────────────────────────────────────────────────────

DISJOINT = "DISJOINT"
EQUAL    = "EQUAL"
SUBSET   = "SUBSET"
SUPERSET = "SUPERSET"
OVERLAP  = "OVERLAP"


def _combine(verdicts: List[str]) -> str:
    """Bottom-up composition rule. Mirrors overlap_checker._combine."""
    if not verdicts:
        return EQUAL
    if any(v == DISJOINT for v in verdicts):
        return DISJOINT
    if any(v == OVERLAP for v in verdicts):
        return OVERLAP
    has_sub = any(v == SUBSET   for v in verdicts)
    has_sup = any(v == SUPERSET for v in verdicts)
    if has_sub and has_sup:
        return OVERLAP
    if has_sub: return SUBSET
    if has_sup: return SUPERSET
    return EQUAL


def _flip(verdict: str) -> str:
    if verdict == SUBSET:   return SUPERSET
    if verdict == SUPERSET: return SUBSET
    return verdict


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _accessor_token(acc: Tuple[int, ...]) -> str:
    """Render an accessor tuple to a stable string token used in signatures."""
    if not acc:
        return "*"
    if len(acc) == 2:
        return f"{acc[0]}:{acc[1]}"
    return ",".join(str(x) for x in acc)


def _fmt_num(v: float) -> str:
    """Same convention as overlap_checker._fmt: drop trailing .0 for ints."""
    return str(int(v)) if v == int(v) else str(v)


# ─────────────────────────────────────────────────────────────────────────────
# Base class
# ─────────────────────────────────────────────────────────────────────────────

class ExprNode(ABC):
    """
    Abstract base for all expression-tree nodes.

    Subclasses must live in this module — enforced via ``__init_subclass__``
    so the closed set is real, not just a convention.
    """

    # Subclassing outside this module is a programming error: the comparator
    # uses pattern matching on the closed set of kinds, and a new kind that
    # the comparator doesn't know about would silently fall through to
    # DISJOINT, which is a confusing failure mode.
    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        if cls.__module__ != ExprNode.__module__:
            raise TypeError(
                f"ExprNode subclasses must live in {ExprNode.__module__}; "
                f"got {cls.__module__}.{cls.__name__}. Add the new kind to "
                f"expr_node.py and extend compare_expr accordingly."
            )

    # ── Required interface ────────────────────────────────────────────────
    @abstractmethod
    def signature(self) -> str:
        """Structural fingerprint, *no* numeric values. Used for bucketing."""

    @abstractmethod
    def full_signature(self) -> str:
        """Structural fingerprint *with* numeric values. Used for fast
        EQUAL detection and stable hashing."""

    @abstractmethod
    def pretty(self) -> str:
        """Faithful source-form rendering."""

    # ── Common projections (overridden where meaningful) ─────────────────
    # These exist so legacy CutStructure consumers (catalogue, monotonicity,
    # sibling-object lookup) can read through CutStructure.func_chain etc.
    # without isinstance checks.

    @property
    def is_leaf(self) -> bool:
        """True if this node has no ExprNode children to recurse into.

        ``FuncNode`` returns True even though it carries an inner expression:
        a function application is a single value-producing operation that
        the *outer* comparator treats as a unit. ``compare_expr`` recurses
        into ``FuncNode.inner`` only after matching ``func_chain``.
        """
        return True

    def outer_func_chain(self) -> str:
        """Outermost function chain if this is a ``FuncNode``, else ""."""
        return ""

    def primary_collection(self) -> str:
        """Innermost collection name reachable through a single chain of
        ``FuncNode``s ending in an ``IdNode``. Empty for composite LHS.

        Composite LHSes have no single primary collection by design; the
        empty-string return is the right conservative behaviour for
        callers that need a unique underlying collection.
        """
        return ""

    def primary_accessor(self) -> Tuple[int, ...]:
        """Accessor of the primary collection, if any. () otherwise."""
        return ()

    def leaf_collections(self) -> List[Tuple[str, Tuple[int, ...]]]:
        """All ``(collection, accessor)`` pairs found at the leaves of the
        tree. Used by ``_top_level_signature`` to populate child keys for
        region-cut bucketing — composite cuts contribute every collection
        they reference."""
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Concrete kinds
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class NumNode(ExprNode):
    """Numeric literal."""
    value: float

    def signature(self) -> str:
        # Values are stripped from structural signatures so cuts that
        # differ only in threshold (e.g. pT > 30 vs pT > 50) bucket
        # together and then differentiate at the interval-comparison step.
        return "#"

    def full_signature(self) -> str:
        return f"#{_fmt_num(self.value)}"

    def pretty(self) -> str:
        return _fmt_num(self.value)


@dataclass(frozen=True)
class IdNode(ExprNode):
    """Bare identifier with optional slice accessor.

    Covers two cases:
      * collection references in arithmetic context (e.g. ``MET`` in
        ``MET > 300``, where ``MET`` is a built-in scalar);
      * unresolved define names that survive substitution (rare, but
        possible — handled defensively).
    """
    collection: str
    accessor: Tuple[int, ...] = ()

    def signature(self) -> str:
        return f"id:{self.collection.lower()}|{_accessor_token(self.accessor)}"

    def full_signature(self) -> str:
        return self.signature()  # no numeric values to add

    def pretty(self) -> str:
        if not self.accessor:
            return self.collection
        if len(self.accessor) == 2 and self.accessor[1] == self.accessor[0] + 1:
            return f"{self.collection}[{self.accessor[0]}]"
        return f"{self.collection}[{self.accessor[0]}:{self.accessor[1]}]"

    def primary_collection(self) -> str:
        return self.collection

    def primary_accessor(self) -> Tuple[int, ...]:
        return self.accessor

    def leaf_collections(self) -> List[Tuple[str, Tuple[int, ...]]]:
        return [(self.collection, self.accessor)]


@dataclass(frozen=True)
class FuncNode(ExprNode):
    """Function chain applied to one or more inner expressions.

    ``func_chain`` is the same dotted-circle convention used elsewhere in
    the IR: ``"pt"``, ``"abs∘eta"``, ``"sqrt"``. ``args`` is the tuple of
    argument expressions in source order. Most ADL functions are
    single-arg (``pT(JET)``, ``abs(eta(JET))``) and produce
    ``args=(IdNode(...),)`` or ``(BinOpNode(...),)``; multi-arg
    functions like ``dR(j, m)``, ``M(p1, p2, p3)``, or
    ``dPhi(METLV[0], pT(j))`` carry every argument so that the
    structural signature reflects all of them.

    Argument order is preserved (treated as non-commutative). Some
    functions in the physics domain are commutative (``dR``, ``M``)
    while others aren't (``dPhi`` modulo sign), and the modeller does
    not know which a user-defined function is. Treating order as
    significant by default is the conservative choice; symmetric
    functions can be added to a known-commutative list in a later
    extension if needed.

    Chain collapsing
    ----------------
    The ``"abs∘eta"`` chain encoding only fires for single-parameter
    function chains: ``abs(eta(JET))`` collapses to one FuncNode
    ``args=(IdNode(JET),)``. Multi-arg functions terminate the
    collapse — they stay as one FuncNode wrapping the full argument
    tuple.

    Backwards-compatibility property: ``inner``
    -------------------------------------------
    Reads ``self.args[0]`` (or an empty IdNode if args is empty).
    Existing code that treats FuncNode as single-arg-and-walks via
    ``.inner`` continues to work for cuts that were single-arg before
    this refactor; for multi-arg cuts ``inner`` returns the first
    argument, which is the most-specific reading we can offer
    legacy callers.
    """
    func_chain: str
    args: Tuple[ExprNode, ...]

    def __post_init__(self):
        # A FuncNode must reference at least one argument expression —
        # zero-arg FUNCTION ASTs are degenerate and shouldn't reach the
        # ExprNode layer. Defensive check.
        if not self.args:
            raise ValueError(
                f"FuncNode {self.func_chain!r} requires at least one argument"
            )

    @property
    def inner(self) -> ExprNode:
        """Backwards-compatibility alias for ``args[0]``.

        Pre-refactor, FuncNode held a single ``inner: ExprNode``. Code
        that walked ``.inner`` to find the innermost IdNode (e.g.
        ``primary_collection`` chains) still works correctly for
        single-arg / chain-collapsed FuncNodes; for multi-arg FuncNodes
        it returns the first argument, which is a reasonable
        approximation of "the primary argument" but consumers that
        actually care about all arguments should iterate ``args``.
        """
        return self.args[0]

    def signature(self) -> str:
        # Signature includes every argument's signature in order. This is
        # what discriminates ``dR(JET[0:1], MET[0])`` from
        # ``dR(JET[0:2], MET[0])`` — the AK4jets accessor lives in the
        # second argument's IdNode signature.
        parts = ",".join(a.signature() for a in self.args)
        return f"fn:{self.func_chain.lower()}({parts})"

    def full_signature(self) -> str:
        parts = ",".join(a.full_signature() for a in self.args)
        return f"fn:{self.func_chain.lower()}({parts})"

    def pretty(self) -> str:
        if len(self.args) == 1:
            return f"{self.func_chain}({self.args[0].pretty()})"
        return f"{self.func_chain}({', '.join(a.pretty() for a in self.args)})"

    def outer_func_chain(self) -> str:
        return self.func_chain

    def primary_collection(self) -> str:
        # Only meaningful for single-arg / chain-collapsed FuncNodes:
        # walk through nested FuncNodes until we hit an IdNode, return
        # its collection. Multi-arg FuncNodes have no single primary
        # collection — return "" and let the caller handle the
        # multi-collection case via ``leaf_collections()``.
        if len(self.args) != 1:
            return ""
        node: ExprNode = self.args[0]
        while isinstance(node, FuncNode) and len(node.args) == 1:
            node = node.args[0]
        if isinstance(node, IdNode):
            return node.collection
        return ""

    def primary_accessor(self) -> Tuple[int, ...]:
        if len(self.args) != 1:
            return ()
        node: ExprNode = self.args[0]
        while isinstance(node, FuncNode) and len(node.args) == 1:
            node = node.args[0]
        if isinstance(node, IdNode):
            return node.accessor
        return ()

    def leaf_collections(self) -> List[Tuple[str, Tuple[int, ...]]]:
        out: List[Tuple[str, Tuple[int, ...]]] = []
        for a in self.args:
            out.extend(a.leaf_collections())
        return out


# Operators recognised by BinOpNode. Commutative ones are flattened and
# sorted at construction; non-commutative ones preserve operand order.
_COMMUTATIVE_OPS = frozenset({"+", "*"})
_BINARY_OPS      = frozenset({"+", "-", "*", "/"})


@dataclass(frozen=True)
class BinOpNode(ExprNode):
    """Binary operator: + - * /.

    For commutative ops (+ and *), ``children`` is an n-ary tuple
    (canonicalised: nested same-op children are flattened, all children
    sorted by signature). For non-commutative ops (- and /), ``children``
    has length exactly 2 in source order.
    """
    op: str
    children: Tuple[ExprNode, ...]

    def __post_init__(self):
        if self.op not in _BINARY_OPS:
            raise ValueError(f"BinOpNode op must be one of {_BINARY_OPS}, "
                             f"got {self.op!r}")
        if len(self.children) < 2:
            raise ValueError(
                f"BinOpNode needs ≥2 children, got {len(self.children)} "
                f"for op {self.op!r}"
            )
        if self.op not in _COMMUTATIVE_OPS and len(self.children) != 2:
            # `a - b - c` is left-associative in source; the parser
            # produces BinOp("-", BinOp("-", a, b), c), and we keep it
            # that way. Flattening into ternary would change semantics.
            raise ValueError(
                f"Non-commutative op {self.op!r} requires exactly 2 children, "
                f"got {len(self.children)}"
            )

    @property
    def is_leaf(self) -> bool:
        return False

    def signature(self) -> str:
        # Children are pre-sorted at construction for commutative ops, so
        # this just renders. Re-sorting here would be defensive but redundant.
        parts = [c.signature() for c in self.children]
        return f"{self.op}({','.join(parts)})"

    def full_signature(self) -> str:
        parts = [c.full_signature() for c in self.children]
        if self.op in _COMMUTATIVE_OPS:
            # Sort by full_signature for stable hashing; commutative-flatten
            # already happened at construction so nesting structure is fixed.
            parts.sort()
        return f"{self.op}({','.join(parts)})"

    def pretty(self) -> str:
        joined = f" {self.op} ".join(c.pretty() for c in self.children)
        return f"({joined})"

    def leaf_collections(self) -> List[Tuple[str, Tuple[int, ...]]]:
        out: List[Tuple[str, Tuple[int, ...]]] = []
        for c in self.children:
            out.extend(c.leaf_collections())
        return out


@dataclass(frozen=True)
class OpaqueNode(ExprNode):
    """Escape hatch for AST shapes we don't model structurally.

    The intent is that this category be vanishingly small for well-formed
    ADL files. When it does fire (e.g. ITE conditional embedded in a cut
    LHS), the source text is preserved verbatim so two identical opaque
    subtrees still compare EQUAL by string. Distinct opaque subtrees
    compare OVERLAP — we cannot prove DISJOINT without understanding the
    structure.

    ``leaf_refs`` carries the collection references the IR builder found
    inside the opaque region, so ``leaf_collections()`` and the bucketing
    code can still build correct child keys.
    """
    repr_str: str
    leaf_refs: Tuple[Tuple[str, Tuple[int, ...]], ...] = ()

    @property
    def is_leaf(self) -> bool:
        # Treated as leaf for dispatch purposes — no structural recursion
        # is possible.
        return True

    def signature(self) -> str:
        return f"opaque:{self.repr_str}"

    def full_signature(self) -> str:
        return self.signature()

    def pretty(self) -> str:
        return self.repr_str

    def leaf_collections(self) -> List[Tuple[str, Tuple[int, ...]]]:
        return list(self.leaf_refs)


# ─────────────────────────────────────────────────────────────────────────────
# Factory functions — always produce canonical trees
# ─────────────────────────────────────────────────────────────────────────────

def num(v: float) -> NumNode:
    """Make a numeric literal node. Integer-valued floats and ints collapse."""
    # Ensure 2 and 2.0 are the same node by canonicalising to float.
    return NumNode(value=float(v))


def ident(collection: str, accessor: Tuple[int, ...] = ()) -> IdNode:
    """Make an identifier node."""
    return IdNode(collection=collection, accessor=tuple(accessor))


def fn(chain: str, *args: ExprNode) -> FuncNode:
    """Make a function-application node with one or more arguments.

    Each argument is taken as-is — callers should pass already-canonical
    ExprNodes (the AST builder does so naturally).

    Single-arg use (``fn('pt', ident('JET'))``) is the common case.
    Multi-arg use (``fn('dR', ident('JET'), ident('MET'))``) is what
    distinguishes ``dR(JET[0:1], MET[0])`` from ``dR(JET[0:2], MET[0])``
    in the structural signature: both arguments contribute, and the
    accessor on each IdNode flows through.
    """
    if not args:
        raise ValueError(f"fn({chain!r}) requires at least one argument")
    return FuncNode(func_chain=chain, args=tuple(args))


def binop(op: str, *children: ExprNode) -> ExprNode:
    """Make a binary-op node, canonicalising on the way in.

    For commutative ops (+, *):
      1. Flatten any child that is a same-op BinOpNode into the parent.
      2. Sort the resulting children by signature.
      3. If exactly one child remains after flattening (degenerate case
         that shouldn't happen with valid input), return it directly.

    For non-commutative ops (-, /), arity is fixed at 2 and order is
    preserved.
    """
    if op not in _BINARY_OPS:
        raise ValueError(f"binop: op must be one of {_BINARY_OPS}, got {op!r}")

    if op in _COMMUTATIVE_OPS:
        flat: List[ExprNode] = []
        for c in children:
            if isinstance(c, BinOpNode) and c.op == op:
                flat.extend(c.children)
            else:
                flat.append(c)
        # Sort by signature for canonical ordering. signature() is
        # numeric-value-free so `2 + x` and `5 + x` sort identically by
        # signature — but they remain distinct nodes via full_signature.
        # The deterministic order is what matters for structural matching.
        flat.sort(key=lambda n: n.signature())
        if len(flat) == 1:
            return flat[0]
        return BinOpNode(op=op, children=tuple(flat))

    if len(children) != 2:
        raise ValueError(
            f"binop({op!r}, ...) requires exactly 2 children, got {len(children)}"
        )
    return BinOpNode(op=op, children=tuple(children))


def opaque(repr_str: str,
           leaf_refs: Tuple[Tuple[str, Tuple[int, ...]], ...] = ()
           ) -> OpaqueNode:
    """Make an opaque-subtree node."""
    return OpaqueNode(repr_str=repr_str, leaf_refs=tuple(leaf_refs))


# ─────────────────────────────────────────────────────────────────────────────
# AST → ExprNode builder
# ─────────────────────────────────────────────────────────────────────────────
# Imports from ir_extractor are deferred to keep module load order clean:
# expr_node has no compile-time dependency on ir_extractor.

def build_expr_node(expr: dict, expr_repr_fn=None) -> ExprNode:
    """Build a canonical ExprNode tree from a (resolved) AST dict.

    ``expr_repr_fn`` is optional and only used when fabricating ``OpaqueNode``
    instances for unmodelled subtrees — passing in ``ir_extractor._expr_repr``
    keeps the rendering consistent. If omitted, ``str(expr)`` is used,
    which is ugly but functional.
    """
    if expr_repr_fn is None:
        expr_repr_fn = _fallback_repr

    tok = expr.get("tok") if isinstance(expr, dict) else ""

    if tok in ("INT", "REAL"):
        return num(expr["value"])

    if tok == "ID":
        from ir_extractor import _normalise_accessor  # local: avoid cycle
        return ident(expr["id"], _normalise_accessor(expr.get("accessor", [])))

    if tok == "FUNCTION":
        # Reproduce the existing chain-collapsing behaviour used by
        # _extract_func_chain_and_collection: a function whose single
        # parameter is itself a function gets folded into a chain like
        # "abs∘eta" with the deepest argument as inner. This keeps the
        # signature compatible with the legacy func_chain field.
        return _build_func_chain(expr, expr_repr_fn)

    if tok in ("EXPROP", "FACTOROP"):
        op = expr["op"]
        if op not in _BINARY_OPS:
            # Unknown arithmetic operator — fall back to opaque rather
            # than guess. This is defensive; the parser should only emit
            # the four standard ops.
            return _opaque_from(expr, expr_repr_fn)
        lhs = build_expr_node(expr["lhs"], expr_repr_fn)
        rhs = build_expr_node(expr["rhs"], expr_repr_fn)
        return binop(op, lhs, rhs)

    # Anything else (LOGICOP, ITE, COMPAREOP nested in an LHS, etc.) is
    # unmodelled at this layer. The caller is expected to split on
    # LOGICOP/COMPAREOP before reaching here, so this is a safety net.
    return _opaque_from(expr, expr_repr_fn)


def _build_func_chain(expr: dict, expr_repr_fn) -> ExprNode:
    """Walk a FUNCTION subtree and collapse single-parameter chains.

    ``abs(eta(JET))`` → FuncNode("abs∘eta", args=(IdNode("JET"),)).
    ``sqrt(2 * pT(Trk) * ...)`` → FuncNode("sqrt", args=(BinOpNode("*", ...),)).
    ``cos(Phi(METLV[0]) - Phi(Trk))`` → FuncNode("cos", args=(BinOpNode("-", ...),)).
    ``dR(JET[0:1], MET[0])`` → FuncNode("dR", args=(IdNode(JET, (0,1)), IdNode(MET, (0,1)))).

    Chain collapsing is single-arg only. As soon as a function has more
    than one parameter, we stop the collapse and emit a multi-arg
    FuncNode whose ``args`` tuple contains every parameter built as its
    own ExprNode. This preserves accessor information on every argument,
    which is what discriminates ``dR(JET[0:1], MET[0])`` from
    ``dR(JET[0:2], MET[0])`` in the structural signature.

    Pre-refactor, only ``params[0]`` was retained and the remaining
    parameters were silently dropped — a long-standing bug that caused
    multi-arg cuts differing only in a non-primary argument's slice to
    incorrectly bucket together as identical.
    """
    chain_parts: List[str] = [expr["id"].lower()]
    inner_expr: dict = expr
    while True:
        params = inner_expr.get("params", [])
        if len(params) != 1:
            # Multi-arg (or zero-arg): stop collapsing the chain. The
            # function we just landed on is the outermost multi-arg
            # function; emit a FuncNode with the full args tuple.
            break
        inner_param = params[0]
        if inner_param.get("tok") == "FUNCTION" and len(inner_param.get("params", [])) == 1:
            # Single-arg function chained inside another single-arg
            # function — extend the chain.
            chain_parts.append(inner_param["id"].lower())
            inner_expr = inner_param
            continue
        # Single-param function whose param is not a single-arg FUNCTION
        # (it's an ID, a BinOp, a multi-arg FUNCTION, etc.): terminate
        # the chain.
        chain = "∘".join(chain_parts)
        inner_node = build_expr_node(inner_param, expr_repr_fn)
        return fn(chain, inner_node)

    # Fell out of the loop because of a multi-arg or zero-arg function.
    chain = "∘".join(chain_parts)
    params = inner_expr.get("params", [])
    if not params:
        # Zero-arg function — degenerate; shouldn't appear in cut LHSes.
        # Emit a single empty IdNode arg as a defensive placeholder.
        return fn(chain, ident(""))

    # Multi-arg case: every parameter becomes an arg in the FuncNode,
    # built recursively so its own structure (accessors, nested funcs,
    # arithmetic) is preserved in the signature.
    arg_nodes = tuple(build_expr_node(p, expr_repr_fn) for p in params)
    return fn(chain, *arg_nodes)


def _opaque_from(expr: dict, expr_repr_fn) -> OpaqueNode:
    """Build an OpaqueNode preserving the source rendering and the
    collection refs found inside the unmodelled subtree."""
    refs: List[Tuple[str, Tuple[int, ...]]] = []
    _collect_refs(expr, refs)
    return opaque(expr_repr_fn(expr), tuple(refs))


def _collect_refs(expr, out: List[Tuple[str, Tuple[int, ...]]]):
    """Walk an arbitrary AST subtree collecting (collection, accessor)
    pairs from ID leaves. Used to populate OpaqueNode.leaf_refs."""
    if not isinstance(expr, dict):
        return
    tok = expr.get("tok", "")
    if tok == "ID":
        from ir_extractor import _normalise_accessor
        out.append((expr["id"], _normalise_accessor(expr.get("accessor", []))))
        return
    if tok == "FUNCTION":
        for p in expr.get("params", []):
            _collect_refs(p, out)
        return
    if tok in ("EXPROP", "FACTOROP", "COMPAREOP", "LOGICOP"):
        _collect_refs(expr.get("lhs"), out)
        _collect_refs(expr.get("rhs"), out)
        return
    if tok == "ITE":
        _collect_refs(expr.get("condition"), out)
        _collect_refs(expr.get("then"), out)
        _collect_refs(expr.get("else"), out)
        return


def _fallback_repr(expr) -> str:
    """Stand-in for ir_extractor._expr_repr when the caller didn't supply
    one. Functional but ugly; production callers should always pass the
    real renderer."""
    return repr(expr)


# ─────────────────────────────────────────────────────────────────────────────
# Comparison
# ─────────────────────────────────────────────────────────────────────────────

def compare_expr(a: ExprNode, b: ExprNode) -> str:
    """Compare two ExprNode trees structurally.

    Returns DISJOINT / EQUAL / SUBSET / SUPERSET / OVERLAP.

    Soundness invariant
    -------------------
    ``compare_expr(a, b) == EQUAL`` iff ``a`` and ``b`` are guaranteed to
    evaluate to the same value on every event by virtue of identical
    canonical structure. SUBSET/SUPERSET are *not* produced by this
    function — they only emerge at the cut level (interval comparison
    of thresholds), because expression-level set relations would require
    monotonicity reasoning we don't do here. Anything weaker than EQUAL
    is OVERLAP (or DISJOINT for definitively different shapes).

    Per-kind rules
    --------------
    * Both NumNode    → EQUAL if values equal, else DISJOINT.
    * Both IdNode     → EQUAL if (collection, accessor) match.
                        Same collection, different accessor → OVERLAP
                        (slice arithmetic is out of scope per Q2).
                        Different collection → DISJOINT.
    * Both FuncNode   → if func_chain differs → DISJOINT;
                        else recurse into inner.
    * Both BinOpNode  → if op differs → DISJOINT;
                        commutative: bipartite-match children;
                        non-commutative: zip pairwise.
                        Different child count → DISJOINT.
    * Both OpaqueNode → EQUAL if repr_str matches exactly, else OVERLAP.
    * Mixed kinds     → DISJOINT for clear shape mismatch.
    """
    # Short-circuit on identity / canonical equality. Cheap and frequent
    # because canonicalisation makes equivalent trees `==`-equal.
    if a is b or a == b:
        return EQUAL

    # ── Same-kind cases ──────────────────────────────────────────────────
    if isinstance(a, NumNode) and isinstance(b, NumNode):
        return EQUAL if a.value == b.value else DISJOINT

    if isinstance(a, IdNode) and isinstance(b, IdNode):
        if a.collection.lower() != b.collection.lower():
            return DISJOINT
        if a.accessor == b.accessor:
            return EQUAL
        # Same collection, different slice accessor. Could in principle
        # be SUBSET/SUPERSET (e.g. JET[0] is one element of JET[0:3]) —
        # that is Q2 territory and we keep current behaviour: report
        # OVERLAP and let outer logic decide.
        return OVERLAP

    if isinstance(a, FuncNode) and isinstance(b, FuncNode):
        if a.func_chain.lower() != b.func_chain.lower():
            return DISJOINT
        if len(a.args) != len(b.args):
            # Same name, different arity → can't reasonably claim equality.
            # In practice this shouldn't happen for the same user-defined
            # function across two ADLs; if it does, the cuts are
            # genuinely different.
            return DISJOINT
        # Same outer function and arity — recurse pairwise on args.
        # Argument order is preserved (non-commutative by default; see
        # the FuncNode docstring on commutativity). EQUAL inners give
        # EQUAL func node; anything weaker propagates via _combine.
        contribs = [compare_expr(ai, bi) for ai, bi in zip(a.args, b.args)]
        return _combine(contribs)

    if isinstance(a, BinOpNode) and isinstance(b, BinOpNode):
        return _compare_binop(a, b)

    if isinstance(a, OpaqueNode) and isinstance(b, OpaqueNode):
        return EQUAL if a.repr_str == b.repr_str else OVERLAP

    # ── Cross-kind: definitively different shapes ───────────────────────
    # A FuncNode can never equal a NumNode regardless of internal
    # contents; a BinOpNode is never a leaf. These are structural
    # mismatches that we return DISJOINT for. The exception we considered
    # was OpaqueNode-vs-anything: an opaque subtree might *contain* the
    # other shape, so we don't want to claim DISJOINT. Use OVERLAP.
    if isinstance(a, OpaqueNode) or isinstance(b, OpaqueNode):
        return OVERLAP
    return DISJOINT


def _compare_binop(a: BinOpNode, b: BinOpNode) -> str:
    """Compare two BinOpNodes. Op must be tested first — different ops
    never compare to EQUAL or anything weaker than DISJOINT."""
    if a.op != b.op:
        return DISJOINT
    if len(a.children) != len(b.children):
        # `a + b` vs `a + b + c` are structurally different. After
        # commutative-flattening at construction these can't accidentally
        # arise from associativity differences — they really are
        # different multisets.
        return DISJOINT

    if a.op in _COMMUTATIVE_OPS:
        # Bipartite-match children. Try to find an assignment from A's
        # children to B's children that makes the combined verdict
        # EQUAL; failing that, the best we can produce is OVERLAP.
        return _commutative_match(a.children, b.children)

    # Non-commutative: zip pairwise. Order matters for - and /.
    contribs = [compare_expr(ca, cb) for ca, cb in zip(a.children, b.children)]
    return _combine(contribs)


# Threshold above which we switch from full-permutation matching (n!) to
# a greedy assignment. n=4 is 24 permutations — cheap. n=5 is 120 —
# still fine. Beyond that the input is unusual and greedy is the
# pragmatic choice.
_PERMUTE_LIMIT = 5


def _commutative_match(a_children: Tuple[ExprNode, ...],
                       b_children: Tuple[ExprNode, ...]) -> str:
    """Try every permutation of B's children against A's; return the
    best (closest-to-EQUAL) combined verdict.

    Because both sides are pre-sorted by signature at construction, the
    *identity* permutation usually already gives the right answer when
    the trees are equivalent. Trying other permutations only matters when
    children differ in numeric values but agree in structure — e.g.
    ``pT(j) > 30  +  size(j)`` and ``size(j)  +  pT(j) > 30`` would
    already match by identity, but ``2*x + 3*y`` vs ``3*y + 2*x`` could
    trip up if the signatures of ``2*x`` and ``3*y`` happened to sort
    differently. Permutation handles those edge cases.
    """
    n = len(a_children)
    if n == 0:
        return EQUAL

    if n > _PERMUTE_LIMIT:
        return _greedy_match(a_children, b_children)

    best: Optional[str] = None
    for perm in permutations(range(n)):
        contribs = [compare_expr(a_children[i], b_children[perm[i]])
                    for i in range(n)]
        v = _combine(contribs)
        if v == EQUAL:
            return EQUAL  # can't do better than this
        # Track the strongest non-EQUAL outcome. Order of preference:
        # SUBSET/SUPERSET stronger than OVERLAP stronger than DISJOINT.
        # (Best for the *reporter*: stronger structural agreement.)
        best = _better_verdict(best, v)
    return best if best is not None else DISJOINT


def _greedy_match(a_children: Tuple[ExprNode, ...],
                  b_children: Tuple[ExprNode, ...]) -> str:
    """Greedy O(n²) fallback for unusually large commutative chains.

    For each A-child, pick the unmatched B-child that gives the best
    pairwise verdict. Not optimal in pathological cases but the input
    sizes that hit this branch are rare.
    """
    used: List[bool] = [False] * len(b_children)
    contribs: List[str] = []
    for ca in a_children:
        best_idx: Optional[int] = None
        best_v: Optional[str] = None
        for j, cb in enumerate(b_children):
            if used[j]:
                continue
            v = compare_expr(ca, cb)
            if v == EQUAL:
                best_idx = j
                best_v = v
                break
            if best_v is None or _better_verdict(best_v, v) == v:
                best_idx = j
                best_v = v
        if best_idx is None:
            return DISJOINT
        used[best_idx] = True
        contribs.append(best_v if best_v is not None else DISJOINT)
    return _combine(contribs)


_VERDICT_RANK = {EQUAL: 4, SUBSET: 3, SUPERSET: 3, OVERLAP: 2, DISJOINT: 1}


def _better_verdict(current: Optional[str], candidate: str) -> str:
    """Return whichever of ``current`` and ``candidate`` is closer to EQUAL."""
    if current is None:
        return candidate
    if _VERDICT_RANK[candidate] > _VERDICT_RANK[current]:
        return candidate
    return current


# ─────────────────────────────────────────────────────────────────────────────
# Module exports
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    "ExprNode", "NumNode", "IdNode", "FuncNode", "BinOpNode", "OpaqueNode",
    "num", "ident", "fn", "binop", "opaque",
    "build_expr_node", "compare_expr",
    "DISJOINT", "EQUAL", "SUBSET", "SUPERSET", "OVERLAP",
]
