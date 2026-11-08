"""
overlap_checker.py  (v6 – 5-value lattice + recursive dependency comparison)
=============================================================================

Labelling rules (per-region-pair, first match wins; output is one of
DISJOINT / EQUAL / SUBSET / SUPERSET / OVERLAP):

  Rule 1 — No shared built-in collections at all  →  DISJOINT.

  Rule 2 — Per-region-variable comparison (recursive descent):
           For every candidate pair of region variables (same top-level
           function on collections with the same built-in root), walk
           both dependency trees jointly and compose a directional
           verdict from:
             * leaf cut nodes (interval arithmetic on the per-axis
               acceptance sets),
             * define nodes (children composed),
             * object nodes (cumulative-cuts per-variable comparison).
           Aggregation is bottom-up and uses the 5-value lattice.

           Pairing is *slice-aware*: each top-level argument key carries
           the constraint's normalised accessor (e.g. "jets|0:3" for a
           slice, "jets|*" for the whole collection). Cuts with different
           slice ranges fall into different buckets and therefore go
           through Rule 3 as unmatched, contributing directionally
           instead of being equated. Two cuts only run through the leaf
           classifier together when their accessors match exactly.

  Rule 3 — Unmatched region variables contribute directionally:
             * A-side only  →  A⊆B contribution
             * B-side only  →  B⊆A contribution

  Rule 4 — Combine contributions into a region-pair verdict:
             * any DISJOINT                                →  DISJOINT
             * all EQUAL, no unmatched either side         →  EQUAL
             * all {EQUAL, A⊆B}, no B-only unmatched       →  SUBSET
             * all {EQUAL, B⊆A}, no A-only unmatched       →  SUPERSET
             * mixed or any OVERLAP                        →  OVERLAP

ADL-pair aggregation:
  * any region pair DISJOINT  →  ADL DISJOINT
  * otherwise                  →  ADL OVERLAP
  (region-level EQUAL/SUBSET/SUPERSET are surfaced in reports but not
  lifted to the ADL verdict.)

Assumption on input ADLs: every ADL has an explicit `size(obj) >= i+1`
cut wherever `obj[i]` is used in a define or region. No implicit size
constraints are inferred here.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from ir_extractor import (
    AnalysisIR, ObjectIR, RegionIR, ResolvedCutIR,
    CutStructure,
    ConstraintExpr, ConstraintLeaf, ConstraintAnd, ConstraintOr,
    constraint_expr_leaves,
    CutDependency, CutRootDependency, DefineDependency,
    BuiltinDependency, ObjectDependency,
    BUILTIN_OBJECTS, canonicalise,
)
from expr_node import compare_expr, BinOpNode, FuncNode, IdNode

# ─────────────────────────────────────────────────────────────────────────────
# 5-value verdict lattice
# ─────────────────────────────────────────────────────────────────────────────

DISJOINT = "DISJOINT"
EQUAL    = "EQUAL"
SUBSET   = "SUBSET"      # A ⊆ B (A is a subset of B)
SUPERSET = "SUPERSET"    # A ⊇ B (A is a superset of B)
OVERLAP  = "OVERLAP"

# Report-only sentinel: a cross-pair whose two sides reference DISJOINT
# underlying sub-collections under a cardinality reducer. The pair
# carries no event-level information about region containment, so it is
# excluded from verdict aggregation; we still emit a row for it so the
# user can see the pair was considered. Never fed to ``_combine``.
INCOMPARABLE = "INCOMPARABLE"

ALL_VERDICTS = (DISJOINT, EQUAL, SUBSET, SUPERSET, OVERLAP)


def _combine(verdicts: List[str]) -> str:
    """
    Bottom-up composition rule used everywhere in the recursive descent:

      * any DISJOINT                          → DISJOINT
      * all EQUAL                              → EQUAL
      * all in {EQUAL, SUBSET}                 → SUBSET
      * all in {EQUAL, SUPERSET}               → SUPERSET
      * mixed SUBSET+SUPERSET or any OVERLAP   → OVERLAP
      * empty list                             → EQUAL (neutral element)
    """
    if not verdicts:
        return EQUAL
    if any(v == DISJOINT for v in verdicts):
        return DISJOINT
    if any(v == OVERLAP for v in verdicts):
        return OVERLAP
    has_sub = any(v == SUBSET for v in verdicts)
    has_sup = any(v == SUPERSET for v in verdicts)
    if has_sub and has_sup:
        return OVERLAP
    if has_sub:
        return SUBSET
    if has_sup:
        return SUPERSET
    return EQUAL


def _flip(v: str) -> str:
    """Flip SUBSET↔SUPERSET; leave the rest unchanged."""
    if v == SUBSET:   return SUPERSET
    if v == SUPERSET: return SUBSET
    return v


# ─────────────────────────────────────────────────────────────────────────────
# Interval arithmetic
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Interval:
    lo: float = -math.inf
    hi: float = math.inf
    lo_open: bool = False
    hi_open: bool = False

    def is_empty(self) -> bool:
        if self.lo > self.hi: return True
        if self.lo == self.hi and (self.lo_open or self.hi_open): return True
        return False

    def intersect(self, other: "Interval") -> "Interval":
        if other.lo > self.lo:    new_lo, new_lo_open = other.lo, other.lo_open
        elif other.lo == self.lo: new_lo, new_lo_open = self.lo, self.lo_open or other.lo_open
        else:                     new_lo, new_lo_open = self.lo, self.lo_open

        if other.hi < self.hi:    new_hi, new_hi_open = other.hi, other.hi_open
        elif other.hi == self.hi: new_hi, new_hi_open = self.hi, self.hi_open or other.hi_open
        else:                     new_hi, new_hi_open = self.hi, self.hi_open

        return Interval(new_lo, new_hi, new_lo_open, new_hi_open)

    def __repr__(self):
        lo_br = "(" if self.lo_open else "["
        hi_br = ")" if self.hi_open else "]"
        lo_s  = "-∞" if self.lo == -math.inf else _fmt(self.lo)
        hi_s  = "+∞" if self.hi ==  math.inf else _fmt(self.hi)
        return f"{lo_br}{lo_s}, {hi_s}{hi_br}"


def _fmt(v: float) -> str:
    return str(int(v)) if v == int(v) else str(v)



def constraint_to_interval(fc: CutStructure) -> Interval:
    op = fc.effective_op()
    v  = fc.threshold
    if op == ">":  return Interval(v, math.inf, lo_open=True)
    if op == ">=": return Interval(v, math.inf)
    if op == "<":  return Interval(-math.inf, v, hi_open=True)
    if op == "<=": return Interval(-math.inf, v)
    if op == "==": return Interval(v, v)
    return Interval(-math.inf, math.inf)


# ─────────────────────────────────────────────────────────────────────────────
# IntervalSet — union of disjoint intervals on a single axis
# ─────────────────────────────────────────────────────────────────────────────
# A single Interval can't represent the acceptance region of a cut like
#   reject abs(eta) [] 1.44 1.56
# whose meaning is `abs(eta) < 1.44  OR  abs(eta) > 1.56` — two open
# half-lines with a forbidden band in between. The IntervalSet is an
# ordered sequence of pairwise-disjoint, non-empty intervals representing
# such a union. Operations preserve the disjoint-and-sorted invariant.
#
# Convention: the empty set has zero intervals; the "everything" set has
# one interval (-∞, +∞). Construction normalises (sorts, merges adjacent
# or overlapping intervals, drops empty ones).

@dataclass
class IntervalSet:
    """Union of disjoint intervals on a single real axis.

    The ``intervals`` list is always sorted by lo and pairwise-disjoint.
    Two intervals ``(a, b)`` and ``(c, d)`` are merged when ``b > c`` or
    ``b == c`` and they share an endpoint inclusively. Empty intervals
    are dropped.
    """
    intervals: List[Interval] = field(default_factory=list)

    def __post_init__(self):
        # Defensive normalisation: callers may pass a raw list.
        self.intervals = self._normalise(list(self.intervals))

    # ── Construction helpers ────────────────────────────────────────────
    @classmethod
    def empty(cls) -> "IntervalSet":
        return cls(intervals=[])

    @classmethod
    def everything(cls) -> "IntervalSet":
        return cls(intervals=[Interval(-math.inf, math.inf)])

    @classmethod
    def from_interval(cls, iv: Interval) -> "IntervalSet":
        if iv.is_empty():
            return cls.empty()
        return cls(intervals=[iv])

    @classmethod
    def from_constraint(cls, fc: CutStructure) -> "IntervalSet":
        """Build an IntervalSet from one CutStructure.

        ``!=`` produces a two-interval union; everything else is a single
        interval (or empty/everything).
        """
        op = fc.effective_op()
        v  = fc.threshold
        if op == "!=":
            return cls(intervals=[
                Interval(-math.inf, v, hi_open=True),
                Interval(v, math.inf, lo_open=True),
            ])
        return cls.from_interval(constraint_to_interval(fc))

    # ── Internal: normalisation ─────────────────────────────────────────
    @staticmethod
    def _normalise(items: List[Interval]) -> List[Interval]:
        """Sort by lo, drop empties, merge overlapping/adjacent intervals.

        Two intervals are *adjacent and mergeable* when one ends where
        the other begins and at least one endpoint at the join is closed.
        E.g. ``(-∞, 5)`` and ``[5, 10)`` merge to ``(-∞, 10)``; but
        ``(-∞, 5)`` and ``(5, 10)`` stay separate (the value 5 itself is
        excluded from both, so the union has a one-point gap there).
        """
        items = [iv for iv in items if not iv.is_empty()]
        if not items:
            return []
        items.sort(key=lambda iv: (iv.lo, iv.lo_open))
        out: List[Interval] = [items[0]]
        for iv in items[1:]:
            cur = out[-1]
            # Determine if iv starts at-or-before cur.hi (with appropriate
            # open/closed handling) — if so, merge.
            if iv.lo < cur.hi:
                merge = True
            elif iv.lo == cur.hi:
                # Touching: merge unless BOTH endpoints at the join are open.
                merge = not (cur.hi_open and iv.lo_open)
            else:
                merge = False

            if merge:
                # Extend cur with iv. New hi is the max; preserve openness
                # such that closed wins over open at the boundary.
                if iv.hi > cur.hi:
                    new_hi, new_hi_open = iv.hi, iv.hi_open
                elif iv.hi == cur.hi:
                    new_hi, new_hi_open = cur.hi, cur.hi_open and iv.hi_open
                else:
                    new_hi, new_hi_open = cur.hi, cur.hi_open
                # lo stays as cur.lo since items are sorted by lo. Same
                # closed-wins rule at the lo boundary if iv.lo == cur.lo.
                new_lo, new_lo_open = cur.lo, cur.lo_open
                if iv.lo == cur.lo and not iv.lo_open:
                    new_lo_open = False
                out[-1] = Interval(new_lo, new_hi, new_lo_open, new_hi_open)
            else:
                out.append(iv)
        return out

    # ── Predicates ───────────────────────────────────────────────────────
    def is_empty(self) -> bool:
        return not self.intervals

    def is_everything(self) -> bool:
        if len(self.intervals) != 1:
            return False
        iv = self.intervals[0]
        return (iv.lo == -math.inf and iv.hi == math.inf
                and not iv.lo_open and not iv.hi_open)

    # ── Set operations ───────────────────────────────────────────────────
    def intersect(self, other: "IntervalSet") -> "IntervalSet":
        """Intersection: pairwise-intersect every (a, b) ∈ self × other.

        Result is automatically disjoint-and-sorted because the
        normalisation pass merges and orders. O(n*m) in the number of
        intervals; n+m would be possible with a sweep but the input
        sizes here are tiny.
        """
        out: List[Interval] = []
        for a in self.intervals:
            for b in other.intervals:
                inter = a.intersect(b)
                if not inter.is_empty():
                    out.append(inter)
        return IntervalSet(intervals=out)

    def union(self, other: "IntervalSet") -> "IntervalSet":
        """Union: concatenate and let normalisation merge."""
        return IntervalSet(intervals=self.intervals + other.intervals)

    def contains_set(self, other: "IntervalSet") -> bool:
        """Test whether ``other ⊆ self``.

        Done by: every interval of ``other`` must be contained in some
        single interval of ``self`` (because both sides are disjoint-
        sorted, an ``other``-interval that spans two ``self``-intervals
        with a gap between would not be contained).
        """
        for ob in other.intervals:
            if not any(_interval_contained(ob, sa) for sa in self.intervals):
                return False
        return True

    # ── Rendering ────────────────────────────────────────────────────────
    def __repr__(self):
        if not self.intervals:
            return "∅"
        return " ∪ ".join(repr(iv) for iv in self.intervals)


def _interval_set_relation(a: IntervalSet, b: IntervalSet) -> str:
    """Classify two IntervalSets into DISJOINT / EQUAL / SUBSET / SUPERSET / OVERLAP.

    Uses the same five-value lattice as ``_combine``: DISJOINT when the
    intersection is empty, EQUAL when each contains the other, SUBSET /
    SUPERSET when only one direction of containment holds, OVERLAP
    otherwise.
    """
    inter = a.intersect(b)
    if inter.is_empty():
        return DISJOINT
    a_in_b = b.contains_set(a)
    b_in_a = a.contains_set(b)
    if a_in_b and b_in_a:
        return EQUAL
    if a_in_b:
        return SUBSET
    if b_in_a:
        return SUPERSET
    return OVERLAP


# ─────────────────────────────────────────────────────────────────────────────
# Chi-square minimization (``~=``) handling
# ─────────────────────────────────────────────────────────────────────────────
# The ``~=`` operator marks a chi-square minimization cut, e.g.
#   define error = (m(Whad) - 80.3692)^2 + 0.1*((m(top) - 172.57)^2)
#   select error ~= 0
# It does not constrain the LHS to a literal value — it tells the
# downstream tooling to minimize the LHS over the event sample. From
# the overlap pipeline's perspective there is no interval-arithmetic
# interpretation; we cannot conclude DISJOINT or SUBSET/SUPERSET from
# a minimization. The contribution rule is simple:
#
#   * Two ``~=`` cuts with structurally-equal LHS, the same operator
#     (both ``~=``), and the same RHS threshold  →  EQUAL.
#   * Anything else (different LHS, different threshold, only one side
#     has the ``~=`` cut, or one side is ``~=`` and the other isn't)
#     →  OVERLAP.
#
# This is encoded once here and called from every leaf-classification
# site so the rule is uniform across the comparator paths.

CHI2_MIN_OP = "~="


def _is_chi2_min_cut(fc) -> bool:
    """True iff ``fc`` is a chi-square minimization cut (``~=``).

    Reads the *effective* operator so that a cut originating from a
    REJECT statement is classified the same way as one from a SELECT.
    """
    return fc.effective_op() == CHI2_MIN_OP


def _tree_has_chi2_min(tree) -> bool:
    """True iff any leaf constraint on ``tree`` is a ``~=`` cut.

    Used at the unmatched-bucket sites where we don't have a paired
    counterpart on the other side and need to know whether the lone cut
    is a chi-square minimization (in which case the directional
    SUBSET/SUPERSET verdict must be downgraded to OVERLAP).
    """
    if tree is None:
        return False
    return any(_is_chi2_min_cut(c)
               for ce in tree.own_constraint_exprs
               for c in constraint_expr_leaves(ce))


def _chi2_min_pair_relation(fc_a, fc_b) -> str:
    """Verdict for a pair of leaves where at least one carries ``~=``.

    Both sides ``~=`` with structurally-equal LHS and equal threshold
    → EQUAL. Every other configuration → OVERLAP. Never DISJOINT, never
    SUBSET/SUPERSET — a minimization cannot prove containment in either
    direction.
    """
    if (_is_chi2_min_cut(fc_a)
            and _is_chi2_min_cut(fc_b)
            and compare_expr(fc_a.lhs, fc_b.lhs) == EQUAL
            and fc_a.threshold == fc_b.threshold):
        return EQUAL
    return OVERLAP


# ─────────────────────────────────────────────────────────────────────────────
# Per-axis ConstraintExpr evaluation
# ─────────────────────────────────────────────────────────────────────────────
# For each cut, we want to compute "what values does this axis allow?"
# An axis is identified by its LHS signature (the structural fingerprint
# of the canonical ExprNode). Walking the ConstraintExpr:
#   * Leaf — if it constrains this axis, return its IntervalSet;
#            otherwise return everything (no constraint).
#   * And  — intersection of children's evaluations.
#   * Or   — union of children's evaluations.
# For a region/object that combines multiple top-level cuts, the cuts
# are themselves conjoined: per-axis acceptance is the intersection of
# each cut's per-axis acceptance.


def evaluate_axis_for_expr(
    expr: ConstraintExpr, axis_signature: str,
) -> IntervalSet:
    """Evaluate the IntervalSet of values allowed on ``axis_signature``
    by a single ConstraintExpr.

    A leaf that does not constrain this axis contributes ``everything``
    — that's the right semantics: a cut on axis X says nothing about
    axis Y, so on axis Y any value is allowed by that cut alone.
    Combined under AND with another cut that does constrain Y, the
    intersection picks up Y's actual restriction.
    """
    if isinstance(expr, ConstraintLeaf):
        if expr.cut.lhs.signature() == axis_signature:
            return IntervalSet.from_constraint(expr.cut)
        return IntervalSet.everything()

    if isinstance(expr, ConstraintAnd):
        # Empty And is the identity. Otherwise intersect children.
        if not expr.children:
            return IntervalSet.everything()
        result = IntervalSet.everything()
        for ch in expr.children:
            result = result.intersect(evaluate_axis_for_expr(ch, axis_signature))
            if result.is_empty():
                return result   # short-circuit
        return result

    if isinstance(expr, ConstraintOr):
        # Empty Or is unsatisfiable. Otherwise union children.
        if not expr.children:
            return IntervalSet.empty()
        # Subtle point: a child that doesn't reference this axis
        # contributes ``everything`` — and ``everything ∪ X = everything``
        # for any X. So an Or where any child is axis-irrelevant evaluates
        # to ``everything`` on that axis. That matches the semantics: the
        # Or is satisfiable on this axis as long as one branch doesn't
        # constrain it.
        result = IntervalSet.empty()
        for ch in expr.children:
            result = result.union(evaluate_axis_for_expr(ch, axis_signature))
            if result.is_everything():
                return result   # short-circuit
        return result

    # Unknown expr kind: be conservative.
    return IntervalSet.everything()


def evaluate_axis_for_exprs(
    exprs: List[ConstraintExpr], axis_signature: str,
) -> IntervalSet:
    """Combined per-axis acceptance from a list of ConstraintExprs that
    are themselves conjoined (e.g. multiple SELECT cuts in a region)."""
    if not exprs:
        return IntervalSet.everything()
    result = IntervalSet.everything()
    for e in exprs:
        result = result.intersect(evaluate_axis_for_expr(e, axis_signature))
        if result.is_empty():
            return result
    return result


def _interval_contained(inner: Interval, outer: Interval) -> bool:
    """Test inner ⊆ outer accounting for open/closed endpoints."""
    if outer.lo > inner.lo:
        return False
    if outer.lo == inner.lo and outer.lo_open and not inner.lo_open:
        return False
    if outer.hi < inner.hi:
        return False
    if outer.hi == inner.hi and outer.hi_open and not inner.hi_open:
        return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class VariableOverlap:
    variable: str
    interval_a: IntervalSet
    interval_b: IntervalSet
    intersection: IntervalSet
    relation: str = OVERLAP
    chain_a: List[str] = field(default_factory=list)
    chain_b: List[str] = field(default_factory=list)

    @property
    def overlaps(self) -> bool:
        return self.relation != DISJOINT

    def has_chain(self) -> bool:
        return bool(self.chain_a) or bool(self.chain_b)

    def provenance_str(self) -> str:
        ca = " -> ".join(self.chain_a) if self.chain_a else self.variable
        cb = " -> ".join(self.chain_b) if self.chain_b else self.variable
        return ca if ca == cb else f"A: {ca}  |  B: {cb}"


@dataclass
class ObjectPairResult:
    """Informational object-pair comparison. Not used for ADL verdict —
    objects are only examined as dependencies during region comparison."""
    object_a: str
    object_b: str
    analysis_a: str
    analysis_b: str
    chain_a: str
    chain_b: str
    root_a: str
    root_b: str
    structure_matched: bool
    dep_values_matched: bool
    variable_overlaps: List[VariableOverlap] = field(default_factory=list)
    verdict: str = OVERLAP
    notes: List[str] = field(default_factory=list)


@dataclass
class CutPairResult:
    surface_a: Set[str]
    surface_b: Set[str]
    structure_matched: bool
    dep_values_matched: bool
    variable_overlaps: List[VariableOverlap] = field(default_factory=list)
    verdict: str = OVERLAP
    notes: List[str] = field(default_factory=list)
    tree_a: Optional[CutDependency] = None
    tree_b: Optional[CutDependency] = None
    # When True, this row is shown in the report for transparency but is
    # excluded from verdict aggregation. Used for cardinality cross-pairs
    # whose underlying sub-collections are disjoint — see the rule in
    # ``_compare_region_variables``.
    informational_only: bool = False
    # Region-inheritance provenance of each side's cut: ``()`` for the
    # region's own cut, ``("presel",)`` for a cut inherited from presel,
    # ``("init", "presel")`` for one owned by init and reached via presel.
    origin_a: Tuple[str, ...] = ()
    origin_b: Tuple[str, ...] = ()
    # True for an unmodellable region-reference line (see
    # ``_collect_opaque_region_cuts``) — lets the report label it properly.
    opaque_region_ref: bool = False


@dataclass
class RegionPairResult:
    region_a: str
    region_b: str
    analysis_a: str
    analysis_b: str
    shared_builtin_objects: Set[str]
    cut_pair_results: List[CutPairResult] = field(default_factory=list)
    variable_overlaps: List[VariableOverlap] = field(default_factory=list)
    verdict: str = OVERLAP
    notes: List[str] = field(default_factory=list)
    cuts_a: List = field(default_factory=list)
    cuts_b: List = field(default_factory=list)

    @property
    def matched_cut_pairs(self) -> List[CutPairResult]:
        return [c for c in self.cut_pair_results
                if c.structure_matched and c.dep_values_matched]

    @property
    def unmatched_cut_pairs(self) -> List[CutPairResult]:
        return [c for c in self.cut_pair_results
                if not c.structure_matched or not c.dep_values_matched]

    @property
    def overlapping_vars(self) -> List[VariableOverlap]:
        return [v for v in self.variable_overlaps if v.overlaps]

    @property
    def non_overlapping_vars(self) -> List[VariableOverlap]:
        return [v for v in self.variable_overlaps if not v.overlaps]


@dataclass
class OverlapReport:
    analysis_a: str
    analysis_b: str
    object_results: List[ObjectPairResult] = field(default_factory=list)
    region_results: List[RegionPairResult] = field(default_factory=list)

    @property
    def overlapping_region_pairs(self) -> List[RegionPairResult]:
        return [r for r in self.region_results if r.verdict == OVERLAP]

    @property
    def disjoint_region_pairs(self) -> List[RegionPairResult]:
        return [r for r in self.region_results if r.verdict == DISJOINT]

    @property
    def equal_region_pairs(self) -> List[RegionPairResult]:
        return [r for r in self.region_results if r.verdict == EQUAL]

    @property
    def subset_region_pairs(self) -> List[RegionPairResult]:
        return [r for r in self.region_results if r.verdict == SUBSET]

    @property
    def superset_region_pairs(self) -> List[RegionPairResult]:
        return [r for r in self.region_results if r.verdict == SUPERSET]

    # Retained (empty) for report.py compatibility
    @property
    def partial_region_pairs(self) -> List[RegionPairResult]:
        return []

    @property
    def no_overlap_pairs(self) -> List[RegionPairResult]:
        return []

    @property
    def structure_mismatch_pairs(self) -> List[RegionPairResult]:
        return []

    @property
    def summary_verdict(self) -> str:
        """
        ADL-level verdict, composed bottom-up from the per-region-pair
        verdicts via the standard ``_combine`` rule:

          * any region pair DISJOINT  → DISJOINT
          * any region pair OVERLAP   → OVERLAP
          * all EQUAL                  → EQUAL
          * all in {EQUAL, SUBSET}     → SUBSET
          * all in {EQUAL, SUPERSET}   → SUPERSET
          * mixed SUBSET + SUPERSET    → OVERLAP

        Object-level verdicts do NOT affect the ADL verdict — objects
        are only examined as dependencies during region comparison.
        """
        return _combine([r.verdict for r in self.region_results])


# ─────────────────────────────────────────────────────────────────────────────
# Grouping helpers
# ─────────────────────────────────────────────────────────────────────────────

def _group_by_func(
    constraints: List[CutStructure],
) -> Dict[str, List[CutStructure]]:
    """Group constraints by their LHS structural signature.

    Two cuts on structurally-equivalent LHSes (same canonical ExprNode
    shape) bucket together; threshold and op differ, but the *thing
    being measured* is the same. The interval comparator inside
    ``_compare_compound_nodes`` then decides EQUAL/SUBSET/etc. based on
    the cuts' actual thresholds.

    This replaces the old ``display_name().lower()`` key, which was a
    string-level approximation that failed on commutative operand order
    and parenthesisation differences.
    """
    groups: Dict[str, List[CutStructure]] = {}
    for fc in constraints:
        key = fc.lhs.signature()
        groups.setdefault(key, []).append(fc)
    return groups


def _group_by_func_chain(
    constraints: List[CutStructure],
) -> Dict[str, List[CutStructure]]:
    """Group by func_chain only (collection-agnostic). Used for
    cumulative-cut comparison where collection names may differ."""
    groups: Dict[str, List[CutStructure]] = {}
    for fc in constraints:
        key = (fc.func_chain or "").lower()
        groups.setdefault(key, []).append(fc)
    return groups


# ─────────────────────────────────────────────────────────────────────────────
# Object structural comparison
# ─────────────────────────────────────────────────────────────────────────────
# ObjectDependency absorbs what the old (removed) ObjectInheritanceChain
# used to do: .roots() (plural — fixes the old scalar-root bug for Union
# objects) and .cumulative_constraint_expr() (ANDs an object's own cuts with
# the OR of every parent branch's cumulative constraints — the actual
# set-membership semantics of a Union object, used by ir_extractor and its
# own tests). But that flattened, OR'd expression is NOT safe to feed
# through the per-axis IntervalSet evaluator for COMPARISON purposes once an
# object has more than one branch with DIFFERENT roots (a genuine Union,
# e.g. ``leptons = Union(electrons, muons)``):
#
#   BUG (fixed below): the old comparator flattened every leaf from every
#   branch into one collection-agnostic func_chain bucket, picked ONE
#   representative leaf's signature as "the" axis (e.g. pT(ELE)), and
#   evaluated the *entire* OR'd expression against that single axis. The
#   other branch (muons) has no leaf matching that axis, so it evaluates to
#   "everything" on it — and "everything" unioned into an OR swallows the
#   whole expression to "everything" on that axis, on BOTH sides being
#   compared. Two ``leptons`` objects built from provably DISJOINT electron
#   cuts (pT>20 vs pT<10) and DISJOINT muon cuts would each show
#   "everything" on the pT(ELE) axis and misreport EQUAL, even though the
#   union as a whole is genuinely disjoint.
#
# The fix: a Union's branches partition the object's acceptance set by
# built-in root (an element can never satisfy two different roots at once —
# an electron can't also be a muon), so the comparison must never mix leaves
# from different roots into one axis bucket. Instead, for every root
# reachable by EITHER side, build a per-root RESTRICTED cumulative
# expression (own constraints AND-ed with only the parent branch(es) whose
# root-set actually includes that root — see ``_restricted_cumulative``) and
# compare those independently, combining the per-root verdicts with the
# usual 5-value lattice. A root present on only one side means that side's
# root-slice is the empty set (that object can never produce an element of
# that type at all), which is trivially contained in whatever the other
# side has there — see the "root present on only one side" branch below for
# the direction this implies.
#
# A plain (non-Union, single-root) object degenerates to comparing exactly
# one root-slice equal to its own ``cumulative_constraint_expr()`` — the
# same behavior as before this fix. This is also the logic used for the
# root-object comparison in the report (_check_object_pair_for_report) and
# for object children embedded deeper in a cut's tree (_compare_dep_nodes),
# which is why this single function serves both call sites.

def _restricted_cumulative(node: CutDependency, root: str) -> ConstraintExpr:
    """The portion of ``node``'s cumulative constraint that applies to
    elements of built-in type ``root`` — like ``cumulative_constraint_expr()``
    but DROPPING (rather than OR-ing in) any parent branch whose root-set
    doesn't include ``root``.

    This is the key difference from ``ObjectDependency.cumulative_constraint_expr()``:
    that method ORs together the cumulative expressions of EVERY parent
    branch, which is the correct SET-MEMBERSHIP semantics (an element
    belongs to the union if it satisfies *any* branch) but is unsafe to
    feed through the per-axis IntervalSet evaluator, since a branch that
    doesn't reference the axis in question evaluates to "everything" and
    poisons the OR. Restricting to one root first means every leaf that
    survives genuinely shares that root's domain, so evaluating the result
    per axis is safe.
    """
    if isinstance(node, BuiltinDependency):
        return node.cumulative_constraint_expr()
    if not isinstance(node, ObjectDependency):
        return ConstraintAnd(())

    own = ConstraintAnd(tuple(node.own_constraint_exprs)) if node.own_constraint_exprs else None
    relevant = [ch for ch in node.children
                if isinstance(ch, (ObjectDependency, BuiltinDependency))
                and root in ch.roots()]
    if not relevant:
        branch_combined = None
    elif len(relevant) == 1:
        branch_combined = _restricted_cumulative(relevant[0], root)
    else:
        branch_combined = ConstraintOr(tuple(
            _restricted_cumulative(ch, root) for ch in relevant
        ))

    parts = [p for p in (own, branch_combined) if p is not None]
    if not parts:
        return ConstraintAnd(())
    if len(parts) == 1:
        return parts[0]
    return ConstraintAnd(tuple(parts))


# Containment prover for cuts outside the interval model (overlap removal
# with allof() and pT-dependent ΔR windows); set by compare().
_PROVER = None


def _compare_object_subtrees(
    obj_a: CutDependency, obj_b: CutDependency,
    var_overlaps_out: Optional[List[VariableOverlap]] = None,
) -> str:
    """The interval comparison below, strengthened by object_containment:
    a containment it proves (A ⊆ B, B ⊆ A) is added to the verdict."""
    v = _compare_object_subtrees_base(obj_a, obj_b, var_overlaps_out)
    if (v in (EQUAL, DISJOINT) or _PROVER is None
            or not isinstance(obj_a, ObjectDependency)
            or not isinstance(obj_b, ObjectDependency)):
        return v
    a_in_b = v == SUBSET or _PROVER.subset(obj_a.name, obj_b.name)
    b_in_a = v == SUPERSET or _PROVER.subset(obj_b.name, obj_a.name)
    if a_in_b and b_in_a:
        return EQUAL
    if a_in_b:
        return SUBSET
    if b_in_a:
        return SUPERSET
    return v


def _compare_object_subtrees_base(
    obj_a: CutDependency, obj_b: CutDependency,
    var_overlaps_out: Optional[List[VariableOverlap]] = None,
) -> str:
    """
    Compare two ObjectDependency nodes root-slice by root-slice (see the
    module comment above for why). Returns
    DISJOINT / EQUAL / SUBSET / SUPERSET / OVERLAP.
    """
    if not isinstance(obj_a, ObjectDependency) or not isinstance(obj_b, ObjectDependency):
        return OVERLAP

    roots_a = obj_a.roots()
    roots_b = obj_b.roots()
    if not roots_a or not roots_b or not (roots_a & roots_b):
        return OVERLAP

    # Root-slices combine via OR (an element belongs to the union if it's
    # in ANY branch), which has different disjointness/containment algebra
    # than the AND-combined axes within one slice. Concretely, for
    # A = ⋃ᵣ Aᵣ and B = ⋃ᵣ Bᵣ over disjoint roots r (an electron can never
    # also be a muon, so cross-root intersections are always empty):
    #
    #   A ∩ B = ⋃ᵣ (Aᵣ ∩ Bᵣ)   -- only COMMON roots can ever contribute
    #
    # so DISJOINT-overall requires *every* common root's slice to be
    # disjoint — a root present on only one side contributes nothing to
    # the intersection either way and can never by itself force or break
    # DISJOINT. This is the opposite of ``_combine``'s "any DISJOINT wins"
    # rule, which models AND-combined axes (there, one disjoint axis truly
    # does make the whole conjunction unsatisfiable together). Reusing
    # ``_combine`` across root-slices was exactly the mistake: it reported
    # DISJOINT for two ``leptons`` objects whenever the ELECTRON slice was
    # disjoint, even when their MUON slices were identical (genuinely
    # overlapping) — the union clearly still shares those muons, so the
    # correct verdict there is OVERLAP, not DISJOINT.
    common_relations: List[str] = []
    only_in_a = False
    only_in_b = False

    for root in sorted(roots_a | roots_b):
        in_a, in_b = root in roots_a, root in roots_b
        if in_a and in_b:
            cum_a = _restricted_cumulative(obj_a, root)
            cum_b = _restricted_cumulative(obj_b, root)
            groups_a = _group_by_func_chain(constraint_expr_leaves(cum_a))
            groups_b = _group_by_func_chain(constraint_expr_leaves(cum_b))

            root_contribs: List[str] = []
            for var in sorted(set(groups_a) | set(groups_b)):
                va, vb = var in groups_a, var in groups_b
                if va and vb:
                    # A func_chain bucket (e.g. "dr") can hold MORE than
                    # one distinct axis: ``dR(ELE, nonbjets)`` and
                    # ``dR(ELE, jets)`` share the func_chain "dr" but are
                    # different physical quantities once ``nonbjets`` and
                    # ``jets`` are distinguished (see IdNode.src_object).
                    # Taking only groups_a[var][0]'s signature — the old
                    # behaviour — silently dropped every other axis in
                    # the bucket from both the verdict and the report.
                    # Evaluate every distinct signature seen on either
                    # side instead; a side that doesn't reference a given
                    # signature contributes "everything" on it (handled
                    # by evaluate_axis_for_expr), which is the correct
                    # "this side doesn't constrain that axis" semantics.
                    sigs_a = {fc.lhs.signature(): fc for fc in groups_a[var]}
                    sigs_b = {fc.lhs.signature(): fc for fc in groups_b[var]}
                    sig_rels: List[str] = []
                    for axis_sig in sorted(set(sigs_a) | set(sigs_b)):
                        iv_a = evaluate_axis_for_expr(cum_a, axis_sig)
                        iv_b = evaluate_axis_for_expr(cum_b, axis_sig)
                        rel = _interval_set_relation(iv_a, iv_b)
                        sig_rels.append(rel)
                        if var_overlaps_out is not None:
                            rep = sigs_a.get(axis_sig) or sigs_b.get(axis_sig)
                            var_overlaps_out.append(VariableOverlap(
                                variable=rep.display_name(),
                                interval_a=iv_a, interval_b=iv_b,
                                intersection=iv_a.intersect(iv_b),
                                relation=rel,
                            ))
                    root_contribs.append(_combine(sig_rels))
                elif va:
                    root_contribs.append(SUBSET)
                else:
                    root_contribs.append(SUPERSET)
            # Within ONE root-slice, own constraints + axes still combine
            # via AND-semantics ("any DISJOINT wins" is correct here), so
            # ``_combine`` is the right tool for this inner reduction.
            common_relations.append(_combine(root_contribs))
        elif in_a:
            # Only A can produce elements of this root at all -- B's
            # slice here is the empty set. This root can never make the
            # objects DISJOINT-overall any more or less true (it
            # contributes nothing to A∩B either way), but it DOES rule
            # out EQUAL and SUBSET (A has something B entirely lacks).
            only_in_a = True
        else:
            only_in_b = True

    if all(v == DISJOINT for v in common_relations):
        return DISJOINT
    if not only_in_a and not only_in_b and all(v == EQUAL for v in common_relations):
        verdict = EQUAL
    elif not only_in_a and all(v in (EQUAL, SUBSET) for v in common_relations):
        verdict = SUBSET
    elif not only_in_b and all(v in (EQUAL, SUPERSET) for v in common_relations):
        verdict = SUPERSET
    else:
        return OVERLAP
    return _adjust_for_dropped(verdict, _cumulative_dropped(obj_a), _cumulative_dropped(obj_b))


def _cumulative_dropped(node: CutDependency) -> List[str]:
    """Comparisons left out of the model of an object and of all its parents
    (see ir_extractor._DROPPED_SINK), with object names canonicalised."""
    import re as _re
    from expr_node import SRC_OBJECT_ALIASES as _al
    out: List[str] = []
    seen = set()
    stack = [node]
    while stack:
        n = stack.pop()
        if id(n) in seen:
            continue
        seen.add(id(n))
        for d in getattr(n, "dropped", []) or []:
            out.append(_re.sub(r"[A-Za-z_][A-Za-z0-9_]*",
                               lambda m: _al.get(m.group(0).lower(), m.group(0).lower()), d))
        stack.extend(ch for ch in getattr(n, "children", []) if isinstance(ch, ObjectDependency))
    return sorted(out)


def _adjust_for_dropped(verdict: str, dropped_a: List[str], dropped_b: List[str]) -> str:
    """The model of each side is looser than the real selection when cuts were
    dropped. Identical dropped cuts on both sides restrict both sets in the
    same way and cancel. Otherwise only the directions that remain true are
    kept: a side with extra unmodelled cuts can only be smaller than modelled."""
    a, b = list(dropped_a), list(dropped_b)
    for d in list(a):
        if d in b:
            a.remove(d)
            b.remove(d)
    if verdict == DISJOINT or (not a and not b):
        return verdict
    if a and b:
        return OVERLAP
    if a:   # real A ⊆ model A
        return {EQUAL: SUBSET, SUBSET: SUBSET}.get(verdict, OVERLAP)
    return {EQUAL: SUPERSET, SUPERSET: SUPERSET}.get(verdict, OVERLAP)


# ─────────────────────────────────────────────────────────────────────────────
# Dependency-tree helpers
# ─────────────────────────────────────────────────────────────────────────────

def _object_children(node: CutDependency) -> List[CutDependency]:
    return [ch for ch in node.children if isinstance(ch, ObjectDependency)]


def _define_children(node: CutDependency) -> List[CutDependency]:
    return [ch for ch in node.children if isinstance(ch, DefineDependency)]


def _root_of_object_subtree(obj_node: CutDependency) -> str:
    """A single representative root, for grouping/bucketing purposes
    (report-signature keys, pairing object children by root). A Union
    object genuinely has more than one root — see ``ObjectDependency.roots()``
    for the full set — but the bucket-keying call sites here only need a
    stable, deterministic representative, matching ``ObjectIR.root_type()``'s
    same convention."""
    if not isinstance(obj_node, ObjectDependency):
        return ""
    roots = obj_node.roots()
    return sorted(roots)[0] if roots else ""


# ─────────────────────────────────────────────────────────────────────────────
# Recursive dependency-node comparison (Rule 2 core)
# ─────────────────────────────────────────────────────────────────────────────

def _compare_dep_nodes(
    node_a: Optional[CutDependency],
    node_b: Optional[CutDependency],
) -> str:
    """
    Compare two dependency nodes and return a 5-value verdict using
    bottom-up composition.
    """
    if node_a is None or node_b is None:
        return OVERLAP

    # Object × object handled by cumulative-constraint comparison
    if isinstance(node_a, ObjectDependency) and isinstance(node_b, ObjectDependency):
        return _compare_object_subtrees(node_a, node_b)

    # Everything else: compose children + own constraints
    return _compare_compound_nodes(node_a, node_b)


def _compare_compound_nodes(
    node_a: CutDependency, node_b: CutDependency,
) -> str:
    contribs: List[str] = []

    own_a = _group_by_func([c for ce in node_a.own_constraint_exprs
                              for c in constraint_expr_leaves(ce)])
    own_b = _group_by_func([c for ce in node_b.own_constraint_exprs
                              for c in constraint_expr_leaves(ce)])

    obj_a_subs = _object_children(node_a)
    obj_b_subs = _object_children(node_b)

    # --- 1. Own (leaf) constraints at this node -------------------------
    # Each axis (LHS signature) appearing in either side is evaluated to
    # an ``IntervalSet`` of accepted values, then compared. The
    # IntervalSet model handles cuts whose per-axis acceptance is a
    # union (e.g. ``reject ... [] a b`` produces two disjoint allowed
    # half-lines) — collapsing this to a single ``Interval`` was the
    # cause of the spurious empty intervals like ``(1.56, 1.44)``.
    #
    # On the verdict computation: when ``lhs_rel == EQUAL`` the two
    # LHSes evaluate to the same value on every event (definitional
    # invariant of compare_expr), so the leaf's contribution is purely
    # the interval-set relation. Per-object inheritance differences
    # between A's and B's named collections are captured by the
    # *object-children* branch below — applying ``obj_rel`` again at
    # the leaf would double-count and, worse, fall through to OVERLAP
    # for composite LHSes (which have no single primary collection),
    # poisoning otherwise-EQUAL composite-cut verdicts. The tests
    # ``test_demorgan_fix.py`` and the structural-equivalence tests
    # both exercise this; the composite-cut self-comparison cases
    # (``size(ELE) + size(MUO) == 0`` etc.) only succeed under this
    # rule.
    for var in sorted(set(own_a) | set(own_b)):
        in_a = var in own_a
        in_b = var in own_b
        if in_a and in_b:
            fc_a = own_a[var][0]
            fc_b = own_b[var][0]
            # Chi-square minimization (``~=``) short-circuit — see
            # _build_var_overlap_from_tree_leaf for the rationale. The
            # rule is the same: EQUAL when both sides carry an identical
            # ``~=`` cut, OVERLAP otherwise. Routed through the dedicated
            # helper so the interval-set machinery never sees ``~=``.
            if _is_chi2_min_cut(fc_a) or _is_chi2_min_cut(fc_b):
                contribs.append(_chi2_min_pair_relation(fc_a, fc_b))
                continue
            iv_a = evaluate_axis_for_exprs(node_a.own_constraint_exprs, var)
            iv_b = evaluate_axis_for_exprs(node_b.own_constraint_exprs, var)
            lhs_rel = compare_expr(fc_a.lhs, fc_b.lhs)
            if lhs_rel == EQUAL:
                # LHSes are guaranteed to evaluate identically. The leaf
                # verdict is purely the interval-set comparison; the
                # object-children branch contributes any per-object
                # inheritance differences separately.
                rel = _interval_set_relation(iv_a, iv_b)
            elif lhs_rel == DISJOINT:
                # LHSes provably differ — only DISJOINT if intervals
                # are also disjoint (cuts can't both be true on any
                # event). Otherwise OVERLAP.
                interval_rel = _interval_set_relation(iv_a, iv_b)
                rel = DISJOINT if interval_rel == DISJOINT else OVERLAP
            else:
                # SUBSET/SUPERSET/OVERLAP at the LHS level → conservative.
                rel = OVERLAP
            contribs.append(rel)
        elif in_a:
            # Unmatched on this axis. A lone ``~=`` cut cannot prove
            # containment in either direction, so it contributes OVERLAP
            # rather than the directional SUBSET/SUPERSET we'd emit for
            # a regular cut.
            fc_a = own_a[var][0]
            contribs.append(OVERLAP if _is_chi2_min_cut(fc_a) else SUBSET)
        else:
            fc_b = own_b[var][0]
            contribs.append(OVERLAP if _is_chi2_min_cut(fc_b) else SUPERSET)

    # --- 2. Object children (paired by built-in root) -------------------
    a_by_root: Dict[str, List[CutDependency]] = {}
    b_by_root: Dict[str, List[CutDependency]] = {}
    for oc in obj_a_subs:
        r = _root_of_object_subtree(oc)
        a_by_root.setdefault(r, []).append(oc)
    for oc in obj_b_subs:
        r = _root_of_object_subtree(oc)
        b_by_root.setdefault(r, []).append(oc)

    for root in sorted(set(a_by_root) | set(b_by_root)):
        in_a = a_by_root.get(root) or []
        in_b = b_by_root.get(root) or []
        if in_a and in_b:
            m = [[_compare_object_subtrees(oa, ob) for ob in in_b] for oa in in_a]
            # Several objects under one root on both sides (e.g. the
            # positive and the negative leptons of ``size(lepPos) >= 2 or
            # size(lepNeg) >= 2``): if they match one-to-one as EQUAL, the
            # children are the same and the cross pairs carry no information.
            import itertools as _it
            if len(in_a) == len(in_b) and len(in_a) > 1 and any(
                    all(m[i][p[i]] == EQUAL for i in range(len(in_a)))
                    for p in _it.permutations(range(len(in_b)))):
                contribs.extend([EQUAL] * len(in_a))
            else:
                for row in m:
                    # A DISJOINT relation between two *objects* (e.g.
                    # positive vs negative leptons) does not make the two
                    # *cuts* exclusive: an event can satisfy a condition on
                    # each collection at the same time. Only the interval
                    # comparison of the leaves (above) may prove DISJOINT.
                    contribs.extend(OVERLAP if r == DISJOINT else r for r in row)
        elif in_a:
            contribs.append(SUBSET)
        else:
            contribs.append(SUPERSET)

    # --- 3. Define children (pair by structural signature) --------------
    def_a_list = _define_children(node_a)
    def_b_list = _define_children(node_b)
    if def_a_list or def_b_list:
        contribs.extend(_pair_and_compare_defines(def_a_list, def_b_list))

    return _combine(contribs)


def _define_signature(node: CutDependency) -> Tuple:
    """A structural signature for aligning define children across A and B.
    Ignores names; uses sorted tuple of object-roots reachable via object
    children, recursively descended through nested defines. Also collects
    the set of top-level function-chains used in constraint leaves."""
    roots: List[str] = []
    funcs: List[str] = []

    def walk(n: CutDependency):
        for ce in n.own_constraint_exprs:
            for c in constraint_expr_leaves(ce):
                funcs.append((c.func_chain or "").lower())
        for ch in n.children:
            if isinstance(ch, ObjectDependency):
                r = _root_of_object_subtree(ch)
                if r:
                    roots.append(r)
            elif isinstance(ch, DefineDependency):
                walk(ch)
            elif isinstance(ch, BuiltinDependency):
                roots.append(canonicalise(ch.name))
    walk(node)
    return (tuple(sorted(roots)), tuple(sorted(funcs)))


def _pair_and_compare_defines(
    defs_a: List[CutDependency],
    defs_b: List[CutDependency],
) -> List[str]:
    """Greedy matching of A-side and B-side defines by structural
    signature. Unmatched ones contribute directionally."""
    contribs: List[str] = []
    sig_a = [_define_signature(d) for d in defs_a]
    sig_b = [_define_signature(d) for d in defs_b]

    used_b: Set[int] = set()
    matched_a: Set[int] = set()

    for i, sa in enumerate(sig_a):
        for j, sb in enumerate(sig_b):
            if j in used_b:
                continue
            if sa == sb:
                contribs.append(_compare_dep_nodes(defs_a[i], defs_b[j]))
                used_b.add(j)
                matched_a.add(i)
                break

    for i in range(len(defs_a)):
        if i not in matched_a:
            contribs.append(SUBSET)
    for j in range(len(defs_b)):
        if j not in used_b:
            contribs.append(SUPERSET)

    return contribs


# ─────────────────────────────────────────────────────────────────────────────
# Region-variable pairing  (Rules 2 + 3)
# ─────────────────────────────────────────────────────────────────────────────

def _top_level_signature(tree: CutDependency) -> Optional[Tuple[str, Tuple[str, ...]]]:
    """
    Structural signature for the top-level cut: ``(lhs_signature, child_keys)``.

    The first element is the LHS expression's structural signature, drawn
    directly from the canonical ``ExprNode`` tree on the cut. This is the
    single source of truth for "shape" — commutativity, associativity, and
    arithmetic structure are baked in by canonicalisation, so two cuts
    with structurally equivalent LHSes produce identical signatures
    regardless of how they were written.

    The second element is the sorted tuple of top-level argument keys
    drawn from ``tree.children``. For object/built-in children the key
    is the *canonical built-in root* (e.g. ``PHO``, ``JET``) suffixed
    with a slice token — collection-name-agnostic, so cuts like
    ``size(photons)`` and ``size(vetophotons)`` (both rooted in PHO)
    share a bucket and get cross-paired. The verdict for any
    cross-pair is computed by ``_compare_compound_nodes``, which folds
    in the underlying object SUBSET/SUPERSET/DISJOINT/EQUAL relation
    via its object-children branch — so the report shows the genuine
    relation between two analyses' cuts even when they reference
    differently-named objects on the same built-in collection.

    Slice tokens are still part of the key, so ``dR(JET[0:3], ELE[0])``
    and ``dR(JET, ELE[0])`` remain in different buckets — slice
    differences indicate cuts that act on different parts of the
    collection. The slice token defaults to ``|*`` for composite cuts
    (no single primary accessor); per-child slices remain encoded
    inside the LHS tree but aren't currently surfaced into the
    signature key.

    Returns ``None`` only when the cut has no constraints at all
    (degenerate case).
    """
    if tree is None or not tree.own_constraint_exprs:
        return None
    leaves = [c for ce in tree.own_constraint_exprs
                for c in constraint_expr_leaves(ce)]
    if not leaves:
        return None
    fc = leaves[0]

    # LHS signature comes straight from the canonical tree. This replaces
    # the old (func_chain, collection-keys) heuristic with the real
    # structural fingerprint.
    lhs_sig = fc.lhs.signature()

    # Slice token for the cut's primary argument. Composite cuts have an
    # empty accessor, defaulting to "*" (whole collection); simple cuts
    # carry their slice on the innermost IdNode and project it through.
    acc = fc.accessor or ()
    slice_tok = "*" if not acc else f"{acc[0]}:{acc[1]}"

    keys: List[str] = []
    for ch in tree.children:
        if isinstance(ch, ObjectDependency):
            # Use the canonical built-in root, NOT the local user-defined
            # object name. This is what enables cross-analysis pairing of
            # cuts that reference differently-named objects on the same
            # underlying built-in collection (e.g. ``photons`` vs
            # ``vetophotons``, both rooted at PHO).
            r = _root_of_object_subtree(ch)
            if r:
                keys.append(f"{canonicalise(r)}|{slice_tok}")
        elif isinstance(ch, BuiltinDependency):
            keys.append(f"{canonicalise(ch.name)}|{slice_tok}")
        elif isinstance(ch, DefineDependency):
            # Composite cuts may pull in defines (e.g. ``ST > 300`` where
            # ST itself decomposes further). Use the define name as a key
            # so cuts referencing the same define pair across sides.
            local = (ch.name or "").strip()
            if local:
                keys.append(f"def:{local.lower()}|{slice_tok}")

    if not keys:
        col = fc.resolved_collection or fc.collection
        if col and col.upper() in BUILTIN_OBJECTS:
            keys.append(f"{canonicalise(col)}|{slice_tok}")

    return (lhs_sig, tuple(sorted(keys)))


def _collect_region_cuts(reg: RegionIR) -> List[ResolvedCutIR]:
    """The region's flattened, comparable cut set: inherited cuts plus
    its own, minus inheritance/``select ALL`` lines (which carry no
    constraint of their own) and minus opaque lines (handled separately,
    see ``_collect_opaque_region_cuts``)."""
    out: List[ResolvedCutIR] = []
    for rc in reg.comparison_cuts():
        if rc.region_role in ("inherit", "all", "opaque"):
            continue
        if rc.command in ("SELECT", "BIN", "REJECT"):
            out.append(rc)
    return out


def _render_origin_path(path: Tuple[str, ...]) -> str:
    return " → ".join(path) if path else "this region"


def _merge_same_axis_cuts(rcs: List[ResolvedCutIR]) -> ResolvedCutIR:
    """Fold several cuts on the SAME variable (one signature bucket, one
    side) into a single synthetic cut.

    A region is the AND of its cuts, so ``Size(X) >= 0`` (inherited from
    a parent) and ``Size(X) == 2`` (the child's own) jointly accept
    ``Size(X) == 2``. Comparing them cross-wise against the other side —
    ``>=0 vs ==2`` → SUPERSET, ``==2 vs >=0`` → SUBSET — mixes into a
    false OVERLAP even for a self-comparison. Concatenating their
    ``own_constraint_exprs`` lets the per-axis evaluator intersect them
    first (``evaluate_axis_for_exprs``), so the side is compared once,
    as a whole. Object/define children are shared (deduplicated by
    identity — the resolver caches them, so equal references are the
    same node).
    """
    tree = CutRootDependency(name=" ∧ ".join(
        (rc.dependency_tree.name or "?") for rc in rcs))
    seen_children: Set[int] = set()
    for rc in rcs:
        t = rc.dependency_tree
        tree.own_constraint_exprs.extend(t.own_constraint_exprs)
        for ch in t.children:
            if id(ch) not in seen_children:
                seen_children.add(id(ch))
                tree.children.append(ch)
    leaf_chains: Dict[int, List[str]] = {}
    for rc in rcs:
        leaf_chains.update(rc.leaf_chains)
    return ResolvedCutIR(
        command="SELECT",
        surface_vars=set().union(*(rc.surface_vars for rc in rcs)),
        resolved_vars=set().union(*(rc.resolved_vars for rc in rcs)),
        builtin_objects=set().union(*(rc.builtin_objects for rc in rcs)),
        constraint_expr=ConstraintAnd(tuple(rc.constraint_expr for rc in rcs)),
        dependency_tree=tree,
        leaf_chains=leaf_chains,
        region_role="own",
    )


def _collect_opaque_region_cuts(reg: RegionIR) -> List[ResolvedCutIR]:
    """Lines whose region reference can't be modelled (``reject R``, R in
    a compound condition, a cycle, an unknown name) — own or inherited."""
    return [rc for rc in reg.comparison_cuts() if rc.region_role == "opaque"]


def _build_var_overlap_from_tree_leaf(
    tree_a: CutDependency, tree_b: CutDependency,
    leaf_chains_a: Optional[Dict[int, List[str]]] = None,
    leaf_chains_b: Optional[Dict[int, List[str]]] = None,
) -> Optional[VariableOverlap]:
    """``leaf_chains_a``/``leaf_chains_b`` are the owning ResolvedCutIR's
    ``leaf_chains`` maps ({id(leaf): chain}) — the per-cut outer-path
    provenance that replaced mutating ``CutStructure.define_chain`` in
    place once object/define dependency nodes became cached and shared
    across cuts (see ir_extractor.DefineResolver._compute_leaf_chains).
    ``leaf.define_chain`` itself now only reports the leaf's LOCAL
    owning-node name, not the outer path from this specific cut's root,
    so it is no longer the right source for the provenance chain shown
    here.
    """
    leaves_a = [c for ce in tree_a.own_constraint_exprs
                  for c in constraint_expr_leaves(ce)]
    leaves_b = [c for ce in tree_b.own_constraint_exprs
                  for c in constraint_expr_leaves(ce)]
    if not leaves_a or not leaves_b:
        return None
    fc_a = leaves_a[0]
    fc_b = leaves_b[0]

    # The axis identifier is the LHS signature of the representative leaf
    # — for cut-kind leaf trees there is only one axis to consider.
    axis_sig = fc_a.lhs.signature()
    iv_a = evaluate_axis_for_exprs(tree_a.own_constraint_exprs, axis_sig)
    iv_b = evaluate_axis_for_exprs(tree_b.own_constraint_exprs, axis_sig)

    # Chi-square minimization (``~=``) short-circuit: bypass interval
    # logic entirely. ``~=`` does not produce an interval-arithmetic
    # acceptance region, so falling through to ``_interval_set_relation``
    # would silently treat the cut as "everything" and give a misleading
    # EQUAL/SUBSET/SUPERSET verdict. The dedicated rule (EQUAL when both
    # sides have an identical ``~=`` cut, OVERLAP otherwise) is encoded
    # in ``_chi2_min_pair_relation``. Reported IntervalSets are left as
    # ``everything`` for transparency — the verdict comes from the
    # special case, not from the intervals.
    if _is_chi2_min_cut(fc_a) or _is_chi2_min_cut(fc_b):
        rel = _chi2_min_pair_relation(fc_a, fc_b)
        every = IntervalSet.everything()
        return VariableOverlap(
            variable=fc_a.display_name(),
            interval_a=every, interval_b=every,
            intersection=every,
            relation=rel,
            chain_a=list((leaf_chains_a or {}).get(id(fc_a), [])),
            chain_b=list((leaf_chains_b or {}).get(id(fc_b), [])),
        )

    # Same option-B logic as _compare_compound_nodes' leaf branch:
    # when LHSes are structurally identical the verdict is the
    # interval-set comparison; per-object inheritance relations are
    # captured separately by callers that walk the object-children
    # branch. This avoids the false OVERLAP that the obj_rel-aware
    # path would produce for composite LHSes (no single primary
    # collection → fallback OVERLAP) even when the cuts are EQUAL.
    lhs_rel = compare_expr(fc_a.lhs, fc_b.lhs)
    if lhs_rel == EQUAL:
        rel = _interval_set_relation(iv_a, iv_b)
    elif lhs_rel == DISJOINT:
        interval_rel = _interval_set_relation(iv_a, iv_b)
        rel = DISJOINT if interval_rel == DISJOINT else OVERLAP
    else:
        rel = OVERLAP
    return VariableOverlap(
        variable=fc_a.display_name(),
        interval_a=iv_a, interval_b=iv_b,
        intersection=iv_a.intersect(iv_b),
        relation=rel,
        chain_a=list((leaf_chains_a or {}).get(id(fc_a), [])),
        chain_b=list((leaf_chains_b or {}).get(id(fc_b), [])),
    )


def _format_signature(sig: Tuple[str, Tuple[str, ...]]) -> str:
    """Render a top-level signature for human-readable reports.

    The signature is ``(lhs_signature, child_keys)``. The LHS signature
    is ExprNode-derived and may be detailed (e.g.
    ``+(fn:size(id:vetoele|*),fn:size(id:vetomu|*))``). For report
    rendering we compress that to a digestible form: just the outer
    structure with the child keys appended.
    """
    lhs_sig, keys = sig
    keys_str = ", ".join(keys) if keys else "·"
    return f"{lhs_sig} :: ({keys_str})"


# ─────────────────────────────────────────────────────────────────────────────
# Cardinality-cut best-pair filtering
# ─────────────────────────────────────────────────────────────────────────────
#
# Within a bucket where every cut on both sides is a cardinality reducer
# (``size``/``count``/``numof``) on a single object/builtin child, only
# *real* counterparts contribute to the verdict aggregation. The rest are
# noise: cross-pairs comparing cardinality of unrelated sub-collections
# don't constrain whether an event lies in region A or region B.
#
# Concretely, for two cuts ``size(X) op_A k_A`` and ``size(Y) op_B k_B``:
#   * EQUAL objects (X = Y): a real counterpart. Contributes
#     ``_compare_dep_nodes`` verdict.
#   * SUBSET / SUPERSET / OVERLAP objects: contributes only when this is
#     the *best* available pairing for both cuts. If either side has an
#     EQUAL pairing (or any strictly-better object relation) elsewhere
#     in the bucket, the cross-pair becomes informational and drops out.
#   * DISJOINT objects: never contributes its full verdict — disjoint
#     sub-collections impose independent constraints that say nothing
#     about region containment. Drops out as informational.
#
# After all cross-pairs are emitted, any cut that didn't participate as
# a real counterpart in *any* pair is treated as unmatched and emits a
# directional (SUBSET / SUPERSET) row, exactly like the side-only-bucket
# fallback.
#
# Two illustrative cases:
#   * ``A = B = {size(bJets)>=1, size(nonbJets)>=2}``  (self-compare):
#     diagonals are EQUAL-objects, off-diagonals are DISJOINT-objects
#     with a better EQUAL pairing available. Only diagonals contribute.
#     Verdict: EQUAL. ✓
#   * ``A = {size(bJets)>=1}, B = {size(nonbJets)>=2}``: only one
#     cross-pair, DISJOINT-objects, no better pair anywhere. Both cuts
#     unmatched → SUBSET + SUPERSET → OVERLAP. ✓

_CARDINALITY_FUNCS = {"size", "count", "numof"}

# Object-relation strength ranking. Higher = better counterpart. Used
# to decide whether a cross-pair is "the best available" for its two
# cuts. DISJOINT is the floor; pairs at the floor never contribute
# their verdict regardless of whether something better exists, because
# disjoint sub-collections genuinely don't constrain each other.
_OBJ_REL_RANK = {EQUAL: 4, SUBSET: 3, SUPERSET: 3, OVERLAP: 2, DISJOINT: 1}


def _is_simple_cardinality_cut(tree: CutDependency) -> bool:
    """True iff this cut is a single ``size``/``count``/``numof`` call
    on a single object or builtin child.

    Composite or mixed cuts (e.g. ``size(X) + size(Y)``,
    ``size(X) and pT(X[0])>30``) intentionally fall through and use the
    general comparison path.
    """
    if tree is None or not tree.own_constraint_exprs:
        return False
    leaves = [c for ce in tree.own_constraint_exprs
                for c in constraint_expr_leaves(ce)]
    if not leaves:
        return False
    fc = leaves[0]
    if fc.lhs.outer_func_chain().lower() not in _CARDINALITY_FUNCS:
        return False
    obj_or_builtin_children = [
        ch for ch in tree.children if isinstance(ch, (ObjectDependency, BuiltinDependency))
    ]
    define_children = [ch for ch in tree.children if isinstance(ch, DefineDependency)]
    return len(obj_or_builtin_children) == 1 and not define_children


def _cardinality_object_child(tree: CutDependency) -> Optional[CutDependency]:
    """The single object/builtin child of a simple cardinality cut.
    Returns ``None`` if the cut isn't a simple cardinality cut."""
    if not _is_simple_cardinality_cut(tree):
        return None
    for ch in tree.children:
        if isinstance(ch, (ObjectDependency, BuiltinDependency)):
            return ch
    return None


