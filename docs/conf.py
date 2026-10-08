# Sphinx configuration for the Qorix Process Framework documentation.
# Metamodel is NOT configured here: qorix_docs() passes the composed metamodel.yaml.
project = "Qorix Process Framework"
version = "0.1"
extensions = [
    "sphinxcontrib.plantuml",
    "score_sphinx_bundle",
]
needs_role_need_template = "{{ title }}"
