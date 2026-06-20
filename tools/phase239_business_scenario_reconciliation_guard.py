# -*- coding: utf-8 -*-
"""Phase 239 business scenario reconciliation guard.

Executes a compact end-to-end ERP scenario against a fresh local database:
materials with/without opening quantities, sub-units, purchases/sales with full
and partial payments, partial sales/purchase returns, receipt/payment vouchers,
BOM and production order consumption/output.  The guard asserts cross-module
inventory, cashbox, voucher, and manufacturing reconciliation.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import traceback
import types
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get('ALRAJHI_PHASE239_RUNTIME', '/tmp/alrajhi_phase239_business_reconciliation'))
shutil.rmtree(RUNTIME, ignore_errors=True)
RUNTIME.mkdir(parents=True, exist_ok=True)
os.environ['ALRAJHI_DATA_DIR'] = str(RUNTIME)
os.environ['ALRAJHI_DB_PATH'] = str(RUNTIME / 'phase239_business.db')

# Headless PyQt shim for CI containers that do not have PyQt5 installed.
try:
    import PyQt5  # noqa: F401
except Exception:
    settings_store = {'network/mode': 'local', 'workflow/enabled': 'false'}

    class QSettings:
        def __init__(self, *a, **k):
            pass

        def value(self, key, default=None, *a, **k):
            return settings_store.get(key, default)

        def setValue(self, key, value):
            settings_store[key] = value

        def remove(self, key):
            settings_store.pop(key, None)

    class QObject:
        pass

    class QTimer:
        @staticmethod
        def singleShot(*a, **k):
            pass

    class Qt:
        pass

    class QSize:
        def __init__(self, *a):
            pass

    class QUrl:
        pass

    def pyqtSignal(*a, **k):
        class Sig:
            def connect(self, *a, **k):
                pass

            def emit(self, *a, **k):
                pass

        return Sig()

    class Dummy:
        def __init__(self, *a, **k):
            pass

        def __getattr__(self, name):
            def f(*a, **k):
                return None
            return f

    qtcore = types.ModuleType('PyQt5.QtCore')
    for name, obj in dict(QSettings=QSettings, QObject=QObject, QTimer=QTimer, Qt=Qt, QSize=QSize, QUrl=QUrl, pyqtSignal=pyqtSignal).items():
        setattr(qtcore, name, obj)
    qtwidgets = types.ModuleType('PyQt5.QtWidgets')
    for name in 'QApplication QWidget QMainWindow QDialog QMessageBox QVBoxLayout QHBoxLayout QLabel QPushButton QLineEdit QTableWidget QTableWidgetItem QComboBox QSpinBox QDoubleSpinBox QDateEdit QTextEdit QCheckBox QGroupBox QFormLayout QTabWidget QFileDialog QInputDialog QProgressDialog QFrame QSplitter QScrollArea'.split():
        setattr(qtwidgets, name, Dummy)
    qtgui = types.ModuleType('PyQt5.QtGui')
    for name in 'QIcon QPixmap QFont QColor QDesktopServices'.split():
        setattr(qtgui, name, Dummy)
    pyqt = types.ModuleType('PyQt5')
    pyqt.QtCore = qtcore
    pyqt.QtWidgets = qtwidgets
    pyqt.QtGui = qtgui
    sys.modules.update({'PyQt5': pyqt, 'PyQt5.QtCore': qtcore, 'PyQt5.QtWidgets': qtwidgets, 'PyQt5.QtGui': qtgui})

sys.path.insert(0, str(ROOT / 'alrajhi_client'))
sys.path.insert(0, str(ROOT))


def D(value) -> Decimal:
    return Decimal(str(value))


def assert_dec(name: str, actual, expected, tolerance=Decimal('0.0001')):
    a = D(actual)
    e = D(expected)
    if abs(a - e) > tolerance:
        raise AssertionError(f'{name}: expected {e}, got {a}')
    return str(a)


def line(item, qty, price, unit='pcs', factor=1, unit_id=None, unit_cost=None):
    q = D(qty)
    p = D(price)
    f = D(factor)
    return {
        'item_id': item,
        'quantity': q,
        'base_qty': q * f,
        'quantity_in_base': q * f,
        'unit_price': p,
        'price': p,
        'total': q * p,
        'unit': unit,
        'unit_id': unit_id,
        'conversion_factor': f,
        'unit_cost': D(unit_cost if unit_cost is not None else price),
    }


def main() -> dict:
    from database.migrations import init_database
    from database.connection import DatabaseConnection
    from auth.session import UserSession

    init_database()
    UserSession.login({'id': 'admin', 'username': 'admin', 'role': 'admin', 'branch_id': None})

    from core.item_types import STOCK, FINISHED_PRODUCT
    from core.services.settings_service import settings_service
    from core.services.warehouse_service import warehouse_service
    from core.services.cashbox_service import cashbox_service
    from core.services.entity_service import entity_service
    from core.services.product_service import product_service
    from core.services.invoice_service import invoice_service
    from core.services.sales_return_service import sales_return_service
    from core.services.purchase_return_service import purchase_return_service
    from core.services.voucher_service import voucher_service
    from core.services.manufacturing_service import manufacturing_service
    from core.services.reporting_service import reporting_service

    try:
        settings_service.set('workflow/enabled', 'false')
    except Exception:
        pass

    db = DatabaseConnection()
    conn = db.get_connection()
    warehouse_service.bootstrap()
    cashbox_service.bootstrap()
    wh = warehouse_service.default_warehouse_id()
    cb = cashbox_service.default_cashbox_id()
    if not wh:
        raise AssertionError('default warehouse was not created')
    if not cb:
        raise AssertionError('default cashbox was not created')

    cat = product_service.add_category({'name': 'Phase239 Scenario Cat'})
    raw_a = product_service.add_item({
        'name': 'P239 Raw A opening with unit', 'category_id': cat, 'item_type': STOCK,
        'purchase_price': D(4), 'selling_price': D(8), 'quantity': D(50), 'unit': 'kg',
        'average_cost': D(4), 'barcode': 'P239-RAW-A', 'reorder_level': D(5),
        'units': [{'unit_name': 'box', 'conversion_factor': D(10), 'barcode': 'P239-RAW-A-BOX'}],
    })
    raw_b = product_service.add_item({
        'name': 'P239 Raw B no opening', 'category_id': cat, 'item_type': STOCK,
        'purchase_price': D(2), 'selling_price': D(5), 'quantity': D(0), 'unit': 'pcs',
        'average_cost': D(2), 'barcode': 'P239-RAW-B', 'reorder_level': D(5),
    })
    raw_c = product_service.add_item({
        'name': 'P239 Raw C opening no unit', 'category_id': cat, 'item_type': STOCK,
        'purchase_price': D(3), 'selling_price': D(8), 'quantity': D(7), 'unit': 'pcs',
        'average_cost': D(3), 'barcode': 'P239-RAW-C', 'reorder_level': D(2),
    })
    final = product_service.add_item({
        'name': 'P239 Finished Product', 'category_id': cat, 'item_type': FINISHED_PRODUCT,
        'purchase_price': D(0), 'selling_price': D(50), 'quantity': D(0), 'unit': 'pcs',
        'average_cost': D(0), 'barcode': 'P239-FINISHED', 'reorder_level': D(1),
    })

    warehouse_service.bootstrap()
    raw_a_units = product_service.item_units(raw_a)
    if not raw_a_units:
        raise AssertionError('sub-units submitted with add_item() were not persisted')
    unit_id = int(raw_a_units[0]['id'])
    assert_dec('raw_a opening warehouse qty', warehouse_service.available_qty(raw_a, wh), 50)
    assert_dec('raw_c opening warehouse qty', warehouse_service.available_qty(raw_c, wh), 7)

    cust = entity_service.add_customer('P239 Customer', '111', '')
    supp = entity_service.add_supplier('P239 Supplier', '222', '')

    def inv_payload(typ, lines, ref, paid):
        total = sum((D(l['total']) for l in lines), D(0))
        return {
            'type': typ,
            'customer_id': cust if typ == 'sale' else None,
            'supplier_id': supp if typ == 'purchase' else None,
            'date': '2026-06-19',
            'reference': ref,
            'notes': 'phase239 scenario',
            'total': total,
            'paid_amount': D(paid),
            'paid': D(paid),
            'warehouse_id': wh,
            'branch_id': None,
            'cashbox_id': cb,
            'bank_account_id': None,
            'payment_method': 'cash',
            'lines': lines,
        }

    purchase_partial = invoice_service.create(inv_payload('purchase', [line(raw_b, 30, 2, unit_cost=2)], 'P239-PARTIAL-PURCHASE', 40))
    purchase_full = invoice_service.create(inv_payload('purchase', [line(raw_c, 5, 3, unit_cost=3)], 'P239-FULL-PURCHASE', 15))
    sale_partial = invoice_service.create(inv_payload('sale', [
        line(raw_a, 2, 50, unit='box', factor=10, unit_id=unit_id, unit_cost=4),
        line(raw_b, 5, 6, unit_cost=2),
    ], 'P239-PARTIAL-SALE', 60))
    sale_full = invoice_service.create(inv_payload('sale', [line(raw_c, 2, 8, unit_cost=3)], 'P239-FULL-SALE', 16))

    voucher_receipt = voucher_service.add({
        'type': 'receipt', 'customer_id': cust, 'supplier_id': None, 'invoice_id': sale_partial,
        'amount': D(50), 'date': '2026-06-20', 'reference': 'P239-RECEIPT',
        'payment_method': 'cash', 'cashbox_id': cb, 'description': 'phase239 partial receipt',
    })
    voucher_payment = voucher_service.add({
        'type': 'payment', 'customer_id': None, 'supplier_id': supp, 'invoice_id': purchase_partial,
        'amount': D(10), 'date': '2026-06-20', 'reference': 'P239-PAYMENT',
        'payment_method': 'cash', 'cashbox_id': cb, 'description': 'phase239 partial payment',
    })

    sale_returnable = sales_return_service.invoice_returnable_lines(sale_partial)
    sale_raw_a = [x for x in sale_returnable if int(x['item_id']) == raw_a][0]
    sales_return = sales_return_service.create_return({
        'original_invoice_id': sale_partial, 'date': '2026-06-21', 'warehouse_id': wh,
        'refund_amount': '0', 'cashbox_id': cb, 'payment_method': 'cash',
        'lines': [{'original_invoice_line_id': sale_raw_a['id'], 'quantity': '0.5', 'unit_id': unit_id, 'unit': 'box'}],
    })
    purchase_returnable = purchase_return_service.invoice_returnable_lines(purchase_partial)
    purchase_raw_b = [x for x in purchase_returnable if int(x['item_id']) == raw_b][0]
    purchase_return = purchase_return_service.create_return({
        'original_invoice_id': purchase_partial, 'date': '2026-06-21', 'warehouse_id': wh,
        'refund_amount': '0', 'cashbox_id': cb, 'payment_method': 'cash',
        'lines': [{'original_invoice_line_id': purchase_raw_b['id'], 'quantity': '3'}],
    })

    bom = manufacturing_service.save_bom({
        'product_id': final,
        'quantity': D(1),
        'lines': [
            {'item_id': raw_a, 'quantity': D(1), 'unit_id': unit_id, 'unit': 'box', 'conversion_factor': D(10), 'base_qty': D(10), 'waste_percent': D(0)},
            {'item_id': raw_b, 'quantity': D(2), 'unit': 'pcs', 'conversion_factor': D(1), 'base_qty': D(2), 'waste_percent': D(0)},
        ],
    })
    required = manufacturing_service.get_required_materials_recursive(final, D(2), wh)
    required_by_item = {int(m['item_id']): m for m in required}
    assert_dec('manufacturing raw_a required qty', required_by_item[raw_a]['required_qty'], 20)
    assert_dec('manufacturing raw_b required qty', required_by_item[raw_b]['required_qty'], 4)
    if not all(m.get('is_sufficient') for m in required):
        raise AssertionError({'required_materials_not_sufficient': required})

    production_order = manufacturing_service.create_production_order(final, D(2), 'phase239 production', wh, wh)
    ok, msg = manufacturing_service.start_production(production_order)
    if not ok:
        raise AssertionError(f'failed to start production: {msg}')
    reservations = manufacturing_service.get_reservations(production_order)
    if len(reservations) != 2:
        raise AssertionError({'expected_two_reservations': reservations})
    for reservation in reservations:
        qty = D(reservation.get('reserved_qty'))
        unit_cost = D(4 if int(reservation['item_id']) == raw_a else 2)
        ok, msg = manufacturing_service.consume_material(production_order, int(reservation['item_id']), qty, unit_cost)
        if not ok:
            raise AssertionError(f"consume failed for {reservation['item_id']}: {msg}")
    ok, msg = manufacturing_service.complete_production(production_order, D(2))
    if not ok:
        raise AssertionError(f'complete production failed: {msg}')

    # Inventory reconciliation after all operations.
    inventory_expected = {
        raw_a: D(15),   # 50 - 20 sale + 5 return - 20 manufacturing
        raw_b: D(18),   # 0 + 30 purchase - 5 sale - 3 purchase return - 4 manufacturing
        raw_c: D(10),   # 7 + 5 full purchase - 2 full sale
        final: D(2),    # 2 produced
    }
    inventory_actual = {}
    for item_id, expected in inventory_expected.items():
        actual = warehouse_service.available_qty(item_id, wh)
        inventory_actual[item_id] = assert_dec(f'warehouse balance item {item_id}', actual, expected)

    sale_invoice = invoice_service.get(sale_partial)
    purchase_invoice = invoice_service.get(purchase_partial)
    assert_dec('partial sale paid after receipt voucher', sale_invoice.get('paid'), 110)
    assert_dec('partial purchase paid after payment voucher', purchase_invoice.get('paid'), 50)

    cash_summary = reporting_service.cash_bank_summary()
    # Immediate invoice paid amounts: +60 -40 +16 -15; vouchers: +50 -10; no return refunds.
    assert_dec('cashbox summary cash_total', cash_summary.get('cash_total'), 61)
    cash_movements = cashbox_service.movements(limit=50, cashbox_id=cb)
    movement_types = {m.get('movement_type') for m in cash_movements}
    for expected_type in ('invoice_sale_payment', 'invoice_purchase_payment', 'receipt', 'payment'):
        if expected_type not in movement_types:
            raise AssertionError({'missing_cash_movement_type': expected_type, 'movement_types': sorted(movement_types)})

    profit_rows = reporting_service.invoice_profit_report(start_date='2026-06-19', end_date='2026-06-22')
    if not isinstance(profit_rows, list):
        raise AssertionError('invoice_profit_report did not return a list')
    if len(profit_rows) < 2:
        raise AssertionError({'invoice_profit_report_missing_sales': profit_rows})
    manufacturing_report = reporting_service.manufacturing_orders_report(start_date='2026-06-19', end_date='2026-06-22', status='completed')
    if not any(int(r.get('id') or 0) == production_order for r in manufacturing_report):
        raise AssertionError({'manufacturing_report_missing_completed_order': manufacturing_report})
    product_costs = reporting_service.product_cost_report(search='P239 Finished', limit=50)
    if not any(int(r.get('id') or 0) == final for r in product_costs):
        raise AssertionError({'product_cost_report_missing_finished_item': product_costs})

    order = manufacturing_service.get_production_order(production_order)
    if not order or order.get('status') != 'completed':
        raise AssertionError({'production_order_not_completed': order})

    report = {
        'runtime_db': os.environ['ALRAJHI_DB_PATH'],
        'ids': {
            'raw_a': raw_a, 'raw_b': raw_b, 'raw_c': raw_c, 'finished': final,
            'purchase_partial': purchase_partial, 'purchase_full': purchase_full,
            'sale_partial': sale_partial, 'sale_full': sale_full,
            'sales_return': sales_return, 'purchase_return': purchase_return,
            'voucher_receipt': voucher_receipt, 'voucher_payment': voucher_payment,
            'bom': bom, 'production_order': production_order,
        },
        'inventory_actual': inventory_actual,
        'cash_total': str(cash_summary.get('cash_total')),
        'cash_movement_types': sorted(movement_types),
        'required_materials': [{k: str(v) if isinstance(v, Decimal) else v for k, v in m.items()} for m in required],
        'profit_row_count': len(profit_rows),
        'manufacturing_report_count': len(manufacturing_report),
        'product_cost_report_count': len(product_costs),
        'production_status': order.get('status'),
    }
    out_dir = ROOT / 'tools' / 'audit_outputs'
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'phase239_business_scenario_reconciliation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    try:
        result = main()
        print('PASS phase239_business_scenario_reconciliation')
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
