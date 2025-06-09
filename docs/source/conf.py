# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from importlib import metadata

project = 'DedupeFlow'
copyright = "2025, M'Hand KEDJAR"
author = "M'Hand KEDJAR"
PACKAGE_VERSION = metadata.version('dedupeflow')
version = release = PACKAGE_VERSION

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
"sphinx.ext.autodoc",
"sphinx.ext.autodoc.typehints",
]

templates_path = ['_templates']
exclude_patterns = []

nitpick_ignore = [
    ('py:class', 'type'),
    ('py:class', 'datetime.datetime'),
    ('py:class', 'datetime.date'),
    ('py:obj', 'datetime.datetime'),
    ('py:obj', 'datetime.date'),
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
