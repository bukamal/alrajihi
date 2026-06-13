# -*- coding: utf-8 -*-
"""Headless manufacturing integration test.

Covers BOM -> production order -> start -> consume -> complete -> reverse.
Asserts operational item stock, warehouse balances, warehouse movements, and
Inventory Ledger effects stay consistent.
"""
from __future__ import annotations
import os, sys, shutil, types, json
from pathlib import Path
from decimal import Decimal
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get('ALRAJHI_MFG_TEST_RUNTIME', '/tmp/alrajhi_manufacturing_runtime'))
if os.environ.get('ALRAJHI_TEST_RESET', '1') == '1':
    shutil.rmtree(RUNTIME, ignore_errors=True)
RUNTIME.mkdir(parents=True, exist_ok=True)
os.environ['ALRAJHI_DATA_DIR'] = str(RUNTIME)
os.environ['ALRAJHI_DB_PATH'] = str(RUNTIME / 'alrajhi_manufacturing_test.db')

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
    from core.services.inventory_service import inventory_service

    db = DatabaseConnection(); conn = db.get_connection()
    warehouse_service.bootstrap()
    wh = warehouse_service.default_warehouse_id()
    supp = entity_service.add_supplier('MFG Supplier','000','')
    cat = product_service.add_category({'name':'MFG Category'})
    raw = product_service.add_item({'name':'MFG Raw','category_id':cat,'item_type':'مخزون','purchase_price':dec(5),'selling_price':dec(0),'quantity':dec(0),'unit':'pcs','average_cost':dec(5),'barcode':'MFG-RAW','reorder_level':dec(0)})
    final = product_service.add_item({'name':'MFG Final','category_id':cat,'item_type':'منتج نهائي','purchase_price':dec(0),'selling_price':dec(20),'quantity':dec(0),'unit':'pcs','average_cost':dec(0),'barcode':'MFG-FIN','reorder_level':dec(0)})
    purchase_id = invoice_service.create({
        'type':'purchase','supplier_id':supp,'customer_id':None,'date':str(date(2026,6,13)),
        'reference':'MFG-PUR-001','notes':'mfg runtime','total':dec(50),'paid_amount':dec(0),
        'warehouse_id':wh,'branch_id':None,'cashbox_id':None,'bank_account_id':None,'payment_method':'cash',
        'lines':[{'item_id':raw,'quantity':dec(10),'base_qty':dec(10),'unit_price':dec(5),'total':dec(50),'unit':'pcs','conversion_factor':dec(1)}]
    })
    bom_id = manufacturing_service.save_bom({'product_id': final, 'quantity': dec(1), 'lines':[{'item_id': raw, 'quantity': dec(2), 'waste_percent': dec(0)}]})
    order_id = manufacturing_service.create_production_order(final, dec(2), 'runtime mfg', raw_warehouse_id=wh, output_warehouse_id=wh)
    ok, msg = manufacturing_service.start_production(order_id)
    assert ok, msg
    ok, msg = manufacturing_service.consume_material(order_id, raw, dec(4), dec(5))
    assert ok, msg
    ok, msg = manufacturing_service.complete_production(order_id, dec(2))
    assert ok, msg

    raw_qty = dec(conn.execute('SELECT quantity FROM items WHERE id=?',(raw,)).fetchone()['quantity'])
    final_qty = dec(conn.execute('SELECT quantity FROM items WHERE id=?',(final,)).fetchone()['quantity'])
    assert raw_qty == dec(6), raw_qty
    assert final_qty == dec(2), final_qty
    wh_raw = dec(conn.execute('SELECT quantity FROM item_warehouse_balances WHERE item_id=? AND warehouse_id=?',(raw,wh)).fetchone()['quantity'])
    wh_final = dec(conn.execute('SELECT quantity FROM item_warehouse_balances WHERE item_id=? AND warehouse_id=?',(final,wh)).fetchone()['quantity'])
    assert wh_raw == dec(6), wh_raw
    assert wh_final == dec(2), wh_final
    ledger = [dict(r) for r in conn.execute('SELECT movement_type,direction,quantity,item_id,warehouse_id FROM inventory_ledger WHERE reference_id=? ORDER BY id',(order_id,)).fetchall()]
    assert any(r['movement_type']=='production_consume_out' and r['direction']=='out' and r['item_id']==raw for r in ledger), ledger
    assert any(r['movement_type']=='production_output_in' and r['direction']=='in' and r['item_id']==final for r in ledger), ledger
    wh_movs = [dict(r) for r in conn.execute('SELECT movement_type,quantity,item_id FROM warehouse_movements WHERE reference_id=? ORDER BY id',(order_id,)).fetchall()]
    assert any(r['movement_type']=='production_consume_out' and dec(r['quantity']) == dec(-4) for r in wh_movs), wh_movs
    assert any(r['movement_type']=='production_output_in' and dec(r['quantity']) == dec(2) for r in wh_movs), wh_movs
    dual = inventory_service.ledger_dual_read(item_id=raw) if hasattr(inventory_service, 'ledger_dual_read') else {}

    ok, msg = manufacturing_service.reverse_production_order(order_id)
    assert ok, msg
    raw_qty2 = dec(conn.execute('SELECT quantity FROM items WHERE id=?',(raw,)).fetchone()['quantity'])
    final_qty2 = dec(conn.execute('SELECT quantity FROM items WHERE id=?',(final,)).fetchone()['quantity'])
    assert raw_qty2 == dec(10), raw_qty2
    assert final_qty2 == dec(0), final_qty2
    wh_raw2 = dec(conn.execute('SELECT quantity FROM item_warehouse_balances WHERE item_id=? AND warehouse_id=?',(raw,wh)).fetchone()['quantity'])
    wh_final2 = dec(conn.execute('SELECT quantity FROM item_warehouse_balances WHERE item_id=? AND warehouse_id=?',(final,wh)).fetchone()['quantity'])
    assert wh_raw2 == dec(10), wh_raw2
    assert wh_final2 == dec(0), wh_final2
    ledger_after = [dict(r) for r in conn.execute('SELECT movement_type,direction,quantity,item_id,warehouse_id FROM inventory_ledger WHERE reference_id=? OR reference_type=? ORDER BY id',(order_id,'production_order_reversal')).fetchall()]
    assert any(r['movement_type']=='production_consume_reverse_in' and r['direction']=='in' for r in ledger_after), ledger_after
    assert any(r['movement_type']=='production_output_reverse_out' and r['direction']=='out' for r in ledger_after), ledger_after
    return {
        'purchase_id': purchase_id,
        'bom_id': bom_id,
        'order_id': order_id,
        'warehouse_id': wh,
        'after_complete': {'raw': str(raw_qty), 'final': str(final_qty), 'wh_raw': str(wh_raw), 'wh_final': str(wh_final)},
        'after_reverse': {'raw': str(raw_qty2), 'final': str(final_qty2), 'wh_raw': str(wh_raw2), 'wh_final': str(wh_final2)},
        'ledger_rows_after_complete': ledger,
        'warehouse_movements': wh_movs,
        'dual_read_keys': sorted(dual.keys()) if isinstance(dual, dict) else type(dual).__name__,
    }

if __name__ == '__main__':
    result = main()
    report = RUNTIME / 'MANUFACTURING_RUNTIME_FLOW_TEST_REPORT.json'
    report.write_text(json.dumps({'status':'PASS','result':result}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('manufacturing_runtime_flow_test: PASS')
    print(json.dumps(result, ensure_ascii=False, indent=2))
