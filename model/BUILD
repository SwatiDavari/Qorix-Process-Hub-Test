package(default_visibility = ["//visibility:public"])

exports_files(["schema/qpm-tier.schema.json"])

filegroup(name = "score_base", srcs = ["tiers/00_score_base/score_base.qpm.yaml"])

filegroup(name = "qorix_overlay", srcs = ["tiers/10_qorix/qorix_overlay.qpm.yaml"])

filegroup(name = "score_process_ids", srcs = ["tiers/00_score_base/score_process_ids.txt"])

filegroup(name = "upstream_yaml", srcs = ["tiers/00_score_base/score_metamodel.upstream.yaml"])
