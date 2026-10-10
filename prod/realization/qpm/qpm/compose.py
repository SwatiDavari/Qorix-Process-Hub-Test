"""Compose a tier chain (base -> overlay(s) -> project) into one resolved model.

Governance rules enforced here (see prod/concepts/tiering.rst):

* exactly one ``base`` tier, first in the chain;
* each tier ``extends`` the tier directly before it;
* ``overlay`` tiers may only ADD or WIDEN (superset rule) - content that is valid
  against the base stays valid against the Qorix overlay;
* ``project`` tiers may only NARROW (tailoring) and every operation needs a
  ``rationale`` (ISO 26262-2 6.4.5 / ASPICE tailoring evidence);
* at most one ``project`` tier, and it must be last.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .model import QpmError, deepcopy, empty_model, load_yaml, validate_tier_doc

OVERLAY_OPS = {
    "add_element_type", "extend_element_type", "extend_enum",
    "add_relation_type", "add_rule", "add_forbidden_words", "widen_rule",
}
PROJECT_OPS = {"restrict_enum", "require_attribute", "exclude_element_type", "add_rule"}

# "links" is the built-in untyped relation, "ANY" the wildcard target (metamodel conventions)
BUILTIN_RELATIONS = {"links"}
WILDCARD_TARGET = "ANY"

ASIL_ORDER = ["QM", "ASIL_A", "ASIL_B", "ASIL_C", "ASIL_D"]
CAL_ORDER = ["CAL1", "CAL2", "CAL3", "CAL4"]


def _types_sel(model: dict[str, Any], sel: Any) -> list[str]:
    if sel in (None, "*"):
        return list(model["element_types"])
    missing = [t for t in sel if t not in model["element_types"]]
    if missing:
        raise QpmError(f"unknown element type(s): {missing}")
    return list(sel)


# ---------------------------------------------------------------- overlay ops
def op_add_element_type(m, op, tier):
    name = op["name"]
    if name in m["element_types"]:
        raise QpmError(f"[{tier}] add_element_type: '{name}' already exists")
    m["element_types"][name] = deepcopy(op["definition"])
    m["provenance"][f"element_types.{name}"] = tier


def op_extend_element_type(m, op, tier):
    name = op["name"]
    et = m["element_types"].get(name)
    if et is None:
        raise QpmError(f"[{tier}] extend_element_type: unknown '{name}'")
    for a, d in (op.get("add_attributes") or {}).items():
        if a in et.setdefault("attributes", {}):
            raise QpmError(f"[{tier}] {name}.{a} already defined")
        if d.get("required"):
            raise QpmError(f"[{tier}] {name}.{a}: overlay may only add OPTIONAL attributes (superset rule)")
        et["attributes"][a] = deepcopy(d)
        m["provenance"][f"element_types.{name}.attributes.{a}"] = tier
    for r, d in (op.get("add_relations") or {}).items():
        rels = et.setdefault("relations", {})
        if d.get("required"):
            raise QpmError(f"[{tier}] {name}.{r}: overlay may only add OPTIONAL relations (superset rule)")
        if r in rels:  # widen targets of an existing relation
            rels[r]["targets"] += [t for t in d["targets"] if t not in rels[r]["targets"]]
        else:
            rels[r] = deepcopy(d)
        m["provenance"][f"element_types.{name}.relations.{r}"] = tier
    for t in op.get("add_tags") or []:
        if t not in et.setdefault("tags", []):
            et["tags"].append(t)


def op_extend_enum(m, op, tier):
    attr, values = op["attribute"], op["values"]
    hit = 0
    for name in _types_sel(m, op.get("types")):
        a = (m["element_types"][name].get("attributes") or {}).get(attr)
        if a is None or "enum" not in a:
            continue
        a["enum"] += [v for v in values if v not in a["enum"]]
        if attr == "safety":
            a["enum"].sort(key=lambda v: ASIL_ORDER.index(v) if v in ASIL_ORDER else 99)
        hit += 1
    if hit == 0:
        raise QpmError(f"[{tier}] extend_enum: no element type has enum attribute '{attr}'")


def op_add_relation_type(m, op, tier):
    if op["name"] in m["relation_types"]:
        raise QpmError(f"[{tier}] relation type '{op['name']}' exists")
    m["relation_types"][op["name"]] = {"forward": op["forward"], "reverse": op["reverse"]}
    m["provenance"][f"relation_types.{op['name']}"] = tier


def op_add_rule(m, op, tier):
    rule = deepcopy(op["rule"])
    if any(r["id"] == rule["id"] for r in m["rules"]):
        raise QpmError(f"[{tier}] rule '{rule['id']}' exists")
    _types_sel(m, rule.get("applies_to", {}).get("types"))
    m["rules"].append(rule)
    m["provenance"][f"rules.{rule['id']}"] = tier


def op_widen_rule(m, op, tier):
    """Widen a graph rule's `expect: or:` list (add alternatives only, never remove)."""
    rule = next((r for r in m["rules"] if r["id"] == op["rule_id"]), None)
    if rule is None:
        raise QpmError(f"[{tier}] widen_rule: rule '{op['rule_id']}' not found")
    exp = (rule.get("check") or {}).get("expect")
    if not isinstance(exp, dict) or "or" not in exp:
        raise QpmError(f"[{tier}] widen_rule: '{op['rule_id']}' has no `expect: or` list to widen")
    for alt in op["add_alternatives"]:
        if alt not in exp["or"]:
            exp["or"].append(alt)
    m["provenance"][f"rules.{rule['id']}"] = tier


