"""
Sound proofs of containment between object definitions (A ⊆ B), including
overlap-removal cuts that the interval model cannot represent.

Each object is rewritten, from the raw ADL conditions, as a union of
*branches* (one per built-in collection it is taken from). A branch is a
conjunction of element-wise cuts of three kinds:

  iv      a property of the element in a set of intervals
          (``pT(ELE) > 7``, ``abs(eta(x)) < 2.47``, ``BTag(x) == 1``)
  allof   ``for every y in Y: dR(element, y) satisfies one of the atoms``,
          each atom being  dR op t(pT)  with  t(pT) = min(c, a + b/pT)
          (a constant threshold d is min(d, d + 0/pT)); this covers
          ``dR(e, allof(J)) > 0.2`` and
          ``dR(m, allof(J)) < 0.2 or dR(m, allof(J)) >= min(0.4, 0.04 + 10/pT(m))``
  opaque  anything else, kept as a canonical string

A ⊆ B is proven when every branch of A lies in a branch of B with the same
built-in root, i.e. when every cut of the B branch is implied by the cuts of
the A branch:

  iv      the A intervals on the same property fit inside the B intervals
  allof   A has an allof cut over a collection Y_A with Y_B ⊆ Y_A (proven
          recursively) and every atom of A implies an atom of B for all pT
          the A branch allows. A condition that holds for every element of a
          larger collection with a stricter threshold holds for every element
          of a smaller collection with a looser threshold. This is valid both
          if CutLang evaluates the OR per jet and if it evaluates each
          ``allof`` comparison separately, and for an empty collection
          (vacuously true on both sides).
  opaque  the identical cut is present on A (same text, same references)

Thresholds are piecewise linear in u = 1/pT, so t_A - t_B is checked
exactly at the ends of the allowed u range and at the kinks.

Nothing is ever claimed from a cut the prover does not understand, so a
False result only means "not proven". Objects with the same name but
different definitions in the two analyses (and everything that refers to
them) are excluded.
"""
from __future__ import annotations

import json
import math
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

INF = math.inf
_NEG = {"<": ">=", "<=": ">", ">": "<=", ">=": "<", "==": "!=", "!=": "=="}
_SWAP = {"<": ">", "<=": ">=", ">": "<", ">=": "<=", "==": "==", "!=": "!="}


# ── interval sets: tuple of (lo, lo_incl, hi, hi_incl) ─────────────────────

def _iv_from(op: str, v: float):
    if op == ">":  return ((v, False, INF, False),)
    if op == ">=": return ((v, True, INF, False),)
    if op == "<":  return ((-INF, False, v, False),)
    if op == "<=": return ((-INF, False, v, True),)
    if op == "==": return ((v, True, v, True),)
    if op == "!=": return ((-INF, False, v, False), (v, False, INF, False))
    return None


_ALL = ((-INF, False, INF, False),)


def _iv_and(x, y):
    out = []
    for (a, ai, b, bi) in x:
        for (c, ci, d, di) in y:
            lo, loi = (a, ai) if a > c else (c, ci) if c > a else (a, ai and ci)
            hi, hii = (b, bi) if b < d else (d, di) if d < b else (b, bi and di)
            if lo < hi or (lo == hi and loi and hii):
                out.append((lo, loi, hi, hii))
    return tuple(out)


def _iv_or(x, y):
    return tuple(x) + tuple(y)


def _piece_in(p, q) -> bool:
    (a, ai, b, bi), (c, ci, d, di) = p, q
    lo_ok = a > c or (a == c and (ci or not ai))
    hi_ok = b < d or (b == d and (di or not bi))
    return lo_ok and hi_ok


def _iv_subset(x, y) -> bool:
    """x ⊆ y (sufficient check: each piece of x inside one piece of y)."""
    return all(any(_piece_in(p, q) for q in y) for p in x)


def _iv_hull(x):
    if not x:
        return None
    lo = min(p[0] for p in x)
    hi = max(p[2] for p in x)
    return lo, hi


# ── thresholds  t(u) = min(c, a + b u),  u = 1/pT ─────────────────────────

def _t(th, u):
    c, a, b = th
    return min(c, a + b * u)


