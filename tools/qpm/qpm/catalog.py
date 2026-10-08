"""Technology-neutral process catalog (workflows, work products, roles, guidance).

Source: process/areas/*.yaml. Checks referential integrity against the catalog
itself plus the SCORE process-ID snapshot, enforces the WF/WP/RWE rules, and
renders Sphinx-needs RST (one adapter among possible others).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .model import QpmError, load_yaml

LIST_FIELDS = ("supported_by", "input", "output", "contains", "has")

LEVELS = {"organisation": "Organisation Level", "project": "Project Level"}
# Maturity scale ML0-ML4; colour = sphinx-design colour name used for cards and badges.
MATURITY = {
    "ML0": ("Not started", "secondary"),
    "ML1": ("Initial", "warning"),
    "ML2": ("Defined", "info"),
    "ML3": ("Applied", "primary"),
    "ML4": ("Optimised", "success"),
}
SCORE_PROCESS_URL = "https://eclipse-score.github.io/process_description/main/"


def load_catalog(area_dir: str | Path) -> list[dict[str, Any]]:
    areas = []
    for p in sorted(Path(area_dir).glob("*.yaml")):
        doc = load_yaml(p)
        doc["_source"] = str(p)
        areas.append(doc)
    if not areas:
        raise QpmError(f"no process areas in {area_dir}")
    return areas


def load_external_ids(path: str | Path) -> set[str]:
    return {l.strip() for l in Path(path).read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")}


def _ids(areas):
    for a in areas:
        for key in ("concepts", "roles", "templates", "workproducts", "workflows"):
            for item in a.get(key) or []:
                yield a, key, item["id"]


def check_catalog(areas: list[dict[str, Any]], external: set[str]) -> list[str]:
    """Return a list of problems (empty == OK)."""
    errs: list[str] = []
    local: dict[str, str] = {}
    for a, key, i in _ids(areas):
        if i in local:
            errs.append(f"duplicate id {i} ({local[i]} / {a['area']['id']})")
        if i in external:
            errs.append(f"{i} collides with a SCORE id - use the qx prefix")
        local[i] = a["area"]["id"]
    known = set(local) | external

    def ref(i, ctx, prefix):
        if not i.startswith(prefix):
            errs.append(f"{ctx}: '{i}' should start with '{prefix}'")
        elif i not in known:
            errs.append(f"{ctx}: unresolved reference '{i}'")

    produced: set[str] = set()
    used_roles: set[str] = set()
    for a in areas:
        aid = a["area"]["id"]
        ref(a["area"]["owner"], f"{aid}.owner", "rl__")
        if a["area"].get("level") not in LEVELS:
            errs.append(f"{aid}.level: must be one of {', '.join(LEVELS)}")
        if a["area"].get("maturity") not in MATURITY:
            errs.append(f"{aid}.maturity: must be one of {', '.join(MATURITY)}")
        for wp in a.get("workproducts") or []:
            ctx = f"{aid}.{wp['id']}"
            if not wp.get("purpose"):
                errs.append(f"{ctx}: work product needs a purpose")
            if wp.get("concept"):
                ref(wp["concept"], ctx, "doc_concept__")
            if wp.get("template"):
                ref(wp["template"], ctx, "gd_temp__")
            for c in wp.get("complies") or []:
                ref(c, ctx, "std_")
        for wf in a.get("workflows") or []:
            ctx = f"{aid}.{wf['id']}"
            ref(wf["responsible"], ctx, "rl__")
            ref(wf["approved_by"], ctx, "rl__")
            if wf["responsible"] == wf["approved_by"]:
                errs.append(f"{ctx}: responsible and approver must differ (four-eyes)")
            for r in wf.get("supported_by") or []:
                ref(r, ctx, "rl__")
            for i in wf.get("input") or []:
                ref(i, ctx, "wp__")
            if not wf.get("output"):
                errs.append(f"{ctx}: workflow must have at least one output WP")
            for o in wf.get("output") or []:
                ref(o, ctx, "wp__")
                produced.add(o)
            for g in wf.get("contains") or []:
                ref(g, ctx, "gd_")
            for h in wf.get("has") or []:
                ref(h, ctx, "doc_")
            roles = {wf["responsible"], wf["approved_by"], *(wf.get("supported_by") or [])}
            used_roles |= roles
            for n, act in enumerate(wf.get("activities") or [], 1):
                if act["by"] not in roles:
                    errs.append(f"{ctx} activity {n}: performer {act['by']} is not responsible/approver/supporter")
    for a in areas:
        for wp in a.get("workproducts") or []:
            if wp["id"] not in produced:
                errs.append(f"{a['area']['id']}.{wp['id']}: no workflow outputs this work product")
        for r in a.get("roles") or []:
            if r["id"] not in used_roles:
                errs.append(f"{a['area']['id']}.{r['id']}: role not used by any workflow")
    return errs


# ------------------------------------------------------------------ RST adapter
def _hdr(text: str, ch: str) -> str:
    return f"{text}\n{ch * len(text)}\n"


def _opt(name: str, val: Any) -> str:
    if not val:
        return ""
    if isinstance(val, list):
        val = ", ".join(val)
    return f"   :{name}: {val}\n"


def _indent(text: str, n: int = 3) -> str:
    pad = " " * n
    return "\n".join(pad + l if l.strip() else "" for l in text.strip().splitlines())


HEADER = (".. Generated by `qpm render-process` from {src} - DO NOT EDIT.\n"
          ".. Edit the YAML source and re-render; CI fails on drift.\n\n")


def render_area(a: dict[str, Any]) -> dict[str, str]:
    ar = a["area"]
    aid = ar["id"]
    src = Path(a["_source"]).as_posix().split("/process/", 1)[-1]
    src = f"process/{src}" if not src.startswith("process/") else src
    files: dict[str, str] = {}
    h = HEADER.format(src=src)

    # index
    idx = h + f".. _qx_area_{aid}:\n\n" + _hdr(ar["title"], "#") + "\n"
    idx += ar["purpose"].strip() + "\n\n"
    ml = ar["maturity"]
    idx += f"* **Level:** {LEVELS[ar['level']]}\n"
    idx += f"* **Maturity:** :bdg-{MATURITY[ml][1]}:`{ml} {MATURITY[ml][0]}`\n"
    idx += f"* **Tier:** {ar['tier']}\n* **Owner:** :need:`{ar['owner']}`\n"
    idx += f"* **Standards:** {', '.join(ar.get('standards') or [])}\n\n"
    for c in a.get("concepts") or []:
        idx += f".. doc_concept:: {c['title']}\n   :id: {c['id']}\n   :status: valid\n   :version: 1\n   :tags: {aid}\n\n"
        idx += _indent(c["body"]) + "\n\n"
    idx += ".. toctree::\n   :maxdepth: 1\n\n   workflows\n   workproducts\n   roles\n   guidance\n"
    files["index.rst"] = idx

    # workflows
    wf_txt = h + _hdr(f"{ar['title']} Workflows", "#") + "\n"
    wf_txt += (".. needflow::\n"
               f"   :filter: \"{aid}\" in tags and type in ['workflow', 'workproduct']\n"
               "   :link_types: input, output\n   :show_link_names:\n\n")
    for wf in a.get("workflows") or []:
        wf_txt += f".. workflow:: {wf['title']}\n   :id: {wf['id']}\n   :status: valid\n   :version: 1\n"
        wf_txt += f"   :tags: {aid}\n"
        for f in ("responsible", "approved_by") + LIST_FIELDS:
            wf_txt += _opt(f, wf.get(f))
        wf_txt += "\n"
        if wf.get("description"):
            wf_txt += _indent(wf["description"]) + "\n\n"
        if wf.get("activities"):
            wf_txt += "   .. list-table:: Activities (RWE)\n      :header-rows: 1\n      :widths: 5 70 25\n\n"
            wf_txt += "      * - #\n        - Activity\n        - Performed by\n"
            for n, act in enumerate(wf["activities"], 1):
                wf_txt += f"      * - {n}\n        - {act['step']}\n        - :need:`{act['by']}`\n"
            wf_txt += "\n"
    files["workflows.rst"] = wf_txt

    # work products (purpose / concept / template triad)
    wp_txt = h + _hdr(f"{ar['title']} Work Products", "#") + "\n"
    for wp in a.get("workproducts") or []:
        wp_txt += f".. workproduct:: {wp['title']}\n   :id: {wp['id']}\n   :status: valid\n   :version: 1\n"
        wp_txt += f"   :tags: {aid}\n"
        wp_txt += _opt("complies", wp.get("complies"))
        wp_txt += _opt("has", wp.get("concept"))
        wp_txt += _opt("contains", wp.get("template"))
        wp_txt += "\n   **Purpose:** " + " ".join(wp["purpose"].split()) + "\n\n"
    files["workproducts.rst"] = wp_txt

    # roles
    rl_txt = h + _hdr(f"{ar['title']} Roles", "#") + "\n"
    for r in a.get("roles") or []:
        rl_txt += f".. role:: {r['title']}\n   :id: {r['id']}\n   :status: valid\n   :version: 1\n   :tags: {aid}\n\n"
        rl_txt += _indent(r["description"]) + "\n\n"
    files["roles.rst"] = rl_txt

    # guidance / templates
    gd_txt = h + _hdr(f"{ar['title']} Guidance", "#") + "\n"
    for t in a.get("templates") or []:
        gd_txt += f".. gd_temp:: {t['title']}\n   :id: {t['id']}\n   :status: valid\n   :version: 1\n   :tags: {aid}\n\n"
        gd_txt += f"   Template file: ``{t['file']}``\n\n"
    files["guidance.rst"] = gd_txt
    return files


def _card(a: dict[str, Any]) -> str:
    ar = a["area"]
    ml = ar["maturity"]
    color = MATURITY[ml][1]
    purpose = " ".join(ar["purpose"].split())
    return (f"   .. grid-item-card:: {ar['title']}\n"
            f"      :link: qx_area_{ar['id']}\n      :link-type: ref\n"
            f"      :class-card: sd-border-{color}\n\n"
            f"      :bdg-{color}:`{ml} {MATURITY[ml][0]}`\n\n      {purpose}\n\n")


def _legend() -> str:
    t = (".. list-table::\n   :header-rows: 1\n   :widths: 20 80\n\n"
         "   * - Level\n     - Meaning\n")
    meaning = {
        "ML0": "Area identified; no process content yet.",
        "ML1": "Workflows, roles and work products are described; not yet applied by a project.",
        "ML2": "Description reviewed and released; templates and guidance complete.",
        "ML3": "Applied by at least one project with evidence of use.",
        "ML4": "Measured and improved from project feedback.",
    }
    for ml, (name, color) in MATURITY.items():
        t += f"   * - :bdg-{color}:`{ml} {name}`\n     - {meaning[ml]}\n"
    return t


def _level_page(level: str, areas: list[dict[str, Any]]) -> str:
    h = HEADER.format(src="process/areas/*.yaml (level: " + level + ")")
    title = LEVELS[level]
    out = h + f".. _qx_{level}_level:\n\n" + _hdr(title, "#") + "\n"
    if level == "organisation":
        out += (_hdr("Our goal", "=") + "\nOne set of company-wide processes that every Qorix project inherits, so a "
                "project only describes what is specific to its product.\n\n"
                + _hdr("What this level covers", "=") + "\nProcesses that apply to Qorix as a company, independent of "
                "any project: governance and compliance, shared infrastructure, training and validation "
                "support. Each one is a process area below.\n\n"
                + _hdr("How this section is modelled", "=") + "\nEvery area uses the same process model - workflows, "
                "work products, roles and guidance - authored as YAML in ``process/areas`` and rendered "
                "to these pages (see :ref:`qx_process_introduction`).\n\n"
                + _hdr("How this section relates to the project level", "=") + "\nProjects apply these processes "
                "and narrow them in their tailoring; they do not redefine them. See "
                ":ref:`qx_project_level`.\n\n")
    else:
        out += (_hdr("What belongs at this level, and what does not", "=") + "\nProcesses a project carries out "
                "for its own product and that no other project shares. Anything that applies to every "
                "project belongs at the :ref:`qx_organisation_level`; project-specific tools and "
                "solutions belong in the project's own documentation.\n\n"
                + _hdr("How this level relates to the two above it", "=") + "\nEclipse S-CORE is the base, the "
                "Qorix organisation level adds to it, and a project level area adds only what neither "
                "covers. Tailoring of inherited processes is recorded in the tailoring reports, not "
                "here.\n\n"
                + _hdr("How each area is modelled", "=") + "\nThe same model as the organisation level: set "
                "``level: project`` in the area's YAML file.\n\n")
    out += _hdr("Structure", "=") + "\n"
    if areas:
        out += ".. toctree::\n   :maxdepth: 1\n\n" + "".join(f"   {a['area']['id']}/index\n" for a in areas)
    else:
        out += "No process areas at this level yet.\n"
    if level == "organisation":
        out += "\n" + _hdr("Status of this section", "=") + "\n"
        out += "".join(f"* {a['area']['title']}: :bdg-{MATURITY[a['area']['maturity']][1]}:"
                       f"`{a['area']['maturity']} {MATURITY[a['area']['maturity']][0]}`\n" for a in areas)
    return out


def render_catalog(areas: list[dict[str, Any]]) -> dict[str, str]:
    """Return {relative_path: content} for docs/process_description/."""
    out: dict[str, str] = {}
    by_level: dict[str, list[dict[str, Any]]] = {lv: [] for lv in LEVELS}
    for a in areas:
        lv = a["area"]["level"]
        by_level[lv].append(a)
        for name, txt in render_area(a).items():
            out[f"{lv}_level/{a['area']['id']}/{name}"] = txt
    for lv, la in by_level.items():
        out[f"{lv}_level/index.rst"] = _level_page(lv, la)

    idx = HEADER.format(src="process/areas/*.yaml") + ".. _qx_process_areas:\n\n" + _hdr("Process Description", "#")
    idx += ("\nDescription of the Qorix processes that are not covered by the upstream Eclipse S-CORE process "
            "description. They are written solution-free and compliant with the applicable standards, so "
            "any Qorix project can apply them.\n\n"
            "The process model these areas follow - workflows, roles, work products, guidance and the "
            "reading order within an area - is explained in :ref:`qx_process_introduction`.\n\n"
            "The section has two layers: the :ref:`qx_organisation_level` holds what applies to Qorix as a "
            "company, the :ref:`qx_project_level` holds processes a project carries out for its own product. "
            "Everything else comes from the upstream S-CORE process description; each project's narrowing "
            "of it is in the tailoring reports.\n\n")
    idx += _hdr("Process area overview", "=") + ("\nEach card opens a process area; its colour shows the area's "
            "current maturity (legend below).\n\n")
    for lv, la in by_level.items():
        idx += _hdr(f"Qorix {LEVELS[lv]}", "-") + "\n"
        if la:
            idx += ".. grid:: 1 2 3 3\n   :gutter: 2\n\n" + "".join(_card(a) for a in la)
        else:
            idx += "No process areas at this level yet.\n\n"
    idx += (_hdr("Eclipse S-CORE", "-") + "\n.. grid:: 1 2 3 3\n   :gutter: 2\n\n"
            "   .. grid-item-card:: Eclipse S-CORE process areas\n"
            f"      :link: {SCORE_PROCESS_URL}\n\n"
            "      The generic, community-level process areas every Qorix process builds on.\n\n")
    idx += _hdr("Legend - maturity level", "-") + "\n" + _legend() + "\n"
    idx += ".. toctree::\n   :maxdepth: 2\n\n   introduction\n   organisation_level/index\n   project_level/index\n"
    out["index.rst"] = idx
    return out