def _compare_region_variables(
    reg_a: RegionIR, reg_b: RegionIR,
) -> Tuple[List[CutPairResult], List[VariableOverlap]]:
    cuts_a = _collect_region_cuts(reg_a)
    cuts_b = _collect_region_cuts(reg_b)

    sig_a: Dict[Tuple[str, Tuple[str, ...]], List[ResolvedCutIR]] = {}
    sig_b: Dict[Tuple[str, Tuple[str, ...]], List[ResolvedCutIR]] = {}
    unsigned_a: List[ResolvedCutIR] = []
    unsigned_b: List[ResolvedCutIR] = []

    for rc in cuts_a:
        s = _top_level_signature(rc.dependency_tree) if rc.dependency_tree else None
        if s is None:
            unsigned_a.append(rc)
        else:
            sig_a.setdefault(s, []).append(rc)

    for rc in cuts_b:
        s = _top_level_signature(rc.dependency_tree) if rc.dependency_tree else None
        if s is None:
            unsigned_b.append(rc)
        else:
            sig_b.setdefault(s, []).append(rc)

    # Several cuts on one side in the same bucket are cuts on the same
    # variable — AND them into one before pairing (see
    # ``_merge_same_axis_cuts``). ``~=`` buckets are left alone: a
    # chi-square minimization has no interval to intersect.
    merged_info: Dict[int, Tuple[str, Tuple[str, ...], List[ResolvedCutIR], RegionIR]] = {}
    for side, sig_map, reg in (("A", sig_a, reg_a), ("B", sig_b, reg_b)):
        for key, rcs in list(sig_map.items()):
            if len(rcs) < 2 or any(_tree_has_chi2_min(rc.dependency_tree) for rc in rcs):
                continue
            merged = _merge_same_axis_cuts(rcs)
            origins: List[Tuple[str, ...]] = []
            for rc in rcs:
                o = reg.cut_origins.get(id(rc), ())
                if o not in origins:
                    origins.append(o)
            if origins == [()]:
                origin: Tuple[str, ...] = ()
            elif len(origins) == 1:
                origin = origins[0]
            else:
                origin = (" + ".join(_render_origin_path(o) for o in origins),)
            merged_info[id(merged.dependency_tree)] = (side, origin, rcs, reg)
            sig_map[key] = [merged]

    cut_pair_results: List[CutPairResult] = []
    headline_vars: List[VariableOverlap] = []

    # Opaque region-reference lines: never matched, always OVERLAP. AND-ing
    # an unknown constraint into a region can only shrink it, so a DISJOINT
    # proven on another axis stays sound — but EQUAL/SUBSET/SUPERSET can no
    # longer be claimed, which OVERLAP enforces through ``_combine``.
    for rc in _collect_opaque_region_cuts(reg_a):
        cut_pair_results.append(CutPairResult(
            surface_a=rc.surface_vars, surface_b=set(),
            structure_matched=False, dep_values_matched=False,
            verdict=OVERLAP, notes=[f"A: {rc.region_note}"],
            tree_a=rc.dependency_tree, opaque_region_ref=True,
        ))
    for rc in _collect_opaque_region_cuts(reg_b):
        cut_pair_results.append(CutPairResult(
            surface_a=set(), surface_b=rc.surface_vars,
            structure_matched=False, dep_values_matched=False,
            verdict=OVERLAP, notes=[f"B: {rc.region_note}"],
            tree_b=rc.dependency_tree, opaque_region_ref=True,
        ))

    for s in sorted(set(sig_a) | set(sig_b), key=lambda t: (t[0], t[1])):
        # t[1] is a tuple[str, ...] → naturally sortable.
        in_a = sig_a.get(s, [])
        in_b = sig_b.get(s, [])

        if in_a and in_b:
            # Detect cardinality-only buckets: both A and B contain only
            # simple ``size``/``count``/``numof`` cuts on a single
            # object/builtin child each. In that regime, a cross-pair
            # whose underlying objects are DISJOINT carries no event-
            # level information and must NOT contribute to the verdict
            # aggregation. The general path below handles all other
            # buckets (including any bucket with a non-cardinality cut
            # on either side) with the original full cross-product.
            cardinality_only = (
                all(_is_simple_cardinality_cut(rc.dependency_tree) for rc in in_a)
                and all(_is_simple_cardinality_cut(rc.dependency_tree) for rc in in_b)
            )

            if cardinality_only:
                # Build the object-relation matrix between every
                # (rc_a, rc_b) pair. Each cut's "best available pairing"
                # is the max-rank object relation it has across the
                # other side; only pairs that are at-best for *both*
                # sides (and not DISJOINT) contribute their verdict.
                obj_rel: Dict[Tuple[int, int], str] = {}
                for ia, rc_a in enumerate(in_a):
                    obj_a = _cardinality_object_child(rc_a.dependency_tree)
                    for ib, rc_b in enumerate(in_b):
                        obj_b = _cardinality_object_child(rc_b.dependency_tree)
                        if obj_a is None or obj_b is None:
                            obj_rel[(ia, ib)] = OVERLAP  # defensive
                        else:
                            obj_rel[(ia, ib)] = _compare_object_subtrees(obj_a, obj_b)

                # Best object-relation rank achievable for each cut.
                best_rank_a = [
                    max((_OBJ_REL_RANK[obj_rel[(ia, ib)]]
                         for ib in range(len(in_b))), default=0)
                    for ia in range(len(in_a))
                ]
                best_rank_b = [
                    max((_OBJ_REL_RANK[obj_rel[(ia, ib)]]
                         for ia in range(len(in_a))), default=0)
                    for ib in range(len(in_b))
                ]

                # Whether each (ia, ib) pair "contributes" (feeds verdict
                # aggregation) depends only on obj_rel/best_rank, which
                # are already fully known — so this can be decided for
                # every pair up front, in one shot, rather than
                # discovered incrementally while emitting rows. That
                # matters because whether a NON-contributing pair is
                # worth *showing* depends on whether either of its two
                # cuts ends up matched somewhere else in the bucket, and
                # that "somewhere else" can be a pair processed later in
                # a naive single pass.
                contributing: Dict[Tuple[int, int], bool] = {}
                for ia in range(len(in_a)):
                    for ib in range(len(in_b)):
                        r = obj_rel[(ia, ib)]
                        rank = _OBJ_REL_RANK[r]
                        contributing[(ia, ib)] = (
                            r != DISJOINT
                            and rank == best_rank_a[ia]
                            and rank == best_rank_b[ib]
                        )

                # Track which cuts ended up in a contributing pair so
                # we know which ones still need a directional row.
                a_matched = [any(contributing[(ia, ib)] for ib in range(len(in_b)))
                             for ia in range(len(in_a))]
                b_matched = [any(contributing[(ia, ib)] for ia in range(len(in_a)))
                             for ib in range(len(in_b))]

                # 1. Emit one row per cross-pair. A pair "contributes"
                #    (feeds verdict aggregation) only if it is a real
                #    counterpart for both sides:
                #      * its object relation is not DISJOINT, AND
                #      * the object-relation rank equals the best
                #        available rank for both rc_a and rc_b.
                #    All other pairs are informational (shown for
                #    transparency, excluded from aggregation) — but only
                #    when they're genuinely being "passed over" in favor
                #    of a real match: if NEITHER rc_a nor rc_b has a
                #    contributing pair anywhere in the bucket, this row
                #    would just restate — a third time — the same "no
                #    real counterpart" conclusion the directional
                #    fallback rows in step 2 already give it, so it's
                #    skipped entirely.
                for ia, rc_a in enumerate(in_a):
                    for ib, rc_b in enumerate(in_b):
                        if not contributing[(ia, ib)]:
                            if not a_matched[ia] and not b_matched[ib]:
                                # No real counterpart exists anywhere for
                                # either cut — step 2's directional rows
                                # already say this; don't repeat it here.
                                continue
                            r = obj_rel[(ia, ib)]
                            if r == DISJOINT:
                                why = (
                                    "Cardinality cuts on disjoint "
                                    "sub-collections under the same root "
                                    "— pair carries no event-level "
                                    "information."
                                )
                            else:
                                why = (
                                    f"Cardinality cross-pair has object "
                                    f"relation {r}, but a stronger "
                                    f"counterpart is available elsewhere "
                                    f"in this bucket — pair excluded "
                                    f"from aggregation in favor of the "
                                    f"better match."
                                )
                            cut_pair_results.append(CutPairResult(
                                surface_a=rc_a.surface_vars,
                                surface_b=rc_b.surface_vars,
                                structure_matched=True, dep_values_matched=True,
                                variable_overlaps=[],
                                verdict=INCOMPARABLE,
                                notes=[why],
                                tree_a=rc_a.dependency_tree,
                                tree_b=rc_b.dependency_tree,
                                informational_only=True,
                            ))
                            continue

                        # Contributing pair: full _compare_dep_nodes
                        # verdict participates in aggregation.
                        v = _compare_dep_nodes(rc_a.dependency_tree,
                                               rc_b.dependency_tree)
                        vo = _build_var_overlap_from_tree_leaf(
                            rc_a.dependency_tree, rc_b.dependency_tree,
                            rc_a.leaf_chains, rc_b.leaf_chains)
                        var_overlaps_for_pair = [vo] if vo is not None else []
                        cut_pair_results.append(CutPairResult(
                            surface_a=rc_a.surface_vars,
                            surface_b=rc_b.surface_vars,
                            structure_matched=True, dep_values_matched=True,
                            variable_overlaps=var_overlaps_for_pair,
                            verdict=v,
                            notes=[f"Matched on {_format_signature(s)}; verdict = {v}."],
                            tree_a=rc_a.dependency_tree,
                            tree_b=rc_b.dependency_tree,
                        ))
                        if vo is not None:
                            headline_vars.append(vo)

                # 2. Emit directional rows for cuts that didn't appear
                #    in any contributing pair — they genuinely lack a
                #    real counterpart on the other side and act as
                #    one-sided restrictions on the region.
                for ia, rc_a in enumerate(in_a):
                    if not a_matched[ia]:
                        cut_pair_results.append(CutPairResult(
                            surface_a=rc_a.surface_vars, surface_b=set(),
                            structure_matched=False, dep_values_matched=False,
                            verdict=SUBSET,
                            notes=[
                                f"Cardinality cut {_format_signature(s)} has no "
                                f"real counterpart in B → A⊆B."
                            ],
                            tree_a=rc_a.dependency_tree,
                        ))
                for ib, rc_b in enumerate(in_b):
                    if not b_matched[ib]:
                        cut_pair_results.append(CutPairResult(
                            surface_a=set(), surface_b=rc_b.surface_vars,
                            structure_matched=False, dep_values_matched=False,
                            verdict=SUPERSET,
                            notes=[
                                f"Cardinality cut {_format_signature(s)} has no "
                                f"real counterpart in A → B⊆A."
                            ],
                            tree_b=rc_b.dependency_tree,
                        ))

            else:
                # General cross-product pairing: emit one matched
                # CutPairResult per (rc_a, rc_b) combination. Each pair
                # gets its own verdict from ``_compare_dep_nodes``,
                # which already folds in the underlying object
                # SUBSET/SUPERSET/DISJOINT/EQUAL relation via
                # ``_compare_compound_nodes``'s object-children branch.
                for rc_a in in_a:
                    for rc_b in in_b:
                        v = _compare_dep_nodes(rc_a.dependency_tree,
                                               rc_b.dependency_tree)
                        vo = _build_var_overlap_from_tree_leaf(
                            rc_a.dependency_tree, rc_b.dependency_tree,
                            rc_a.leaf_chains, rc_b.leaf_chains)
                        var_overlaps_for_pair = [vo] if vo is not None else []
                        cut_pair_results.append(CutPairResult(
                            surface_a=rc_a.surface_vars,
                            surface_b=rc_b.surface_vars,
                            structure_matched=True, dep_values_matched=True,
                            variable_overlaps=var_overlaps_for_pair,
                            verdict=v,
                            notes=[f"Matched on {_format_signature(s)}; verdict = {v}."],
                            tree_a=rc_a.dependency_tree,
                            tree_b=rc_b.dependency_tree,
                        ))
                        if vo is not None:
                            headline_vars.append(vo)

        elif in_a:
            # Bucket has cuts only on A side — emit one directional
            # CutPairResult per cut for report-row granularity.
            for rc_a in in_a:
                # Chi-square minimization (``~=``) cannot prove
                # containment in either direction. A lone ``~=`` cut on
                # the A side contributes OVERLAP, not SUBSET.
                if _tree_has_chi2_min(rc_a.dependency_tree):
                    cut_pair_results.append(CutPairResult(
                        surface_a=rc_a.surface_vars, surface_b=set(),
                        structure_matched=False, dep_values_matched=False,
                        verdict=OVERLAP,
                        notes=[
                            f"Region variable {_format_signature(s)} present only "
                            f"in A and is a chi-square minimization (~=); "
                            f"contributes OVERLAP."
                        ],
                        tree_a=rc_a.dependency_tree,
                    ))
                    continue
                cut_pair_results.append(CutPairResult(
                    surface_a=rc_a.surface_vars, surface_b=set(),
                    structure_matched=False, dep_values_matched=False,
                    verdict=SUBSET,
                    notes=[f"Region variable {_format_signature(s)} present only in A → A⊆B."],
                    tree_a=rc_a.dependency_tree,
                ))
        else:
            # Bucket has cuts only on B side — emit one directional
            # CutPairResult per cut for report-row granularity.
            for rc_b in in_b:
                # Chi-square minimization (``~=``) cannot prove
                # containment in either direction. A lone ``~=`` cut on
                # the B side contributes OVERLAP, not SUPERSET.
                if _tree_has_chi2_min(rc_b.dependency_tree):
                    cut_pair_results.append(CutPairResult(
                        surface_a=set(), surface_b=rc_b.surface_vars,
                        structure_matched=False, dep_values_matched=False,
                        verdict=OVERLAP,
                        notes=[
                            f"Region variable {_format_signature(s)} present only "
                            f"in B and is a chi-square minimization (~=); "
                            f"contributes OVERLAP."
                        ],
                        tree_b=rc_b.dependency_tree,
                    ))
                    continue
                cut_pair_results.append(CutPairResult(
                    surface_a=set(), surface_b=rc_b.surface_vars,
                    structure_matched=False, dep_values_matched=False,
                    verdict=SUPERSET,
                    notes=[f"Region variable {_format_signature(s)} present only in B → B⊆A."],
                    tree_b=rc_b.dependency_tree,
                ))

    for rc in unsigned_a:
        # Same chi-square override for cuts that produced no top-level
        # signature at all.
        if _tree_has_chi2_min(rc.dependency_tree):
            cut_pair_results.append(CutPairResult(
                surface_a=rc.surface_vars, surface_b=set(),
                structure_matched=False, dep_values_matched=False,
                verdict=OVERLAP,
                notes=[
                    "A-side chi-square minimization (~=) cut with no derivable "
                    "top-level signature; contributes OVERLAP."
                ],
                tree_a=rc.dependency_tree,
            ))
            continue
        cut_pair_results.append(CutPairResult(
            surface_a=rc.surface_vars, surface_b=set(),
            structure_matched=False, dep_values_matched=False,
            verdict=SUBSET,
            notes=["A-side cut with no derivable top-level signature → A⊆B."],
            tree_a=rc.dependency_tree,
        ))
    for rc in unsigned_b:
        if _tree_has_chi2_min(rc.dependency_tree):
            cut_pair_results.append(CutPairResult(
                surface_a=set(), surface_b=rc.surface_vars,
                structure_matched=False, dep_values_matched=False,
                verdict=OVERLAP,
                notes=[
                    "B-side chi-square minimization (~=) cut with no derivable "
                    "top-level signature; contributes OVERLAP."
                ],
                tree_b=rc.dependency_tree,
            ))
            continue
        cut_pair_results.append(CutPairResult(
            surface_a=set(), surface_b=rc.surface_vars,
            structure_matched=False, dep_values_matched=False,
            verdict=SUPERSET,
            notes=["B-side cut with no derivable top-level signature → B⊆A."],
            tree_b=rc.dependency_tree,
        ))

    # Stamp inheritance provenance. Each ResolvedCutIR owns a unique root
    # dependency tree, so the tree identity maps a row back to its cut.
    origin_by_tree_a = {id(rc.dependency_tree): reg_a.cut_origins.get(id(rc), ())
                        for rc in reg_a.comparison_cuts()}
    origin_by_tree_b = {id(rc.dependency_tree): reg_b.cut_origins.get(id(rc), ())
                        for rc in reg_b.comparison_cuts()}
    def _merge_note(info) -> str:
        side, _origin, rcs, reg = info
        parts = []
        for rc in rcs:
            o = reg.cut_origins.get(id(rc), ())
            tag = f" [from {_render_origin_path(o)}]" if o else ""
            parts.append(f"{rc.dependency_tree.name}{tag}")
        return (f"{side}: {len(rcs)} cuts on this variable combined (AND) "
                f"before comparison: " + "; ".join(parts) + ".")

    for cp in cut_pair_results:
        if cp.tree_a is not None:
            info = merged_info.get(id(cp.tree_a))
            if info is not None:
                cp.origin_a = info[1]
                cp.notes.append(_merge_note(info))
            else:
                cp.origin_a = origin_by_tree_a.get(id(cp.tree_a), ())
        if cp.tree_b is not None:
            info = merged_info.get(id(cp.tree_b))
            if info is not None:
                cp.origin_b = info[1]
                cp.notes.append(_merge_note(info))
            else:
                cp.origin_b = origin_by_tree_b.get(id(cp.tree_b), ())

    return cut_pair_results, headline_vars


