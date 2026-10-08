"""Tiny, technology-neutral condition language shared by all adapters.

Grammar (same as SCORE graph checks so expressions pass through unchanged)::

    expr  := "attr == value" | "attr != value" | "attr contains value" | "attr != []"
           | {and: [expr, ...]} | {or: [expr, ...]} | {not: expr}
"""
from __future__ import annotations

from typing import Any


def evaluate(expr: Any, item: dict[str, Any]) -> bool:
    if isinstance(expr, dict):
        ((op, arg),) = expr.items()
        if op == "and":
            return all(evaluate(e, item) for e in arg)
        if op == "or":
            return any(evaluate(e, item) for e in arg)
        if op == "not":
            return not evaluate(arg, item)
        raise ValueError(f"unknown operator {op}")
    for sym in (" != ", " == ", " contains "):
        if sym in expr:
            left, right = (s.strip() for s in expr.split(sym, 1))
            val = item.get(left)
            if sym == " contains ":
                return right in str(val or "")
            if right == "[]":
                val_empty = val in (None, "", [])
                return not val_empty if sym == " != " else val_empty
            eq = str(val if val is not None else "") == right
            return eq if sym == " == " else not eq
    raise ValueError(f"cannot parse expression: {expr!r}")
