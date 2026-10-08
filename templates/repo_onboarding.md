# Repository Onboarding Checklist

- [ ] `MODULE.bazel`: `bazel_dep(name = "qorix_process_framework", version = "<x.y.z>")` + Qorix/SCORE registries in `.bazelrc`
- [ ] `process/tailoring.qpm.yaml` copied from `projects/_template`, approved via wf__qx_gc_tailor_project
- [ ] `BUILD`: `qorix_docs(project = "...", tailoring = "//process:tailoring.qpm.yaml")`
- [ ] `docs/` with `conf.py` (extension `score_sphinx_bundle`) and `index.rst`
- [ ] CI: `bazel run //:docs`, `bazel run //:docs_check`, `qpm lint-needs` on `//:needs_json`
- [ ] Branch protection: CODEOWNERS for `process/` = G&C
- [ ] First green build confirmed by project lead
