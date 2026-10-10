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

from qpm import catalog, registers, reports  # noqa: E402
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


# ---------------------------------------------------------------- scope replication, outcomes, capabilities, gates
def _errs(areas):
    return "\n".join(catalog.check_catalog(areas, catalog.load_standards(STANDARDS)))


def _area(areas, aid):
    return next(a for a in areas if a["area"]["id"] == aid)


def _wf(areas, wid):
    return next(w for a in areas for w in a["workflows"] if w["id"] == wid)


def _with_child(areas):
    """Add an in-memory FEAT assembly under change_management (none exists in the hub)."""
    areas.append({
        "area": dict(next(a for a in areas if a["area"]["id"] == "change_management")["area"],
                     id="cm_child", code="cmc", scope="FEAT", part_of="change_management"),
        "workflows": [dict(_wf(areas, "wf_qx_cm_manage_org_change"), id="wf_qx_cmc_child", activities=[], achieves=[],
                           gate=[], input=["wp_qx_cm_policies"], output=["wp_qx_cmc_out"])],
        "workproducts": [], "outcomes": [], "capabilities": [], "templates": [], "roles": [],
    })
    _wf(areas, "wf_qx_cm_manage_org_change")["input"].append("wp_qx_cmc_out")
    return areas


def test_hub_has_only_glob_assemblies():
    areas = catalog.load_catalog(ASSEMBLIES)
    assert {a["area"].get("scope") for a in areas} == {"GLOB"}
    assert _errs(areas) == ""


def test_part_of_needs_a_parent_one_scope_up():
    areas = _with_child(catalog.load_catalog(ASSEMBLIES))
    _area(areas, "cm_child")["area"]["part_of"] = None
    assert "must be part_of an assembly one scope up" in _errs(areas)
    areas = _with_child(catalog.load_catalog(ASSEMBLIES))
    _area(areas, "cm_child")["area"]["scope"] = "UNIT"
    assert "exactly one scope above" in _errs(areas)


def test_part_of_unknown_parent_and_glob_with_parent():
    areas = _with_child(catalog.load_catalog(ASSEMBLIES))
    _area(areas, "cm_child")["area"]["part_of"] = "nowhere"
    assert "unknown assembly" in _errs(areas)
    areas = catalog.load_catalog(ASSEMBLIES)
    _area(areas, "change_management")["area"]["part_of"] = "quality_assurance"
    assert "cannot be part_of" in _errs(areas)


def test_part_of_interface_must_be_consumed_by_parent():
    areas = _with_child(catalog.load_catalog(ASSEMBLIES))
    _wf(areas, "wf_qx_cm_manage_org_change")["input"].remove("wp_qx_cmc_out")
    assert "broken interface" in _errs(areas)


def test_part_of_cycle_is_detected():
    areas = _with_child(catalog.load_catalog(ASSEMBLIES))
    _area(areas, "change_management")["area"]["part_of"] = "cm_child"
    errs = _errs(areas)
    assert "cycle" in errs


def test_outcome_needs_workflow_capability_and_clause():
    areas = catalog.load_catalog(ASSEMBLIES)
    _wf(areas, "wf_qx_qa_internal_audit")["achieves"] = []
    _wf(areas, "wf_qx_qa_maintain_qms")["achieves"] = []
    assert "no workflow achieves this outcome" in _errs(areas)
    areas = catalog.load_catalog(ASSEMBLIES)
    _area(areas, "quality_assurance")["capabilities"] = []
    assert "no capability realizes this outcome" in _errs(areas)
    areas = catalog.load_catalog(ASSEMBLIES)
    _area(areas, "quality_assurance")["outcomes"][0]["complies"] = ["std_req_nothing"]
    assert "unresolved standard clause" in _errs(areas)


def test_capability_must_be_exercised_and_resolve():
    areas = catalog.load_catalog(ASSEMBLIES)
    for act in _wf(areas, "wf_qx_qa_internal_audit")["activities"]:
        act.pop("capability", None)
    assert "no workflow activity exercises this capability" in _errs(areas)
    areas = catalog.load_catalog(ASSEMBLIES)
    _wf(areas, "wf_qx_qa_internal_audit")["activities"][0]["capability"] = "cap_qx_qa_missing"
    assert "unresolved capability" in _errs(areas)


