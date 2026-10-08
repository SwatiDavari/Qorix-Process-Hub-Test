# Sphinx configuration for the Qorix Process Framework documentation.
# Metamodel is NOT configured here: qorix_docs() passes the composed metamodel.yaml.
project = "Qorix Process Framework"
version = "0.1"
extensions = [
    "sphinxcontrib.plantuml",
    "score_sphinx_bundle",
]
needs_role_need_template = "{{ title }}"

# score_process_description 2.1.2 ships a 'root_cause' key unknown to docs-as-code 8.3.0 (upstream data, not ours)
suppress_warnings = ["needs.unknown_external_keys"]
project_url = "https://github.com/SwatiDavari/Qorix-Process-Hub-Test"