def op_add_forbidden_words(m, op, tier):
    m["lint"]["forbidden_words"].append(deepcopy(op["entry"]))


# ---------------------------------------------------------------- project ops
def op_restrict_enum(m, op, tier, strict=True):
    attr, keep = op["attribute"], op["values"]
    for name in _types_sel(m, op.get("types")):
        a = (m["element_types"][name].get("attributes") or {}).get(attr)
        if a is None or "enum" not in a:
            continue
        bad = [v for v in keep if v not in a["enum"]]
        if bad and strict:
            raise QpmError(f"[{tier}] restrict_enum {name}.{attr}: {bad} not allowed by parent tier (tailoring may only narrow)")
        narrowed = [v for v in a["enum"] if v in keep]
        if not narrowed:
            raise QpmError(f"[{tier}] restrict_enum {name}.{attr}: would leave no allowed value")
        a["enum"] = narrowed


def op_require_attribute(m, op, tier):
    for name in _types_sel(m, op.get("types")):
        a = (m["element_types"][name].get("attributes") or {}).get(op["attribute"])
        if a is not None:
            a["required"] = True


def op_exclude_element_type(m, op, tier):
    name = op["name"]
    if name not in m["element_types"]:
        raise QpmError(f"[{tier}] exclude_element_type: unknown '{name}'")
    del m["element_types"][name]
    for other, et in m["element_types"].items():
        for r, d in list((et.get("relations") or {}).items()):
            if name in d["targets"]:
                d["targets"].remove(name)
                if not d["targets"]:
                    if d["required"]:
                        raise QpmError(f"[{tier}] excluding '{name}' empties mandatory relation {other}.{r}")
                    del et["relations"][r]
    for rule in m["rules"]:
        ts = rule.get("applies_to", {}).get("types", [])
        if name in ts:
            ts.remove(name)
    m["rules"] = [r for r in m["rules"] if r.get("applies_to", {}).get("types")]


OPS: dict[str, Callable] = {k[3:]: v for k, v in globals().items() if k.startswith("op_")}