def _th_ge(ts, tz, umin, umax, strict) -> bool:
    """ts(u) >= tz(u) (or > if strict) for all u in [umin, umax]."""
    pts = {umin, umax}
    for (c, a, b) in (ts, tz):
        if b != 0:
            k = (c - a) / b
            if umin < k < umax:
                pts.add(k)
    for u in pts:
        d = _t(ts, u) - _t(tz, u)
        if d < -1e-12 or (strict and d <= 1e-12):
            return False
    return True


def _atom_implies(sa, za, pt_range) -> bool:
    """For every dR and every pT in range: dR (sa) ⇒ dR (za)."""
    (ops, ths), (opz, thz) = sa, za
    lo_pt, hi_pt = pt_range
    if ths[2] == 0 and thz[2] == 0:
        umin, umax = 0.0, 0.0             # constants: pT irrelevant
    else:
        if lo_pt is None or lo_pt <= 0:
            return False
        umin = 0.0 if hi_pt in (None, INF) else 1.0 / hi_pt
        umax = 1.0 / lo_pt
    if ops in (">", ">=") and opz in (">", ">="):
        return _th_ge(ths, thz, umin, umax, strict=(ops == ">=" and opz == ">"))
    if ops in ("<", "<=") and opz in ("<", "<="):
        return _th_ge(thz, ths, umin, umax, strict=(ops == "<=" and opz == "<"))
    return False


# ── parsing raw ADL conditions ──────────────────────────────────────────────

def _num(n) -> Optional[float]:
    if isinstance(n, dict) and n.get("tok") in ("REAL", "INT") and "value" in n:
        return float(n["value"])
    if (isinstance(n, dict) and n.get("tok") == "EXPROP" and n.get("op") == "-"
            and n.get("lhs") is None):
        v = _num(n.get("rhs"))
        return -v if v is not None else None
    return None


def _plain_id(n) -> Optional[str]:
    if (isinstance(n, dict) and n.get("tok") == "ID" and not n.get("accessor")
            and not n.get("alias") and not n.get("dotop")):
        return n["id"]
    return None


def _elem_chain(n, E) -> Optional[str]:
    """``f(g(element))`` -> "f.g", else None."""
    chain = []
    while isinstance(n, dict) and n.get("tok") == "FUNCTION" and len(n.get("params") or []) == 1:
        chain.append(n["id"].lower())
        n = n["params"][0]
    if chain and _plain_id(n) in E and chain[0] not in ("size", "allof", "anyof"):
        return ".".join(chain)
    return None


def _threshold(n, E) -> Optional[Tuple[float, float, float]]:
    """A number d, ``a + b/pT(element)`` or ``min(c, that)`` -> (c, a, b)."""
    v = _num(n)
    if v is not None:
        return (v, v, 0.0)
    if not isinstance(n, dict):
        return None
    if n.get("tok") == "FUNCTION" and n.get("id", "").lower() == "min" and len(n.get("params") or []) == 2:
        p, q = n["params"]
        for c_node, e_node in ((p, q), (q, p)):
            c = _num(c_node)
            inner = _threshold(e_node, E)
            if c is not None and inner is not None:
                return (min(c, inner[0]), inner[1], inner[2])
        return None
    if n.get("tok") == "EXPROP" and n.get("op") == "+":
        for x, y in ((n.get("lhs"), n.get("rhs")), (n.get("rhs"), n.get("lhs"))):
            a = _num(x)
            if a is None:
                continue
            if (isinstance(y, dict) and y.get("tok") == "FACTOROP" and y.get("op") == "/"
                    and _num(y.get("lhs")) is not None
                    and _elem_chain(y.get("rhs"), E) == "pt"):
                return (INF, a, _num(y["lhs"]))
    return None


def _allof_lhs(n, E) -> Optional[str]:
    """``dR(element, allof(Y))`` (either argument order) -> "y"."""
    if not (isinstance(n, dict) and n.get("tok") == "FUNCTION"
            and n.get("id", "").lower() == "dr" and len(n.get("params") or []) == 2):
        return None
    p, q = n["params"]
    for x, y in ((p, q), (q, p)):
        if (_plain_id(y) in E and isinstance(x, dict) and x.get("tok") == "FUNCTION"
                and x.get("id", "").lower() == "allof" and len(x.get("params") or []) == 1):
            yn = _plain_id(x["params"][0])
            if yn is not None:
                return yn
    return None


