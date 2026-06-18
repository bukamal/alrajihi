# -*- coding: utf-8 -*-
"""Phase 198 guard: currency/settings startup circular import fix."""
from __future__ import annotations
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
client = ROOT / 'alrajhi_client'

currency = (client / 'currency.py').read_text(encoding='utf-8')
top_level_currency = currency.split('def _settings_service():', 1)[0]
assert 'from core.services.settings_service import settings_service' not in top_level_currency, 'currency.py must not import settings_service at module import time'
assert 'def _settings_service()' in currency, 'currency.py must expose a lazy _settings_service helper'
assert 'from core.services.settings_service import settings_service' in re.search(
    r'def _settings_service\(\):.*?(?=\n\nclass CurrencyManager)', currency, re.S
).group(0), 'settings_service import must be inside _settings_service() only'
assert 'cls._instance._gateway = None' in currency, 'currency gateway must be lazy during startup'
assert '@property\n    def gateway' in currency, 'CurrencyManager.gateway lazy property is required'
assert 'cls._instance.gateway = create_currency_gateway()' not in currency, 'currency gateway must not be created during __new__'

# Simulate the reported import chain without requiring PyQt5 to be installed in CI.
import sys, types
qtcore = types.ModuleType('PyQt5.QtCore')
class QSettings:
    def __init__(self, *args, **kwargs):
        self._store = {}
    def value(self, key, default=None):
        return self._store.get(key, default)
    def setValue(self, key, value):
        self._store[key] = value
qtcore.QSettings = QSettings
pyqt5 = types.ModuleType('PyQt5')
sys.modules.setdefault('PyQt5', pyqt5)
sys.modules.setdefault('PyQt5.QtCore', qtcore)
sys.path.insert(0, str(client))

from core.services.warehouse_service import warehouse_service  # noqa: F401
from core.services.settings_service import settings_service  # noqa: F401
from currency import currency as currency_manager
assert currency_manager._gateway is None, 'Currency gateway should remain lazy after import'
print('phase198_startup_circular_import_guard: OK')