def test_gate_inputs_and_status_are_checked():
    areas = catalog.load_catalog(ASSEMBLIES)
    _wf(areas, "wf_qx_rel_release_org_baseline")["gate"].append({"wp": "wp_qx_gc_does_not_exist", "min_status": "approved"})
    assert "does not resolve" in _errs(areas)
    areas = catalog.load_catalog(ASSEMBLIES)
    _wf(areas, "wf_qx_rel_release_org_baseline")["gate"][0]["min_status"] = "finished"
    assert "min_status" in _errs(areas)
    areas = catalog.load_catalog(ASSEMBLIES)
    _wf(areas, "wf_qx_rel_release_org_baseline")["input"].remove("wp_qx_cfg_baseline")
    assert "must be an input" in _errs(areas)


def test_gate_blocks_approval_until_criteria_are_met():
    areas = catalog.load_catalog(ASSEMBLIES)
    _wf(areas, "wf_qx_rel_release_org_baseline")["status"] = "approved"
    assert "gate not met" in _errs(areas)
    for w in (w for a in areas for w in a["workproducts"] if w["id"] in {
            "wp_qx_cfg_baseline", "wp_qx_cm_change_package"}):
        w["status"] = "approved"
    next(w for a in areas for w in a["workproducts"] if w["id"] == "wp_qx_qa_audit_report")["status"] = "released"
    assert "gate not met" not in _errs(areas)


def test_overlay_adds_outcome_and_capability_types():
    m = compose([BASE, OVERLAY])
    assert {"outcome", "capability"} <= set(m["element_types"])
    assert "achieves" in m["element_types"]["workflow"]["relations"]
    assert m["element_types"]["capability"]["relations"]["realizes"]["targets"] == ["outcome"]


# ---------------------------------------------------------------- limits the docs engine enforces
def test_workflow_needs_an_input():
    areas = catalog.load_catalog(ASSEMBLIES)
    _wf(areas, "wf_qx_cfg_identify_items")["input"] = []
    assert "at least one input" in _errs(areas)


def test_id_length_is_limited():
    areas = catalog.load_catalog(ASSEMBLIES)
    a = _area(areas, "change_management")
    a["templates"][0]["id"] = "gd_temp_qx_cm_" + "x" * 40
    assert "the maximum is 45" in _errs(areas)


def test_iso15288_ids_match_the_standard_id_pattern():
    m = compose([BASE, OVERLAY])
    pat = m["element_types"]["std_req"]["attributes"]["id"]["pattern"]
    import re
    assert re.match(pat, "std_req_iso15288_635") and re.match(pat, "std_req_aspice_40_sup_10")
    assert re.match(m["element_types"]["std_wp"]["attributes"]["id"]["pattern"], "std_wp_iso15288_x")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))


# ---------------------------------------------------------------- objectives, policies, minimum definition
def _reg():
    areas = catalog.load_catalog(ASSEMBLIES)
    stds = catalog.load_standards(STANDARDS)
    objs, pols = registers.load_registers(STANDARDS)
    return copy.deepcopy(areas), stds, copy.deepcopy(objs), copy.deepcopy(pols)


def _rerrs(areas, stds, objs, pols):
    return "\n".join(registers.check_registers(objs, pols, areas, stds)[0])


def test_registers_are_consistent():
    areas, stds, objs, pols = _reg()
    assert objs and pols
    assert registers.check_registers(objs, pols, areas, stds)[0] == []


def test_objective_must_be_technology_neutral():
    areas, stds, objs, pols = _reg()
    objs[0]["statement"] = "Meet ASIL D under ISO 26262 using Bazel."
    e = _rerrs(areas, stds, objs, pols)
    assert "ASIL" in e and "ISO" in e and "Bazel" in e


def test_objective_needs_owner_measure_and_resolving_links():
    areas, stds, objs, pols = _reg()
    objs[0]["owner"] = "rl_qx_nobody"
    objs[0]["measure"] = ""
    objs[0]["drives"] = ["pol_qx_x_missing"]
    objs[0]["delivered_by"] = ["no_such_assembly"]
    e = _rerrs(areas, stds, objs, pols)
    for frag in ("unknown role", "missing measure", "unknown policy", "unknown assembly"):
        assert frag in e, frag


