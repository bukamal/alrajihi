#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 238 guard: manufacturing recognizes BOM materials after item-type i18n.

This reproduces the reported failure: items created while the UI language is not
Arabic may store localized item_type values such as "Finished product" and
"Inventory". Manufacturing must still treat the product as a finished product,
load its BOM, calculate required materials, and create reservations for the
production order.
"""
from __future__ import annotations

import os
import shutil
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get('ALRAJHI_PHASE238_RUNTIME', '/tmp/alrajhi_phase238_runtime'))
shutil.rmtree(RUNTIME, ignore_errors=True)
RUNTIME.mkdir(parents=True, exist_ok=True)
os.environ['ALRAJHI_DATA_DIR'] = str(RUNTIME)
os.environ['ALRAJHI_DB_PATH'] = str(RUNTIME / 'phase238.db')

try:
    import PyQt5  # noqa: F401
except Exception:
    settings_store = {'network/mode': 'local'}
    class QSettings:
        def __init__(self, *a, **k): pass
        def value(self, key, default=None, *a, **k): return settings_store.get(key, default)
        def setValue(self, key, value): settings_store[key] = value
        def remove(self, key): settings_store.pop(key, None)
    class QObject: pass
    class QTimer:
        @staticmethod
        def singleShot(*a, **k): return None
    class Qt:
        RightToLeft = 1; LeftToRight = 0; AlignRight = 2; AlignVCenter = 128
    class QSize:
        def __init__(self, *a): pass
    class QUrl: pass
    def pyqtSignal(*a, **k):
        class Signal:
            def connect(self, *a, **k): return None
            def emit(self, *a, **k): return None
        return Signal()
    class Dummy:
        def __init__(self, *a, **k): pass
        def __getattr__(self, name):
            def f(*a, **k): return None
            return f
    qtcore = types.ModuleType('PyQt5.QtCore')
    for name, obj in dict(QSettings=QSettings, QObject=QObject, QTimer=QTimer, Qt=Qt, QSize=QSize, QUrl=QUrl, pyqtSignal=pyqtSignal).items(): setattr(qtcore, name, obj)
    qtwidgets = types.ModuleType('PyQt5.QtWidgets')
    for name in 'QApplication QWidget QMainWindow QDialog QMessageBox QVBoxLayout QHBoxLayout QLabel QPushButton QLineEdit QTableWidget QTableWidgetItem QComboBox QSpinBox QDoubleSpinBox QDateEdit QTextEdit QCheckBox QGroupBox QFormLayout QTabWidget QFileDialog QInputDialog QProgressDialog QFrame QSplitter QScrollArea'.split(): setattr(qtwidgets, name, Dummy)
    qtgui = types.ModuleType('PyQt5.QtGui')
    for name in 'QIcon QPixmap QFont QColor QDesktopServices QKeySequence'.split(): setattr(qtgui, name, Dummy)
    pyqt = types.ModuleType('PyQt5'); pyqt.QtCore = qtcore; pyqt.QtWidgets = qtwidgets; pyqt.QtGui = qtgui
    sys.modules.update({'PyQt5': pyqt, 'PyQt5.QtCore': qtcore, 'PyQt5.QtWidgets': qtwidgets, 'PyQt5.QtGui': qtgui})

sys.path.insert(0, str(ROOT / 'alrajhi_client'))
sys.path.insert(0, str(ROOT))

from database.migrations import init_database
from database.connection import DatabaseConnection
from auth.session import UserSession
from core.item_types import FINISHED_PRODUCT, STOCK, normalize_item_type, is_finished_product

init_database()
UserSession.login({'id': 'admin', 'username': 'admin', 'role': 'admin', 'branch_id': None})
db = DatabaseConnection()
conn = db.get_connection()
conn.execute("INSERT OR IGNORE INTO users(id, username, password_hash, salt, full_name, role) VALUES(?,?,?,?,?,?)", ('admin', 'admin', 'x', 'x', 'Admin', 'admin'))
# Use localized legacy values on purpose. These are the values that broke BOM recognition.
cur = conn.execute("""
    INSERT INTO items(user_id, name, item_type, purchase_price, selling_price, quantity, unit, average_cost)
    VALUES('admin', 'Finished Good EN', 'Finished product', '0', '100', '0', 'pcs', '0')
""")
product_id = int(cur.lastrowid)
cur = conn.execute("""
    INSERT INTO items(user_id, name, item_type, purchase_price, selling_price, quantity, unit, average_cost)
    VALUES('admin', 'Raw Material EN', 'Inventory', '5', '0', '100', 'pcs', '5')
""")
material_id = int(cur.lastrowid)
cur = conn.execute("""
    INSERT INTO warehouses(user_id, name, code, is_default, is_active, created_at, updated_at)
    VALUES('admin', 'Main Warehouse', 'MAIN', 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
""")
warehouse_id = int(cur.lastrowid)
conn.execute("""
    INSERT INTO item_warehouse_balances(user_id, item_id, warehouse_id, quantity, average_cost, updated_at)
    VALUES('admin', ?, ?, '100', '5', CURRENT_TIMESTAMP)
""", (material_id, warehouse_id))
conn.commit()

from core.services.manufacturing_service import manufacturing_service

assert normalize_item_type('Finished product') == FINISHED_PRODUCT
assert normalize_item_type('Inventory') == STOCK
assert is_finished_product('Finished product')

bom_id = manufacturing_service.save_bom({
    'product_id': product_id,
    'quantity': '1',
    'lines': [{'item_id': material_id, 'quantity': '2', 'unit_id': None, 'waste_percent': '0'}],
})
bom = manufacturing_service.get_bom_for_product(product_id)
assert bom and bom.get('lines'), 'BOM saved but manufacturing did not return lines for product'
materials = manufacturing_service.get_required_materials_recursive(product_id, '3', warehouse_id)
assert materials and len(materials) == 1, f'Required materials missing: {materials}'
mat = materials[0]
assert int(mat.get('item_id')) == material_id
assert str(mat.get('required_qty')) in {'6', '6.0', '6.00', '6.0000'} or float(mat.get('required_qty')) == 6.0
assert mat.get('is_sufficient') is True, f'Material should be sufficient: {mat}'
order_id = manufacturing_service.create_production_order({
    'product_id': product_id,
    'planned_qty': '3',
    'raw_warehouse_id': warehouse_id,
    'output_warehouse_id': warehouse_id,
    'notes': 'phase238 guard',
})
order = manufacturing_service.get_production_order(order_id)
assert order and order.get('reservations'), f'Production order created without material reservations: {order}'
print({'bom_id': bom_id, 'order_id': order_id, 'reservation_count': len(order.get('reservations') or [])})
