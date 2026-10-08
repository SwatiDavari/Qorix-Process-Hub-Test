load("@rules_python//python:defs.bzl", "py_binary", "py_library", "py_test")

package(default_visibility = ["//visibility:public"])

exports_files(["requirements_lock.txt"])

py_library(
    name = "qpm_lib",
    srcs = glob(["qpm/**/*.py"], exclude = ["qpm/__main__.py"]),
    data = ["//:prod/concepts/schema/qpm-tier.schema.json"],
    imports = ["."],
    deps = [
        "@qpm_pip//jsonschema",
        "@qpm_pip//pyyaml",
    ],
)

py_binary(
    name = "qpm_cli",
    srcs = ["qpm/__main__.py"],
    main = "qpm/__main__.py",
    deps = [":qpm_lib"],
)

py_test(
    name = "qpm_test",
    srcs = ["tests/test_qpm.py"],
    data = glob(["tests/fixtures/**"], allow_empty = True) + [
        "//:qorix_overlay",
        "//:qorix_base",
        "//:assemblies",
        "//needs:standards",
        "//dist:tailorings",
    ],
    main = "tests/test_qpm.py",
    deps = [
        ":qpm_lib",
        "@qpm_pip//pytest",
    ],
)
