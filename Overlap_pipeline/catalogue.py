"""
catalogue.py
============
Builds and renders the OverlapObject catalogue for an AnalysisIR.

An "overlap object" is any named entity whose dependency structure
can be compared between analyses:
  - ADL objects      (object jets, object bJets, …)
  - ADL defines      (define HT, define MHT, …)
  - Region cuts      (select MHT > 300, select size(jets) >= 2, …)

Each overlap object is represented with:
  - Its source kind and name
  - Its dependency tree (CutDependency)
  - Its struct_sig  (shape + func names + ops, no values)
  - Its full_dep_sig (shape + func names + ops + values)
  - Its own CutStructures
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from ir_extractor import (
    AnalysisIR, ObjectIR, RegionIR, ResolvedCutIR,
    CutStructure, CutDependency, DefineDependency,
    constraint_expr_leaves,
)


# ─────────────────────────────────────────────────────────────────────────────
# OverlapObject
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OverlapObject:
    """
    A single comparable entity extracted from an ADL analysis.

    kind        – "object" | "define" | "region_cut"
    name        – declared name (e.g. "jets", "HT", "select MHT > 300")
    region      – region name (for region_cut), empty otherwise
    node        – the CutDependency-family tree for this entity: an
                  ObjectDependency for "object" (``ObjectIR.chain`` is
                  already a CutDependency subclass since the class-
                  hierarchy refactor, so objects and defines/cuts share
                  a single representation here), a DefineDependency/
                  CutRootDependency subtree for "define"/"region_cut",
                  or None if it couldn't be found/built.
    """
    kind: str
    name: str
    region: str = ""
    node: Optional[CutDependency] = None

    @property
    def struct_sig(self) -> tuple:
        if self.node is not None:
            return self.node.struct_sig()
        return ()

    @property
    def full_dep_sig(self) -> tuple:
        if self.node is not None:
            return self.node.full_dep_sig()
        return ()

    @property
    def children_full_dep_sig(self) -> tuple:
        if self.node is not None:
            return self.node.children_full_dep_sig()
        return ()

    def display_label(self) -> str:
        if self.kind == "object":
            return f"[obj] {self.name}"
        if self.kind == "define":
            return f"[def] {self.name}"
        if self.kind == "region_cut":
            return f"[cut] {self.name}  (in {self.region})"
        return self.name

    def constraint_summary(self) -> str:
        if self.node is not None:
            leaves = [c for ce in self.node.own_constraint_exprs
                        for c in constraint_expr_leaves(ce)]
        else:
            leaves = []
        if not leaves:
            return "(no direct constraints)"
        return ",  ".join(
            f"{c.display_name()} {c.effective_op()} {c.threshold}"
            for c in leaves
        )


# ─────────────────────────────────────────────────────────────────────────────
# Catalogue builder
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AnalysisCatalogue:
    source_file: str
    objects: List[OverlapObject] = field(default_factory=list)
    defines: List[OverlapObject] = field(default_factory=list)
    region_cuts: List[OverlapObject] = field(default_factory=list)

    @property
    def all_overlap_objects(self) -> List[OverlapObject]:
        return self.objects + self.defines + self.region_cuts


def build_catalogue(ir: AnalysisIR) -> AnalysisCatalogue:
    cat = AnalysisCatalogue(source_file=ir.source_file)

    # ── Objects ───────────────────────────────────────────────────────────────
    for name, obj in ir.objects.items():
        oo = OverlapObject(
            kind="object",
            name=name,
            node=obj.chain,
        )
        cat.objects.append(oo)

    # ── Defines ───────────────────────────────────────────────────────────────
    for name in ir.defines_raw:
        # Find the region cut whose surface includes this define,
        # or build a synthetic tree from the first region cut that references it
        dep_tree = _find_define_tree(ir, name)
        oo = OverlapObject(
            kind="define",
            name=name,
            node=dep_tree,
        )
        cat.defines.append(oo)

    # ── Region cuts ───────────────────────────────────────────────────────────
    for rname, reg in ir.regions.items():
        for rc in reg.resolved_cuts:
            label = _expr_label(rc)
            oo = OverlapObject(
                kind="region_cut",
                name=label,
                region=rname,
                node=rc.dependency_tree,
            )
            cat.region_cuts.append(oo)

    return cat


def _find_define_tree(ir: AnalysisIR, define_name: str) -> Optional[CutDependency]:
    """
    Find the CutDependency subtree node for a define by searching region cuts.
    Returns the first DefineDependency child node with matching name.
    """
    def search(node: CutDependency, name: str) -> Optional[CutDependency]:
        if isinstance(node, DefineDependency) and node.name.lower() == name.lower():
            return node
        for ch in node.children:
            r = search(ch, name)
            if r:
                return r
        return None

    for reg in ir.regions.values():
        for rc in reg.resolved_cuts:
            if rc.dependency_tree:
                found = search(rc.dependency_tree, define_name)
                if found:
                    return found
    return None


def _expr_label(rc: ResolvedCutIR) -> str:
    """Human-readable label for a region cut."""
    if rc.dependency_tree:
        return rc.dependency_tree.name
    svars = ", ".join(sorted(rc.surface_vars))
    return f"{rc.command}({svars})"


# ─────────────────────────────────────────────────────────────────────────────
# Terminal rendering
# ─────────────────────────────────────────────────────────────────────────────

def render_catalogue_terminal(cat: AnalysisCatalogue) -> str:
    import os
    lines = []
    label = os.path.basename(cat.source_file)
    SEP = "─" * 70
    lines.append(f"\n\033[1m{'═'*70}\033[0m")
    lines.append(f"\033[1m  Overlap Object Catalogue: \033[96m{label}\033[0m")
    lines.append(f"{'═'*70}")

    for section, items, heading in [
        (cat.objects,     cat.objects,     "Objects"),
        (cat.defines,     cat.defines,     "Defines"),
        (cat.region_cuts, cat.region_cuts, "Region Cuts"),
    ]:
        if not items:
            continue
        lines.append(f"\n\033[1m  {heading}\033[0m\n  {SEP}")
        for oo in items:
            kind_color = {
                "object":     "\033[33m",   # orange
                "define":     "\033[95m",   # purple
                "region_cut": "\033[94m",   # blue
            }.get(oo.kind, "")
            RESET = "\033[0m"
            region_tag = f"  \033[90m(region: {oo.region})\033[0m" if oo.region else ""
            lines.append(f"  {kind_color}{oo.display_label()}{RESET}{region_tag}")
            cs = oo.constraint_summary()
            lines.append(f"    constraints: \033[96m{cs}\033[0m")
            if oo.node:
                tree_str = oo.node.pretty(indent=2)
                lines.append(f"    dep tree:\n{tree_str}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# HTML rendering
# ─────────────────────────────────────────────────────────────────────────────

def render_catalogue_html(cat: AnalysisCatalogue) -> str:
    import os
    label = os.path.basename(cat.source_file)

    kind_colors = {
        "object":     ("var(--orange)", "obj"),
        "define":     ("var(--purple)", "def"),
        "region_cut": ("var(--blue)",   "cut"),
    }

    rows = ""
    for oo in cat.all_overlap_objects:
        color, tag_label = kind_colors.get(oo.kind, ("var(--muted)", "?"))
        region_cell = f'<span style="color:var(--muted);font-size:.72rem">{oo.region}</span>' \
                      if oo.region else "—"
        cs = oo.constraint_summary()
        cs_html = f'<code style="color:var(--cyan)">{cs}</code>' if cs else "—"

        dep_html = ""
        if oo.node:
            dep_html = _dep_tree_mini_html(oo.node)

        rows += (
            f"<tr>"
            f'<td><span style="background:{color}22;color:{color};padding:.1rem .35rem;'
            f'border-radius:3px;font-size:.68rem;font-family:monospace">{tag_label}</span></td>'
            f"<td><code>{oo.name}</code></td>"
            f"<td>{region_cell}</td>"
            f"<td>{cs_html}</td>"
            f"<td>{dep_html}</td>"
            f"</tr>"
        )

    return f"""
    <div class="section">
      <div class="section-title">Overlap Object Catalogue — {label}</div>
      <table>
        <thead><tr>
          <th>Kind</th><th>Name</th><th>Region</th>
          <th>Own constraints</th><th>Dependency chain</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """


def _dep_tree_mini_html(tree: CutDependency, depth: int = 0) -> str:
    if tree is None or depth > 4:
        return ""
    kind_colors = {
        "cut":     "var(--blue)",
        "define":  "var(--purple)",
        "object":  "var(--orange)",
        "builtin": "var(--green)",
    }
    kind_labels = {"cut":"cut","define":"def","object":"obj","builtin":"BLT"}
    color = kind_colors.get(tree.kind, "var(--muted)")
    label = kind_labels.get(tree.kind, "?")
    indent = depth * 12

    nc_parts = []
    for ce in tree.own_constraint_exprs:
        for c in constraint_expr_leaves(ce):
            eff = c.effective_op()
            val = int(c.threshold) if c.threshold == int(c.threshold) else c.threshold
            nc_parts.append(
                f'<span style="color:var(--cyan);font-size:.68rem">'
                f'{c.display_name()} {eff} {val}</span>'
            )
    nc_html = ('<span style="color:var(--muted)"> ← </span>' + ", ".join(nc_parts)) \
              if nc_parts else ""

    children_html = "".join(
        _dep_tree_mini_html(ch, depth + 1) for ch in tree.children
    )
    return (
        f'<div style="margin-left:{indent}px;white-space:nowrap;font-size:.72rem">'
        f'<span style="background:{color}22;color:{color};padding:.02rem .25rem;'
        f'border-radius:2px;font-family:monospace;margin-right:.2rem">{label}</span>'
        f'<span style="font-family:monospace">{tree.name}</span>'
        f'{nc_html}</div>'
        f'{children_html}'
    )