# ─────────────────────────────────────────────────────────────────────────────
# Rule 2b — cardinality-bound disjointness proof
# ─────────────────────────────────────────────────────────────────────────────
#
# The per-variable pairing above compares ``size(X)`` with ``size(Y)`` only
# when both land in the same signature bucket, and ``IdNode.src_object``
# deliberately keeps differently-named objects in different buckets (pairing
# them by interval alone would be unsound: ``size(X)==0`` vs ``size(Y)>=1`` is
# NOT disjoint unless Y ⊆ X). So the classic veto pattern
#
#     A:  size(vetoEle) == 0, size(vetoMuo) == 0     (pT > 7)
#     B:  size(Union(sigEle, sigMuo)) >= 1           (pT > 10)
#
# never got compared at all and fell through to SUBSET + SUPERSET → OVERLAP.
# Proving it disjoint needs two things the bucket machinery can't do:
#
#   * decompose a Union into its branches — size(Union(a, b)) ≤ size(a)+size(b)
#     — and bound each branch separately; and
#   * use SEVERAL cuts of the other region together (the electron branch is
#     killed by the electron veto, the muon branch by the muon veto; neither
#     veto alone suffices).
#
# The proof, over every cardinality cut of both regions (an event in A∩B
# satisfies all of them):
#
#   1. Upper bounds.  A cut ``size(X1) + … + size(Xn) <= u`` (also ``==``,
#      ``<``) gives size(Xi) ≤ u for each term (counts are non-negative).
#      Every leaf branch x of Xi (one built-in root plus the conjunction of
#      element cuts on the path down to it) has size(x) ≤ size(Xi) ≤ u.
#   2. Lower bounds.  For a cut ``size(Y1) + … + size(Ym) >= l`` (l ≥ 1),
#      size(Yj) ≤ Σ over Yj's leaf branches b of size(b), and size(b) ≤ u
#      whenever b ⊆ x for some upper-bounded branch x with the same root
#      (b's element cuts imply x's). Unbounded branches count as ∞.
#   3. If the summed upper bound is < l, no event can satisfy both → DISJOINT.
#
# Element cuts inside an object (``select pT(sigLep) > 20`` inside
# ``hardLep``) are per-element properties regardless of which name the user
# wrote, so they are keyed by function chain alone ("pt") when they refer to
# the object itself or anything on its inheritance path; anything else
# (indexed access, multi-argument functions, other collections) is keyed by
# its full LHS signature and must match exactly. Every approximation errs
# toward "no proof": a branch condition we can't interpret on the subset side
# is dropped (makes b larger), and one we can't interpret on the superset
# side blocks the implication.

