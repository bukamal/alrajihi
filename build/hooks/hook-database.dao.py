# -*- coding: utf-8 -*-
"""Collect lazy DAO submodules for the top-level database package."""
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("database.dao")
