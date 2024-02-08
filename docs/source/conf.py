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
    "autoapi.extension",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
]
napoleon_numpy_docstring = False
# pygments_style = "sphinx" # use default white or "sphinx" style for code-blocks

# autoapi
autoapi_dirs = ["../../eelib"]
autoapi_template_dir = "../_autoapi_templates"
autoapi_options = [
    "members",
    "undoc-members",
    "private-members",
    "show-module-summary",
    "special-members",
    "show-inheritance",
]

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
