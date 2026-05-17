"""
report.py  (v3 – structure-gated results)
==========================================
Renders OverlapReport with:
  - Per-object structural match / mismatch
  - Per-region cut-pair breakdown (matched vs unmatched by structure)
  - Variable overlap table with provenance chains
  - Full dependency tree display per cut
"""

from __future__ import annotations
import math, os
from typing import List, Optional
from catalogue import AnalysisCatalogue, build_catalogue, render_catalogue_html
from overlap_checker import (
    OverlapReport, RegionPairResult, ObjectPairResult,
    VariableOverlap, CutPairResult,
)
from ir_extractor import CutDependency, constraint_expr_leaves

# ─────────────────────────────────────────────────────────────────────────────
# Shared constants
# ─────────────────────────────────────────────────────────────────────────────

VERDICT_LABEL = {
    "OVERLAP":             "⚠  OVERLAP",
    "DISJOINT":            "✓  DISJOINT",
    "EQUAL":               "=  EQUAL",
    "SUBSET":              "⊆  SUBSET (A⊆B)",
    "SUPERSET":            "⊇  SUPERSET (A⊇B)",
    "PARTIAL":             "~  PARTIAL",
    "NO_OVERLAP":          "✓  NO OVERLAP",
    "STRUCTURE_MISMATCH":  "≠  STRUCT MISMATCH",
    "DEP_VALUES_MISMATCH": "≠  DEP VALUES DIFFER",
    "UNKNOWN":             "?  UNKNOWN",
}

# ─────────────────────────────────────────────────────────────────────────────
# Terminal renderer
# ─────────────────────────────────────────────────────────────────────────────

RESET = "\033[0m"; BOLD = "\033[1m"
RED   = "\033[91m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
CYAN  = "\033[96m"; GREY  = "\033[90m"; MAGENTA = "\033[95m"
BLUE  = "\033[94m"; ORANGE = "\033[33m"

VERDICT_COLOR = {
    "OVERLAP":            RED,
    "DISJOINT":           GREEN,
    "EQUAL":              BLUE,
    "SUBSET":             MAGENTA,
    "SUPERSET":           MAGENTA,
    "PARTIAL":            YELLOW,
    "NO_OVERLAP":         GREEN,
    "STRUCTURE_MISMATCH": GREY,
    "UNKNOWN":            GREY,
}

def _c(text, color): return f"{color}{text}{RESET}"
def _verdict_str(v):
    return _c(VERDICT_LABEL.get(v, v), VERDICT_COLOR.get(v, GREY))


def render_terminal(reports: List[OverlapReport], verbose: bool = True) -> str:
    lines = []
    SEP  = "─" * 76
    SEP2 = "═" * 76

    for report in reports:
        la = os.path.basename(report.analysis_a)
        lb = os.path.basename(report.analysis_b)
        lines += [
            f"\n{BOLD}{SEP2}{RESET}",
            f"{BOLD}  {_c(la, CYAN)}  ↔  {_c(lb, CYAN)}{RESET}",
            f"  Overall: {_verdict_str(report.summary_verdict)}",
            SEP2,
        ]

        # Objects
        if report.object_results:
            lines.append(f"\n{BOLD}  Object Definitions{RESET}")
            lines.append(SEP)
            for obj in report.object_results:
                status = _verdict_str(obj.verdict)
                match_tag = _c("[STRUCT MATCH]", GREEN) if obj.structure_matched \
                            else _c("[STRUCT MISMATCH]", GREY)
                lines.append(
                    f"  {_c(obj.object_a,BOLD)} ({obj.root_a})"
                    f"  ↔  {_c(obj.object_b,BOLD)} ({obj.root_b})"
                    f"  {match_tag}  {status}"
                )
                if verbose and obj.structure_matched:
                    for vo in obj.variable_overlaps:
                        _append_var_row(lines, vo)
                    for n in obj.notes:
                        lines.append(f"    {GREY}↳ {n}{RESET}")

        # Regions
        lines.append(f"\n{BOLD}  Region Pairs{RESET}")
        lines.append(SEP)
        ORDER = ("OVERLAP","SUBSET","SUPERSET","EQUAL","PARTIAL","UNKNOWN","DISJOINT","NO_OVERLAP","STRUCTURE_MISMATCH")
        for reg in sorted(report.region_results,
                          key=lambda r: ORDER.index(r.verdict)
                          if r.verdict in ORDER else 99):
            shared = ", ".join(sorted(reg.shared_builtin_objects)) or "—"
            lines.append(
                f"  {_c(reg.region_a,BOLD)}  ↔  {_c(reg.region_b,BOLD)}"
                f"    {_verdict_str(reg.verdict)}"
                f"    {GREY}[{shared}]{RESET}"
            )
            if verbose:
                matched   = reg.matched_cut_pairs
                unmatched = reg.unmatched_cut_pairs
                if matched:
                    lines.append(f"    {GREEN}{len(matched)} structurally-matched cut pair(s):{RESET}")
                    for cp in matched:
                        sa = ", ".join(sorted(cp.surface_a)) or "?"
                        sb = ", ".join(sorted(cp.surface_b)) or "?"
                        lines.append(f"      {CYAN}{sa}{RESET}  ↔  {CYAN}{sb}{RESET}  {_verdict_str(cp.verdict)}")
                        for vo in cp.variable_overlaps:
                            _append_var_row(lines, vo, indent=8)
                if unmatched:
                    lines.append(f"    {GREY}{len(unmatched)} cut(s) with no structural match (skipped):{RESET}")
                    for cp in unmatched:
                        sa = ", ".join(sorted(cp.surface_a)) or "?"
                        lines.append(f"      {GREY}{sa}{RESET}")
                for n in reg.notes:
                    lines.append(f"    {GREY}↳ {n}{RESET}")

    return "\n".join(lines)


