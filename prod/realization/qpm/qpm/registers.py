"""Objective and policy registers: the top of the digital thread.

Source: needs/objectives.yaml and needs/policies.yaml (next to needs/standards.yaml).
Chain: objective drives policy, policy drives outcome. Also holds the minimum-definition rules for assemblies.
Renders Sphinx-needs RST like catalog.py.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .catalog import HEADER, MAX_ID_LENGTH, _hdr, _need, _opt
from .model import load_yaml

OBJ_RE = re.compile(r"^obj_qx_[a-z]+_[a-z0-9]+(_[a-z0-9]+)*$")
POL_RE = re.compile(r"^pol_qx_[a-z]+_[a-z0-9]+(_[a-z0-9]+)*$")
OBJ_SCOPES = {"GLOB", "PROJECT"}
# Objectives stay technology neutral: no standard, integrity level, tool or product-domain term in title, statement or measure.
FORBIDDEN = ("ISO", "IEC", "IEEE", "SAE", "ASIL", "CAL", "ASPICE", "SOTIF", "AUTOSAR", "SCORE", "HARA", "TARA", "CSMS",
             "FSMS", "Bazel", "GitHub", "Jira", "Sphinx", "Python", "Eclipse")
FORBIDDEN_RE = re.compile(r"\b(" + "|".join(FORBIDDEN) + r")\b|\b\d{4,5}\b", re.I)
OBJ_FIELDS = ("title", "statement", "measure", "target", "scope", "owner", "status")


def load_registers(standards_path: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    d = Path(standards_path).parent
    objs = load_yaml(d / "objectives.yaml") if (d / "objectives.yaml").is_file() else {}
    pols = load_yaml(d / "policies.yaml") if (d / "policies.yaml").is_file() else {}
    return list((objs or {}).get("objectives") or []), list((pols or {}).get("policies") or [])


def check_registers(objs: list[dict[str, Any]], pols: list[dict[str, Any]], areas: list[dict[str, Any]],
                    standards: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errs: list[str] = []
    warns: list[str] = []
    std = {s["id"] for s in standards}
    roles = {r["id"] for a in areas for r in a.get("roles") or []}
    wps = {w["id"]: a["area"]["id"] for a in areas for w in a.get("workproducts") or []}
    outs = {o["id"] for a in areas for o in a.get("outcomes") or []}
    asm = {a["area"]["id"] for a in areas}
    pol_ids = {p.get("id") for p in pols}
    obj_ids = {o.get("id") for o in objs}
    seen: set[str] = set()
    driven: set[str] = set()
    for o in objs:
        oid = o.get("id", "?")
        if oid in seen:
            errs.append(f"objective {oid}: duplicate id")
        seen.add(oid)
        if not OBJ_RE.match(oid) or "__" in oid:
            errs.append(f"objective {oid}: id must be obj_qx_<assembly code>_<name>, lower case, no double underscore")
        if len(oid) > MAX_ID_LENGTH:
            errs.append(f"objective {oid}: id longer than {MAX_ID_LENGTH} characters")
        for f in OBJ_FIELDS:
            if not o.get(f):
                errs.append(f"objective {oid}: missing {f}")
        for f in ("title", "statement", "measure"):
            hits = sorted({m.group(0) for m in FORBIDDEN_RE.finditer(str(o.get(f, "")))})
            if hits:
                errs.append(f"objective {oid}.{f}: names {', '.join(repr(h) for h in hits)}; objectives stay technology "
                            "neutral (standards belong to the policy and its complies links)")
        sc = o.get("scope")
        if sc and sc not in OBJ_SCOPES:
            errs.append(f"objective {oid}.scope: must be one of {', '.join(sorted(OBJ_SCOPES))}")
        ct = o.get("contributes_to") or []
        if sc == "PROJECT" and not ct:
            errs.append(f"objective {oid}: a PROJECT objective must contribute_to a GLOB objective")
        if sc == "GLOB" and ct:
            errs.append(f"objective {oid}: a GLOB objective cannot contribute_to another objective")
        for c in ct:
            if c not in obj_ids:
                errs.append(f"objective {oid}.contributes_to: unknown objective '{c}'")
        if o.get("owner") and o["owner"] not in roles:
            errs.append(f"objective {oid}.owner: unknown role '{o['owner']}'")
        for a in o.get("delivered_by") or []:
            if a not in asm:
                errs.append(f"objective {oid}.delivered_by: unknown assembly '{a}'")
        if not o.get("delivered_by"):
            errs.append(f"objective {oid}: missing delivered_by")
        for p in o.get("drives") or []:
            driven.add(p)
            if p not in pol_ids:
                errs.append(f"objective {oid}.drives: unknown policy '{p}'")
        if not o.get("drives"):
            warns.append(f"objective {oid}: drives no policy")
    seen = set()
    for p in pols:
        pid = p.get("id", "?")
        if pid in seen:
            errs.append(f"policy {pid}: duplicate id")
        seen.add(pid)
        if not POL_RE.match(pid) or "__" in pid:
            errs.append(f"policy {pid}: id must be pol_qx_<assembly code>_<name>, lower case, no double underscore")
        if len(pid) > MAX_ID_LENGTH:
            errs.append(f"policy {pid}: id longer than {MAX_ID_LENGTH} characters")
        for f in ("title", "scope", "status", "standards", "work_product", "assembly", "drives"):
            if not p.get(f):
                errs.append(f"policy {pid}: missing {f}")
        for s in p.get("standards") or []:
            if s not in std:
                errs.append(f"policy {pid}.standards: unresolved standard clause '{s}'")
        w = p.get("work_product")
        if w and w not in wps:
            errs.append(f"policy {pid}.work_product: unknown work product '{w}'")
        elif w and p.get("assembly") and wps[w] != p["assembly"]:
            errs.append(f"policy {pid}.work_product: '{w}' belongs to '{wps[w]}', not to '{p['assembly']}'")
        if p.get("assembly") and p["assembly"] not in asm:
            errs.append(f"policy {pid}.assembly: unknown assembly '{p['assembly']}'")
        for oc in p.get("drives") or []:
            if oc not in outs:
                errs.append(f"policy {pid}.drives: unresolved outcome '{oc}'")
        if pid not in driven:
            errs.append(f"policy {pid}: no objective drives this policy")
    return errs, warns


def check_minimum(areas: list[dict[str, Any]]) -> list[str]:
    """Minimum definition of a process: outcomes with clauses, capabilities, at least one workflow with an entry gate (a first workflow fed by an external input has nothing to gate on),
    work products linked to a clause (or marked internal), roles with responsible and approver."""
    errs: list[str] = []
    for a in areas:
        aid = a["area"]["id"]
        if not a.get("outcomes"):
            errs.append(f"{aid}: minimum definition needs at least one outcome")
        if not a.get("capabilities"):
            errs.append(f"{aid}: minimum definition needs at least one capability")
        for o in a.get("outcomes") or []:
            if not o.get("complies"):
                errs.append(f"{aid}.{o['id']}: outcome needs at least one complies clause")
        wfs = a.get("workflows") or []
        if not wfs:
            errs.append(f"{aid}: minimum definition needs at least one workflow")
        if wfs and not any(w.get("gate") for w in wfs):
            errs.append(f"{aid}: minimum definition needs at least one workflow with an entry gate")
        for wf in wfs:
            if not wf.get("responsible") or not wf.get("approved_by"):
                errs.append(f"{aid}.{wf['id']}: workflow needs a responsible and an approver")
            if not wf.get("achieves"):
                errs.append(f"{aid}.{wf['id']}: workflow must achieve at least one outcome")
        for w in a.get("workproducts") or []:
            if not w.get("complies") and not w.get("internal"):
                errs.append(f"{aid}.{w['id']}: work product needs a complies clause or internal: true")
    return errs


def _cell(items: list[str] | None) -> str:
    return ", ".join(f"``{i}``" for i in items) if items else "none"


def render_registers(objs: list[dict[str, Any]], pols: list[dict[str, Any]], areas: list[dict[str, Any]],
                     standards: list[dict[str, Any]]) -> dict[str, str]:
    """Return {path relative to prod/: content} for the objective and policy registers."""
    out: dict[str, str] = {}
    titles = {p["id"]: p["title"] for p in pols}
    stds = {s["id"]: f"{s['standard']} {s['clause']}" for s in standards}
    if objs:
        t = HEADER.format(src="needs/objectives.yaml") + ".. _qx_objective_register:\n\n" + _hdr("Objective register", "#")
        t += ("\nThe business objectives of the hub, in technology neutral wording. Each objective drives one or more "
              "policies (see :ref:`qx_policy_register`). The rules are on :ref:`qx_objectives`.\n\n"
              ".. list-table::\n   :header-rows: 1\n   :widths: 20 28 24 14 14\n\n"
              "   * - ID\n     - Objective\n     - Measure\n     - Drives\n     - Delivered by\n")
        for o in objs:
            t += (f"   * - ``{o['id']}``\n     - {o['title']}\n     - {o['measure']}\n"
                  f"     - {', '.join(titles.get(p, p) for p in o.get('drives') or []) or 'none yet'}\n"
                  f"     - {_cell(o.get('delivered_by'))}\n")
        t += "\n"
        for o in objs:
            body = (f"   {o['statement']}\n\n   Measure: {o['measure']}\n\n   Target: {o['target']}. Scope: {o['scope']}. "
                    f"Owner: ``{o['owner']}``.\n\n   Delivered by: {_cell(o.get('delivered_by'))}.\n")
            if o.get("anchor"):
                body += f"\n   15288 anchor: {o['anchor']}.\n"
            opts = _opt("drives", o.get("drives")) + _opt("contributes_to", o.get("contributes_to"))
            t += _need("objective", o["title"], o["id"], o.get("status", "draft"), "objectives", opts) + body + "\n"
        out["missions/objective_register.rst"] = t
    if pols:
        t = HEADER.format(src="needs/policies.yaml") + ".. _qx_policy_register:\n\n" + _hdr("Policy register", "#")
        t += ("\nThe organisation level policies. Each is driven by one or more objectives (see "
              ":ref:`qx_objective_register`) and drives the outcomes of the processes that carry it out.\n\n"
              ".. list-table::\n   :header-rows: 1\n   :widths: 16 26 22 18 18\n\n"
              "   * - Policy\n     - Standards\n     - Work product\n     - Assembly\n     - Page\n")
        for p in pols:
            t += (f"   * - ``{p['id']}``\n     - {', '.join(stds.get(s, s) for s in p['standards'])}\n"
                  f"     - ``{p['work_product']}``\n     - ``{p['assembly']}``\n     - :doc:`{p['title']} <{p.get('page', p['id'])}>`\n")
        t += "\n"
        for p in pols:
            body = f"   {p['scope']}\n\n   Work product: ``{p['work_product']}``. Assembly: ``{p['assembly']}``.\n"
            opts = _opt("drives", p.get("drives")) + _opt("complies", p.get("standards"))
            t += _need("policy", p["title"], p["id"], p.get("status", "draft"), "policies", opts) + body + "\n"
        out["policies/register.rst"] = t
    return out
