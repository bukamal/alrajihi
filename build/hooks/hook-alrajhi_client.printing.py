# -*- coding: utf-8 -*-
"""PyInstaller hook for the package-qualified printing package."""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = collect_submodules("alrajhi_client.printing")
# includes print_templates.py and _template_loader.py as source files
datas = collect_data_files("alrajhi_client.printing", includes=["*.py"], include_py_files=True)
