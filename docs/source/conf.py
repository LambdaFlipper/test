# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

"""
Author: elenia@TUBS
Copyright 2024 elenia
This file is part of eELib, which is free software under the terms of the GNU GPL Version 3.
"""

import time

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "eELib"
copyright = f'2023-{time.strftime("%Y")}, elenia'
author = "elenia"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
]
napoleon_numpy_docstring = False
# pygments_style = "sphinx" # use default white or "sphinx" style for code-blocks

# allow duplicate section titles without warning
suppress_warnings = ["autosectionlabel.*"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", ".venv", "venv"]

# in module index, alphabetically sort by the second level
modindex_common_prefix = ["eelib."]

# shorten objects names e.g. "eelib.core.control.EMS.EMS_model.HEMS" to "HEMS". This enhances readability of the index
add_module_names = False

# autodoc config
autoclass_content = "both"  # display "init" or "class" docstring or "both"

autodoc_class_signature = (  # wether the signature of classes shall be displayed "mixed" with the class or "separated" into a method
    "mixed"
)

autodoc_member_order = (  # wether the members (e.g. methods of a class) shall be ordered "alphabetical" or "bysource" as in the python file
    "bysource"
)

autodoc_default_options = {
    "members": True,
    "undoc-members": True,  # members missing docstrings
    "private-members": True,  # members like _get_component
    "special-members": False,  # members like __init__
    "inherited-members": False,  # members that are already documented in the base class
    "show-inheritance": True,  # show base classes from which the viewed class inherits
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "logo_only": True,
    "display_version": True,
    "prev_next_buttons_location": "both",
    "style_external_links": False,
    "style_nav_header_background": "#343131",
    # Toc options
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": -1,
    "includehidden": True,
    "titles_only": False,
}
html_logo = "_static/eelib_logo.png"
html_favicon = "_static/eelib_favicon.png"
