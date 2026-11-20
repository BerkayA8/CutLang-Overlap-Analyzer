"""
formal_adl.py
=============
Front end for ADL files written in the formal syntax of learn-adl
(https://github.com/ADL4HEP/learn-adl, adl_syntax_summary.md).

It parses a formal ADL file and lowers it to the same JSON AST the C++
CutLang parser (adl_to_json) produces, so the rest of the overlap pipeline
(ir_extractor, overlap_checker, object_containment) runs unchanged.

What is lowered exactly
-----------------------
- object blocks: ``take X`` / ``take union(a, b)`` (several TAKE statements) /
  ``take sort(X, key, dir)`` (the order does not change the set: ``take X``);
  plain attribute names (``pt``, ``eta``, flags) become ``attr(<take>)``,
  ``this`` becomes the take name, as in CutLang files.
- ``reject C`` becomes ``select not C`` with the negation pushed to the leaves.
  ``any(dR(this, Y) < r)`` under a negation becomes ``dR(this, allof(Y)) >= r``
  (the CutLang form of overlap removal); a pT-dependent radius written as
  ``(a + b - abs(c - d)) / 2`` becomes ``min(...)``.
- ``[]`` / ``][`` range checks become two comparisons.
- input collections are mapped to CutLang built-ins (electrons -> ELE, ...);
  ``pt(MET)`` -> ``MET``.
- regions: ``take R`` (region inheritance) -> ``select R``; global defines.
- boolean defines compared with 1 / 0 are inlined.

Everything else (composites and anything that refers to them, RestFrames,
mT2, BDT/ONNX scores and the other ADL-PROPOSAL functions, slices,
cross-object identity tests, ...) is replaced by an opaque attribute whose
name is unique to this file and to the text of the expression. The overlap
analyzer can compare an opaque cut only with the identical cut of the same
file, so nothing is ever proven from it: verdicts stay sound, they only
become weaker.
"""
from __future__ import annotations

import hashlib
import re
from typing import Dict, List, Optional, Set, Tuple

# ── lexer ────────────────────────────────────────────────────────────────────

_TOK = re.compile(r"""
    (?P<ws>[ \t]+)
  | (?P<num>(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?)
  | (?P<str>"[^"]*")
  | (?P<range>\[\]|\]\[)
  | (?P<op>==|!=|<=|>=|<|>|\+|-|\*|/|\^|\(|\)|\[|\]|,|:|\.|=)
  | (?P<id>[A-Za-z_][A-Za-z0-9_]*)
""", re.X)


class ParseError(Exception):
    pass


def _lex(text: str):
    out, i = [], 0
    while i < len(text):
        m = _TOK.match(text, i)
        if not m:
            raise ParseError(f"cannot read {text[i:i+20]!r}")
        i = m.end()
        k = m.lastgroup
        if k == "ws":
            continue
        out.append((k, m.group(k)))
    out.append(("end", ""))
    return out


# ── expression parser (Pratt) → generic tree ─────────────────────────────────
# tree nodes: ("num", v) ("id", name) ("str", s) ("call", name, [args])
# ("index", base, idx|None, lo, hi) ("dot", base, name) ("bin", op, a, b)
# ("neg", a) ("not", a) ("range", kind, x, lo, hi) ("named", expr, name)

