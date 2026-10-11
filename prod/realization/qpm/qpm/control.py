"""Document control taken from git: effective date, review date, version bumps, review reminders.

The process.yaml keeps the facts a person decides (status, owner, version). The dates are derived:
    effective date  = day the current version line first reached the checked-out branch (approved or released only)
    review date     = effective date + review cycle (12 months unless the process sets review_cycle_months)
"""
from __future__ import annotations

import calendar
import datetime as dt
import re
import subprocess
from pathlib import Path
from typing import Any

from .model import QpmError, load_yaml

DEFAULT_REVIEW_MONTHS = 12
LEVELS = ("major", "minor", "patch")
_VER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse_version(v: str) -> tuple[int, int, int]:
    m = _VER.match(str(v))
    if not m:
        raise QpmError(f"version '{v}' must look like 1.0.0")
    return tuple(int(x) for x in m.groups())  # type: ignore[return-value]


def bump_version(v: str, level: str) -> str:
    ma, mi, pa = parse_version(v)
    if level == "major":
        return f"{ma + 1}.0.0"
    if level == "minor":
        return f"{ma}.{mi + 1}.0"
    if level == "patch":
        return f"{ma}.{mi}.{pa + 1}"
    raise QpmError(f"level must be one of {', '.join(LEVELS)}")


def add_months(d: dt.date, n: int) -> dt.date:
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def _git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if r.returncode:
        raise QpmError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def repo_root(start: str | Path = ".") -> Path:
    return Path(_git(Path(start), "rev-parse", "--show-toplevel").strip())


def _process_file(a: dict[str, Any]) -> Path:
    return Path(a["_source"]) / "process" / "process.yaml"


def effective_date(root: Path, process_file: Path, version: str) -> str | None:
    """Earliest commit that introduced the current `version:` line; None when history does not show it."""
    rel = process_file.resolve().relative_to(root.resolve()).as_posix()
    out = _git(root, "log", "--reverse", "--format=%cs", f"-S  version: {version}", "--", rel).split()
    return out[0] if out else None


def derive(areas: list[dict[str, Any]], root: Path) -> dict[str, dict[str, str]]:
    """{assembly id: {effective, review}} for every approved or released assembly with a date from git."""
    res: dict[str, dict[str, str]] = {}
    for a in areas:
        ar = a["area"]
        if ar.get("status") not in ("approved", "released"):
            continue
        eff, rev = str(ar.get("effective_date")), str(ar.get("review_date"))
        if eff == "auto":
            eff = effective_date(root, _process_file(a), str(ar["version"])) or ""
        if not eff:
            continue
        if rev == "auto":
            months = int(ar.get("review_cycle_months") or DEFAULT_REVIEW_MONTHS)
            rev = add_months(dt.date.fromisoformat(eff), months).isoformat()
        res[ar["id"]] = {"effective": eff, "review": rev}
    return res


def base_versions(root: Path, assemblies: Path, ref: str) -> dict[str, str]:
    """{assembly id: version} of every process.yaml under `assemblies` at git ref."""
    rel = assemblies.resolve().relative_to(root.resolve()).as_posix()
    res: dict[str, str] = {}
    for f in _git(root, "ls-tree", "-r", "--name-only", ref, "--", rel).split():
        if not f.endswith("/process/process.yaml"):
            continue
        import yaml
        doc = yaml.safe_load(_git(root, "show", f"{ref}:{f}")) or {}
        ar = doc.get("assembly") or {}
        if ar.get("id"):
            res[ar["id"]] = str(ar.get("version", ""))
    return res


def changed_assemblies(root: Path, areas: list[dict[str, Any]], ref: str) -> set[str]:
    """Assemblies with any file changed between ref and the working tree (generated index.rst files excluded)."""
    files = _git(root, "diff", "--name-only", ref, "--").split()
    files += _git(root, "ls-files", "--others", "--exclude-standard").split()
    hit: set[str] = set()
    for a in areas:
        d = Path(a["_source"]).resolve().relative_to(root.resolve()).as_posix() + "/"
        sub = [Path(b["_source"]).resolve().relative_to(root.resolve()).as_posix() + "/" for b in areas
               if b is not a and Path(b["_source"]).resolve().as_posix().startswith(Path(a["_source"]).resolve().as_posix() + "/")]
        if any(f.startswith(d) and f.endswith(".yaml") and not any(f.startswith(s) for s in sub) for f in files):
            hit.add(a["area"]["id"])
    return hit


def check_bumps(areas: list[dict[str, Any]], changed: set[str], base: dict[str, str]) -> list[str]:
    errs = []
    for a in areas:
        ar = a["area"]
        aid = ar["id"]
        if aid not in changed or aid not in base or not base[aid]:
            continue
        if parse_version(ar["version"]) <= parse_version(base[aid]):
            errs.append(f"{aid}: content changed but version {ar['version']} is not above {base[aid]} "
                        f"(run: qpm bump --process {aid} --level patch|minor|major)")
    return errs


def bump(areas: list[dict[str, Any]], process: str, level: str) -> tuple[Path, str, str]:
    a = next((x for x in areas if x["area"]["id"] == process), None)
    if not a:
        raise QpmError(f"unknown process '{process}'")
    f = _process_file(a)
    old = str(a["area"]["version"])
    new = bump_version(old, level)
    txt = f.read_text(encoding="utf-8")
    txt2 = re.sub(rf"^(  version: ){re.escape(old)}\s*$", rf"\g<1>{new}", txt, count=1, flags=re.M)
    if txt2 == txt:
        raise QpmError(f"{f}: version line not found")
    f.write_text(txt2, encoding="utf-8")
    return f, old, new


def review_due(areas: list[dict[str, Any]], dates: dict[str, dict[str, str]], today: dt.date,
               within_days: int = 30) -> list[dict[str, str]]:
    out = []
    for a in areas:
        ar = a["area"]
        d = dates.get(ar["id"])
        if not d:
            continue
        left = (dt.date.fromisoformat(d["review"]) - today).days
        if left <= within_days:
            out.append({"id": ar["id"], "title": ar["title"], "owner": ar["owner"], "review": d["review"],
                        "state": "overdue" if left < 0 else "due soon", "days": str(left)})
    return sorted(out, key=lambda x: int(x["days"]))
