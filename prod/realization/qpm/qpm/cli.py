"""qpm - Qorix Process Metamodel command line.

    qpm compose          --tier F [--tier F ...] --out-dir D
    qpm check-process    --assemblies D --standards F
    qpm render-process   --assemblies D --standards F --out-dir D [--check]
    qpm lint-needs       --tier F [...] --needs-json F
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import catalog, registers, reports
from .adapters import sphinx_needs
from .compose import compose
from .model import QpmError, dump_json, dump_yaml, load_yaml


def _write_tree(files: dict[str, str], out_dir: Path, check: bool) -> int:
    drift = []
    for rel, txt in files.items():
        p = out_dir / rel
        if check:
            if not p.exists() or p.read_text(encoding="utf-8") != txt:
                drift.append(rel)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(txt, encoding="utf-8")
    if drift:
        print("generated files out of date (run qpm render-process):\n  " + "\n  ".join(drift), file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="qpm", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("compose")
    s.add_argument("--tier", action="append", required=True)
    s.add_argument("--out-dir", required=True)

    for name in ("check-process", "render-process"):
        s = sub.add_parser(name)
        s.add_argument("--assemblies", dest="areas", required=True)
        s.add_argument("--standards", required=True)
        if name == "render-process":
            s.add_argument("--out-dir", required=True)
            s.add_argument("--check", action="store_true")

    s = sub.add_parser("lint-needs")
    s.add_argument("--tier", action="append", required=True)
    s.add_argument("--needs-json", required=True)

    a = ap.parse_args(argv)
    try:
        if a.cmd == "compose":
            m = compose(a.tier)
            out = Path(a.out_dir)
            metamodel, unsupported = sphinx_needs.emit(m, legacy_graph_checks=True)
            dump_json(m, out / "resolved_model.json")
            dump_yaml(metamodel, out / "metamodel.yaml")
            (out / "tailoring_report.rst").write_text(reports.tailoring_report_rst(m, unsupported), encoding="utf-8")
            print(f"composed {' -> '.join(t['id'] for t in m['tiers'])}: "
                  f"{len(m['element_types'])} types, {len(m['rules'])} rules ({len(unsupported)} via lint-needs)")
        elif a.cmd in ("check-process", "render-process"):
            areas = catalog.load_catalog(a.areas)
            stds = catalog.load_standards(a.standards)
            errs = catalog.check_catalog(areas, stds)
            objs, pols = registers.load_registers(a.standards)
            rerrs, rwarns = registers.check_registers(objs, pols, areas, stds)
            errs += rerrs + registers.check_minimum(areas)
            for w in rwarns:
                print(f"warning: {w}", file=sys.stderr)
            if errs:
                print("process catalog errors:\n  " + "\n  ".join(errs), file=sys.stderr)
                return 1
            if a.cmd == "check-process":
                print(f"process catalog OK ({len(areas)} assemblies)")
                return 0
            files = catalog.render_catalog(areas, stds)
            files.update(registers.render_registers(objs, pols, areas, stds))
            return _write_tree(files, Path(a.out_dir), a.check)
        elif a.cmd == "lint-needs":
            problems = reports.lint_needs(compose(a.tier), a.needs_json)
            for p in problems:
                print(p)
            return 1 if problems else 0
    except QpmError as e:
        print(f"qpm: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
