from datetime import date
from importlib.metadata import version as get_version

project = "PAWS: Bakery"
copyright = f"{date.today().year}, Pawsgineer"
author = "Pawsgineer"
version = get_version("paws_bakery")
release = version

nitpicky = True
linkcheck_exclude_documents = [
    r".*/changelog$",
]
# linkcheck_ignore = [
#     r"https://github.com/.*/commit/.*",
# ]

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "myst_parser",
    # "enum_tools.autoenum",
    # "sphinx.ext.napoleon",
    # "sphinx_autodoc_typehints",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

myst_enable_extensions = ["colon_fence", "fieldlist", "deflist"]
# myst_heading_anchors = 7
myst_footnote_transition = True
myst_dmath_double_inline = True
myst_enable_checkboxes = True


ANNOUNCEMENT_HTML = """
    <p>
        <strong>
            This add-on is a passion project created and maintained by a sole dev.
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
    "source_repository": "https://github.com/pawsgineer/b3d_paws_bakery/",
    "source_branch": "main",
    "source_directory": "docs/",
    #
    "dark_css_variables": {
        "color-brand-primary": "#bfff50",
        "color-brand-content": "#bfff50",
        "color-announcement-text": "#e6ffa0",
        "color-announcement-background": "#67746357",
        # "color-admonition-background": "#ffa70040",
        "color-inline-code-background": "#5b831c88",
        "color-code-background": "#5b831c88",
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
    "footer_icons": [
        {
            "name": "Patreon",
            "url": "https://www.patreon.com/pawsgineer",
            "html": "",
            "class": "fa-brands fa-solid fa-patreon fa-2x",
        },
        {
            "name": "itch.io",
            "url": "https://pawsgineer.itch.io/",
            "html": "",
            "class": "fa-brands fa-solid fa-itch-io fa-2x",
        },
        {
            "name": "GitHub",
            "url": "https://github.com/pawsgineer/b3d_paws_bakery",
            "html": "",
            "class": "fa-brands fa-solid fa-github fa-2x",
        },
    ],
}

html_static_path = ["_static"]
html_css_files = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/7.0.1/css/fontawesome.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/7.0.1/css/solid.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/7.0.1/css/brands.min.css",
    "custom.css",
]

epub_show_urls = "footnote"
