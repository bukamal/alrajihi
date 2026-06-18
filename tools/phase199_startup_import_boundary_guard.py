# -*- coding: utf-8 -*-
"""Phase 199 startup/import-boundary guard.

This is intentionally static: CI/build environments may not have PyQt5, but we
can still prevent the exact class of startup breakage that caused the circular
import after Phase 197/198.
"""
from __future__ import annotations

from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'


def read(rel: str) -> str:
    return (CLIENT / rel).read_text(encoding='utf-8')


def assert_no_eager_from_imports(rel: str, forbidden_prefixes: tuple[str, ...]) -> None:
    text = read(rel)
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ''
            if any(mod == prefix or mod.startswith(prefix + '.') for prefix in forbidden_prefixes):
                raise AssertionError(f'{rel} has eager from-import from {mod!r}; use lazy __getattr__ mapping')
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if any(name == prefix or name.startswith(prefix + '.') for prefix in forbidden_prefixes):
                    raise AssertionError(f'{rel} has eager import {name!r}; use lazy __getattr__ mapping')


def assert_lazy_package(rel: str, required_names: list[str]) -> None:
    text = read(rel)
    if 'def __getattr__(' not in text:
        raise AssertionError(f'{rel} must expose names through module __getattr__')
    if 'import_module(' not in text:
        raise AssertionError(f'{rel} must use importlib.import_module for lazy resolution')
    for name in required_names:
        if repr(name) not in text and f'"{name}"' not in text:
            raise AssertionError(f'{rel} lazy export missing {name}')


def assert_currency_remains_lazy() -> None:
    text = read('currency.py')
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == 'core.services.settings_service':
            if any(alias.name == 'settings_service' for alias in node.names):
                raise AssertionError('currency.py must not import settings_service at module load time')
    if 'def _settings_service()' not in text:
        raise AssertionError('currency.py must keep lazy _settings_service() helper')
    if 'cls._instance._gateway = None' not in text or 'def gateway(self):' not in text:
        raise AssertionError('CurrencyManager.gateway must remain lazy')


def main() -> None:
    assert_lazy_package('database/__init__.py', ['SettingsRepository', 'ExpenseRepository', 'item_dao'])
    assert_lazy_package('database/repositories/__init__.py', ['SettingsRepository', 'ExpenseRepository', 'BranchRepository'])
    assert_lazy_package('database/dao/__init__.py', ['expense_dao', 'item_dao', 'manufacturing_dao'])

    # These package initializers must not import repository/DAO modules eagerly.
    assert_no_eager_from_imports('database/__init__.py', ('database.repositories', 'database.dao'))
    assert_no_eager_from_imports('database/repositories/__init__.py', ('database.repositories',))
    assert_no_eager_from_imports('database/dao/__init__.py', ('database.dao',))
    assert_currency_remains_lazy()
    print('phase199_startup_import_boundary_guard passed')


if __name__ == '__main__':
    main()
