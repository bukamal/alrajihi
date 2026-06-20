# -*- coding: utf-8 -*-
"""PyInstaller hook for the top-level database package used by release builds.

The Windows build adds ``alrajhi_client`` to ``sys.path``.  That makes
``alrajhi_client/database`` importable as the top-level package ``database``.
The package intentionally exposes repositories and DAO singletons via lazy
``__getattr__`` lookups, so PyInstaller cannot discover these modules from the
static import graph unless they are collected explicitly.
"""
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("database")
