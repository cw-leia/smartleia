# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("../"))


# -- Project information -----------------------------------------------------

project = "LEIA"
copyright = "2019-2020, ANSSI"
author = "ANSSI"

# The full version, including alpha/beta/rc tags
release = "0.2.2"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.autodoc",
    "sphinxcontrib.wavedrom",
    "sphinxcontrib.spelling",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    # "autoapi.extension",
    "recommonmark",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "nbsphinx",
    #  "sphinx.ext.autosummary"
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "**.ipynb_checkpoints"]

# The master toctree document.
master_doc = "index"

# -- Napoleon configuration --------------------------------------------------

napoleon_use_param = True
napoleon_use_ivar = True

# -- Autodoc configuration ---------------------------------------------------

# autodoc_default_options = {
#   'members': '',#'var1, var2',
#   'member-order': 'bysource',
#   'special-members': '__init__',
#   'undoc-members': False,
#   'exclude-members': '__weakref__'
# }

autoclass_content = "both"
autodoc_member_order = "bysource"

# -- Autoapi configuration ---------------------------------------------------

# autoapi_options = ['members', 'special-members']
# autoapi_include_summaries = True

# autoapi_dirs = ['../../leia_smartreader']
# autoapi_dirs = ["../"]
# autoapi_include_summaries = True
# autoapi_keep_files = True


# -- Nbsphinx configuration --------------------------------------------------

pygments_style = "sphinx"

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [(master_doc, "leia", "LEIA Documentation", [author], 1)]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    "css/custom.css",
]
