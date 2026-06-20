# -*- coding: utf-8 -*-
"""PyInstaller hook for package-qualified database imports."""
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("alrajhi_client.database")
