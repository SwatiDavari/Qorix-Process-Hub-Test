"""qorix_docs(): one macro every Qorix repo calls to get a tailored docs build.

    load("@qorix_process_framework//bzl:qorix_docs.bzl", "qorix_docs")
    qorix_docs(
        project = "Qorix Performance",
        tailoring = "//process:tailoring.qpm.yaml",
    )

It composes SCORE base -> Qorix overlay -> project tailoring with `qpm compose`
and hands the generated metamodel to score_docs_as_code's docs().
"""

load("@score_docs_as_code//:docs.bzl", "docs")

_FW = "@qorix_process_framework"
_BASE = _FW + "//model:score_base"
_OVERLAY = _FW + "//model:qorix_overlay"
_QPM = _FW + "//tools/qpm:qpm_cli"

def qorix_docs(project, tailoring = None, source_dir = "docs", external_needs = [], **kwargs):
    """Tailored docs build.

    Args:
      project: Human-readable project name.
      tailoring: Label of the project's tailoring.qpm.yaml (None = Qorix overlay only).
      source_dir: Sphinx source directory.
      external_needs: Extra needs.json labels (SCORE process needs are always added).
      **kwargs: Forwarded to score_docs_as_code docs().
    """
    tiers = [_BASE, _OVERLAY] + ([tailoring] if tailoring else [])
    out = "_qpm"
    native.genrule(
        name = "qpm_compose",
        srcs = tiers,
        outs = [out + "/metamodel.yaml", out + "/resolved_model.json", out + "/tailoring_report.rst"],
        tools = [_QPM],
        cmd = "$(location {qpm}) compose {tiers} --out-dir $(RULEDIR)/{out}".format(
            qpm = _QPM,
            tiers = " ".join(["--tier $(location {})".format(t) for t in tiers]),
            out = out,
        ),
    )
    docs(
        project = project,
        source_dir = source_dir,
        metamodel = ":" + out + "/metamodel.yaml",
        external_needs = ["@score_process_description//:needs_json_file"] + external_needs,
        **kwargs
    )