@dataclass
class _CardinalityBound:
    side: str                       # "A" or "B"
    label: str                      # source-form cut text, for notes
    terms: List[CutDependency]      # objects/builtins whose sizes are summed
    lo: float                       # integer lower bound (≥ 0)
    hi: float                       # integer upper bound (may be +inf)


def _integer_hull(iv: IntervalSet) -> Optional[Tuple[float, float]]:
    """Smallest [lo, hi] (non-negative integers, hi may be +inf) containing
    every integer of ``iv``. None if ``iv`` holds no non-negative integer."""
    lo: Optional[float] = None
    hi: Optional[float] = None
    for itv in iv.intervals:
        il = 0.0 if itv.lo == -math.inf else float(math.ceil(itv.lo))
        if itv.lo_open and il == itv.lo:
            il += 1
        il = max(il, 0.0)
        if itv.hi == math.inf:
            ih = math.inf
        else:
            ih = float(math.floor(itv.hi))
            if itv.hi_open and ih == itv.hi:
                ih -= 1
        if ih < il:
            continue
        lo = il if lo is None else min(lo, il)
        hi = ih if hi is None else max(hi, ih)
    return None if lo is None else (lo, hi)


def _find_object_node(tree: CutDependency, name: str,
                      _seen: Optional[Set[int]] = None) -> Optional[CutDependency]:
    """The ObjectDependency called ``name`` among ``tree``'s direct object
    children or those reached through define wrappers."""
    if _seen is None:
        _seen = set()
    if id(tree) in _seen:
        return None
    _seen.add(id(tree))
    nl = name.lower()
    for ch in tree.children:
        if isinstance(ch, ObjectDependency) and ch.name.lower() == nl:
            return ch
    for ch in tree.children:
        if isinstance(ch, DefineDependency):
            hit = _find_object_node(ch, name, _seen)
            if hit is not None:
                return hit
    return None


