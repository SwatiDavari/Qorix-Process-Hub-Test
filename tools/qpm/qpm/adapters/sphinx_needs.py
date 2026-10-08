"""Sphinx-needs adapter: resolved QPM model -> SCORE docs-as-code ``metamodel.yaml``.

The output is consumed by ``docs(metamodel = ...)`` of ``score_docs_as_code``.
Neutral rule kinds that docs-as-code cannot express are returned in
``unsupported`` and enforced instead by ``qpm lint-needs`` on ``needs.json``.
"""
from __future__ import annotations

from typing import Any

from ..model import attr_to_pattern

NAME = "sphinx-needs (score_docs_as_code)"
SUPPORTED_RULE_KINDS = {"graph"}


def _opts(attrs: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    mand = {n: attr_to_pattern(a) for n, a in attrs.items() if a["required"]}
    opt = {n: attr_to_pattern(a) for n, a in attrs.items() if not a["required"]}
    return mand, opt


def emit(model: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    out: dict[str, Any] = {}
    mand, opt = _opts(model["defaults"]["attributes"])
    out["needs_types_base_options"] = {"optional_options": opt, "mandatory_options": mand}

    pw: dict[str, Any] = {}
    for fw in model["lint"]["forbidden_words"]:
        entry: dict[str, Any] = {}
        if fw.get("applies_to_tags"):
            entry["types"] = list(fw["applies_to_tags"])
        entry.update({k: list(v) for k, v in fw["fields"].items()})
        pw[fw["id"]] = entry
    out["prohibited_words_checks"] = pw

    types: dict[str, Any] = {}
    for name, et in model["element_types"].items():
        t: dict[str, Any] = {"title": et["title"]}
        if et.get("description"):
            t["description"] = et["description"]
        t.update(et.get("presentation") or {})
        if et["prefix"] != f"{name}__":  # SCORE default prefix is "<type>__"
            t["prefix"] = et["prefix"]
        m, o = _opts(et.get("attributes") or {})
        if m:
            t["mandatory_options"] = m
        if o:
            t["optional_options"] = o
        rels = et.get("relations") or {}
        ml = {r: ", ".join(v["targets"]) for r, v in rels.items() if v["required"]}
        ol = {r: ", ".join(v["targets"]) for r, v in rels.items() if not v["required"]}
        if ml:
            t["mandatory_links"] = ml
        if ol:
            t["optional_links"] = ol
        if et.get("tags"):
            t["tags"] = list(et["tags"])
        if "id_parts" in et:
            t["parts"] = et["id_parts"]
        types[name] = t
    out["needs_types"] = types

    out["needs_extra_links"] = {
        n: {"incoming": r["reverse"], "outgoing": r["forward"]} for n, r in model["relation_types"].items()
    }

    checks: dict[str, Any] = {}
    unsupported: list[dict[str, Any]] = []
    for rule in model["rules"]:
        if rule["kind"] not in SUPPORTED_RULE_KINDS:
            unsupported.append(rule)
            continue
        a, c = rule["applies_to"], rule["check"]
        needs: dict[str, Any] = {"include": ", ".join(a["types"])}
        if a.get("exclude"):
            needs["exclude"] = ", ".join(a["exclude"])
        if "where" in a:
            needs["condition"] = a["where"]
        g: dict[str, Any] = {"needs": needs}
        g["check"] = {c["relation"]: c["expect"]}
        g["explanation"] = rule.get("explanation", "")
        if rule.get("severity") == "info":
            g["info_only"] = True
        checks[rule["id"]] = g
    out["graph_checks"] = checks
    return out, unsupported