def test_project_objective_must_contribute_to_a_glob_objective():
    areas, stds, objs, pols = _reg()
    objs[0]["scope"] = "PROJECT"
    assert "must contribute_to" in _rerrs(areas, stds, objs, pols)
    objs[0]["contributes_to"] = [objs[1]["id"]]
    assert "must contribute_to" not in _rerrs(areas, stds, objs, pols)
    objs[2]["contributes_to"] = [objs[1]["id"]]
    assert "GLOB objective cannot contribute_to" in _rerrs(areas, stds, objs, pols)


def test_policy_needs_an_objective_and_resolving_links():
    areas, stds, objs, pols = _reg()
    for o in objs:
        o["drives"] = [d for d in o.get("drives") or [] if d != pols[0]["id"]]
    assert "no objective drives this policy" in _rerrs(areas, stds, objs, pols)
    pols[0]["drives"] = ["oc_qx_missing"]
    pols[0]["standards"] = ["std_req_nope"]
    pols[0]["work_product"] = "wp_qx_qa_qms_plan"
    e = _rerrs(areas, stds, objs, pols)
    assert "unresolved outcome" in e and "unresolved standard" in e and "belongs to" in e


def test_objective_without_policy_is_only_a_warning():
    areas, stds, objs, pols = _reg()
    errs, warns = registers.check_registers(objs, pols, areas, stds)
    assert errs == [] and any("drives no policy" in w for w in warns)


def test_minimum_definition_holds_for_every_assembly():
    assert registers.check_minimum(catalog.load_catalog(ASSEMBLIES)) == []


def test_minimum_definition_detects_gaps():
    areas = copy.deepcopy(catalog.load_catalog(ASSEMBLIES))
    a = _area(areas, "safety")
    a["outcomes"] = []
    a["capabilities"] = []
    for w in a["workflows"]:
        w["gate"] = []
    a["workproducts"][0].pop("complies", None)
    a["workproducts"][0].pop("internal", None)
    e = "\n".join(registers.check_minimum(areas))
    for frag in ("at least one outcome", "at least one capability", "at least one workflow with an entry gate", "complies clause or internal"):
        assert frag in e, frag


def test_rendered_registers_are_current():
    areas = catalog.load_catalog(ASSEMBLIES)
    stds = catalog.load_standards(STANDARDS)
    objs, pols = registers.load_registers(STANDARDS)
    files = registers.render_registers(objs, pols, areas, stds)
    assert set(files) == {"missions/objective_register.rst", "policies/register.rst"}
    for rel, txt in files.items():
        assert (ROOT / "prod" / rel).read_text(encoding="utf-8") == txt, rel


def test_overlay_adds_objective_and_policy_types():
    m = compose([BASE, OVERLAY])
    assert {"objective", "policy"} <= set(m["element_types"])
    assert m["element_types"]["objective"]["relations"]["drives"]["targets"] == ["policy"]


def test_overlay_widens_workproduct_rule_to_15288_and_aspice():
    m = compose([BASE, OVERLAY])
    alts = next(r for r in m["rules"] if r["id"] == "workproduct_aspice_40")["check"]["expect"]["or"]
    assert {"id contains aspice_40_iic", "id contains std_wp"} <= set(alts)
    assert {"id contains std_req_iso15288", "id contains std_req_aspice_40"} <= set(alts)


def test_every_workproduct_has_a_known_kind():
    from qpm import kinds
    areas = catalog.load_catalog(ASSEMBLIES)
    assert kinds.check_kinds(areas) == []
    cat, _ = kinds.load_kinds()
    used = {wp["kind"] for a in areas for wp in a.get("workproducts") or []}
    assert used <= set(cat) and len(cat) >= 10


def test_missing_or_unknown_kind_is_reported():
    from qpm import kinds
    areas = catalog.load_catalog(ASSEMBLIES)
    wp = areas[0]["workproducts"][0]
    wp["kind"] = "banana"
    assert any("unknown kind 'banana'" in e for e in kinds.check_kinds(areas))
    del wp["kind"]
    assert any("kind is required" in e for e in kinds.check_kinds(areas))


def test_overlay_adds_workproduct_kind_attribute():
    m = compose([BASE, OVERLAY])
    from qpm import kinds
    cat, _ = kinds.load_kinds()
    assert set(m["element_types"]["workproduct"]["attributes"]["kind"]["enum"]) == set(cat)