def _cardinality_terms(lhs, tree: CutDependency) -> Optional[List[CutDependency]]:
    """``size(X)`` or ``size(X) + size(Y) + …`` (whole collections only) →
    the dependency nodes of X, Y, …; None for anything else."""
    terms = list(lhs.children) if (isinstance(lhs, BinOpNode) and lhs.op == "+") else [lhs]
    out: List[CutDependency] = []
    for t in terms:
        if not (isinstance(t, FuncNode)
                and t.func_chain.lower() in _CARDINALITY_FUNCS
                and len(t.args) == 1
                and isinstance(t.args[0], IdNode)
                and not t.args[0].accessor):
            return None
        idn: IdNode = t.args[0]
        if idn.src_object:
            node = _find_object_node(tree, idn.src_object)
        elif idn.collection.upper() in BUILTIN_OBJECTS:
            node = BuiltinDependency(name=canonicalise(idn.collection))
        else:
            node = None
        if node is None:
            return None
        out.append(node)
    return out


def _collect_cardinality_bounds(reg: RegionIR, side: str) -> List[_CardinalityBound]:
    """Integer bounds on every cardinality expression constrained by the
    region. Cuts on the same expression are intersected first."""
    by_sig: Dict[str, Tuple[List[ConstraintExpr], List[CutDependency], List[str]]] = {}
    for rc in _collect_region_cuts(reg):
        tree = rc.dependency_tree
        if tree is None:
            continue
        for leaf in constraint_expr_leaves(rc.constraint_expr):
            if _is_chi2_min_cut(leaf):
                continue
            terms = _cardinality_terms(leaf.lhs, tree)
            if not terms:
                continue
            sig = leaf.lhs.signature()
            entry = by_sig.setdefault(sig, ([], terms, []))
            if not any(e is rc.constraint_expr for e in entry[0]):
                entry[0].append(rc.constraint_expr)
                entry[2].append(tree.name)
    out: List[_CardinalityBound] = []
    for sig, (exprs, terms, labels) in by_sig.items():
        # Sound per-axis projection: an AND with other axes leaves this
        # axis's restriction intact; an OR with another axis widens it to
        # "everything" (no bound), never narrower than the truth.
        hull = _integer_hull(evaluate_axis_for_exprs(exprs, sig))
        if hull is None:
            continue
        out.append(_CardinalityBound(side, " ∧ ".join(labels), terms, hull[0], hull[1]))
    return out


