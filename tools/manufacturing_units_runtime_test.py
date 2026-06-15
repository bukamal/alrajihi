# -*- coding: utf-8 -*-
"""Headless manufacturing unit-conversion integration test.

Covers BOM quantity denominator, secondary item units conversion_factor,
waste ratio, material reservations, stock/warehouse movements, and final
product unit cost.
"""
from __future__ import annotations
import os, sys, shutil, types, json
from pathlib import Path
from decimal import Decimal
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get('ALRAJHI_MFG_UNITS_TEST_RUNTIME', '/tmp/alrajhi_manufacturing_units_runtime'))
if os.environ.get('ALRAJHI_TEST_RESET', '1') == '1':
    shutil.rmtree(RUNTIME, ignore_errors=True)
RUNTIME.mkdir(parents=True, exist_ok=True)
os.environ['ALRAJHI_DATA_DIR'] = str(RUNTIME)
os.environ['ALRAJHI_DB_PATH'] = str(RUNTIME / 'alrajhi_manufacturing_units_test.db')

try:
    import PyQt5  # noqa
except Exception:
    settings_store = {'network/mode': 'local'}
    class QSettings:
        def __init__(self,*a,**k): pass
        def value(self,k,d=None,*a,**kw): return settings_store.get(k,d)
        def setValue(self,k,v): settings_store[k]=v
    class QObject: pass
    class QTimer:
        @staticmethod
        def singleShot(*a, **k): pass
    def pyqtSignal(*a, **k):
        class Sig:
            def connect(self,*a,**k): pass
            def emit(self,*a,**k): pass
        return Sig()
    class Dummy:
        def __init__(self,*a,**k): pass
        def __getattr__(self,n):
            def f(*a,**k): return None
            return f
    qtcore=types.ModuleType('PyQt5.QtCore')
    for n,o in dict(QSettings=QSettings,QObject=QObject,QTimer=QTimer,pyqtSignal=pyqtSignal,Qt=Dummy,QSize=Dummy,QUrl=Dummy).items(): setattr(qtcore,n,o)
    qtwidgets=types.ModuleType('PyQt5.QtWidgets')
    for n in 'QApplication QWidget QMainWindow QDialog QMessageBox QVBoxLayout QHBoxLayout QLabel QPushButton QLineEdit QTableWidget QTableWidgetItem QComboBox QSpinBox QDoubleSpinBox QDateEdit QTextEdit QCheckBox QGroupBox QFormLayout QTabWidget QFileDialog QInputDialog QProgressDialog QFrame QSplitter QScrollArea'.split(): setattr(qtwidgets,n,Dummy)
    qtgui=types.ModuleType('PyQt5.QtGui')
    for n in 'QIcon QPixmap QFont QColor QDesktopServices QKeySequence'.split(): setattr(qtgui,n,Dummy)
    pyqt=types.ModuleType('PyQt5'); pyqt.QtCore=qtcore; pyqt.QtWidgets=qtwidgets; pyqt.QtGui=qtgui
    sys.modules.update({'PyQt5':pyqt,'PyQt5.QtCore':qtcore,'PyQt5.QtWidgets':qtwidgets,'PyQt5.QtGui':qtgui})

sys.path.insert(0, str(ROOT/'alrajhi_client'))
sys.path.insert(0, str(ROOT))

def dec(v): return Decimal(str(v))
def assert_dec(actual, expected, label):
    actual = dec(actual); expected = dec(expected)
    if abs(actual - expected) > dec('0.000001'):
        raise AssertionError(f'{label}: expected {expected}, got {actual}')

