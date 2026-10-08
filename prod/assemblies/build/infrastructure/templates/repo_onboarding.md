# Repository Onboarding Checklist

- [ ] `MODULE.bazel`: `bazel_dep(name = "qorix_process_framework", version = "<x.y.z>")` + registries in `.bazelrc` (copy from the hub)
- [ ] `process/tailoring.qpm.yaml` copied from `dist/_template`, approved via wf_qx_gc_tailor_project
- [ ] `BUILD`: `qorix_docs(project = "...", tailoring = "//process:tailoring.qpm.yaml")`
- [ ] `docs/` with `conf.py` (extension `score_sphinx_bundle`) and `index.rst`
- [ ] CI: `bazel run //:docs`, `bazel run //:docs_check`, `qpm lint-needs` on `//:needs_json`
- [ ] Branch protection: CODEOWNERS for `process/` = G&C
- [ ] First green build confirmed by project lead
