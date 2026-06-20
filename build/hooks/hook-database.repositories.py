# -*- coding: utf-8 -*-
"""Collect lazy repository submodules for the top-level database package."""
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("database.repositories")