def _apply_integrity(m: dict[str, Any], project: dict[str, Any], tier: str) -> None:
    """Translate project integrity ceilings into enum restrictions."""
    integ = project.get("integrity") or {}
    if "asil_max" in integ:
        keep = ASIL_ORDER[: ASIL_ORDER.index(integ["asil_max"]) + 1]
        op_restrict_enum(m, {"attribute": "safety", "values": keep}, tier, strict=False)
    if integ.get("cal_max") not in (None, "TBD"):
        keep = CAL_ORDER[: CAL_ORDER.index(integ["cal_max"]) + 1]
        op_restrict_enum(m, {"attribute": "cal", "values": keep}, tier, strict=False)


def compose(paths: list[str | Path]) -> dict[str, Any]:
    if not paths:
        raise QpmError("no tiers given")
    m = empty_model()
    prev: str | None = None
    for i, p in enumerate(paths):
        doc = load_yaml(p)
        validate_tier_doc(doc, str(p))
        t = doc["tier"]
        kind, tid = t["kind"], t["id"]
        if i == 0 and kind != "base":
            raise QpmError(f"{p}: first tier must be kind=base")
        if i > 0:
            if kind == "base":
                raise QpmError(f"{p}: only one base tier allowed")
            if t.get("extends") != prev:
                raise QpmError(f"{p}: tier '{tid}' must extend '{prev}', found '{t.get('extends')}'")
            if m["tiers"][-1]["kind"] == "project":
                raise QpmError(f"{p}: nothing may follow a project tier")
        m["tiers"].append({"id": tid, "kind": kind, "rank": i, "extends": t.get("extends"),
                           "title": t.get("title", ""), "source": str(p)})

        if kind == "base":
            for key in ("defaults", "element_types", "relation_types", "rules", "lint"):
                if key in doc:
                    m[key] = deepcopy(doc[key])
            for n in m["element_types"]:
                m["provenance"][f"element_types.{n}"] = tid
            for r in m["rules"]:
                m["provenance"][f"rules.{r['id']}"] = tid
            for n in m["relation_types"]:
                m["provenance"][f"relation_types.{n}"] = tid
        else:
            allowed = OVERLAY_OPS if kind == "overlay" else PROJECT_OPS
            if kind == "project":
                if "project" not in doc:
                    raise QpmError(f"{p}: project tier needs a 'project' block")
                m["project"] = deepcopy(doc["project"])
            for op in doc.get("operations") or []:
                name = op["op"]
                if name not in allowed:
                    raise QpmError(f"[{tid}] op '{name}' not permitted in a {kind} tier")
                if kind == "project" and not op.get("rationale"):
                    raise QpmError(f"[{tid}] op '{name}' needs a rationale (tailoring evidence)")
                OPS[name](m, op, tid)
                m["tailoring_log"].append({
                    "tier": tid, "op": name,
                    "target": op.get("name") or op.get("attribute") or op.get("rule", {}).get("id")
                    or op.get("entry", {}).get("id"),
                    "rationale": op.get("rationale", ""),
                })
            if kind == "project":
                _apply_integrity(m, m["project"], tid)
        prev = tid
    check_integrity(m)
    return m


def check_integrity(m: dict[str, Any]) -> None:
    """Referential integrity of the resolved model."""
    errs = []
    for name, et in m["element_types"].items():
        for r, d in (et.get("relations") or {}).items():
            if r not in m["relation_types"] and r not in BUILTIN_RELATIONS:
                errs.append(f"{name}.{r}: relation type not declared")
            for tgt in d["targets"]:
                if tgt != WILDCARD_TARGET and tgt not in m["element_types"]:
                    errs.append(f"{name}.{r}: unknown target type '{tgt}'")
    prefixes: dict[str, str] = {}
    for name, et in m["element_types"].items():
        if et["prefix"] in prefixes:
            errs.append(f"prefix '{et['prefix']}' used by {prefixes[et['prefix']]} and {name}")
        prefixes[et["prefix"]] = name
    for rule in m["rules"]:
        for t in rule.get("applies_to", {}).get("types", []):
            if t not in m["element_types"]:
                errs.append(f"rule {rule['id']}: unknown type '{t}'")
    if errs:
        raise QpmError("integrity errors:\n  " + "\n  ".join(errs))