def _leaf_branches(node: CutDependency, _path: frozenset = frozenset(), _depth: int = 0,
                   ) -> Optional[List[Tuple[str, Tuple[ConstraintExpr, ...], frozenset]]]:
    """Every built-in branch of an object: ``(root, element cuts on the
    path, lowercased names on the path)``. None when any branch can't be
    traced to a recognised built-in (unknown parent, empty object)."""
    if _depth > 25:
        return None
    if isinstance(node, BuiltinDependency):
        roots = node.roots()
        if len(roots) != 1:
            return None
        r = next(iter(roots))
        return [(r, (), _path | {r.lower(), node.name.lower()})]
    if not isinstance(node, ObjectDependency):
        return None
    path = _path | {node.name.lower()}
    parents = [ch for ch in node.children
               if isinstance(ch, (ObjectDependency, BuiltinDependency))]
    if not parents:
        return None
    out = []
    for p in parents:
        sub = _leaf_branches(p, path, _depth + 1)
        if sub is None:
            return None
        for r, exprs, names in sub:
            out.append((r, tuple(node.own_constraint_exprs) + exprs, names))
    return out


def _branch_dropped(names: frozenset, ir_nodes: Dict[str, CutDependency]) -> List[str]:
    """Unmodelled (dropped) cuts of the objects on a branch path."""
    out: List[str] = []
    for n in names:
        node = ir_nodes.get(n)
        if node is not None:
            out += _cumulative_dropped_own(node)
    return sorted(out)


