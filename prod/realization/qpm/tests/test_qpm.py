"""qpm self-tests. Run: `bazel test //prod/realization/qpm:qpm_test` or `pytest prod/realization/qpm/tests`."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "prod" / "realization" / "qpm"))

from qpm import catalog, reports  # noqa: E402
from qpm.adapters import sphinx_needs  # noqa: E402
from qpm.compose import compose  # noqa: E402
from qpm.model import QpmError, dump_yaml, load_yaml  # noqa: E402

BASE = ROOT / "prod/concepts/tiers/00_qorix_base/qorix_base.qpm.yaml"
OVERLAY = ROOT / "prod/concepts/tiers/10_qorix/qorix_overlay.qpm.yaml"
STANDARDS = ROOT / "needs/standards.yaml"
ASSEMBLIES = ROOT / "prod/assemblies"
PERF = ROOT / "dist/performance/tailoring.qpm.yaml"
CP = ROOT / "dist/products_cp/tailoring.qpm.yaml"


def _tmp_tier(doc) -> Path:
    f = Path(tempfile.mkdtemp()) / "t.qpm.yaml"
    dump_yaml(doc, f)
    return f


# ---------------------------------------------------------------- technology independence
def test_base_emits_complete_metamodel():
    """compose(base) -> emit(sphinx-needs) loses nothing: every type and rule is emitted."""
    base = compose([BASE])
    emitted, unsupported = sphinx_needs.emit(base)
    assert set(emitted["needs_types"]) == set(base["element_types"])
    assert len(emitted["graph_checks"]) + len(unsupported) == len(base["rules"])


# ---------------------------------------------------------------- tiering
def test_overlay_is_superset_of_base():
    m = compose([BASE, OVERLAY])
    assert m["element_types"]["feat_req"]["attributes"]["safety"]["enum"] == ["QM", "ASIL_A", "ASIL_B", "ASIL_C", "ASIL_D"]
    assert m["element_types"]["feat_req"]["attributes"]["cal"]["required"] is False
    base = compose([BASE])
    for name, et in base["element_types"].items():
        for a, d in (et.get("attributes") or {}).items():
            got = m["element_types"][name]["attributes"][a]
            assert got["required"] == d["required"]
            if "enum" in d:
                assert set(d["enum"]) <= set(got["enum"])


def test_project_ceilings():
    perf = compose([BASE, OVERLAY, PERF])["element_types"]
    assert perf["comp_req"]["attributes"]["safety"]["enum"] == ["QM", "ASIL_A", "ASIL_B"]
    assert "gc_finding" not in perf
    cp = compose([BASE, OVERLAY, CP])["element_types"]
    assert cp["comp_req"]["attributes"]["safety"]["enum"][-1] == "ASIL_D"
    assert cp["comp_req"]["attributes"]["cal"] == {
        "required": True, "enum": ["CAL1", "CAL2", "CAL3"],
        "description": "Cybersecurity Assurance Level (ISO/SAE 21434 Annex E)"}


def test_overlay_cannot_add_required_attribute():
    doc = load_yaml(OVERLAY)
    doc["operations"] = [{"op": "extend_element_type", "name": "feat_req",
                          "add_attributes": {"x": {"required": True, "pattern": ".*"}}}]
    with pytest.raises(QpmError, match="superset"):
        compose([BASE, _tmp_tier(doc)])


def test_overlay_cannot_narrow():
    doc = load_yaml(OVERLAY)
    doc["operations"] = [{"op": "restrict_enum", "attribute": "safety", "values": ["QM"]}]
    with pytest.raises(QpmError, match="not permitted"):
        compose([BASE, _tmp_tier(doc)])


def test_project_cannot_widen_and_needs_rationale():
    doc = load_yaml(PERF)
    doc["operations"] = [{"op": "restrict_enum", "attribute": "safety", "values": ["QM", "ASIL_X"], "rationale": "x"}]
    with pytest.raises(QpmError, match="only narrow"):
        compose([BASE, OVERLAY, _tmp_tier(doc)])
    doc["operations"] = [{"op": "require_attribute", "attribute": "cal", "types": ["feat_req"]}]
    with pytest.raises(QpmError, match="rationale"):
        compose([BASE, OVERLAY, _tmp_tier(doc)])


def test_chain_order_enforced():
    with pytest.raises(QpmError, match="must extend"):
        compose([BASE, PERF])
    with pytest.raises(QpmError, match="first tier"):
        compose([OVERLAY])


def test_schema_rejects_unknown_keys():
    doc = copy.deepcopy(load_yaml(PERF))
    doc["bogus"] = 1
    with pytest.raises(QpmError, match="schema"):
        compose([BASE, OVERLAY, _tmp_tier(doc)])


# ---------------------------------------------------------------- adapter output
def test_emitted_metamodel_contains_overlay():
    out, unsupported = sphinx_needs.emit(compose([BASE, OVERLAY, CP]))
    fr = out["needs_types"]["feat_req"]
    assert fr["mandatory_options"]["safety"] == "^(QM|ASIL_A|ASIL_B|ASIL_C|ASIL_D)$"
    assert fr["mandatory_options"]["cal"] == "^(CAL1|CAL2|CAL3)$"
    assert out["needs_types"]["workproduct"]["optional_links"]["has"] == "doc_concept"
    assert "qx_arch_asil_d_fulfilment" in out["graph_checks"]
    assert [r["id"] for r in unsupported] == ["qx_sec_cal_required"]


def test_lint_needs():
    m = compose([BASE, OVERLAY, CP])
    needs = {"current_version": "1", "versions": {"1": {"needs": {
        "feat_req_a_ok": {"id": "feat_req_a_ok", "type": "feat_req", "security": "YES", "cal": "CAL2"},
        "feat_req_a_bad": {"id": "feat_req_a_bad", "type": "feat_req", "security": "YES"},
        "feat_req_a_nosec": {"id": "feat_req_a_nosec", "type": "feat_req", "security": "NO"},
    }}}}
    f = Path(tempfile.mkdtemp()) / "needs.json"
    f.write_text(json.dumps(needs))
    problems = reports.lint_needs(m, f)
    assert len(problems) == 1 and problems[0].startswith("feat_req_a_bad")


# ---------------------------------------------------------------- process catalog
def test_catalog_is_consistent():
    areas = catalog.load_catalog(ASSEMBLIES)
    assert catalog.check_catalog(areas, catalog.load_standards(STANDARDS)) == []


def test_catalog_detects_violations():
    areas = catalog.load_catalog(ASSEMBLIES)
    wf = next(x for x in areas if x["workflows"])["workflows"][0]
    wf["approved_by"] = wf["responsible"]
    wf["input"].append("wp_qx_gc_does_not_exist")
    wf["activities"].append({"step": "x", "by": "rl_qx_trn_training_coordinator"})
    errs = "\n".join(catalog.check_catalog(areas, catalog.load_standards(STANDARDS)))
    assert "four-eyes" in errs and "unresolved" in errs and "performer" in errs


def test_catalog_rejects_bad_status_and_cluster():
    areas = catalog.load_catalog(ASSEMBLIES)
    areas[0]["area"]["status"] = "unknown"
    areas[0]["area"]["cluster"] = "nowhere"
    errs = "\n".join(catalog.check_catalog(areas, catalog.load_standards(STANDARDS)))
    assert ".status:" in errs and ".cluster:" in errs


def test_external_work_products_are_not_produced_here():
    areas = catalog.load_catalog(ASSEMBLIES)
    wp = next(w for a in areas for w in a.get("workproducts") or [] if w.get("origin") == "external")
    next(x for x in areas if x["workflows"])["workflows"][0]["output"].append(wp["id"])
    errs = "\n".join(catalog.check_catalog(areas, catalog.load_standards(STANDARDS)))
    assert "origin 'external'" in errs


def test_assembly_classification_is_checked():
    areas = catalog.load_catalog(ASSEMBLIES)
    areas[0]["area"]["enabler"] = "XYZ"
    errs = "\n".join(catalog.check_catalog(areas, catalog.load_standards(STANDARDS)))
    assert ".enabler:" in errs


def test_double_underscore_ids_are_rejected():
    areas = catalog.load_catalog(ASSEMBLIES)
    a = next(x for x in areas if x["roles"])
    a["roles"][0]["id"] = "rl_qx_" + a["area"]["code"] + "__bad"
    errs = "\n".join(catalog.check_catalog(areas, catalog.load_standards(STANDARDS)))
    assert "double underscore" in errs


def test_id_scheme_is_enforced():
    areas = catalog.load_catalog(ASSEMBLIES)
    a = next(x for x in areas if x["roles"])
    a["roles"][0]["id"] = "rl_qx_other_bad"
    errs = "\n".join(catalog.check_catalog(areas, catalog.load_standards(STANDARDS)))
    assert "scheme <type>_qx_<code>_<name>" in errs


def test_no_double_underscore_in_composed_model():
    m = compose([BASE, OVERLAY, CP])
    emitted, _ = sphinx_needs.emit(m)
    assert "__" not in json.dumps(emitted)


def test_rendered_rst_is_current():
    areas = catalog.load_catalog(ASSEMBLIES)
    for rel, txt in catalog.render_catalog(areas, catalog.load_standards(STANDARDS)).items():
        assert (ROOT / "prod" / rel).read_text(encoding="utf-8") == txt, rel


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
