# Sphinx configuration for the Qorix Process Hub documentation.
# Metamodel is NOT configured here: qorix_docs() passes the composed metamodel.yaml.
project = "Qorix Process Hub"
version = "0.1"
extensions = [
    "sphinxcontrib.plantuml",
    "score_sphinx_bundle",
]
needs_role_need_template = "{{ title }}"

# Template files and code under prod/ are not documentation pages.
exclude_patterns = ["assemblies/**/templates/*.md", "realization/qpm/**", "realization/bzl/**", "concepts/tiers/**", "concepts/schema/**"]

project_url = "https://github.com/SwatiDavari/Qorix-Process-Hub-Test"

# Qorix branding (overrides the docs engine defaults)
html_static_path = ["_static"]
html_css_files = ["qorix.css"]
html_theme_options = {
    "logo": {"text": "QORIX"},
    "icon_links": [
        {"name": "Qorix Engineering on GitHub", "url": "https://github.com/qorix-engineering",
         "icon": "fa-brands fa-github", "type": "fontawesome"},
    ],
    "navbar_end": ["theme-switcher", "navbar-icon-links"],  # no version switcher (no versions.json)
}

# Need cards: use the plain "clean" layout (styled in _static/qorix.css) instead of the engine's default.
needs_default_layout = "clean"


def _force_qorix_layout(app, config):
    config.needs_default_layout = "clean"


def setup(app):
    # priority > 500 so this runs after the docs engine's own config-inited hook
    app.connect("config-inited", _force_qorix_layout, priority=900)