def _cumulative_dropped_own(node: CutDependency) -> List[str]:
    import re as _re
    from expr_node import SRC_OBJECT_ALIASES as _al
    return [_re.sub(r"[A-Za-z_][A-Za-z0-9_]*",
                    lambda m: _al.get(m.group(0).lower(), m.group(0).lower()), d)
            for d in (getattr(node, "dropped", []) or [])]


def _object_nodes_by_name(*trees) -> Dict[str, CutDependency]:
    found: Dict[str, CutDependency] = {}
    stack = list(trees)
    while stack:
        n = stack.pop()
        if n is None:
            continue
        if isinstance(n, ObjectDependency):
            if n.name.lower() in found:
                continue
            found[n.name.lower()] = n
        stack.extend(getattr(n, "children", []) or [])
    return found


def _flatten_conjuncts(exprs) -> List[ConstraintExpr]:
    out: List[ConstraintExpr] = []
    for e in exprs:
        if isinstance(e, ConstraintAnd):
            out.extend(_flatten_conjuncts(e.children))
        else:
            out.append(e)
    return out


def _element_axis_key(cut: CutStructure, path_names: frozenset) -> Tuple[str, str]:
    """Key identifying what an object-level cut measures. A single-argument
    property of the element being filtered (``pT(this)``, ``abs∘eta(parent)``)
    is keyed by its function chain alone, since the collection label on it
    is just whichever name the user wrote. Everything else keeps its full
    structural signature."""
    lhs = cut.lhs
    if (isinstance(lhs, FuncNode) and len(lhs.args) == 1
            and isinstance(lhs.args[0], IdNode)
            and not lhs.args[0].accessor
            and lhs.func_chain.lower() not in _CARDINALITY_FUNCS):
        idn: IdNode = lhs.args[0]
        ref = (idn.src_object or idn.collection).lower()
        if ref in path_names:
            return ("elem", lhs.func_chain.lower())
    return ("sig", lhs.signature())


def _branch_interval(conjuncts: List[ConstraintExpr], key: Tuple[str, str],
                     path_names: frozenset) -> IntervalSet:
    """What a branch's own conjuncts allow on ``key``. Leaves and
    single-axis ORs of leaves (``reject abs(eta) [] 1.37 1.52``) are used
    exactly; anything else and ``~=`` leaves are ignored, which can only
    widen the result (safe on the subset side of an implication)."""
    iv = IntervalSet.everything()
    for c in conjuncts:
        if isinstance(c, ConstraintLeaf) and not _is_chi2_min_cut(c.cut):
            if _element_axis_key(c.cut, path_names) == key:
                iv = iv.intersect(IntervalSet.from_constraint(c.cut))
        elif (isinstance(c, ConstraintOr) and c.children
              and all(isinstance(k, ConstraintLeaf) and not _is_chi2_min_cut(k.cut)
                      and _element_axis_key(k.cut, path_names) == key
                      for k in c.children)):
            union = IntervalSet.empty()
            for k in c.children:
                union = union.union(IntervalSet.from_constraint(k.cut))
            iv = iv.intersect(union)
    return iv


def _branch_implies(sub_conj: List[ConstraintExpr], sub_names: frozenset,
                    req: ConstraintExpr, sup_names: frozenset) -> bool:
    """Does every element passing ``sub_conj`` also pass ``req``?"""
    if isinstance(req, ConstraintLeaf):
        if _is_chi2_min_cut(req.cut):
            return False
        key = _element_axis_key(req.cut, sup_names)
        return IntervalSet.from_constraint(req.cut).contains_set(
            _branch_interval(sub_conj, key, sub_names))
    if isinstance(req, ConstraintAnd):
        return all(_branch_implies(sub_conj, sub_names, ch, sup_names)
                   for ch in req.children)
    if isinstance(req, ConstraintOr):
        if any(_branch_implies(sub_conj, sub_names, ch, sup_names)
               for ch in req.children):
            return True
        # OR of leaves on one axis (e.g. ``reject abs(eta) [] 1.44 1.56``):
        # implied if the branch's range on that axis fits inside the union.
        kids = req.children
        if kids and all(isinstance(k, ConstraintLeaf) and not _is_chi2_min_cut(k.cut)
                        for k in kids):
            keys = {_element_axis_key(k.cut, sup_names) for k in kids}
            if len(keys) == 1:
                union = IntervalSet.empty()
                for k in kids:
                    union = union.union(IntervalSet.from_constraint(k.cut))
                return union.contains_set(
                    _branch_interval(sub_conj, next(iter(keys)), sub_names))
        return False
    return False


def _prover_branch_in(root, names, xroot, xnames) -> bool:
    """object_containment fallback: the branch (root, names) of one object
    lies in the branch (xroot, xnames) of another."""
    if _PROVER is None or root != xroot:
        return False
    b = _PROVER.branch_by_path(root, names)
    xb = _PROVER.branch_by_path(xroot, xnames)
    return b is not None and xb is not None and _PROVER.branch_implies(b[2], xb[2])