def _canon(n, E):
    if isinstance(n, dict):
        if n.get("tok") == "ID" and n.get("id", "") in E:
            n = dict(n, id="THIS")
        return {k: _canon(v, E) for k, v in n.items()}
    if isinstance(n, list):
        return [_canon(v, E) for v in n]
    return n


def _refs(n, out: Set[str]):
    if isinstance(n, dict):
        if n.get("tok") == "ID":
            out.add(n.get("id", ""))
        for v in n.values():
            _refs(v, out)
    elif isinstance(n, list):
        for v in n:
            _refs(v, out)


class _Cut(tuple):
    """('iv', axis, intervals) | ('allof', y, atoms) | ('opaque', text)."""


def _cmp_cut(n, neg, E):
    op = n.get("op")
    lhs, rhs = n.get("lhs"), n.get("rhs")
    if op not in _NEG:
        return None
    if neg:
        op = _NEG[op]
    for l, r, o in ((lhs, rhs, op), (rhs, lhs, _SWAP[op])):
        v = _num(r)
        ax = _elem_chain(l, E)
        if v is not None and ax is not None:
            return _Cut(("iv", ax, _iv_from(o, v)))
        y = _allof_lhs(l, E)
        if y is not None and o in ("<", "<=", ">", ">="):
            th = _threshold(r, E)
            if th is not None and not neg:
                return _Cut(("allof", y, ((o, th),)))
    return None


def _parse(n, neg, E) -> List[_Cut]:
    """Conjunction of cuts equivalent to (or, for 'opaque', standing for)
    the condition ``n`` (negated if ``neg``)."""
    opaque = [_Cut(("opaque", ("NOT " if neg else "") + json.dumps(_canon(n, E), sort_keys=True)))]
    if not isinstance(n, dict):
        return opaque
    tok = n.get("tok")
    if tok == "LOGICOP" and n.get("op", "").lower() in ("and", "or"):
        is_and = (n["op"].lower() == "and") ^ neg
        if is_and:
            return _parse(n.get("lhs"), neg, E) + _parse(n.get("rhs"), neg, E)
        kids = [_parse(n.get("lhs"), neg, E), _parse(n.get("rhs"), neg, E)]
        if all(len(k) == 1 for k in kids):
            a, b = kids[0][0], kids[1][0]
            if a[0] == b[0] == "iv" and a[1] == b[1]:
                return [_Cut(("iv", a[1], _iv_or(a[2], b[2])))]
            if a[0] == b[0] == "allof" and a[1] == b[1]:
                return [_Cut(("allof", a[1], a[2] + b[2]))]
        return opaque
    if tok == "LOGICOP" and n.get("op", "").lower() == "not":
        return _parse(n.get("rhs") or n.get("lhs"), not neg, E)
    if tok == "COMPAREOP":
        c = _cmp_cut(n, neg, E)
        return [c] if c is not None else opaque
    return opaque


# ── the prover ──────────────────────────────────────────────────────────────

Branch = Tuple[str, FrozenSet[str], Tuple[_Cut, ...]]   # (root, object path, cuts)


