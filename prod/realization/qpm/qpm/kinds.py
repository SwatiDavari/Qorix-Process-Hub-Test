"""Artifact kinds: neutral classification of work products (needs/artifact_kinds.yaml)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .model import load_yaml

KINDS_FILE = Path(__file__).resolve().parents[4] / "needs" / "artifact_kinds.yaml"


def load_kinds(path: str | Path | None = None) -> tuple[dict[str, str], dict[str, str]]:
    """Return (kind -> category title, kind -> purpose)."""
    d = load_yaml(Path(path) if path else KINDS_FILE) or {}
    cat: dict[str, str] = {}
    pur: dict[str, str] = {}
    for c in d.get("categories") or []:
        for k in c.get("kinds") or []:
            cat[k["id"]] = c["title"]
            pur[k["id"]] = k.get("purpose", "")
    return cat, pur


def check_kinds(areas: list[dict[str, Any]], path: str | Path | None = None) -> list[str]:
    cat, _ = load_kinds(path)
    errs: list[str] = []
    for a in areas:
        aid = a["area"]["id"]
        for wp in a.get("workproducts") or []:
            k = wp.get("kind")
            if not k:
                errs.append(f"{aid}.{wp['id']}: kind is required (one of {', '.join(sorted(cat))})")
            elif k not in cat:
                errs.append(f"{aid}.{wp['id']}: unknown kind '{k}' (allowed: {', '.join(sorted(cat))})")
    return errs
