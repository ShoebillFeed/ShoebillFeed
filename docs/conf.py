# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

project = "Shoebill Feed"
copyright = "Shoebill Feed contributors"
author = "Shoebill Feed contributors"

extensions = [
    "myst_parser",
    "sphinx.ext.autosectionlabel",
]

source_suffix = {
    ".md": "markdown",
}

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "substitution",
]

# Keep autosectionlabel scoped to each document -- otherwise identically
# named headings across different pages (e.g. "Configuration" appearing in
# more than one page) collide.
autosectionlabel_prefix_document = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 3,
}

# Rendered docs are published at the repo's GitHub Pages root
# (https://<user>.github.io/<repo>/), set via the gh-pages.yml workflow.
html_baseurl = ""
