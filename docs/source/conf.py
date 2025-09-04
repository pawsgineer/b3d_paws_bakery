project = "PAWS: Bakery"
copyright = "2025, Pawsgineer"
# author = "Graziella"
version = "0.1.0"
release = version


extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]


ANNOUNCEMENT_HTML = """
    <p>
        <strong>
            This add-on is a passion project made and maintained by a single dev.
        </strong>
    </p>
    <p>
        If you'd like to help keep the add-on up to date and fund new features, please
        consider supporting me:
    </p>
    <p>
        <a href="https://www.patreon.com/pawsgineer" target="_blank">Patreon</a>
        <a href="https://pawsgineer.itch.io/" target="_blank">itch.io</a>
    </p>
    """

html_theme = "furo"
html_theme_options = {
    "dark_css_variables": {
        "color-brand-primary": "#bfff50",
        "color-brand-content": "#bfff50",
        "color-announcement-text": "#e6ffa0",
        "color-announcement-background": "#67746357",
        # "color-admonition-background": "#ffa70040",
    },
    "light_css_variables": {
        "color-brand-primary": "#3e8600",
        "color-brand-content": "#3e8600",
        "color-announcement-text": "#e6ffa0",
        "color-announcement-background": "#677463",
        # "color-admonition-background": "#ffa700",
        "header-height": "8rem",
    },
    "announcement": ANNOUNCEMENT_HTML,
}

html_static_path = ["_static"]
html_css_files = [
    "custom.css",
]

epub_show_urls = "footnote"