def _prove_cardinality_disjoint(reg_a: RegionIR, reg_b: RegionIR) -> Optional[str]:
    """A human-readable proof that no event passes both regions, using the
    cardinality bounds described above; None if no such proof is found.

    Each upper-bounded cut is a *container* with capacity c (for
    ``size(Y1)+…+size(Yn) <= c`` the capacity is shared by all its terms).
    Every branch of the required collection Z must be assigned to a
    container holding a superset branch of the same root. A container's
    capacity is charged once for branches of distinct roots (an electron
    is never a muon, so they are distinct elements of the container); n
    branches of the SAME root assigned to one container are charged n·c,
    since a Union of overlapping same-root objects may repeat elements.
    The cheapest assignment gives the bound on size(Z).
    """
    bounds = (_collect_cardinality_bounds(reg_a, "A")
              + _collect_cardinality_bounds(reg_b, "B"))
    if not bounds:
        return None

    # containers: (capacity, label, [(root, conjuncts, path names)])
    containers = []
    for bd in bounds:
        if bd.hi == math.inf:
            continue
        brs_all = []
        for t in bd.terms:
            brs = _leaf_branches(t)
            if brs is not None:
                brs_all += [(r, _flatten_conjuncts(e), n) for r, e, n in brs]
        if brs_all:
            containers.append((bd.hi, f"{bd.side}: {bd.label}", brs_all))

    # Unmodelled cuts (see ir_extractor._DROPPED_SINK): a container branch
    # with extra unmodelled cuts can be smaller than modelled, so a Z branch
    # is only proven to lie in it if the Z branch carries the same cuts.
    _nodes = _object_nodes_by_name(
        *[rc.dependency_tree for rc in _collect_region_cuts(reg_a)],
        *[rc.dependency_tree for rc in _collect_region_cuts(reg_b)])

    def _dropped_ok(sub_names, sup_names) -> bool:
        need = _branch_dropped(sup_names, _nodes)
        have = _branch_dropped(sub_names, _nodes)
        for d in need:
            if d in have:
                have.remove(d)
            else:
                return False
        return True

    for bd in bounds:
        if bd.lo < 1:
            continue
        z_branches = []          # (root, term name, candidate container idxs)
        ok = True
        for t in bd.terms:
            brs = _leaf_branches(t)
            if brs is None:
                ok = False
                break
            for r, exprs, names in brs:
                conj = _flatten_conjuncts(exprs)
                cands = [ci for ci, (_c, _l, cbrs) in enumerate(containers)
                         if any(xr == r and all(_branch_implies(conj, names, req, xn)
                                                for req in xconj)
                                and _dropped_ok(names, xn)
                                or _prover_branch_in(r, names, xr, xn)
                                for xr, xconj, xn in cbrs)]
                if not cands:
                    ok = False
                    break
                z_branches.append((r, t.name, cands))
            if not ok:
                break
        if not ok:
            continue

        def cost(assign):
            per: Dict[int, Dict[str, int]] = {}
            for (r, _n, _c), ci in zip(z_branches, assign):
                per.setdefault(ci, {}).setdefault(r, 0)
                per[ci][r] += 1
            return sum(containers[ci][0] * max(cnt.values()) for ci, cnt in per.items())

        # Exhaustive search over assignments (branch counts are tiny);
        # greedy cheapest-candidate fallback beyond the cap.
        n_combo = 1
        for _r, _n, c in z_branches:
            n_combo *= len(c)
        if n_combo <= 4096:
            import itertools
            best = min(itertools.product(*[c for _r, _n, c in z_branches]), key=cost)
        else:
            best = tuple(min(c, key=lambda ci: containers[ci][0]) for _r, _n, c in z_branches)
        total = cost(best)
        if total < bd.lo:
            used = [f"{r} branch of {n} ⊆ ({containers[ci][1]}, ≤ {_fmt(containers[ci][0])})"
                    for (r, n, _c), ci in zip(z_branches, best)]
            return (f"Cardinality bound: {bd.side}: {bd.label} needs ≥ {_fmt(bd.lo)}, "
                    f"but the other cuts allow at most {_fmt(total)} — "
                    + "; ".join(used) + ". No event can pass both regions.")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Region-pair comparison  (Rules 1, 2, 3, 4)
# ─────────────────────────────────────────────────────────────────────────────

def _check_region_pair(
    reg_a: RegionIR, name_a: str,
    reg_b: RegionIR, name_b: str,
    ir_a: AnalysisIR, ir_b: AnalysisIR,
) -> RegionPairResult:
    shared_builtins = reg_a.all_builtin_objects() & reg_b.all_builtin_objects()

    # Rule 1
    if not shared_builtins:
        return RegionPairResult(
            region_a=name_a, region_b=name_b,
            analysis_a=ir_a.source_file, analysis_b=ir_b.source_file,
            shared_builtin_objects=shared_builtins,
            verdict=DISJOINT,
            notes=["No shared built-in collections between these regions (Rule 1)."],
            cuts_a=reg_a.comparison_cuts(), cuts_b=reg_b.comparison_cuts(),
        )

    # Rules 2 & 3
    cut_pair_results, headline_vars = _compare_region_variables(reg_a, reg_b)

    # Rule 4: combine
    # Informational-only rows (e.g. cardinality cross-pairs on disjoint
    # sub-collections, tagged INCOMPARABLE) are shown in the report but
    # excluded from verdict aggregation by design — they carry no
    # event-level information about region containment.
    aggregating = [cp for cp in cut_pair_results if not cp.informational_only]
    informational = [cp for cp in cut_pair_results if cp.informational_only]
    contribs = [cp.verdict for cp in aggregating]
    verdict = _combine(contribs) if contribs else OVERLAP

    # Rule 2b: the per-variable pairing can't combine cuts across
    # differently-named objects or decompose Union objects; try the
    # cardinality-bound proof. It only ever adds a (sound) DISJOINT.
    if verdict != DISJOINT:
        proof = _prove_cardinality_disjoint(reg_a, reg_b)
        if proof is not None:
            cp = CutPairResult(
                surface_a=set(), surface_b=set(),
                structure_matched=True, dep_values_matched=True,
                verdict=DISJOINT, notes=[proof],
            )
            cut_pair_results.append(cp)
            aggregating.append(cp)
            verdict = DISJOINT

    notes: List[str] = []
    by_v: Dict[str, int] = {}
    for cp in aggregating:
        by_v[cp.verdict] = by_v.get(cp.verdict, 0) + 1
    if by_v:
        summary = ", ".join(f"{v}={n}" for v, n in sorted(by_v.items()))
        notes.append(f"Cut-pair contributions: {summary}.")
    if informational:
        notes.append(
            f"{len(informational)} cardinality cross-pair(s) on disjoint "
            f"sub-collections shown for transparency but excluded from "
            f"verdict aggregation."
        )
    notes.append(f"Combined verdict: {verdict}.")
    notes.extend(_region_inheritance_notes(reg_a, "A"))
    notes.extend(_region_inheritance_notes(reg_b, "B"))

    return RegionPairResult(
        region_a=name_a, region_b=name_b,
        analysis_a=ir_a.source_file, analysis_b=ir_b.source_file,
        shared_builtin_objects=shared_builtins,
        cut_pair_results=cut_pair_results,
        variable_overlaps=headline_vars,
        verdict=verdict,
        notes=notes,
        cuts_a=reg_a.comparison_cuts(), cuts_b=reg_b.comparison_cuts(),
    )


def _region_inheritance_notes(reg: RegionIR, side: str) -> List[str]:
    """Human-readable inheritance summary + warnings for one side."""
    out: List[str] = []
    if reg.parents:
        out.append(f"{side}: {reg.name} inherits from {', '.join(reg.parents)}.")
    for w in reg.warnings:
        out.append(f"{side} ⚠ {reg.name}: {w}")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Object-level comparison for the report (informational only)
# ─────────────────────────────────────────────────────────────────────────────

def _dep_chain_repr(node: Optional[CutDependency]) -> str:
    """A short, readable linear rendering of an object's inheritance chain,
    e.g. ``"goodJets -> jets -> JET"``, for display purposes only (report
    notes/tables). Mirrors the old (removed) ``ObjectInheritanceChain.__repr__``
    format. Walks the first ObjectDependency/BuiltinDependency child at each
    level -- a Union object has more than one branch (see ``roots()``), but a
    single representative path is all a display string needs."""
    if node is None:
        return "Chain()"
    names = [node.name]
    cur = node
    while True:
        nxt = next(
            (ch for ch in cur.children
             if isinstance(ch, (ObjectDependency, BuiltinDependency))),
            None,
        )
        if nxt is None:
            break
        names.append(nxt.name)
        cur = nxt
    return "Chain(" + " -> ".join(names) + ")"


def _check_object_pair_for_report(
    obj_a: ObjectIR, ir_a: AnalysisIR,
    obj_b: ObjectIR, ir_b: AnalysisIR,
) -> ObjectPairResult:
    chain_a = obj_a.chain
    chain_b = obj_b.chain
    root_a = obj_a.root_type()
    root_b = obj_b.root_type()
    roots_a = chain_a.roots() if chain_a is not None else set()
    roots_b = chain_b.roots() if chain_b is not None else set()

    var_overlaps: List[VariableOverlap] = []
    if roots_a and roots_b and (roots_a & roots_b):
        verdict = _compare_object_subtrees(chain_a, chain_b,
                                            var_overlaps_out=var_overlaps)
    else:
        verdict = OVERLAP

    struct_matched = bool(roots_a and roots_b and (roots_a & roots_b))
    dep_values_matched = (verdict == EQUAL)

    notes: List[str] = []
    if verdict == EQUAL:
        notes.append("All cumulative cuts identical.")
    elif verdict == SUBSET:
        notes.append("A's cumulative cuts are a strict restriction of B's (A⊆B).")
    elif verdict == SUPERSET:
        notes.append("B's cumulative cuts are a strict restriction of A's (B⊆A).")
    elif verdict == DISJOINT:
        notes.append("Cumulative cuts contain a disjoint interval pair.")
    elif not struct_matched:
        notes.append("Different built-in roots (or unknown).")
    else:
        notes.append("Cumulative cuts overlap without strict containment.")

    return ObjectPairResult(
        object_a=obj_a.name, object_b=obj_b.name,
        analysis_a=ir_a.source_file, analysis_b=ir_b.source_file,
        chain_a=_dep_chain_repr(chain_a), chain_b=_dep_chain_repr(chain_b),
        root_a=root_a, root_b=root_b,
        structure_matched=struct_matched,
        dep_values_matched=dep_values_matched,
        variable_overlaps=var_overlaps,
        verdict=verdict,
        notes=notes,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

def _all_builtins_in_ir(ir: AnalysisIR) -> Set[str]:
    builtins: Set[str] = set()
    for obj in ir.objects.values():
        # All roots, not ``root_type()``'s single representative: a Union
        # object spans several built-in collections.
        if obj.chain is not None:
            builtins |= obj.chain.roots()
    for reg in ir.regions.values():
        builtins |= reg.all_builtin_objects()
    return builtins


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def compare(
    ir_a: AnalysisIR, ir_b: AnalysisIR,
) -> OverlapReport:
    import expr_node as _en
    from object_containment import ObjectProver
    global _PROVER
    _en.SRC_OBJECT_ALIASES.clear()
    _PROVER = ObjectProver(ir_a, ir_b)
    try:
        _en.SRC_OBJECT_ALIASES.update(_equal_object_aliases(ir_a, ir_b))
        return _compare_impl(ir_a, ir_b)
    finally:
        _en.SRC_OBJECT_ALIASES.clear()
        _PROVER = None


def _equal_object_aliases(ir_a: AnalysisIR, ir_b: AnalysisIR) -> Dict[str, str]:
    """Canonical names for objects proven EQUAL across the two analyses.

    Signatures of cuts embed the referenced object's name (IdNode.src_object),
    so identical definitions written under different names (``cleanJets`` in
    one file, ``s16cleanJets`` in the other) never matched, and nothing that
    depends on them (overlap removal, multiplicity cuts) could be compared.
    Objects are compared bottom-up; whenever a pair is EQUAL, both names are
    mapped to one representative and the comparison is repeated, so EQUAL
    parents (jets, electrons) make their overlap-removed children comparable.
    """
    import expr_node as _en
    parent: Dict[str, str] = {}

    def find(x: str) -> str:
        while parent.get(x, x) != x:
            x = parent[x]
        return x

    pairs = [(oa, ob) for oa in ir_a.objects.values() for ob in ir_b.objects.values()
             if oa.chain is not None and ob.chain is not None
             and oa.root_type() != "UNKNOWN" and oa.root_type() == ob.root_type()
             and oa.name.lower() != ob.name.lower()]
    for _ in range(10):
        changed = False
        for oa, ob in pairs:
            na, nb = find(oa.name.lower()), find(ob.name.lower())
            if na == nb:
                continue
            if _compare_object_subtrees(oa.chain, ob.chain) == EQUAL:
                rep, other = sorted((na, nb))
                parent[other] = rep
                changed = True
        aliases = {n: find(n) for n in list(parent)}
        _en.SRC_OBJECT_ALIASES.clear()
        _en.SRC_OBJECT_ALIASES.update(aliases)
        if not changed:
            break
    return {n: find(n) for n in list(parent)}


def _compare_impl(
    ir_a: AnalysisIR, ir_b: AnalysisIR,
) -> OverlapReport:
    report = OverlapReport(analysis_a=ir_a.source_file, analysis_b=ir_b.source_file)

    builtins_a = _all_builtins_in_ir(ir_a)
    builtins_b = _all_builtins_in_ir(ir_b)
    no_shared_builtins = not (builtins_a & builtins_b)

    for obj_a in ir_a.objects.values():
        for obj_b in ir_b.objects.values():
            if obj_a.root_type() == "UNKNOWN" or obj_b.root_type() == "UNKNOWN":
                continue
            if obj_a.root_type() != obj_b.root_type():
                continue
            report.object_results.append(
                _check_object_pair_for_report(obj_a, ir_a, obj_b, ir_b)
            )

    if no_shared_builtins:
        for name_a, reg_a in ir_a.regions.items():
            for name_b, reg_b in ir_b.regions.items():
                report.region_results.append(RegionPairResult(
                    region_a=name_a, region_b=name_b,
                    analysis_a=ir_a.source_file, analysis_b=ir_b.source_file,
                    shared_builtin_objects=set(),
                    verdict=DISJOINT,
                    notes=["No shared built-in collections between "
                           "the two ADLs (Rule 1)."],
                    cuts_a=reg_a.comparison_cuts(), cuts_b=reg_b.comparison_cuts(),
                ))
    else:
        for name_a, reg_a in ir_a.regions.items():
            for name_b, reg_b in ir_b.regions.items():
                report.region_results.append(
                    _check_region_pair(reg_a, name_a, reg_b, name_b, ir_a, ir_b)
                )

    return report


def compare_many(analyses: List[AnalysisIR]) -> List[OverlapReport]:
    reports = []
    for i in range(len(analyses)):
        for j in range(i+1, len(analyses)):
            reports.append(compare(analyses[i], analyses[j]))
    return reports
