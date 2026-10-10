"""Technology-neutral process catalog (workflows, work products, roles, guidance).

Source: prod/assemblies/<cluster>/<process>/<subcomponent>/*.yaml plus needs/standards.yaml. Checks referential
integrity within the catalog, enforces the WF/WP/RWE rules, and renders
Sphinx-needs RST (one adapter among possible others).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .model import QpmError, load_yaml

LIST_FIELDS = ("supported_by", "input", "output", "achieves", "contains", "has")

# Lifecycle of assemblies and their elements; value = badge colour.
STATUS = {"draft": "secondary", "proposed": "info", "approved": "primary", "released": "success",
          "deprecated": "warning", "retired": "dark", "valid": "success"}
CLUSTERS = {"compliance": "Compliance", "engineering": "Engineering", "build": "Build",
            "testing": "Testing", "organisation": "Organisation", "common": "Common"}


# Optional grouping inside a cluster page: process.yaml `assembly.group` must be one of these, in this order.
CLUSTER_GROUPS = {"engineering": ["Plan and control", "Requirements and verification", "Control and release",
                                  "Assure and improve"]}


# Assembly layout: prod/assemblies/<cluster>/<process>/<subcomponent>/<file>.yaml
# (the five subcomponents of every process; each also holds its generated index.rst)
MAX_ID_LENGTH = 45   # the docs engine's metamodel limit on need ids
ASSEMBLY_FILES = {
    "process/process.yaml": None,           # assembly header, getting_started, concepts
    "workflows/workflows.yaml": "workflows",
    "work_products/work_products.yaml": "work_products",
    "roles/roles.yaml": "roles",
    "templates/templates.yaml": "templates",
}
SUBCOMPONENTS = ("process", "workflows", "work_products", "roles", "templates")
ENABLERS = {"PRD", "TST", "BLD", "DOC", "SAF", "SEC", "-"}
SCOPES = {"GLOB", "FEAT", "COMP", "UNIT", "-"}
LAYERS = {"INT", "REQ", "ARC", "DES", "IMP", "-"}
# ID scheme: <type>_qx_<assembly code>_<name>  - never a double underscore
TYPE_PREFIX = {"workflows": "wf_", "work_products": "wp_", "roles": "rl_", "templates": "gd_temp_", "concepts": "doc_concept_",
               "outcomes": "oc_", "capabilities": "cap_"}
# Scope axis (rank = depth of the composition): a process at one scope is part_of the same process one scope up.
SCOPE_RANK = {"GLOB": 0, "FEAT": 1, "COMP": 2, "UNIT": 3}
# Status a gate work product may hold, lowest first. deprecated / retired never satisfy a gate.
GATE_RANK = {"draft": 0, "proposed": 1, "approved": 2, "released": 3}


def load_catalog(prod_dir: str | Path) -> list[dict[str, Any]]:
    """Load every assembly folder <cluster>/<process>/ below ``prod_dir`` into one catalog entry each."""
    areas = []
    for f in sorted(Path(prod_dir).glob("*/*/process/process.yaml")):
        d = f.parent.parent
        doc: dict[str, Any] = {"_source": d.as_posix(), "_path": d.relative_to(prod_dir).as_posix()}
        for rel, key in ASSEMBLY_FILES.items():
            g = d / rel
            if not g.is_file():
                raise QpmError(f"{d}: missing {rel}")
            data = load_yaml(g) or {}
            if key is None:
                doc["area"] = data.get("assembly") or {}
                doc["concepts"] = data.get("concepts") or []
                doc["getting_started"] = data.get("getting_started")
                doc["outcomes"] = data.get("outcomes") or []
                doc["capabilities"] = data.get("capabilities") or []
            else:
                doc["workproducts" if key == "work_products" else key] = data.get(key) or []
        ar = doc["area"]
        if ar.get("id") != d.name or ar.get("cluster") != d.parent.name:
            raise QpmError(f"{d}: process.yaml id/cluster must equal the folder names ({d.parent.name}/{d.name})")
        areas.append(doc)
    if not areas:
        raise QpmError(f"no assemblies in {prod_dir}")
    return areas


def load_standards(path: str | Path) -> list[dict[str, Any]]:
    """Qorix standards catalogue: the standard clauses work products comply with."""
    doc = load_yaml(path)
    return list(doc.get("standards") or [])


def _ids(areas):
    for a in areas:
        for key in ("concepts", "outcomes", "capabilities", "roles", "templates", "workproducts", "workflows"):
            for item in a.get(key) or []:
                yield a, key, item["id"]


def check_catalog(areas: list[dict[str, Any]], standards: list[dict[str, Any]]) -> list[str]:
    """Return a list of problems (empty == OK)."""
    errs: list[str] = []
    local: dict[str, str] = {}
    for st in standards:
        if not st["id"].startswith(("std_req_", "std_wp_")):
            errs.append(f"standards.{st['id']}: id must start with std_req_ or std_wp_")
        if st["id"] in local:
            errs.append(f"duplicate id {st['id']} (standards)")
        local[st["id"]] = "standards"
    for a, key, i in _ids(areas):
        if i in local:
            errs.append(f"duplicate id {i} ({local[i]} / {a['area']['id']})")
        local[i] = a["area"]["id"]
        want = TYPE_PREFIX["work_products" if key == "workproducts" else key] + f"qx_{a['area'].get('code')}_"
        if not i.startswith(want):
            errs.append(f"{a['area']['id']}.{i}: id must start with '{want}' (scheme <type>_qx_<code>_<name>)")
    for i in local:
        if "__" in i:
            errs.append(f"{i}: double underscore is not allowed in ids")
        if len(i) > MAX_ID_LENGTH:
            errs.append(f"{i}: id is {len(i)} characters, the maximum is {MAX_ID_LENGTH}")
    known = set(local)

    def ref(i, ctx, prefix):
        if not i.startswith(prefix):
            errs.append(f"{ctx}: '{i}' should start with '{prefix}'")
        elif i not in known:
            errs.append(f"{ctx}: unresolved reference '{i}'")

    produced: set[str] = set()
    used_roles: set[str] = set()
    owners = {a["area"]["owner"] for a in areas}
    for a in areas:
        aid = a["area"]["id"]
        ref(a["area"]["owner"], f"{aid}.owner", "rl_")
        if a["area"].get("status") not in STATUS:
            errs.append(f"{aid}.status: must be one of {', '.join(STATUS)}")
        if a["area"].get("cluster") not in CLUSTERS:
            errs.append(f"{aid}.cluster: must be one of {', '.join(CLUSTERS)}")
        grp, allowed = a["area"].get("group"), CLUSTER_GROUPS.get(a["area"].get("cluster"))
        if allowed and grp not in allowed:
            errs.append(f"{aid}.group: must be one of {', '.join(allowed)}")
        if grp and not allowed:
            errs.append(f"{aid}.group: cluster '{a['area'].get('cluster')}' defines no groups")
        for key, allowed in (("enabler", ENABLERS), ("scope", SCOPES), ("layer", LAYERS)):
            if a["area"].get(key) not in allowed:
                errs.append(f"{aid}.{key}: must be one of {', '.join(sorted(allowed))}")
        for wp in a.get("workproducts") or []:
            ctx = f"{aid}.{wp['id']}"
            if not wp.get("purpose"):
                errs.append(f"{ctx}: work product needs a purpose")
            if wp.get("concept"):
                ref(wp["concept"], ctx, "doc_concept_")
            if wp.get("template"):
                ref(wp["template"], ctx, "gd_temp_")
            for c in wp.get("complies") or []:
                ref(c, ctx, "std_")
        for wf in a.get("workflows") or []:
            ctx = f"{aid}.{wf['id']}"
            ref(wf["responsible"], ctx, "rl_")
            ref(wf["approved_by"], ctx, "rl_")
            if wf["responsible"] == wf["approved_by"]:
                errs.append(f"{ctx}: responsible and approver must differ (four-eyes)")
            for r in wf.get("supported_by") or []:
                ref(r, ctx, "rl_")
            for i in wf.get("input") or []:
                ref(i, ctx, "wp_")
            if not wf.get("input"):
                errs.append(f"{ctx}: workflow must have at least one input WP")
            if not wf.get("output"):
                errs.append(f"{ctx}: workflow must have at least one output WP")
            for o in wf.get("output") or []:
                ref(o, ctx, "wp_")
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
            if wp.get("origin") == "external":
                if wp["id"] in produced:
                    errs.append(f"{a['area']['id']}.{wp['id']}: origin 'external' but a Qorix workflow outputs it")
                continue
            if wp["id"] not in produced:
                errs.append(f"{a['area']['id']}.{wp['id']}: no workflow outputs this work product")
        for r in a.get("roles") or []:
            if r["id"] not in used_roles and r["id"] not in owners:
                errs.append(f"{a['area']['id']}.{r['id']}: role not used by any workflow")
    errs += _check_layers(areas, known)
    return errs


def _check_layers(areas: list[dict[str, Any]], known: set[str]) -> list[str]:
    """Replication across scopes (part_of), outcomes, capabilities and gates."""
    errs: list[str] = []
    by_id = {a["area"]["id"]: a for a in areas}
    wps = {w["id"]: w for a in areas for w in a.get("workproducts") or []}
    outcomes = {o["id"]: o for a in areas for o in a.get("outcomes") or []}
    caps = {c["id"]: c for a in areas for c in a.get("capabilities") or []}

    # --- composition: part_of one scope up, interface between child and parent, no cycle
    for a in areas:
        ar = a["area"]
        aid, scope, parent = ar["id"], ar.get("scope", "-"), ar.get("part_of")
        if scope in SCOPE_RANK and scope != "GLOB" and not parent:
            errs.append(f"{aid}.part_of: a {scope} assembly must be part_of an assembly one scope up")
        if not parent:
            continue
        if scope not in SCOPE_RANK or scope == "GLOB":
            errs.append(f"{aid}.part_of: a '{scope}' assembly cannot be part_of another assembly")
            continue
        p = by_id.get(parent)
        if p is None:
            errs.append(f"{aid}.part_of: unknown assembly '{parent}'")
            continue
        pscope = p["area"].get("scope", "-")
        if SCOPE_RANK.get(pscope, -9) != SCOPE_RANK[scope] - 1:
            errs.append(f"{aid}.part_of: parent '{parent}' is {pscope}; it must be exactly one scope above {scope}")
        outs = {o for wf in a.get("workflows") or [] for o in wf.get("output") or []}
        ins = {i for wf in p.get("workflows") or [] for i in wf.get("input") or []}
        if not outs & ins:
            errs.append(f"{aid}.part_of: no output work product of this assembly is an input of '{parent}' (broken interface)")
    for a in areas:
        seen: set[str] = set()
        cur = a["area"]["id"]
        while cur in by_id and by_id[cur]["area"].get("part_of"):
            if cur in seen:
                errs.append(f"{a['area']['id']}.part_of: composition cycle through '{cur}'")
                break
            seen.add(cur)
            cur = by_id[cur]["area"]["part_of"]

    # --- outcomes and capabilities
    achieved: set[str] = set()
    used: set[str] = set()
    for a in areas:
        aid = a["area"]["id"]
        for o in a.get("outcomes") or []:
            if not o.get("statement"):
                errs.append(f"{aid}.{o['id']}: outcome needs a statement")
            for c in o.get("complies") or []:
                if not c.startswith("std_") or c not in known:
                    errs.append(f"{aid}.{o['id']}: unresolved standard clause '{c}'")
        for c in a.get("capabilities") or []:
            if not c.get("description"):
                errs.append(f"{aid}.{c['id']}: capability needs a description")
            if not c.get("realizes"):
                errs.append(f"{aid}.{c['id']}: capability must realize at least one outcome")
            for r in c.get("realizes") or []:
                if r not in outcomes:
                    errs.append(f"{aid}.{c['id']}: unresolved outcome '{r}'")
        for wf in a.get("workflows") or []:
            ctx = f"{aid}.{wf['id']}"
            for oc in wf.get("achieves") or []:
                if oc in outcomes:
                    achieved.add(oc)
                else:
                    errs.append(f"{ctx}: unresolved outcome '{oc}'")
            for n, act in enumerate(wf.get("activities") or [], 1):
                cap = act.get("capability")
                if cap:
                    if cap in caps:
                        used.add(cap)
                    else:
                        errs.append(f"{ctx} activity {n}: unresolved capability '{cap}'")
            for g in wf.get("gate") or []:
                w, m = g.get("wp"), g.get("min_status")
                if w not in wps:
                    errs.append(f"{ctx}: gate work product '{w}' does not resolve")
                    continue
                if w not in (wf.get("input") or []):
                    errs.append(f"{ctx}: gate work product '{w}' must be an input of the workflow")
                if m not in GATE_RANK:
                    errs.append(f"{ctx}: gate min_status '{m}' must be one of {', '.join(GATE_RANK)}")
                elif wf.get("status") in ("approved", "released"):
                    if GATE_RANK.get(wps[w].get("status"), -1) < GATE_RANK[m]:
                        errs.append(f"{ctx}: gate not met - '{w}' is {wps[w].get('status')}, needs at least {m}")
    for oc in outcomes:
        if oc not in achieved:
            errs.append(f"{oc}: no workflow achieves this outcome")
        if not any(oc in (c.get("realizes") or []) for c in caps.values()):
            errs.append(f"{oc}: no capability realizes this outcome")
    for cap in caps:
        if cap not in used:
            errs.append(f"{cap}: no workflow activity exercises this capability")
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


def _md(text: str) -> str:
    """Convert the Markdown subset used in process texts (inline code, pipe tables) to RST."""
    import re
    lines, out, i = text.strip().splitlines(), [], 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                if not re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            if out and out[-1] != "":
                out.append("")
            out += [".. list-table::", "   :header-rows: 1", ""]
            for row in rows:
                out.append("   * - " + row[0])
                out += ["     - " + c for c in row[1:]]
            out.append("")
            continue
        out.append(lines[i])
        i += 1
    txt = "\n".join(out)
    return re.sub(r"(?<!`)`([^`\n]+)`(?!`)", r"``\1``", txt)


def _need(kind: str, title: str, nid: str, status: str, tag: str, opts: str = "") -> str:
    return (f".. {kind}:: {title}\n   :id: {nid}\n   :status: {status}\n   :version: 1\n"
            f"   :tags: {tag}\n{opts}\n")


def render_area(a: dict[str, Any], areas: list[dict[str, Any]] | None = None) -> dict[str, str]:
    """Render one assembly into its five subcomponent pages (<sub>/index.rst)."""
    ar = a["area"]
    aid, path = ar["id"], a["_path"]
    h = HEADER.format(src=f"prod/assemblies/{path}/<subcomponent>/*.yaml")
    files: dict[str, str] = {}

    # process: identity, classification, getting started, concepts
    idx = h + f".. _qx_assembly_{aid}:\n\n" + _hdr(ar["title"], "#") + "\n"
    idx += " ".join(ar["purpose"].split()) + "\n\n"
    idx += f"* **Assembly:** {CLUSTERS[ar['cluster']]} / {ar['title']} (code ``{ar['code']}``)\n"
    idx += f"* **Status:** :bdg-{STATUS[ar['status']]}:`{ar['status']}`\n"
    idx += (f"* **Enabler / Scope / Layer:** {ar.get('enabler', '-')} / {ar.get('scope', '-')} / "
            f"{ar.get('layer', '-')}\n")
    if ar.get("part_of"):
        idx += f"* **Part of:** :ref:`qx_assembly_{ar['part_of']}`\n"
    kids = [b["area"]["id"] for b in areas or [] if b["area"].get("part_of") == aid]
    if kids:
        idx += "* **Parts:** " + ", ".join(f":ref:`qx_assembly_{k}`" for k in kids) + "\n"
    idx += f"* **Owner:** :need:`{ar['owner']}`\n"
    idx += f"* **Standards:** {', '.join(ar.get('standards') or [])}\n\n"
    if a.get("getting_started"):
        idx += _need("doc_getstrt", f"Getting started on {ar['title']}",
                     f"doc_getstrt_qx_{ar['code']}_getting_started", "valid", aid)
        idx += _indent(_md(a["getting_started"])) + "\n\n"
    for c in a.get("concepts") or []:
        idx += _need("doc_concept", c["title"], c["id"], c.get("status", "valid"), aid)
        idx += _indent(_md(c["body"])) + "\n\n"
    for o in a.get("outcomes") or []:
        idx += _need("outcome", o["title"], o["id"], o.get("status", "draft"), aid, _opt("complies", o.get("complies")))
        idx += _indent(_md(o["statement"])) + "\n\n"
    for c in a.get("capabilities") or []:
        idx += _need("capability", c["title"], c["id"], c.get("status", "draft"), aid, _opt("realizes", c.get("realizes")))
        idx += _indent(_md(c["description"])) + "\n\n"
    idx += ".. toctree::\n   :maxdepth: 1\n\n" + "".join(
        f"   /assemblies/{path}/{sub}/index\n" for sub in SUBCOMPONENTS[1:])
    files["process/index.rst"] = idx

    # workflows
    wf_txt = h + _hdr(f"{ar['title']} Workflows", "#") + "\n"
    if not a.get("workflows"):
        wf_txt += "No workflows defined yet.\n"
    else:
        wf_txt += (".. needflow::\n"
                   f"   :filter: \"{aid}\" in tags and type in ['workflow', 'workproduct']\n"
                   "   :link_types: input, output\n   :show_link_names:\n\n")
    for wf in a.get("workflows") or []:
        opts = "".join(_opt(f, wf.get(f)) for f in ("responsible", "approved_by") + LIST_FIELDS)
        exercised = list(dict.fromkeys(x["capability"] for x in wf.get("activities") or [] if x.get("capability")))
        opts += _opt("exercises", exercised)
        wf_txt += _need("workflow", wf["title"], wf["id"], wf.get("status", "valid"), aid, opts)
        if wf.get("description"):
            wf_txt += _indent(_md(wf["description"])) + "\n\n"
        if wf.get("activities"):
            has_cap = bool(exercised)
            wf_txt += ("   .. list-table:: Activities (RWE)\n      :header-rows: 1\n      :widths: "
                       + ("5 50 20 25" if has_cap else "5 70 25") + "\n\n")
            wf_txt += "      * - #\n        - Activity\n        - Performed by\n"
            wf_txt += "        - Capability\n" if has_cap else ""
            for n, act in enumerate(wf["activities"], 1):
                wf_txt += f"      * - {n}\n        - {act['step']}\n        - :need:`{act['by']}`\n"
                if has_cap:
                    cap = act.get("capability")
                    wf_txt += f"        - :need:`{cap}`\n" if cap else "        -\n"
            wf_txt += "\n"
        if wf.get("gate"):
            wf_txt += ("   **Gate.** This workflow cannot be approved until every work product below has reached "
                       "its minimum status.\n\n"
                       "   .. list-table:: Gate (entry criteria)\n      :header-rows: 1\n      :widths: 40 20 40\n\n"
                       "      * - Work product\n        - Minimum status\n        - Produced by\n")
            for g in wf["gate"]:
                prod = [w2["id"] for b in areas or [a] for w2 in b.get("workflows") or [] if g["wp"] in (w2.get("output") or [])]
                who = ", ".join(f":need:`{x}`" for x in prod) or "outside these assemblies"
                wf_txt += f"      * - :need:`{g['wp']}`\n        - {g['min_status']}\n        - {who}\n"
            wf_txt += "\n"
    files["workflows/index.rst"] = wf_txt

    # work products (purpose / concept / template triad)
    wp_txt = h + _hdr(f"{ar['title']} Work Products", "#") + "\n"
    for wp in a.get("workproducts") or []:
        opts = _opt("complies", wp.get("complies")) + _opt("has", wp.get("concept")) + _opt("typed_by", wp.get("template"))
        wp_txt += _need("workproduct", wp["title"], wp["id"], wp.get("status", "valid"), aid, opts)
        wp_txt += "   **Purpose:** " + _md(" ".join(wp["purpose"].split())) + "\n\n"
        if wp.get("kind"):
            wp_txt += f"   **Kind:** {wp['kind']}\n\n"
        if wp.get("origin") == "external":
            wp_txt += "   **Produced by:** processes outside these areas; used here as an input.\n\n"
    if not a.get("workproducts"):
        wp_txt += "No work products defined yet.\n"
    files["work_products/index.rst"] = wp_txt

    # roles
    rl_txt = h + _hdr(f"{ar['title']} Roles", "#") + "\n"
    for r in a.get("roles") or []:
        rl_txt += _need("role", r["title"], r["id"], r.get("status", "valid"), aid)
        rl_txt += _indent(_md(r["description"])) + "\n\n"
    if not a.get("roles"):
        rl_txt += "No roles defined yet.\n"
    files["roles/index.rst"] = rl_txt

    # templates / guidance
    gd_txt = h + _hdr(f"{ar['title']} Templates", "#") + "\n"
    for t in a.get("templates") or []:
        gd_txt += _need("gd_temp", t["title"], t["id"], t.get("status", "valid"), aid)
        if t.get("description"):
            gd_txt += _indent(_md(t["description"])) + "\n\n"
        if t.get("file"):
            gd_txt += f"   Template file: ``{t['file']}``\n\n"
    if not a.get("templates"):
        gd_txt += "No templates defined yet.\n"
    files["templates/index.rst"] = gd_txt
    return files


def _std_badge(s: str) -> str:
    """One standard as a badge; colour by family: ISO/IEC/IEEE 15288, Automotive SPICE, other."""
    s = " ".join(s.split())
    if s.startswith("ISO/IEC/IEEE 15288"):
        return f":bdg-primary:`{('15288 ' + s[len('ISO/IEC/IEEE 15288'):].strip()).strip()}`"
    if s.startswith("ASPICE 4.0 "):
        return f":bdg-info:`{s[len('ASPICE 4.0 '):]}`"
    return f":bdg-dark-line:`{s}`"


def _std_list(ar: dict[str, Any]) -> list[str]:
    """Standards of an assembly, grouped by family: 15288 first, then Automotive SPICE, then the rest."""
    fam = lambda x: 0 if x.startswith("ISO/IEC/IEEE 15288") else 1 if x.startswith("ASPICE 4.0 ") else 2
    return sorted(ar.get("standards") or [], key=fam)


def _table(areas: list[dict[str, Any]], owners: dict[str, str], group: str = "") -> str:
    out = (".. list-table::" + (f" {group}" if group else "") + "\n   :header-rows: 1\n   :widths: 26 16 26 9 12 11\n   :class: qx-reg\n\n"
           "   * - Process\n     - Owner\n     - Standards\n     - Workflows\n     - Work products\n     - Status\n")
    for a in areas:
        ar = a["area"]
        stds = ("\n\n" + " " * 7).join(_std_badge(x) for x in _std_list(ar))
        out += (f"   * - :ref:`{ar['title']} <qx_assembly_{ar['id']}>`\n"
                f"     - {owners.get(ar['owner'], ar['owner'])}\n"
                f"     - {stds}\n".replace("     - \n", "     -\n") +
                f"     - {len(a.get('workflows') or [])}\n     - {len(a.get('workproducts') or [])}\n"
                f"     - :bdg-{STATUS[ar['status']]}:`{ar['status']}`\n")
    return out + "\n"


def _std_family(x: str) -> int:
    return 0 if x.startswith("ISO/IEC/IEEE 15288") else 1 if x.startswith("ASPICE 4.0 ") else 2


def _std_short(x: str) -> str:
    x = " ".join(x.split())
    if x.startswith("ISO/IEC/IEEE 15288"):
        return ("15288 " + x[len("ISO/IEC/IEEE 15288"):].strip()).strip()
    if x.startswith("ASPICE 4.0 "):
        return x[len("ASPICE 4.0 "):]
    return x


def _matrix(areas: list[dict[str, Any]], owners: dict[str, str]) -> str:
    """Standards coverage: one row per process, one column per standard clause the cluster cites."""
    cols = sorted({x for a in areas for x in a["area"].get("standards") or []}, key=lambda x: (_std_family(x), x))
    out = (".. list-table::\n   :header-rows: 1\n   :class: qx-reg qx-matrix\n\n   * - Process\n"
           + "".join(f"     - {_std_short(c)}\n" for c in cols))
    for a in areas:
        have = set(a["area"].get("standards") or [])
        out += f"   * - :ref:`{a['area']['title']} <qx_assembly_{a['area']['id']}>`\n"
        out += "".join(f"     - {'●' if c in have else ''}\n".replace("     - \n", "     -\n") for c in cols)
    return out + "\n"


def _score(n: int, ok: bool | None = None) -> str:
    return f":bdg-{'success' if (n >= 1 if ok is None else ok) else 'danger'}:`{n}`"


def _scorecard(areas: list[dict[str, Any]], owners: dict[str, str]) -> str:
    """Completeness against the minimum definition; recomputed from the YAML on every render."""
    out = (".. list-table::\n   :header-rows: 1\n   :class: qx-reg qx-scorecard\n\n"
           "   * - Process\n     - Outcomes\n     - Capabilities\n     - Workflows\n     - With gates\n"
           "     - Work products\n     - Roles\n     - Templates\n")
    for a in areas:
        wfs = a.get("workflows") or []
        gated = sum(1 for w in wfs if w.get("gate"))
        out += (f"   * - :ref:`{a['area']['title']} <qx_assembly_{a['area']['id']}>`\n"
                f"     - {_score(len(a.get('outcomes') or []))}\n     - {_score(len(a.get('capabilities') or []))}\n"
                f"     - {_score(len(wfs))}\n"
                f"     - :bdg-{'success' if gated >= 1 else 'danger'}:`{gated} / {len(wfs)}`\n"
                f"     - {_score(len(a.get('workproducts') or []))}\n     - {_score(len(a.get('roles') or []))}\n"
                f"     - {_score(len(a.get('templates') or []))}\n")
    return out + "\n"


def _cluster_body(cluster: str, areas: list[dict[str, Any]], owners: dict[str, str]) -> str:
    """Cluster content for every cluster: three tabular tabs (grouped register, standards coverage
    matrix, completeness scorecard). Clusters without groups show one register table."""
    groups = CLUSTER_GROUPS.get(cluster) or []
    by: dict[str, list[dict[str, Any]]] = {}
    for a in sorted(areas, key=lambda x: x["area"]["title"]):
        by.setdefault(a["area"].get("group") or "", []).append(a)
    order = [g for g in groups if g in by] + [g for g in by if g not in groups]
    flat = [a for g in order for a in by[g]]
    register = "".join(_table(by[g], owners, g) for g in order)
    return (".. tab-set::\n   :class: qx-tabs\n\n   .. tab-item:: Grouped register\n\n" + _indent(register, 6) + "\n\n"
            "   .. tab-item:: Standards coverage\n\n" + _indent(_matrix(flat, owners), 6) + "\n\n"
            "   .. tab-item:: Completeness\n\n" + _indent(_scorecard(flat, owners), 6) + "\n\n")


def _cluster_page(cluster: str, areas: list[dict[str, Any]], owners: dict[str, str]) -> str:
    out = HEADER.format(src=f"prod/assemblies/{cluster}/*/process/process.yaml") + f".. _qx_cluster_{cluster}:\n\n"
    out += _hdr(CLUSTERS[cluster], "#") + "\n"
    out += _cluster_body(cluster, areas, owners)
    out += ".. toctree::\n   :hidden:\n\n" + "".join(f"   /assemblies/{a['_path']}/process/index\n" for a in areas)
    return out


def _standards_page(standards: list[dict[str, Any]]) -> str:
    out = HEADER.format(src="needs/standards.yaml") + ".. _qx_needs:\n\n" + _hdr("Needs", "#")
    out += ("\nWhat the hub must satisfy: the standard clauses that Qorix work products comply with. Each "
            "work product links to its clauses with ``complies``, so compliance is traceable in both "
            "directions.\n\n")
    groups: dict[str, list[dict[str, Any]]] = {}
    for st in standards:
        groups.setdefault(st["standard"], []).append(st)
    for name, items in groups.items():
        out += _hdr(name, "=") + "\n"
        for st in items:
            kind = "std_req" if st["id"].startswith("std_req_") else "std_wp"
            out += (f".. {kind}:: {st['title']}\n   :id: {st['id']}\n   :status: valid\n   :version: 1\n\n"
                    f"   Clause: {st['clause']}\n\n")
    return out


def _cluster_index(used: list[str], by_cluster: dict[str, list[dict[str, Any]]]) -> str:
    """One row per cluster linking to its page; the registers live on the cluster pages only."""
    out = (".. list-table::\n   :header-rows: 1\n   :widths: 22 58 10 10\n   :class: qx-reg\n\n"
           "   * - Cluster\n     - Processes\n     - Workflows\n     - Work products\n")
    for c in used:
        las = sorted(by_cluster[c], key=lambda x: x["area"]["title"])
        names = ", ".join(f":ref:`{a['area']['title']} <qx_assembly_{a['area']['id']}>`" for a in las)
        out += (f"   * - :ref:`{CLUSTERS[c]} <qx_cluster_{c}>`\n     - {names}\n"
                f"     - {sum(len(a.get('workflows') or []) for a in las)}\n"
                f"     - {sum(len(a.get('workproducts') or []) for a in las)}\n")
    return out + "\n"


def render_catalog(areas: list[dict[str, Any]], standards: list[dict[str, Any]]) -> dict[str, str]:
    """Return {path relative to prod/: content}: assembly pages, cluster pages, Assemblies and Needs pages."""
    out: dict[str, str] = {}
    owners = {r["id"]: r["title"] for a in areas for r in a.get("roles") or []}
    by_cluster: dict[str, list[dict[str, Any]]] = {c: [] for c in CLUSTERS}
    for a in areas:
        by_cluster.setdefault(a["area"]["cluster"], []).append(a)
        for name, txt in render_area(a, areas).items():
            out[f"assemblies/{a['_path']}/{name}"] = txt
    used = [c for c, la in by_cluster.items() if la]
    for c in used:
        out[f"assemblies/{c}/index.rst"] = _cluster_page(c, by_cluster[c], owners)

    idx = HEADER.format(src="prod/assemblies/*/*/process/process.yaml") + ".. _qx_assemblies:\n\n"
    idx += _hdr("Assemblies", "#")
    idx += ("\nEach assembly is one Qorix process. It answers **A -> B: how, who, when, by what means, "
            "what** - with workflows (IN work products -> activities -> OUT work products), the roles "
            "that perform them (responsible, approver, expertise) and the work products and templates "
            "they use. The process model is described in :ref:`qx_process_model`.\n\n"
            "Assemblies are grouped into cluster assemblies. Each is classified by enabler, scope and "
            "layer:\n\n"
            ".. list-table::\n   :header-rows: 1\n   :class: qx-reg\n\n"
            "   * - Enabler\n     - Scope\n     - Layer\n"
            "   * - PRD, TST, BLD, DOC, SAF, SEC\n     - GLOB, FEAT, COMP, UNIT\n     - INT, REQ, ARC, DES, IMP\n\n")
    idx += _hdr("Clusters", "=") + "\n" + _cluster_index(used, by_cluster)
    idx += ".. toctree::\n   :hidden:\n\n" + "".join(f"   {c}/index\n" for c in used)
    out["assemblies/index.rst"] = idx
    out["needs.rst"] = _standards_page(standards)
    return out
