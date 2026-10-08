# Qorix Process Framework

One process framework for every Qorix project. It builds on Eclipse SCORE: SCORE is
the base, the Qorix overlay sits on top, and each project adds its own tailoring.
Everything is described in a **technology-neutral metamodel (QPM)**. Sphinx-needs and Bazel
(`score_docs_as_code`) are adapters on top of it, not the source of truth.

```
Eclipse SCORE processes  (ASIL B, CAL TBD, ASPICE L3)        tier 0 base     model/tiers/00_score_base  (imported)
        │                                   ▲ qpm export-upstream → Qorix Fork → SCORE PR
        ▼                                   │
Qorix processes  (ASIL B + ASIL D, CAL 3, ASPICE L3)         tier 1 overlay  model/tiers/10_qorix       (add / widen only)
  + G&C · Infrastructure · Validation · Training                              process/areas/*.yaml
        ▼
Project tailoring  (Performance: ASIL B · Products CP: ASIL D, CAL 3 · BL · QD · CPM)
                                                             tier 2 project  projects/<id>/              (narrow only + rationale)
```

## Repository layout

| Path | What it is |
|---|---|
| `model/schema/qpm-tier.schema.json` | JSON schema for every tier file |
| `model/tiers/00_score_base/` | SCORE metamodel (pinned upstream copy), its QPM import, SCORE process-ID snapshot |
| `model/tiers/10_qorix/qorix_overlay.qpm.yaml` | Qorix overlay: ASIL A/C/D, CAL, WP purpose/concept/template, G&C findings, training |
| `projects/<id>/tailoring.qpm.yaml` | Project tailoring. `_template/` is the starting point |
| `process/areas/*.yaml` | Neutral process content: workflows, work products, roles, concepts, templates |
| `templates/` | Work-product templates (Markdown) |
| `tools/qpm/` | `qpm` CLI: import, compose, adapters, catalog checks, reports, tests |
| `bzl/qorix_docs.bzl` | `qorix_docs()` macro: compose, then call `score_docs_as_code` `docs()` |
| `docs/` | Framework docs. `process_areas/` and `tailoring/` are **generated** |
| `upstream/score_proposal/` | Generated SCORE proposal (metamodel diff + PR text) for the Qorix Fork |
| `examples/consumer_repo/` | How a project repo consumes the framework |

## Quick start

```bash
pip install -r tools/qpm/requirements_lock.txt
python -m pytest tools/qpm/tests -q      # round trip, tiering rules, catalog checks
./tools/regen.sh                          # regenerate docs/process_areas, docs/tailoring, upstream/
bazel run //:docs                         # Sphinx-needs build with the composed metamodel
```

## qpm commands

| Command | Purpose |
|---|---|
| `qpm import-score` | SCORE `metamodel.yaml` to QPM base tier. Rerun this whenever SCORE is bumped. |
| `qpm compose --tier … --out-dir D` | Resolve the tier chain. Writes `resolved_model.json`, `metamodel.yaml` (Sphinx-needs) and `tailoring_report.rst` |
| `qpm check-process` / `render-process` | Validate the process catalog and render RST (`--check` = drift test) |
| `qpm export-upstream` | Build a SCORE metamodel diff from the `upstream: candidate` overlay ops |
| `qpm lint-needs` | Enforce rules no adapter can express (e.g. CAL required if `security == YES`) on `needs.json` |

## Onboarding a project

1. Copy `projects/_template/tailoring.qpm.yaml` and set `asil_max`, `cal_max` and `aspice_target_level`. Add narrowing operations, each with a `rationale`.
2. Get it approved through workflow `wf__qx_gc_tailor_project` (approver: Head of G&C).
3. In the project repo, follow `examples/consumer_repo`: add `bazel_dep(qorix_process_framework)` and call `qorix_docs(tailoring = …)`.
4. In CI, run `bazel run //:docs_check`, then `qpm lint-needs` on the project `needs.json`.

## Rules the composer enforces

* **Overlay (superset rule).** An overlay may only add types, optional attributes and relations, enum values and rules. Anything that is valid against SCORE stays valid against Qorix, which keeps the Qorix Fork pushable upstream.
* **Project (narrowing rule).** A project tier may only restrict enums, make attributes required, exclude types or add rules. Every operation needs a rationale, and that file is the tailoring evidence.
* **Chain rule.** There is exactly one base tier, and each tier extends the one before it. The project tier comes last.

Full design: [`DESIGN.md`](DESIGN.md) (detail pages in `docs/design/`).