def _append_var_row(lines, vo: VariableOverlap, indent: int = 6):
    status  = _c("OVERLAP", RED) if vo.overlaps else _c("DISJOINT", GREEN)
    prov    = vo.provenance_str()
    pad     = " " * indent
    prov_s  = f"  {GREY}({prov}){RESET}" if prov and prov != vo.variable else ""
    lines.append(
        f"{pad}{_c(vo.variable, CYAN):<22}"
        f"  A:{str(vo.interval_a):<18}"
        f"  B:{str(vo.interval_b):<18}"
        f"  ∩:{str(vo.intersection):<18}"
        f"  {status}{prov_s}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# HTML helpers
# ─────────────────────────────────────────────────────────────────────────────

_HTML_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600&family=Space+Grotesk:wght@300;400;600;700&display=swap');
:root{
  --bg:#0d1117;--surf:#161b22;--surf2:#21262d;--surf3:#2d333b;
  --border:#30363d;--text:#e6edf3;--muted:#7d8590;
  --blue:#79c0ff;--green:#3fb950;--red:#ff7b72;--yellow:#d29922;
  --purple:#bc8cff;--cyan:#56d364;--orange:#ffa657;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'Space Grotesk',sans-serif;
     padding:2rem;line-height:1.6;font-size:14px}
h1{color:var(--blue);font-size:1.5rem;padding-bottom:.6rem;
   border-bottom:1px solid var(--border);margin-bottom:1.5rem}
.report{background:var(--surf);border:1px solid var(--border);border-radius:10px;
        margin-bottom:2rem;overflow:hidden}
.report-header{background:var(--surf2);padding:.9rem 1.4rem;
               display:flex;justify-content:space-between;align-items:center;
               border-bottom:1px solid var(--border)}
.pair-label{font-weight:700;color:var(--blue)}
.report-body{padding:1.4rem}
.section{margin-bottom:1.5rem}
.section-title{font-size:.68rem;text-transform:uppercase;letter-spacing:.12em;
               color:var(--muted);margin-bottom:.5rem;font-weight:600}
table{width:100%;border-collapse:collapse;font-size:.8rem;
      font-family:'JetBrains Mono',monospace}
th{background:var(--surf2);color:var(--muted);text-align:left;
   padding:.35rem .7rem;border-bottom:1px solid var(--border);font-size:.72rem}
td{padding:.35rem .7rem;border-bottom:1px solid var(--surf2);vertical-align:top}
tr:last-child td{border:none}
.tag{display:inline-block;padding:.12rem .45rem;border-radius:4px;
     font-size:.68rem;font-weight:700;letter-spacing:.03em;
     font-family:'Space Grotesk',sans-serif}
.tag-OVERLAP            {background:#ff7b7222;color:var(--red)}
.tag-DISJOINT           {background:#3fb95022;color:var(--green)}
.tag-EQUAL              {background:#79c0ff22;color:var(--blue)}
.tag-SUBSET             {background:#bc8cff22;color:var(--purple)}
.tag-SUPERSET           {background:#bc8cff22;color:var(--purple)}
.tag-PARTIAL            {background:#d2992222;color:var(--yellow)}
.tag-NO_OVERLAP         {background:#3fb95022;color:var(--green)}
.tag-STRUCTURE_MISMATCH {background:#7d859022;color:var(--muted)}
.tag-UNKNOWN            {background:#7d859022;color:var(--muted)}
.tag-DEP_VALUES_MISMATCH{background:#d2992215;color:var(--yellow)}
.iv{font-family:'JetBrains Mono',monospace;font-size:.76rem}
.iv-ok{color:var(--red)}
.iv-no{color:var(--green)}
.match-yes{color:var(--green);font-size:.72rem;font-weight:600}
.match-no {color:var(--muted);font-size:.72rem}
.chain-step{font-family:'JetBrains Mono',monospace;font-size:.7rem}
details summary{cursor:pointer;color:var(--blue);font-size:.8rem;
                list-style:none;padding:.25rem 0;user-select:none}
details summary::before{content:"▶  "}
details[open] summary::before{content:"▼  "}
.cut-pair-block{background:var(--surf2);border-radius:6px;
                padding:.6rem .8rem;margin:.4rem 0}
.cut-pair-header{display:flex;justify-content:space-between;
                 align-items:center;margin-bottom:.3rem}
.surface-label{font-family:'JetBrains Mono',monospace;font-size:.75rem;
               color:var(--cyan)}
.cut-content{font-family:'JetBrains Mono',monospace;font-size:.78rem;
             color:var(--cyan)}
.cut-missing{font-family:'JetBrains Mono',monospace;font-size:.75rem;
             color:var(--muted);font-style:italic}
.dep-tree-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:.5rem}
.dep-tree-pane{background:var(--surf3);border-radius:5px;padding:.5rem .7rem;
               overflow-x:auto}
.note{color:var(--muted);font-size:.75rem;font-style:italic;padding:.1rem 0}
.builtin-tag{background:#79c0ff15;color:var(--blue);padding:.1rem .3rem;
             border-radius:3px;font-size:.68rem;font-family:'JetBrains Mono',monospace}
.unmatched-row td{opacity:.45}
</style>
"""


def _tag(v: str) -> str:
    lbl = {
        "OVERLAP":             "⚠ OVERLAP",
        "DISJOINT":            "✓ DISJOINT",
        "EQUAL":               "= EQUAL",
        "SUBSET":              "⊆ SUBSET (A⊆B)",
        "SUPERSET":            "⊇ SUPERSET (A⊇B)",
        "PARTIAL":             "~ PARTIAL",
        "NO_OVERLAP":          "✓ NO OVERLAP",
        "STRUCTURE_MISMATCH":  "≠ STRUCT MISMATCH",
        "DEP_VALUES_MISMATCH": "≠ DEP VALUES DIFFER",
        "UNKNOWN":             "? UNKNOWN",
    }
    return f'<span class="tag tag-{v}">{lbl.get(v, v)}</span>'


def _chain_html(chain: List[str]) -> str:
    if not chain:
        return '<span style="color:var(--muted);font-size:.7rem">(direct)</span>'
    parts = []
    for i, step in enumerate(chain):
        color = "var(--orange)" if i == len(chain) - 1 else "var(--purple)"
        parts.append(
            f'<span class="chain-step" style="color:{color}">{step}</span>'
        )
    arrow = ' <span style="color:var(--muted)">→</span> '
    return arrow.join(parts)


def _dep_tree_html(tree: Optional[CutDependency], depth: int = 0) -> str:
    if tree is None:
        return ""
    kind_colors = {
        "cut":     "var(--blue)",
        "define":  "var(--purple)",
        "object":  "var(--orange)",
        "builtin": "var(--green)",
    }
    kind_labels = {"cut": "cut", "define": "def", "object": "obj", "builtin": "BLT"}
    color = kind_colors.get(tree.kind, "var(--muted)")
    label = kind_labels.get(tree.kind, "?")
    indent = depth * 16

    nc_parts = []
    for ce in tree.own_constraint_exprs:
        for c in constraint_expr_leaves(ce):
            eff = c.effective_op()
            val = int(c.threshold) if c.threshold == int(c.threshold) else c.threshold
            nc_parts.append(
                f'<span style="color:var(--cyan);font-size:.7rem">'
                f'{c.display_name()} {eff} {val}</span>'
            )
    nc_html = ""
    if nc_parts:
        nc_html = (
            ' <span style="color:var(--muted)">← </span>'
            + ", ".join(nc_parts)
        )

    children_html = "".join(_dep_tree_html(ch, depth + 1) for ch in tree.children)

    return (
        f'<div style="margin-left:{indent}px;padding:1px 0;white-space:nowrap">'
        f'<span style="background:{color}22;color:{color};padding:.05rem .28rem;'
        f'border-radius:3px;font-size:.65rem;font-family:monospace;margin-right:.3rem">'
        f'{label}</span>'
        f'<span style="font-family:monospace;font-size:.76rem">{tree.name}</span>'
        f'{nc_html}</div>'
        f'{children_html}'
    )


def _var_table_html(var_overlaps: List[VariableOverlap]) -> str:
    if not var_overlaps:
        return '<p class="note">No shared numeric variables.</p>'
    has_chains = any(vo.has_chain() for vo in var_overlaps)
    chain_th   = "<th>Provenance chain</th>" if has_chains else ""
    rows = ""
    for vo in var_overlaps:
        cls_ix = "iv-ok" if vo.overlaps else "iv-no"
        chain_td = ""
        if has_chains:
            ca = _chain_html(vo.chain_a)
            cb = _chain_html(vo.chain_b)
            inner = ca if vo.chain_a == vo.chain_b else (
                f'{ca}<br><span style="color:var(--muted)">vs</span><br>{cb}'
            )
            chain_td = f"<td>{inner}</td>"
        rows += (
            f"<tr>"
            f"<td><code>{vo.variable}</code></td>"
            f"<td class='iv'>{vo.interval_a}</td>"
            f"<td class='iv'>{vo.interval_b}</td>"
            f"<td class='iv {cls_ix}'>{vo.intersection}</td>"
            f"<td>{_tag('OVERLAP' if vo.overlaps else 'NO_OVERLAP')}</td>"
            f"{chain_td}"
            "</tr>"
        )
    return (
        "<table><thead><tr>"
        "<th>Variable</th><th>Range A</th><th>Range B</th>"
        f"<th>Intersection</th><th>Status</th>{chain_th}"
        "</tr></thead><tbody>" + rows + "</tbody></table>"
    )


def _cut_pair_html(cp: CutPairResult) -> str:
    sa = ", ".join(sorted(cp.surface_a)) or "—"
    sb = ", ".join(sorted(cp.surface_b)) or "—"

    if not cp.structure_matched:
        # Unmatched cut pair — present only in one of the two ADLs.
        # The original rendering only showed the surface variable names
        # (e.g. ``ak4jets, dr, metlv``) which is uninformative when the
        # two sides bucket separately because of slicing or arithmetic
        # differences: the user can't tell *which* version of the cut
        # is missing on the other side. Show the actual cut content
        # via ``tree.name`` (the source-form expression as the user
        # wrote it), tag the verdict (SUBSET when A-only, SUPERSET
        # when B-only) instead of generic "struct mismatch", and use
        # a clear "(only in A/B)" placeholder for the empty side.
        a_label = (
            cp.tree_a.name
            if cp.tree_a is not None and cp.tree_a.name
            else (sa if cp.surface_a else None)
        )
        b_label = (
            cp.tree_b.name
            if cp.tree_b is not None and cp.tree_b.name
            else (sb if cp.surface_b else None)
        )
        a_html = (
            f'<span class="cut-content">{a_label}</span>'
            if a_label
            else '<span class="cut-missing">(no matching cut in A)</span>'
        )
        b_html = (
            f'<span class="cut-content">{b_label}</span>'
            if b_label
            else '<span class="cut-missing">(no matching cut in B)</span>'
        )
        # Use the verdict tag (SUBSET / SUPERSET / OVERLAP / EQUAL /
        # DISJOINT) so the structural consequence is visible. The
        # OVERLAP case occurs for chi-square minimization (~=) cuts
        # that are present only on one side: they cannot establish
        # containment in either direction, so the verdict is OVERLAP
        # rather than the directional SUBSET/SUPERSET we'd see for a
        # regular missing cut. Without this branch, the renderer would
        # mislabel the row as "STRUCT MISMATCH" even though the
        # CutPairResult correctly carries verdict=OVERLAP.
        # STRUCTURE_MISMATCH stays only as a defensive fallback for
        # any unexpected verdict value.
        tag_value = (
            cp.verdict
            if cp.verdict in ("SUBSET", "SUPERSET", "OVERLAP", "EQUAL", "DISJOINT")
            else "STRUCTURE_MISMATCH"
        )
        notes_html = "".join(f'<div class="note">↳ {n}</div>' for n in cp.notes)
        return (
            f'<div class="cut-pair-block" style="opacity:.7">'
            f'<div class="cut-pair-header">'
            f'<span class="surface-label">{a_html}  ↔  {b_html}</span>'
            f'{_tag(tag_value)}'
            f'</div>{notes_html}'
            f'<div style="color:var(--muted);font-size:.7rem;margin-top:.2rem">'
            f'Cut present only in one ADL — no structural counterpart on the other side.'
            f'</div>'
            f'</div>'
        )
    if not cp.dep_values_matched:
        sb2 = ", ".join(sorted(cp.surface_b)) or "(none matched)"
        notes_html2 = "".join(f'<div class="note">↳ {n}</div>' for n in cp.notes)
        return (
            f'<div class="cut-pair-block" style="opacity:.55">'
            f'<div class="cut-pair-header">'
            f'<span class="surface-label">{sa}  ↔  {sb2}</span>'
            f'<span style="color:var(--yellow);font-size:.72rem;font-weight:600">'
            f'= struct match  ≠ dep values differ</span>'
            f'</div>{notes_html2}'
            f'<div style="color:var(--muted);font-size:.75rem;margin-top:.2rem">'
            f'Dependency structures match but underlying cut values differ — '
            f'not comparable.</div>'
            f'</div>'
        )

    var_section = ""
    if cp.variable_overlaps:
        var_section = (
            f"<details><summary>{len(cp.variable_overlaps)} variable(s)</summary>"
            f"{_var_table_html(cp.variable_overlaps)}</details>"
        )

    tree_section = ""
    if cp.tree_a or cp.tree_b:
        tree_a_html = _dep_tree_html(cp.tree_a)
        tree_b_html = _dep_tree_html(cp.tree_b)
        tree_section = (
            f'<details><summary>Dependency trees</summary>'
            f'<div class="dep-tree-grid">'
            f'<div class="dep-tree-pane">'
            f'<div class="section-title">Analysis A – {sa}</div>'
            f'{tree_a_html}</div>'
            f'<div class="dep-tree-pane">'
            f'<div class="section-title">Analysis B – {sb}</div>'
            f'{tree_b_html}</div>'
            f'</div></details>'
        )

    notes_html = "".join(f'<div class="note">↳ {n}</div>' for n in cp.notes)
    match_badge = '<span class="match-yes">= struct match</span>'
    return (
        f'<div class="cut-pair-block">'
        f'<div class="cut-pair-header">'
        f'<span class="surface-label">{sa}  ↔  {sb}</span>'
        f'<span>{match_badge}  {_tag(cp.verdict)}</span>'
        f'</div>'
        f'{notes_html}{var_section}{tree_section}'
        f'</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main HTML renderer
# ─────────────────────────────────────────────────────────────────────────────

def render_html(reports: List[OverlapReport], catalogues: List[AnalysisCatalogue] = None) -> str:
    body = ""
    for report in reports:
        la = os.path.basename(report.analysis_a)
        lb = os.path.basename(report.analysis_b)

        # ── Objects section ───────────────────────────────────────────────────
        obj_rows = ""
        if report.object_results:
            for obj in report.object_results:
                match_badge = (
                    '<span class="match-yes">= struct match</span>'
                    if obj.structure_matched else
                    '<span class="match-no">≠ struct mismatch</span>'
                )
                var_section = ""
                if obj.structure_matched and obj.variable_overlaps:
                    var_section = (
                        f"<details><summary>{len(obj.variable_overlaps)} variable(s)</summary>"
                        f"{_var_table_html(obj.variable_overlaps)}</details>"
                    )
                notes_html = "".join(
                    f'<div class="note">↳ {n}</div>' for n in obj.notes
                )
                obj_rows += (
                    f"<tr{'  class=\"unmatched-row\"' if not obj.structure_matched else ''}>"
                    f"<td><strong>{obj.object_a}</strong>"
                    f'<br><span style="color:var(--muted);font-size:.72rem">{obj.chain_a}</span></td>'
                    f"<td><strong>{obj.object_b}</strong>"
                    f'<br><span style="color:var(--muted);font-size:.72rem">{obj.chain_b}</span></td>'
                    f"<td>{match_badge}  {_tag(obj.verdict)}{notes_html}{var_section}</td>"
                    "</tr>"
                )
            obj_html = (
                '<div class="section"><div class="section-title">Object Definitions</div>'
                '<table><thead><tr>'
                '<th>Object A (chain)</th><th>Object B (chain)</th><th>Result</th>'
                '</tr></thead><tbody>' + obj_rows + '</tbody></table></div>'
            )
        else:
            obj_html = ""

        # ── Regions section ───────────────────────────────────────────────────
        reg_rows = ""
        ORDER = ("OVERLAP","SUBSET","SUPERSET","EQUAL","PARTIAL","UNKNOWN","DISJOINT","NO_OVERLAP","STRUCTURE_MISMATCH")
        for reg in sorted(
            report.region_results,
            key=lambda r: ORDER.index(r.verdict) if r.verdict in ORDER else 99
        ):
            builtins_html = "".join(
                f'<span class="builtin-tag">{b}</span>'
                for b in sorted(reg.shared_builtin_objects)
            ) or '<span class="note">none</span>'

            # Cut-pair breakdown
            cp_html = "".join(_cut_pair_html(cp) for cp in reg.cut_pair_results)
            n_matched   = len(reg.matched_cut_pairs)
            n_unmatched = len(reg.unmatched_cut_pairs)
            summary_txt = (
                f"{n_matched} matched"
                + (f", {n_unmatched} unmatched" if n_unmatched else "")
            )
            cuts_section = (
                f"<details open><summary>Cut pairs ({summary_txt})</summary>"
                f"{cp_html}</details>"
            )

            notes_html = "".join(f'<div class="note">↳ {n}</div>' for n in reg.notes)
            reg_rows += (
                f"<tr>"
                f"<td><strong>{reg.region_a}</strong></td>"
                f"<td><strong>{reg.region_b}</strong></td>"
                f'<td>{builtins_html}</td>'
                f"<td>{_tag(reg.verdict)}{notes_html}{cuts_section}</td>"
                "</tr>"
            )

        reg_html = (
            '<div class="section"><div class="section-title">Region Pairs</div>'
            '<table><thead><tr>'
            '<th>Region A</th><th>Region B</th>'
            '<th>Shared physics</th><th>Result & cut pairs</th>'
            '</tr></thead><tbody>' + reg_rows + '</tbody></table></div>'
        )

        body += f"""
        <div class="report">
          <div class="report-header">
            <div class="pair-label">{la}  ↔  {lb}</div>
            <div>Overall: {_tag(report.summary_verdict)}</div>
          </div>
          <div class="report-body">
            {obj_html}
            {reg_html}
          </div>
        </div>
        """

    cat_html = ""
    if catalogues:
        for cat in catalogues:
            cat_html += render_catalogue_html(cat)
        cat_html = (
            '<details><summary style="color:var(--blue);font-size:.9rem;'
            'cursor:pointer;padding:.5rem 0">▶  Overlap Object Catalogues</summary>'
            + cat_html + '</details>'
        )

    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
        "<title>ADL Overlap Report</title>"
        + _HTML_STYLE + "</head><body>"
        + "<h1>ADL Analysis Overlap Report</h1>"
        + body + cat_html + "</body></html>"
    )


def save_html(reports: List[OverlapReport], path: str,
              catalogues: List[AnalysisCatalogue] = None):
    with open(path, "w") as fh:
        fh.write(render_html(reports, catalogues=catalogues))
    print(f"HTML report saved: {path}")
