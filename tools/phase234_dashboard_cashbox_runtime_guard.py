# -*- coding: utf-8 -*-
"""Phase 234 runtime guard for dashboard cashbox totals."""
from __future__ import annotations
import os, sys, shutil, types
from pathlib import Path
from decimal import Decimal

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path('/tmp/alrajhi_phase234_cashbox_runtime')
shutil.rmtree(RUNTIME, ignore_errors=True)
RUNTIME.mkdir(parents=True, exist_ok=True)
os.environ['ALRAJHI_DATA_DIR'] = str(RUNTIME)
os.environ['ALRAJHI_DB_PATH'] = str(RUNTIME / 'phase234_cashbox.db')

try:
    import PyQt5  # noqa
except Exception:
    class QSettings:
        _s = {'network/mode': 'local'}
        def __init__(self,*a,**k): pass
        def value(self,k,d=None,*a,**kw): return self._s.get(k,d)
        def setValue(self,k,v): self._s[k]=v
    class QObject: pass
    def pyqtSignal(*a, **k):
        class Sig:
            def connect(self,*a,**k): pass
            def emit(self,*a,**k): pass
        return Sig()
    qtcore=types.ModuleType('PyQt5.QtCore'); qtcore.QSettings=QSettings; qtcore.QObject=QObject; qtcore.pyqtSignal=pyqtSignal
    pyqt=types.ModuleType('PyQt5'); pyqt.QtCore=qtcore
    sys.modules.update({'PyQt5':pyqt,'PyQt5.QtCore':qtcore})

sys.path.insert(0, str(ROOT / 'alrajhi_client'))
sys.path.insert(0, str(ROOT))

from database.migrations import init_database
from auth.session import UserSession
init_database()
UserSession.login({'id': 'admin', 'username': 'admin', 'role': 'admin', 'branch_id': None})

from core.services.cashbox_service import cashbox_service
from core.services.reporting_service import reporting_service
from core.services.dashboard_service import dashboard_service

cashbox_service.bootstrap()
cashbox_id = cashbox_service.default_cashbox_id()
if not cashbox_id:
    raise AssertionError('No default cashbox created')

cashbox_service.gateway.record_movement({
    'branch_id': None,
    'cashbox_id': cashbox_id,
    'bank_account_id': None,
    'movement_type': 'phase234_test_receipt',
    'amount': Decimal('125.50'),
    'direction': 'in',
    'reference_type': 'phase234_test',
    'reference_id': 1,
    'description': 'phase234 cashbox dashboard test',
    'movement_date': None,
})
summary = reporting_service.cash_bank_summary()
if Decimal(str(summary.get('cash_total') or 0)) < Decimal('125.50'):
    raise AssertionError(f'cash_bank_summary did not include movement balance: {summary}')
snapshot = dashboard_service.snapshot(use_cache=False)
liquidity = snapshot.get('cash_bank_summary', {})
movement = snapshot.get('cashbox_movement', {})
if Decimal(str(liquidity.get('cash_total') or 0)) < Decimal('125.50'):
    raise AssertionError(f'Dashboard snapshot cash total missing: {liquidity}')
if Decimal(str(movement.get('general', {}).get('received') or 0)) < Decimal('125.50'):
    raise AssertionError(f'Dashboard movement received missing: {movement}')
print('phase234 dashboard cashbox runtime guard passed')
