# -*- coding: utf-8 -*-
"""PyInstaller hook for the top-level printing package used by release builds."""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = collect_submodules("printing")
# includes print_templates.py and _template_loader.py as source files
datas = collect_data_files("printing", includes=["*.py"], include_py_files=True)