class ObjectProver:
    def __init__(self, *irs):
        self.objs: Dict[str, object] = {}
        bad: Set[str] = set()
        defs: Dict[str, str] = {}
        for ir in irs:
            for o in ir.objects.values():
                k = o.name
                d = json.dumps([list(o.takes),
                                [(rc.command, rc.raw_expr) for rc in o.own_cuts]],
                               sort_keys=True)
                if k in defs and defs[k] != d:
                    bad.add(k)
                defs.setdefault(k, d)
                self.objs.setdefault(k, o)
        # anything referring to an ambiguous name is ambiguous too
        refs: Dict[str, Set[str]] = {}
        for k, o in self.objs.items():
            r = set(o.takes)
            for rc in o.own_cuts:
                _refs(rc.raw_expr, r)
            refs[k] = r
        changed = True
        while changed:
            changed = False
            for k, r in refs.items():
                if k not in bad and r & bad:
                    bad.add(k)
                    changed = True
        self.bad = bad
        self.lower: Dict[str, Optional[str]] = {}
        for k in self.objs:
            self.lower[k.lower()] = None if k.lower() in self.lower else k
        self._br: Dict[str, Optional[List[Branch]]] = {}
        self._sub: Dict[Tuple[str, str], bool] = {}

    # branches of a named object or built-in collection
    def branches(self, name: str, _stack=()) -> Optional[List[Branch]]:
        k = name
        if k in self._br:
            return self._br[k]
        if k in self.bad or k in _stack or len(_stack) > 30:
            return None
        o = self.objs.get(k)
        if o is None:
            # built-in collection
            res = [(name.upper(), frozenset(), ())]
            self._br[k] = res
            return res
        if not o.takes:
            self._br[k] = None
            return None
        E = {k, "this", "THIS"} | set(o.takes)
        own: List[_Cut] = []
        for rc in o.own_cuts:
            if rc.command not in ("SELECT", "REJECT") or rc.raw_expr is None:
                self._br[k] = None
                return None
            own += _parse(rc.raw_expr, rc.command == "REJECT", E)
        out: List[Branch] = []
        for t in o.takes:
            sub = self.branches(t, _stack + (k,))
            if sub is None:
                self._br[k] = None
                return None
            for root, path, cuts in sub:
                out.append((root, path | {k.lower()}, cuts + tuple(own)))
        self._br[k] = out
        return out

    def subset(self, x: str, z: str, _stack=()) -> bool:
        """Every element of collection x is an element of collection z."""
        key = (x, z)
        if key[0] == key[1] and key[0] not in self.bad:
            return True
        if key in self._sub:
            return self._sub[key]
        if key in _stack or len(_stack) > 30:
            return False
        bx, bz = self.branches(x), self.branches(z)
        ok = (bx is not None and bz is not None and
              all(any(rx == rz and self.branch_implies(cx, cz, _stack + (key,))
                      for rz, _pz, cz in bz)
                  for rx, _px, cx in bx))
        self._sub[key] = ok
        return ok

    def branch_implies(self, cx, cz, _stack=()) -> bool:
        """Every element passing all cuts cx passes all cuts cz."""
        ivs: Dict[str, tuple] = {}
        for c in cx:
            if c[0] == "iv":
                ivs[c[1]] = _iv_and(ivs.get(c[1], _ALL), c[2])
        h = _iv_hull(ivs.get("pt", _ALL))
        pt_range = (None, None) if h is None else h
        if any(not v for v in ivs.values()):
            return True                                   # empty branch
        opaque_x = [c[1] for c in cx if c[0] == "opaque"]
        for c in cz:
            if c[0] == "iv":
                if not _iv_subset(ivs.get(c[1], _ALL), c[2]):
                    return False
            elif c[0] == "allof":
                if not any(d[0] == "allof"
                           and self.subset(c[1], d[1], _stack)
                           and all(any(_atom_implies(sa, za, pt_range) for za in c[2])
                                   for sa in d[2])
                           for d in cx):
                    return False
            else:
                if c[1] not in opaque_x:
                    return False
        return True

    # helpers for the multiplicity rule, which works on dependency-tree branches
    def branch_by_path(self, root: str, names: FrozenSet[str]) -> Optional[Branch]:
        """The branch whose built-in root is ``root`` and whose objects are
        the (lowercased) ``names`` of a dependency-tree branch. Names that
        are also built-in collections (``ELE`` vs an object ``ele``) may be
        on the dependency path without being objects of the branch."""
        objs = {n for n in names if n in self.lower}
        if any(self.lower[n] is None for n in objs):
            return None
        for top in sorted(objs):
            for b in self.branches(self.lower[top]) or []:
                if (_canonical_root(b[0]) == root and b[1] <= names
                        and all(n in {b[0].lower(), root.lower()}
                                for n in objs - b[1])):
                    return b
        return None


def _canonical_root(r: str) -> str:
    try:
        from ir_extractor import canonicalise
        return canonicalise(r)
    except Exception:
        return r.upper()
