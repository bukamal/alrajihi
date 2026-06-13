#!/usr/bin/env python3
"""Detect form-validation error labels used without being initialized."""
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'alrajhi_client'
errors = []
for path in ROOT.rglob('*.py'):
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except Exception:
        continue
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        assigned = set()
        loaded = set()
        methods = {n.name for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for node in ast.walk(cls):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'self':
                name = node.attr
                if not name.endswith('_error') or name.startswith('_'):
                    continue
                if isinstance(node.ctx, ast.Store):
                    assigned.add(name)
                elif isinstance(node.ctx, ast.Load):
                    loaded.add(name)
        missing = sorted(n for n in loaded - assigned if n not in methods)
        if missing:
            errors.append(f"{path.relative_to(ROOT)}:{cls.name}: missing {', '.join(missing)}")

if errors:
    print('Form validation guard failed:')
    print('\n'.join(errors))
    raise SystemExit(1)
print('Form validation guard passed.')