def main():
    from database.migrations import init_database
    from database.connection import DatabaseConnection
    from auth.session import UserSession
    init_database()
    UserSession.login({'id':'admin','username':'admin','role':'admin','branch_id':None})

    from core.services.entity_service import entity_service
    from core.services.product_service import product_service
    from core.services.invoice_service import invoice_service
    from core.services.warehouse_service import warehouse_service
    from core.services.manufacturing_service import manufacturing_service

    db = DatabaseConnection(); conn = db.get_connection()
    warehouse_service.bootstrap()
    wh = warehouse_service.default_warehouse_id()
    supp = entity_service.add_supplier('MFG Unit Supplier','000','')
    cat = product_service.add_category({'name':'MFG Unit Category'})
    raw = product_service.add_item({'name':'MFG Unit Raw','category_id':cat,'item_type':'مخزون','purchase_price':dec(2),'selling_price':dec(0),'quantity':dec(0),'unit':'pcs','average_cost':dec(2),'barcode':'MFG-UNIT-RAW','reorder_level':dec(0)})
    final = product_service.add_item({'name':'MFG Unit Final','category_id':cat,'item_type':'منتج نهائي','purchase_price':dec(0),'selling_price':dec(25),'quantity':dec(0),'unit':'pcs','average_cost':dec(0),'barcode':'MFG-UNIT-FIN','reorder_level':dec(0)})
    product_service.add_unit(raw, 'box', 12)
    unit_id = conn.execute('SELECT id FROM item_units WHERE item_id=? AND unit_name=?', (raw, 'box')).fetchone()['id']

    invoice_service.create({
        'type':'purchase','supplier_id':supp,'customer_id':None,'date':str(date(2026,6,15)),
        'reference':'MFG-UNIT-PUR-001','notes':'mfg units runtime','total':dec(200),'paid_amount':dec(0),
        'warehouse_id':wh,'branch_id':None,'cashbox_id':None,'bank_account_id':None,'payment_method':'cash',
        'lines':[{'item_id':raw,'quantity':dec(100),'base_qty':dec(100),'unit_price':dec(2),'total':dec(200),'unit':'pcs','conversion_factor':dec(1)}]
    })

    # BOM: 1 box of raw material produces 2 final units, with 10% waste.
    # Planned output 4 final units => 1 * 12 * (4 / 2) * 1.10 = 26.4 pcs.
    bom_id = manufacturing_service.save_bom({'product_id': final, 'quantity': dec(2), 'lines':[{'item_id': raw, 'quantity': dec(1), 'unit_id': unit_id, 'waste_percent': dec('0.10')}]})
    required = manufacturing_service.get_required_materials(bom_id, dec(4))
    assert required, 'required materials empty'
    assert_dec(required[0]['required_qty'], '26.4', 'required_qty with BOM qty/unit/waste')

    order_id = manufacturing_service.create_production_order(final, dec(4), 'unit conversion runtime', raw_warehouse_id=wh, output_warehouse_id=wh)
    reserved = conn.execute('SELECT reserved_qty FROM material_reservations WHERE order_id=? AND item_id=?', (order_id, raw)).fetchone()['reserved_qty']
    assert_dec(reserved, '26.4', 'reserved_qty')

    ok, msg = manufacturing_service.start_production(order_id); assert ok, msg
    ok, msg = manufacturing_service.consume_material(order_id, raw, dec('26.4'), dec(2)); assert ok, msg
    ok, msg = manufacturing_service.complete_production(order_id, dec(4)); assert ok, msg

    raw_qty = conn.execute('SELECT quantity FROM items WHERE id=?',(raw,)).fetchone()['quantity']
    final_row = conn.execute('SELECT quantity, average_cost FROM items WHERE id=?',(final,)).fetchone()
    wh_raw = conn.execute('SELECT quantity FROM item_warehouse_balances WHERE item_id=? AND warehouse_id=?',(raw,wh)).fetchone()['quantity']
    wh_final = conn.execute('SELECT quantity FROM item_warehouse_balances WHERE item_id=? AND warehouse_id=?',(final,wh)).fetchone()['quantity']
    out_cost = conn.execute('SELECT unit_cost FROM production_outputs WHERE order_id=?',(order_id,)).fetchone()['unit_cost']
    assert_dec(raw_qty, '73.6', 'raw item qty after complete')
    assert_dec(wh_raw, '73.6', 'raw warehouse qty after complete')
    assert_dec(final_row['quantity'], '4', 'final item qty after complete')
    assert_dec(wh_final, '4', 'final warehouse qty after complete')
    assert_dec(out_cost, '13.2', 'final unit cost from consumed raw')
    assert_dec(final_row['average_cost'], '13.2', 'final average cost')

    ok, msg = manufacturing_service.reverse_production_order(order_id); assert ok, msg
    raw_qty2 = conn.execute('SELECT quantity FROM items WHERE id=?',(raw,)).fetchone()['quantity']
    final_qty2 = conn.execute('SELECT quantity FROM items WHERE id=?',(final,)).fetchone()['quantity']
    wh_raw2 = conn.execute('SELECT quantity FROM item_warehouse_balances WHERE item_id=? AND warehouse_id=?',(raw,wh)).fetchone()['quantity']
    wh_final2 = conn.execute('SELECT quantity FROM item_warehouse_balances WHERE item_id=? AND warehouse_id=?',(final,wh)).fetchone()['quantity']
    assert_dec(raw_qty2, '100', 'raw item qty after reverse')
    assert_dec(wh_raw2, '100', 'raw warehouse qty after reverse')
    assert_dec(final_qty2, '0', 'final item qty after reverse')
    assert_dec(wh_final2, '0', 'final warehouse qty after reverse')

    result = {
        'bom_id': bom_id,
        'order_id': order_id,
        'unit_id': unit_id,
        'formula': '1 box * 12 pcs * (4 / 2 BOM qty) * 1.10 waste = 26.4 pcs',
        'required_qty': str(required[0]['required_qty']),
        'reserved_qty': str(reserved),
        'after_complete': {'raw_item_qty': str(raw_qty), 'raw_wh_qty': str(wh_raw), 'final_item_qty': str(final_row['quantity']), 'final_wh_qty': str(wh_final), 'final_unit_cost': str(out_cost), 'final_average_cost': str(final_row['average_cost'])},
        'after_reverse': {'raw_item_qty': str(raw_qty2), 'raw_wh_qty': str(wh_raw2), 'final_item_qty': str(final_qty2), 'final_wh_qty': str(wh_final2)},
    }
    report = RUNTIME / 'MANUFACTURING_UNITS_RUNTIME_TEST_REPORT.json'
    report.write_text(json.dumps({'status':'PASS','result':result}, ensure_ascii=False, indent=2), encoding='utf-8')
    return result

if __name__ == '__main__':
    result = main()
    print('manufacturing_units_runtime_test: PASS')
    print(json.dumps(result, ensure_ascii=False, indent=2))
