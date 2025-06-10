.. DedupeFlow documentation master file, created by
   sphinx-quickstart on Sun Jun  8 22:46:57 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

DedupeFlow Documentation
========================

**DedupeFlow** is a modern Python library for data deduplication and record linkage.
It provides efficient algorithms and flexible configuration options for identifying
duplicate records in datasets.

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   configuration
   comparators
   strategies
   cli
   examples

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/core
   api/comparators
   api/strategies
   api/models
   api/types

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   contributing
   changelog
   roadmap

Key Features
------------

* **Multiple Comparison Algorithms**: String, numeric, and date comparators
* **Configurable Strategies**: Flexible matching and blocking strategies
* **Modern Architecture**: Built with Pydantic, type hints, and clean design patterns
* **High Performance**: Efficient algorithms with optional blocking for large datasets
* **CLI Interface**: Easy-to-use command-line tool
* **Extensible**: Plugin architecture for custom comparators and strategies

Quick Example
-------------

.. code-block:: python

   import pandas as pd
   from dedupeflow import DedupeEngine
   from dedupeflow.models import DedupeConfig, FieldConfig

   # Load your data
   data = pd.read_csv("customers.csv")

   # Configure deduplication
   config = DedupeConfig(
       fields=[
           FieldConfig(name="name", comparator="string", weight=0.4),
           FieldConfig(name="email", comparator="string", weight=0.3),
           FieldConfig(name="phone", comparator="string", weight=0.3),
       ],
       global_threshold=0.8
   )

   # Run deduplication
   engine = DedupeEngine(config)
   results = engine.deduplicate(data)

   print(f"Found {results.total_matches} potential duplicates")

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
