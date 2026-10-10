# Qorix Process Hub

One process hub for every Qorix project. The Qorix base process model is the base, the
Qorix overlay adds the Qorix processes, and each project adds its own tailoring.
Everything is described in a **technology-neutral metamodel (QPM)**. Sphinx-needs and Bazel
are adapters on top of it, not the source of truth.

## Repository structure (system of interest, ISO/IEC/IEEE 15288)

```
Qorix-Process-Hub/                 root = system of interest
├── needs/                         what the hub must satisfy: standards catalogue (standards.yaml)
├── prod/                          the system (also the Sphinx source of the hub site)
│   ├── missions/                  why the hub exists, structure, ID scheme
│   ├── concepts/                  process model, tiering, metamodel, tiers (00_qorix_base, 10_qorix), schema
│   ├── realization/               qpm tool, qorix_docs() macro, regen.sh
│   └── assemblies/
│       └── <cluster>/<process>/   cluster assembly / process assembly
│           ├── process/           process.yaml: identity, classification, status, getting started, concepts
│           ├── workflows/         workflows.yaml
│           ├── work_products/     work_products.yaml
│           ├── roles/             roles.yaml
│           └── templates/         templates.yaml + template files
└── dist/                          distributions: one tailoring per project (#1 performance, #2 products_cp, …)
```

Each subcomponent folder also holds its generated `index.rst`; the Needs, Assemblies, cluster
and Dist pages are generated too (never edit by hand). Site sections: Needs · Missions ·
Concepts · Realization · Assemblies · Dist.

| Cluster | Assemblies (code) |
|---|---|
| `compliance` | Governance & Compliance (`gc`), Safety (`saf`), Security (`sec`) |
| `engineering` | Project Planning and Control (`plan`), Risk Management (`risk`), Decision Management (`dec`), Measurement and Metrics (`meas`), Requirements Management and Traceability (`req`), Configuration Management (`cfg`), Change Management (`cm`), Problem Resolution (`prb`), Quality Assurance (`qa`), Verification and Reviews (`vnr`), Information and Documentation Management (`info`), Release Management (`rel`), Supplier and Acquisition Management (`sup`), Process Improvement and Tailoring (`pim`) |
| `build` | Infrastructure (`infra`) |
| `testing` | Validation (`val`) |
| `organisation` | Training (`trn`) |

Every assembly is classified by enabler (PRD, TST, BLD, DOC, SAF, SEC), scope (GLOB, FEAT,
COMP, UNIT) and layer (INT, REQ, ARC, DES, IMP).

## Identifiers

`<type>_qx_<assembly code>_<name>`, for example `wf_qx_gc_tailor_project`,
`wp_qx_saf_safety_tailoring`, `rl_qx_qa_quality_office`, `gd_temp_qx_sec_csms_template`.
A double underscore is never allowed; `qpm render-process` and the self-tests reject it.

## Quick start

```bash
pip install -r prod/realization/qpm/requirements_lock.txt
python -m pytest prod/realization/qpm/tests -q   # adapter completeness, tiering rules, catalog and ID checks
./prod/realization/regen.sh                       # regenerate assembly, Needs, Assemblies and Dist pages
bash prod/realization/publish.sh             # check, regenerate, commit and push to main, then watch CI (--dry-run to preview)
bazel run //:docs                                 # Sphinx-needs build with the composed metamodel
```

## qpm commands

| Command | Purpose |
|---|---|
| `qpm compose --tier … --out-dir D` | Resolve the tier chain. Writes `resolved_model.json`, `metamodel.yaml` (Sphinx-needs) and `tailoring_report.rst` |
| `qpm check-process` / `render-process --assemblies prod/assemblies --standards needs/standards.yaml --out-dir prod` | Validate the assemblies and render RST (`--check` = drift test) |
| `qpm lint-needs` | Enforce rules no adapter can express (e.g. CAL required if `security == YES`) on `needs.json` |

## Onboarding a project

1. Copy `dist/_template/tailoring.qpm.yaml` to `dist/<project>/` and set `asil_max`, `cal_max` and `aspice_target_level`. Add narrowing operations, each with a `rationale`.
2. Get it approved through workflow `wf_qx_gc_tailor_project` (approver: Head of G&C).
3. In the project repo, follow `examples/consumer_repo`: add `bazel_dep(qorix_process_framework)` and call `qorix_docs(tailoring = …)`.
4. In CI, run `bazel run //:docs_check`, then `qpm lint-needs` on the project `needs.json`.

## Rules the composer enforces

* **Overlay (superset rule).** An overlay may only add types, optional attributes and relations, enum values and rules. Anything that is valid against the base stays valid against Qorix.
* **Project (narrowing rule).** A project tier may only restrict enums, make attributes required, exclude types or add rules. Every operation needs a rationale, and that file is the tailoring evidence.
* **Chain rule.** There is exactly one base tier, and each tier extends the one before it. The project tier comes last.

Full design: [`DESIGN.md`](DESIGN.md) (detail pages in `prod/concepts/`).
