# -*- coding: utf-8 -*-
"""Phase 231 guard: dashboard monetary Decimal usage must import Decimal.

Phase 228 simplified the dashboard but retained cash/project amount rendering that
uses Decimal. Missing the import causes runtime crashes when refreshing the
DashboardWidget or toggling cash visibility.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'dashboard_widget.py'
text = path.read_text(encoding='utf-8')
tree = ast.parse(text)

uses_decimal = any(isinstance(node, ast.Name) and node.id == 'Decimal' and isinstance(node.ctx, ast.Load) for node in ast.walk(tree))
imports_decimal = False
for node in tree.body:
    if isinstance(node, ast.ImportFrom) and node.module == 'decimal':
        if any(alias.name == 'Decimal' for alias in node.names):
            imports_decimal = True
    if isinstance(node, ast.Import):
        if any(alias.name == 'decimal' for alias in node.names):
            imports_decimal = True

if uses_decimal and not imports_decimal:
    raise AssertionError('dashboard_widget.py uses Decimal but does not import it from decimal')

required_methods = ('_render_cash_amounts', '_refresh_project_card')
missing_methods = [name for name in required_methods if f'def {name}(' not in text]
if missing_methods:
    raise AssertionError(f'Dashboard amount-rendering methods are missing or renamed; review Decimal guard: {missing_methods}')

print('phase231 dashboard Decimal import guard passed')