class _P:
    def __init__(self, text):
        self.t = _lex(text)
        self.i = 0

    def peek(self, k=0):
        return self.t[self.i + k]

    def eat(self, val=None):
        tok = self.t[self.i]
        if val is not None and tok[1] != val:
            raise ParseError(f"expected {val!r}, got {tok[1]!r}")
        self.i += 1
        return tok

    def done(self):
        return self.peek()[0] == "end"

    def expr(self):
        return self.or_()

    def or_(self):
        a = self.and_()
        while self.peek() == ("id", "or"):
            self.eat()
            a = ("bin", "or", a, self.and_())
        return a

    def and_(self):
        a = self.not_()
        while self.peek() == ("id", "and"):
            self.eat()
            a = ("bin", "and", a, self.not_())
        return a

    def not_(self):
        if self.peek() == ("id", "not"):
            self.eat()
            return ("not", self.not_())
        return self.cmp()

    def cmp(self):
        a = self.add()
        k, v = self.peek()
        if k == "op" and v in ("==", "!=", "<", ">", "<=", ">="):
            self.eat()
            return ("bin", v, a, self.add())
        if k == "range":
            self.eat()
            lo = self.add()
            hi = self.add()
            return ("range", v, a, lo, hi)
        return a

    def add(self):
        a = self.mul()
        while self.peek() in (("op", "+"), ("op", "-")):
            op = self.eat()[1]
            a = ("bin", op, a, self.mul())
        return a

    def mul(self):
        a = self.unary()
        while self.peek() in (("op", "*"), ("op", "/")):
            op = self.eat()[1]
            a = ("bin", op, a, self.unary())
        return a

    def unary(self):
        if self.peek() == ("op", "-"):
            self.eat()
            return ("neg", self.unary())
        return self.pow()

    def pow(self):
        a = self.postfix()
        if self.peek() == ("op", "^"):
            self.eat()
            return ("bin", "^", a, self.unary())
        return a

    def postfix(self):
        a = self.primary()
        while True:
            k, v = self.peek()
            if (k, v) == ("op", "("):
                if a[0] != "id":
                    raise ParseError("call of a non-name")
                self.eat()
                args = []
                if self.peek() != ("op", ")"):
                    args.append(self.arg())
                    while self.peek() == ("op", ","):
                        self.eat()
                        args.append(self.arg())
                self.eat(")")
                a = ("call", a[1], args)
            elif (k, v) == ("op", "["):
                self.eat()
                lo = hi = idx = None
                if self.peek() == ("op", ":"):
                    self.eat()
                    lo = ("num", 0.0)
                    hi = None if self.peek() == ("op", "]") else self.add()
                else:
                    first = self.add()
                    if self.peek() == ("op", ":"):
                        self.eat()
                        lo = first
                        hi = None if self.peek() == ("op", "]") else self.add()
                    else:
                        idx = first
                self.eat("]")
                a = ("index", a, idx, lo, hi)
            elif (k, v) == ("op", "."):
                self.eat()
                a = ("dot", a, self.eat()[1])
            else:
                return a

    def arg(self):
        e = self.expr()
        if self.peek()[0] == "id" and self.peek()[1] not in ("and", "or", "not"):
            return ("named", e, self.eat()[1])          # cartesian(x a, ...)
        return e

    def primary(self):
        k, v = self.eat()
        if k == "num":
            return ("num", float(v))
        if k == "str":
            return ("str", v)
        if k == "id":
            return ("id", v)
        if (k, v) == ("op", "("):
            e = self.expr()
            self.eat(")")
            return e
        raise ParseError(f"unexpected {v!r}")


def parse_expr(text: str):
    p = _P(text)
    e = p.expr()
    if not p.done():
        raise ParseError(f"trailing text at {p.peek()[1]!r}")
    return e


# ── block reader ─────────────────────────────────────────────────────────────

_BLOCK = ("info", "object", "composite", "region", "table", "histo", "histolist")


def read_blocks(text: str):
    """[(kind, name, [(keyword, rest, lineno)])] and global defines as
    ("define", name, [("=", body, lineno)])."""
    blocks = []
    cur = None
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indented = raw[:1] in (" ", "\t")
        words = line.strip().split(None, 1)
        kw = words[0]
        rest = words[1] if len(words) > 1 else ""
        if not indented and kw in _BLOCK:
            cur = (kw, rest.strip(), [])
            blocks.append(cur)
            continue
        if not indented and kw == "define":
            name, _, body = rest.partition("=")
            blocks.append(("define", name.strip(), [("=", body.strip(), n)]))
            cur = None
            continue
        if cur is None:
            raise ParseError(f"line {n}: statement outside a block: {line.strip()!r}")
        cur[2].append((kw, rest, n))
    return blocks


