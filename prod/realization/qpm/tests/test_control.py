"""Document control from git: dates, version bumps, review reminders."""
from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "prod" / "realization" / "qpm"))

from qpm import catalog, control  # noqa: E402
from qpm.model import QpmError  # noqa: E402


def _git(d, *a, when=None):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    if when:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = f"{when}T12:00:00"
    subprocess.run(["git", "-C", str(d), *a], check=True, capture_output=True, env=env)


def _proc(d, version, status="approved", eff="auto", rev="auto", cycle=""):
    f = Path(d) / "pa" / "process"
    f.mkdir(parents=True, exist_ok=True)
    (f / "process.yaml").write_text(
        f"assembly:\n  id: pa\n  status: {status}\n  version: {version}\n  effective_date: {eff}\n  review_date: {rev}\n{cycle}",
        encoding="utf-8")


def _area(d, **kw):
    ar = {"id": "pa", "title": "P A", "owner": "rl_x", "status": "approved", "version": "1.0.0",
          "effective_date": "auto", "review_date": "auto"}
    ar.update(kw)
    return {"area": ar, "_source": str(Path(d) / "pa")}


def test_version_arithmetic():
    assert control.bump_version("1.2.3", "patch") == "1.2.4"
    assert control.bump_version("1.2.3", "minor") == "1.3.0"
    assert control.bump_version("1.2.3", "major") == "2.0.0"
    with pytest.raises(QpmError):
        control.parse_version("1.0")
    with pytest.raises(QpmError):
        control.bump_version("1.0.0", "huge")


def test_add_months_clamps_to_month_end():
    assert control.add_months(dt.date(2026, 1, 31), 1) == dt.date(2026, 2, 28)
    assert control.add_months(dt.date(2026, 3, 16), 12) == dt.date(2027, 3, 16)


def test_dates_come_from_the_commit_that_introduced_the_version():
    with tempfile.TemporaryDirectory() as d:
        _git(d, "init", "-q")
        _proc(d, "1.0.0")
        _git(d, "add", "-A")
        _git(d, "commit", "-qm", "one", when="2026-03-16")
        (Path(d) / "pa" / "other.txt").write_text("x")
        _git(d, "add", "-A")
        _git(d, "commit", "-qm", "unrelated", when="2026-04-01")
        root = control.repo_root(d)
        got = control.derive([_area(d)], root)["pa"]
        assert got == {"effective": "2026-03-16", "review": "2027-03-16"}
        _proc(d, "1.1.0")
        _git(d, "add", "-A")
        _git(d, "commit", "-qm", "two", when="2026-05-01")
        assert control.derive([_area(d, version="1.1.0")], root)["pa"]["effective"] == "2026-05-01"
        assert control.derive([_area(d, version="1.1.0", review_cycle_months=6)], root)["pa"]["review"] == "2026-11-01"


def test_drafts_and_explicit_dates():
    with tempfile.TemporaryDirectory() as d:
        _git(d, "init", "-q")
        _proc(d, "1.0.0", status="draft")
        _git(d, "add", "-A")
        _git(d, "commit", "-qm", "one", when="2026-03-16")
        root = control.repo_root(d)
        assert control.derive([_area(d, status="draft")], root) == {}
        got = control.derive([_area(d, effective_date="2026-02-01", review_date="2026-08-01")], root)["pa"]
        assert got == {"effective": "2026-02-01", "review": "2026-08-01"}


def test_changed_process_needs_a_version_bump():
    with tempfile.TemporaryDirectory() as d:
        _git(d, "init", "-q")
        _proc(d, "1.0.0")
        _git(d, "add", "-A")
        _git(d, "commit", "-qm", "one", when="2026-03-16")
        root = control.repo_root(d)
        base = control.base_versions(root, Path(d), "HEAD")
        assert base == {"pa": "1.0.0"}
        _proc(d, "1.0.0", eff="2026-03-16")          # content change, same version
        a = [_area(d)]
        changed = control.changed_assemblies(root, a, "HEAD")
        assert changed == {"pa"}
        assert "not above 1.0.0" in control.check_bumps(a, changed, base)[0]
        assert control.check_bumps([_area(d, version="1.0.1")], changed, base) == []
        assert control.check_bumps(a, changed, {}) == []             # new process: nothing to compare
        f, old, new = control.bump(a, "pa", "minor")
        assert (old, new) == ("1.0.0", "1.1.0") and "version: 1.1.0" in f.read_text()


def test_review_reminders_sorted_by_urgency():
    areas = [_area("/x", id="a", title="A"), _area("/x", id="b", title="B"), _area("/x", id="c", title="C")]
    dates = {"a": {"effective": "2025-01-01", "review": "2026-09-01"},
             "b": {"effective": "2025-11-01", "review": "2026-10-20"},
             "c": {"effective": "2026-01-01", "review": "2027-01-01"}}
    due = control.review_due(areas, dates, dt.date(2026, 10, 11), 30)
    assert [(x["id"], x["state"]) for x in due] == [("a", "overdue"), ("b", "due soon")]


def test_page_shows_git_dates_when_given_and_a_clear_placeholder_otherwise():
    areas = catalog.load_catalog(str(ROOT / "prod/assemblies"))
    a = areas[0]
    a["area"]["status"] = "approved"
    aid = a["area"]["id"]
    plain = catalog.render_area(a, areas)["process/index.rst"]
    assert "auto (from git)" in plain
    filled = catalog.render_area(a, areas, {aid: {"effective": "2026-03-16", "review": "2027-03-16"}})["process/index.rst"]
    assert "2026-03-16" in filled and "2027-03-16" in filled
    a["area"]["status"] = "draft"
    assert "TBD until approved" in catalog.render_area(a, areas)["process/index.rst"]
