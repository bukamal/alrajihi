# -*- coding: utf-8 -*-
"""Stable import path for source-tree and CI tests.

The application supports both package-qualified imports (``alrajhi_client.*``)
and the PyInstaller/source runtime style where ``alrajhi_client`` is placed on
``sys.path`` and modules are imported as top-level packages (``printing.*``,
``features.*``).  Tests should exercise both forms consistently.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"

for path in (ROOT, CLIENT):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)