# ── lowering to the adl_to_json schema ───────────────────────────────────────

INPUTS = {"electrons": "ELE", "muons": "MUO", "taus": "TAU", "photons": "PHO",
          "jets": "JET", "fatjets": "FJET", "truthParticles": "TRUTH",
          # no CutLang counterpart: distinct roots that match nothing else
          "trackjets": "AK8JET_TRACKJETS", "bhadrons": "TAPPIONTRACKS"}
SINGLE_INPUTS = {"MET"}
# attribute functions whose argument is a collection or an indexed object
ATTRS_OK = {"pt", "eta", "phi", "mass", "e", "charge", "pdgid", "m"}
SAFE_FUNCS = {"size", "abs", "sqrt", "cos", "sin", "tan", "log",
              "dr", "dphi", "deta", "sum", "min", "max"}
_NEG = {">=": "<", "<=": ">", ">": "<=", "<": ">=", "==": "!=", "!=": "=="}


def _ID(name, acc=None):
    return {"tok": "ID", "id": name, "alias": "", "dotop": "",
            "accessor": acc or [], "type": ""}


def _NUM(v):
    return {"tok": "REAL" if v != int(v) else "INT", "value": float(v)}


def _CMP(op, a, b):
    return {"tok": "COMPAREOP", "op": op, "lhs": a, "rhs": b}


def _LOG(op, a, b):
    return {"tok": "LOGICOP", "op": op, "lhs": a, "rhs": b}


def _FN(name, params):
    # adl_to_json emits parameters in reverse order; mimic it
    return {"tok": "FUNCTION", "id": name, "params": list(reversed(params))}


class Opaque(Exception):
    pass


