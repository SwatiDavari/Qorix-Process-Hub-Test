# Root = system of interest (ISO/IEC/IEEE 15288): needs/, prod/, dist/.
# The hub's own documentation is built from prod/ (Qorix base + Qorix overlay, no project tailoring).
load("//prod/realization/bzl:qorix_docs.bzl", "qorix_docs")

package(default_visibility = ["//visibility:public"])

exports_files(["prod/concepts/schema/qpm-tier.schema.json"])

filegroup(name = "qorix_base", srcs = ["prod/concepts/tiers/00_qorix_base/qorix_base.qpm.yaml"])

filegroup(name = "qorix_overlay", srcs = ["prod/concepts/tiers/10_qorix/qorix_overlay.qpm.yaml"])

# assemblies: prod/assemblies/<cluster>/<process>/<subcomponent>/<file>.yaml
filegroup(name = "assemblies", srcs = glob(["prod/assemblies/*/*/*/*.yaml"]))

qorix_docs(
    project = "Qorix Process Hub",
    source_dir = "prod",
    tailoring = None,
)
