"""Qorix Process Metamodel (QPM) - technology-neutral model primitives.

A QPM model is plain data (dict/list/str) so it can be serialised to YAML or
JSON and consumed by any adapter (Sphinx-needs, Jira, codebeamer, ...).

Resolved model layout::

    qpm: "1.0"
    tiers: [ {id, kind, rank, extends}, ... ]      # composition chain
    project: {...} | null                          # tailoring metadata
    defaults: {attributes: {...}}                  # apply to every element type
    element_types: {name: ElementType}
    relation_types: {name: {forward, reverse}}
    rules: [Rule]
    lint: {forbidden_words: [...]}
    provenance: {"element_types.<name>": tier_id, ...}
    tailoring_log: [ {tier, op, target, rationale, upstream} ]

ElementType::

    title, prefix, id_parts, description?, tags: [..]
    attributes: {name: {required: bool, enum: [..] | pattern: str}}
    relations:  {name: {required: bool, targets: [type, ..]}}
    presentation: {color?, style?}
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import yaml

QPM_VERSION = "1.0"
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "model" / "schema" / "qpm-tier.schema.json"

_ENUM_RE = re.compile(r"^\^\(([A-Za-z0-9_\-]+(?:\|[A-Za-z0-9_\-]+)*)\)\$$")


class QpmError(Exception):
    """Raised for any model, composition or tailoring violation."""


def pattern_to_attr(pattern: str, required: bool) -> dict[str, Any]:
    """Convert a regex constraint to a neutral attribute (enum when possible)."""
    m = _ENUM_RE.match(pattern)
    if m:
        return {"required": required, "enum": m.group(1).split("|")}
    return {"required": required, "pattern": pattern}


def attr_to_pattern(attr: dict[str, Any]) -> str:
    if "enum" in attr:
        return "^(" + "|".join(attr["enum"]) + ")$"
    return attr["pattern"]


def load_yaml(path: str | Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def dump_yaml(data: Any, path: str | Path | None = None) -> str:
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100)
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
    return text


def dump_json(data: Any, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_tier_doc(doc: dict[str, Any], source: str = "<tier>") -> None:
    """Validate a tier file against the QPM JSON schema."""
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(e.path))
    if errors:
        msgs = [f"  {'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors[:10]]
        raise QpmError(f"{source}: schema violations\n" + "\n".join(msgs))


def empty_model() -> dict[str, Any]:
    return {
        "qpm": QPM_VERSION,
        "tiers": [],
        "project": None,
        "defaults": {"attributes": {}},
        "element_types": {},
        "relation_types": {},
        "rules": [],
        "lint": {"forbidden_words": []},
        "provenance": {},
        "tailoring_log": [],
    }


def deepcopy(x: Any) -> Any:
    return copy.deepcopy(x)