class Lowerer:
    def __init__(self, text: str, label: str):
        self.blocks = read_blocks(text)
        self.fid = hashlib.sha1(text.encode()).hexdigest()[:8]
        self.objects: Dict[str, str] = {}       # object name -> take name used for attributes
        self.composites: Set[str] = set()
        self.regions: Set[str] = set()
        self.defines: Dict[str, object] = {}    # name -> parsed body
        self.bool_defines: Set[str] = set()
        self.opaque_count = 0
        self.notes: List[str] = []
        self.local_defines: Set[str] = set()   # per-instance defines of the current object
        self._inlining: Set[str] = set()
        self.comp_info: Dict[str, Optional[dict]] = {}
        for kind, name, stmts in self.blocks:
            if kind == "object":
                # object names are made unique per file: the analyzer matches
                # variables of two analyses by object name, and two files may
                # use the same name (baseLep, sigJet, ...) for different objects
                self.objects[name] = f"o{self.fid}_{name}"
            elif kind == "composite":
                self.composites.add(name)
                self.comp_info[name] = self._read_composite(stmts)
            elif kind == "region":
                self.regions.add(name)
            elif kind == "define":
                try:
                    self.defines[name] = parse_expr(stmts[0][1])
                except ParseError:
                    self.defines[name] = None
        for name, body in self.defines.items():
            if body is not None and body[0] in ("bin", "range", "not") and (
                    body[0] != "bin" or body[1] in ("==", "!=", "<", ">", "<=", ">=", "and", "or")):
                self.bool_defines.add(name)

    # opaque attribute / variable unique to this file and expression text
    def opaque(self, tree, elem=None):
        self.opaque_count += 1
        h = hashlib.sha1((self.fid + repr(tree)).encode()).hexdigest()[:10]
        name = f"opq_{self.fid}_{h}"
        return _FN(name, [_ID(elem)]) if elem else _ID(name)

    # ---- numeric / value expressions ----
    def value(self, t, elem=None):
        k = t[0]
        if k == "num":
            return _NUM(t[1])
        if k == "neg":
            inner = t[1]
            if inner[0] == "num":
                return _NUM(-inner[1])
            return {"tok": "EXPROP", "op": "-", "lhs": _NUM(0), "rhs": self.value(inner, elem)}
        if k == "bin" and t[1] in ("+", "-"):
            return {"tok": "EXPROP", "op": t[1], "lhs": self.value(t[2], elem), "rhs": self.value(t[3], elem)}
        if k == "bin" and t[1] in ("*", "/"):
            return {"tok": "FACTOROP", "op": t[1], "lhs": self.value(t[2], elem), "rhs": self.value(t[3], elem)}
        if k == "bin" and t[1] == "^":
            raise Opaque()
        if k == "id":
            n = t[1]
            if elem and n == "this":
                return _ID(elem)
            if n in SINGLE_INPUTS:
                return _ID(n)
            if n in self.objects:
                return _ID(self.objects[n])
            if n in self.defines:
                # inlined, so that two analyses' defines are compared by their
                # bodies, never by their names
                if n in self.bool_defines or self.defines[n] is None or n in self._inlining:
                    raise Opaque()
                self._inlining.add(n)
                try:
                    return self.value(self.defines[n])
                finally:
                    self._inlining.discard(n)
            if n in self.composites or n in self.regions:
                raise Opaque()
            if elem and n in self.local_defines:
                raise Opaque()             # per-instance define: its body is not lowered
            if elem:                       # attribute of the current instance
                return _FN(n, [_ID(elem)])
            raise Opaque()                 # event-level input or unknown name
        if k == "index":
            base, idx, lo, hi = t[1], t[2], t[3], t[4]
            if idx is not None and base[0] == "id" and base[1] in self.objects and idx[0] == "num":
                return _ID(self.objects[base[1]], [int(idx[1])])
            raise Opaque()                 # slices and other indexing
        if k == "call":
            name, args = t[1], t[2]
            ln = name.lower()
            if ln in ATTRS_OK and len(args) == 1:
                a = args[0]
                if a[0] == "id" and a[1] == "MET" and ln == "pt":
                    return _ID("MET")
                if a[0] == "id" and a[1] == "this" and elem:
                    return _FN(name, [_ID(elem)])
                if a[0] == "bin" and a[1] == "+":
                    return _FN(name, [self.lvsum(a, elem)])
                return _FN(name, [self.collection(a, elem)])
            if ln in SAFE_FUNCS:
                if ln == "size":
                    return _FN(name, [self.collection(args[0], elem, allow_slice=False)])
                if ln in ("min", "max", "sum") and len(args) != 1:
                    raise Opaque()
                if ln in ("dr", "dphi", "deta"):
                    return _FN(name, [self.lvsum(a, elem) if a[0] == "bin" and a[1] == "+"
                                      else self.collection(a, elem) for a in args])
                return _FN(name, [self.value(a, elem) for a in args])
            raise Opaque()                 # proposals, any/all as values, composite members
        raise Opaque()


    # ---- 4-vector sums: attribute of (a + b) ----
    def lvsum(self, t, elem=None):
        items = []

        def walk(x):
            if x[0] == "bin" and x[1] == "+":
                walk(x[2]); walk(x[3])
            else:
                items.append(self.collection(x, elem))
        walk(t)
        return _FN("lvsum", items)

    # ---- composites over one-element slices (at most one candidate) ----
    def _read_composite(self, stmts):
        info = {"binds": {}, "guards": [], "conds": [], "objs": {}, "defs": {}}
        try:
            for kw, rest, n in stmts:
                if kw == "take":
                    t = parse_expr(rest)
                    if not (t[0] == "call" and t[1] in ("cartesian", "disjoint")):
                        return None
                    for a in t[2]:
                        if a[0] != "named":
                            return None
                        e, name = a[1], a[2]
                        if not (e[0] == "index" and e[1][0] == "id" and e[2] is None):
                            return None
                        lo = e[3][1] if e[3] is not None and e[3][0] == "num" else None
                        hi = e[4][1] if e[4] is not None and e[4][0] == "num" else None
                        if lo is None or hi is None or hi - lo != 1:
                            return None        # several candidates: not modelled
                        coll = e[1]
                        info["binds"][name] = ("index", coll, ("num", lo), None, None)
                        info["guards"].append(("bin", ">=", ("call", "size", [coll]), ("num", lo + 1)))
                    if t[1] == "disjoint" and len({b[1][1] for b in info["binds"].values()}) < len(info["binds"]):
                        pass                   # distinct slices of one collection are distinct instances
                elif kw == "select":
                    info["conds"].append(parse_expr(rest))
                elif kw == "reject":
                    info["conds"].append(("not", parse_expr(rest)))
                elif kw == "object":
                    name, _, body = rest.partition("=")
                    info["objs"][name.strip()] = parse_expr(body.strip())
                elif kw == "define":
                    name, _, body = rest.partition("=")
                    info["defs"][name.strip()] = parse_expr(body.strip())
                else:
                    return None
        except ParseError:
            return None
        return info

    def _subst(self, t, info, depth=0):
        if depth > 50:
            raise Opaque()
        if not isinstance(t, tuple):
            return t
        if t[0] == "id":
            n = t[1]
            if n in info["binds"]:
                return info["binds"][n]
            if n in info["objs"]:
                return self._subst(info["objs"][n], info, depth + 1)
            if n in info["defs"]:
                return self._subst(info["defs"][n], info, depth + 1)
            return t
        if t[0] == "dot":
            return ("call", t[2], [self._subst(t[1], info, depth + 1)])
        out = []
        for x in t:
            if isinstance(x, tuple):
                out.append(self._subst(x, info, depth + 1))
            elif isinstance(x, list):
                out.append([self._subst(y, info, depth + 1) for y in x])
            else:
                out.append(x)
        return tuple(out)

    def _comp_cond(self, info):
        terms = info["guards"] + [self._subst(c, info) for c in info["conds"]]
        cond = terms[0]
        for x in terms[1:]:
            cond = ("bin", "and", cond, x)
        return cond

    def _refs_composite(self, t, found):
        if isinstance(t, tuple):
            if t[0] == "id" and t[1] in self.composites:
                found.add(t[1])
            for x in t[1:]:
                if isinstance(x, (tuple, list)):
                    self._refs_composite(x, found)
        elif isinstance(t, list):
            for x in t:
                self._refs_composite(x, found)
        return found

    def _replace_comp_calls(self, t, comp, info):
        """f(C) -> f's body with the bindings substituted."""
        if isinstance(t, list):
            return [self._replace_comp_calls(x, comp, info) for x in t]
        if not isinstance(t, tuple):
            return t
        if t[0] == "call" and len(t[2]) == 1 and t[2][0] == ("id", comp):
            f = t[1]
            if f in info["defs"]:
                return self._subst(info["defs"][f], info)
            if f in info["objs"]:
                return self._subst(info["objs"][f], info)
            raise Opaque()
        if t[0] == "id" and t[1] == comp:
            raise Opaque()
        return tuple(self._replace_comp_calls(x, comp, info) if isinstance(x, (tuple, list)) else x for x in t)

    def expand(self, t):
        """Rewrite region-level references to single-candidate composites."""
        if not isinstance(t, tuple):
            return t
        if t[0] in ("not",):
            return ("not", self.expand(t[1]))
        if t[0] == "bin" and t[1] in ("and", "or"):
            return ("bin", t[1], self.expand(t[2]), self.expand(t[3]))
        comps = self._refs_composite(t, set())
        if not comps:
            return t
        for c in comps:
            if self.comp_info.get(c) is None:
                raise Opaque()
        # size(C) op k with at most one candidate
        if t[0] == "bin" and t[1] in _NEG and t[2][0] == "call" and t[2][1] == "size" \
                and len(t[2][2]) == 1 and t[2][2][0][0] == "id" and t[2][2][0][1] in comps and t[3][0] == "num":
            info = self.comp_info[t[2][2][0][1]]
            op, k = t[1], t[3][1]
            nonempty = {(">=", 1), (">", 0), ("==", 1), ("!=", 0)}
            empty = {("==", 0), ("<", 1), ("<=", 0), ("!=", 1)}
            if (op, k) in nonempty:
                return self._comp_cond(info)
            if (op, k) in empty:
                return ("not", self._comp_cond(info))
            raise Opaque()
        # any(P) with P using f(C): candidate exists and P holds for it
        if t[0] == "call" and t[1] == "any" and len(t[2]) == 1:
            p = t[2][0]
            cond = None
            for c in sorted(comps):
                info = self.comp_info[c]
                p = self._replace_comp_calls(p, c, info)
                cc = self._comp_cond(info)
                cond = cc if cond is None else ("bin", "and", cond, cc)
            return ("bin", "and", cond, p)
        raise Opaque()

    def collection(self, t, elem=None, allow_slice=False):
        if t[0] == "id":
            if t[1] == "this" and elem:
                return _ID(elem)
            if t[1] in self.objects:
                return _ID(self.objects[t[1]])
            if t[1] in SINGLE_INPUTS:
                return _ID(t[1])
            if t[1] in INPUTS:
                return _ID(INPUTS[t[1]])
        if t[0] == "index" and t[2] is not None and t[1][0] == "id" and t[1][1] in self.objects \
                and t[2][0] == "num":
            return _ID(self.objects[t[1][1]], [int(t[2][1])])
        if t[0] == "call" and t[1].lower() in ATTRS_OK:
            return self.value(t, elem)
        raise Opaque()

    # ---- boolean expressions, negation pushed to the leaves ----
    def boolean(self, t, neg=False, elem=None):
        try:
            if elem is None:
                t = self.expand(t)
            return self._boolean(t, neg, elem)
        except Opaque:
            leaf = _CMP("==" if not neg else "!=", self.opaque(t, elem), _NUM(1))
            return leaf

    def _boolean(self, t, neg, elem):
        k = t[0]
        if k == "not":
            return self._boolean(t[1], not neg, elem)
        if k == "bin" and t[1] in ("and", "or"):
            op = t[1]
            if neg:
                op = "or" if op == "and" else "and"
            return _LOG(op, self.boolean(t[2], neg, elem), self.boolean(t[3], neg, elem))
        if k == "range":
            x, lo, hi = t[2], t[3], t[4]
            if t[1] == "[]":
                tree = ("bin", "and", ("bin", ">=", x, lo), ("bin", "<=", x, hi))
            else:
                tree = ("bin", "and", ("bin", ">", x, lo), ("bin", "<", x, hi))
            return self._boolean(tree, neg, elem)
        if k == "bin" and t[1] in _NEG:
            op, a, b = t[1], t[2], t[3]
            # a boolean expression compared with 1 / 0 (e.g. a composite flag)
            def _is_bool(e):
                return (e[0] == "not" or e[0] == "range"
                        or (e[0] == "bin" and e[1] in ("and", "or", "==", "!=", "<", ">", "<=", ">=")))
            for x, y in ((a, b), (b, a)):
                if _is_bool(x) and y[0] == "num" and y[1] in (0.0, 1.0) and op in ("==", "!="):
                    truth = (y[1] == 1) == (op == "==")
                    return self._boolean(x, neg ^ (not truth), elem)
            # boolean define compared with 1 / 0
            for x, y in ((a, b), (b, a)):
                if x[0] == "id" and x[1] in self.bool_defines and y[0] == "num" and op in ("==", "!="):
                    truth = (y[1] == 1) == (op == "==")
                    return self._boolean(self.defines[x[1]], neg ^ (not truth), elem)
            # overlap removal: any(dR(this, Y) op r) only under a negation
            if neg and elem is None:
                pass
            if neg:
                op = _NEG[op]
            return _CMP(op, self.value(a, elem), self.value(b, elem))
        if k == "call" and t[1] == "any" and len(t[2]) == 1 and elem:
            inner = t[2][0]
            if neg and inner[0] == "bin" and inner[1] in ("<", "<=", ">", ">="):
                lowered = self._allof(inner, elem)
                if lowered is not None:
                    return lowered
            raise Opaque()
        if k == "call" and t[1] == "all" and len(t[2]) == 1 and elem:
            inner = t[2][0]
            if not neg and inner[0] == "bin" and inner[1] in ("<", "<=", ">", ">="):
                lowered = self._allof(("bin", _NEG[inner[1]], inner[2], inner[3]), elem)
                if lowered is not None:
                    return lowered
            raise Opaque()
        raise Opaque()

    def _allof(self, cmp, elem):
        """not any(dR(this, Y) op r)  ->  dR(this, allof(Y)) negop r"""
        op, a, b = cmp[1], cmp[2], cmp[3]
        if not (a[0] == "call" and a[1] == "dR" and len(a[2]) == 2):
            return None
        p, q = a[2]
        if p == ("id", "this") and q[0] == "id" and q[1] in self.objects:
            other = q[1]
        elif q == ("id", "this") and p[0] == "id" and p[1] in self.objects:
            other = p[1]
        else:
            return None
        radius = self.radius(b, elem)
        dr = _FN("dR", [_ID(elem), _FN("allof", [_ID(self.objects[other])])])
        return _CMP(_NEG[op], dr, radius)

    def radius(self, t, elem):
        """(a + b - abs(c - d)) / 2 = min(a+b-..)  ->  min(c0, a0 + k/pt)"""
        m = self._as_min(t)
        if m is not None:
            return m(elem)
        return self.value(t, elem)

    def _as_min(self, t):
        # ( X - abs(Y) ) / 2 with X = A + B, Y = A - B (up to constants): min(A, B)
        if not (t[0] == "bin" and t[1] == "/" and t[3] == ("num", 2.0)):
            return None
        s = t[2]
        if not (s[0] == "bin" and s[1] == "-" and s[3][0] == "call" and s[3][1] == "abs"):
            return None
        X, Y = s[2], s[3][2][0]
        # X = K1 + k/pt, Y = K2 - k/pt  ->  min(c, a + k/pt) with c = (K1+K2)/2, a = (K1-K2)/2
        def split(e):
            if e[0] == "bin" and e[1] in ("+", "-") and e[2][0] == "num":
                return e[2][1], e[1], e[3]
            return None
        sx, sy = split(X), split(Y)
        if not (sx and sy and sx[1] == "+" and sy[1] == "-" and sx[2] == sy[2]):
            return None
        K1, K2, term = sx[0], sy[0], sx[2]
        c, a = (K1 + K2) / 2, (K1 - K2) / 2
        if not (term[0] == "bin" and term[1] == "/" and term[2][0] == "num" and term[3] == ("id", "pt")):
            return None
        k = term[2][1]

        def build(elem):
            inner = {"tok": "EXPROP", "op": "+", "lhs": _NUM(a),
                     "rhs": {"tok": "FACTOROP", "op": "/", "lhs": _NUM(k),
                             "rhs": _FN("pt", [_ID(elem)])}}
            return _FN("min", [_NUM(c), inner])
        return build

    # ---- blocks ----
    def lower(self) -> List[dict]:
        out = []
        for kind, name, stmts in self.blocks:
            if kind == "object":
                out.append(self.object(name, stmts))
            elif kind == "region":
                out.append(self.region(name, stmts))
            # global defines are inlined where they are used
        return out

    def object(self, name, stmts):
        self.local_defines = {r.partition("=")[0].strip() for kw, r, n in stmts if kw == "define"}
        takes, sel, elem = [], [], None
        for kw, rest, n in stmts:
            if kw != "take":
                continue
            t = parse_expr(rest)
            while t[0] == "call" and t[1] == "sort":
                t = t[2][0]
            if t[0] == "call" and t[1] == "union":
                parts = t[2]
            else:
                parts = [t]
            for p in parts:
                while p[0] == "call" and p[1] == "sort":
                    p = p[2][0]
                if p[0] == "id" and p[1] in self.objects:
                    takes.append(self.objects[p[1]])
                elif p[0] == "id" and p[1] in INPUTS:
                    takes.append(INPUTS[p[1]])
                elif p[0] == "index" and p[1][0] == "id" and p[1][1] in self.objects:
                    # a slice is a subset of the collection: take it, plus an opaque cut
                    takes.append(self.objects[p[1][1]])
                    sel.append(("opaque-subset", p))
                else:
                    # recluster(), muonCorrection(), ...: a new collection, related to
                    # nothing else in any analysis
                    takes.append(f"OPQROOT_{self.fid}_{name}")
        elem = takes[0] if len(takes) == 1 else self.objects[name]
        statements = [{"tok": "TAKE", "condition": _ID(t)} for t in takes]
        for item in sel:
            statements.append({"tok": "SELECT", "condition":
                               _CMP("==", self.opaque(item[1], elem), _NUM(1))})
        for kw, rest, n in stmts:
            if kw in ("select", "reject"):
                t = parse_expr(rest)
                statements.append({"tok": "SELECT", "condition": self.boolean(t, kw == "reject", elem)})
            elif kw == "define":
                pass                        # per-instance defines: their uses become opaque
            elif kw != "take":
                self.notes.append(f"object {name}: '{kw}' ignored")
        # per-instance defines referenced in cuts are unknown names -> attribute of elem!
        return {"tok": "OBJECT", "id": self.objects[name], "statements": statements}

    def region(self, name, stmts):
        # conditions already applied through inheritance are not repeated
        # (composite expansion would otherwise copy the candidate's cuts into
        # every region that refers to it, and the analyzer pairs identical
        # compound cuts one to one)
        import json as _json
        if not hasattr(self, "_region_conds"):
            self._region_conds = {}
        seen = set()
        for kw, rest, n in stmts:
            if kw == "take":
                seen |= self._region_conds.get(rest.strip(), set())
        statements = []
        for kw, rest, n in stmts:
            if kw == "take":
                statements.append({"tok": "SELECT", "condition": _ID(rest.strip())})
            elif kw in ("select", "reject"):
                t = parse_expr(rest)
                cond = self.boolean(t, kw == "reject")
                # a top-level conjunction is the same as one select per conjunct
                stack, parts = [cond], []
                while stack:
                    c = stack.pop()
                    if c.get("tok") == "LOGICOP" and c.get("op") == "and":
                        stack.append(c["rhs"]); stack.append(c["lhs"])
                    else:
                        parts.append(c)
                for c in parts:
                    key = _json.dumps(c, sort_keys=True)
                    if key in seen:
                        continue
                    seen.add(key)
                    statements.append({"tok": "SELECT", "condition": c})
            elif kw == "weight":
                pass
            else:
                self.notes.append(f"region {name}: '{kw}' ignored")
        self._region_conds[name] = seen
        return {"tok": "REGION", "id": name, "statements": statements}


def is_formal_adl(text: str) -> bool:
    body = "\n".join(l.split("#", 1)[0] for l in text.splitlines())
    return bool(re.search(r"^\s*take\s+(electrons|muons|jets|photons|taus|fatjets|union\(|sort\()", body, re.M)
                or re.search(r"^composite\s", body, re.M)
                or re.search(r"\bany\(|\ball\(", body))


def parse_formal_file(path: str) -> Tuple[List[dict], "Lowerer"]:
    text = open(path, encoding="utf-8").read()
    lw = Lowerer(text, path)
    return lw.lower(), lw
