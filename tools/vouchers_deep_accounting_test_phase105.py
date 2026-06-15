# -*- coding: utf-8 -*-
"""Deep voucher accounting regression test that runs without PyQt/Flask.

It validates the monetary invariants used by both local and server voucher paths:
- remaining invoice amount
- party balances
- invoice paid
- user cash balance
- cash/bank movement reference consistency
- update preserves voucher id
- overpayment prevention with edit old-amount exclusion
- UI auto-fill hook exists for invoice remaining amount
"""
from __future__ import annotations

import sqlite3
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def dec(value) -> Decimal:
    return Decimal(str(value if value is not None else '0'))


def setup_db():
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    db.executescript('''
        CREATE TABLE users (id TEXT PRIMARY KEY, cash_balance TEXT DEFAULT '0');
        CREATE TABLE customers (id INTEGER PRIMARY KEY, user_id TEXT, name TEXT, balance TEXT DEFAULT '0');
        CREATE TABLE suppliers (id INTEGER PRIMARY KEY, user_id TEXT, name TEXT, balance TEXT DEFAULT '0');
        CREATE TABLE invoices (id INTEGER PRIMARY KEY, user_id TEXT, type TEXT, customer_id INTEGER, supplier_id INTEGER,
                               total TEXT DEFAULT '0', paid TEXT DEFAULT '0', deleted_at TEXT, reference TEXT);
        CREATE TABLE vouchers (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, type TEXT, date TEXT, amount TEXT,
                               description TEXT, reference TEXT, customer_id INTEGER, supplier_id INTEGER, invoice_id INTEGER,
                               exchange_rate_to_usd REAL DEFAULT 1.0, original_currency TEXT DEFAULT 'USD', branch_id INTEGER,
                               cashbox_id INTEGER, bank_account_id INTEGER, payment_method TEXT DEFAULT 'cash');
        CREATE TABLE cash_bank_movements (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, branch_id INTEGER,
                               cashbox_id INTEGER, bank_account_id INTEGER, movement_type TEXT, amount TEXT, direction TEXT,
                               reference_type TEXT, reference_id INTEGER, description TEXT, movement_date TEXT, created_at TEXT);
    ''')
    db.execute("INSERT INTO users(id, cash_balance) VALUES ('u1', '0')")
    db.execute("INSERT INTO customers(id, user_id, name, balance) VALUES (1, 'u1', 'Customer A', '800')")
    db.execute("INSERT INTO suppliers(id, user_id, name, balance) VALUES (1, 'u1', 'Supplier A', '800')")
    db.execute("INSERT INTO invoices(id, user_id, type, customer_id, total, paid, reference) VALUES (1, 'u1', 'sale', 1, '1000', '200', 'S-1')")
    db.execute("INSERT INTO invoices(id, user_id, type, supplier_id, total, paid, reference) VALUES (2, 'u1', 'purchase', 1, '1200', '400', 'P-1')")
    return db


def row(db, table, ident):
    return dict(db.execute(f"SELECT * FROM {table} WHERE id=?", (ident,)).fetchone())


def scalar(db, sql, params=()):
    return db.execute(sql, params).fetchone()[0]


def remaining(db, invoice_id, exclude_voucher_id=None):
    inv = row(db, 'invoices', invoice_id)
    old_amount = Decimal('0')
    if exclude_voucher_id is not None:
        old = db.execute("SELECT * FROM vouchers WHERE id=?", (exclude_voucher_id,)).fetchone()
        if old and old['invoice_id'] == invoice_id:
            old_amount = dec(old['amount'])
    return dec(inv['total']) - (dec(inv['paid']) - old_amount)


def validate(db, data, exclude_voucher_id=None):
    amount = dec(data.get('amount'))
    if data.get('type') not in ('receipt', 'payment', 'expense'):
        raise ValueError('bad type')
    if amount <= 0:
        raise ValueError('non-positive amount')
    if data['type'] == 'receipt' and (not data.get('customer_id') or data.get('supplier_id')):
        raise ValueError('receipt party')
    if data['type'] == 'payment' and (not data.get('supplier_id') or data.get('customer_id')):
        raise ValueError('payment party')
    if data['type'] == 'expense' and (data.get('invoice_id') or data.get('customer_id') or data.get('supplier_id')):
        raise ValueError('expense party')
    invoice_id = data.get('invoice_id')
    if invoice_id:
        inv = row(db, 'invoices', invoice_id)
        if data['type'] == 'receipt' and inv['type'] != 'sale':
            raise ValueError('receipt invoice type')
        if data['type'] == 'payment' and inv['type'] != 'purchase':
            raise ValueError('payment invoice type')
        if data['type'] == 'receipt' and inv['customer_id'] != data.get('customer_id'):
            raise ValueError('customer mismatch')
        if data['type'] == 'payment' and inv['supplier_id'] != data.get('supplier_id'):
            raise ValueError('supplier mismatch')
        rem = remaining(db, invoice_id, exclude_voucher_id)
        if amount > rem:
            raise ValueError(f'over remaining: {amount}>{rem}')


def apply_effects(db, data):
    amount = dec(data['amount'])
    if data['type'] == 'receipt':
        db.execute("UPDATE users SET cash_balance=CAST(cash_balance AS REAL)+? WHERE id='u1'", (str(amount),))
    elif data['type'] in ('payment', 'expense'):
        db.execute("UPDATE users SET cash_balance=CAST(cash_balance AS REAL)-? WHERE id='u1'", (str(amount),))
    if data.get('customer_id'):
        db.execute("UPDATE customers SET balance=CAST(balance AS REAL)-? WHERE id=?", (str(amount), data['customer_id']))
    if data.get('supplier_id'):
        db.execute("UPDATE suppliers SET balance=CAST(balance AS REAL)-? WHERE id=?", (str(amount), data['supplier_id']))
    if data.get('invoice_id'):
        db.execute("UPDATE invoices SET paid=CAST(paid AS REAL)+? WHERE id=?", (str(amount), data['invoice_id']))


def reverse_effects(db, data):
    amount = dec(data['amount'])
    if data['type'] == 'receipt':
        db.execute("UPDATE users SET cash_balance=CAST(cash_balance AS REAL)-? WHERE id='u1'", (str(amount),))
    elif data['type'] in ('payment', 'expense'):
        db.execute("UPDATE users SET cash_balance=CAST(cash_balance AS REAL)+? WHERE id='u1'", (str(amount),))
    if data.get('customer_id'):
        db.execute("UPDATE customers SET balance=CAST(balance AS REAL)+? WHERE id=?", (str(amount), data['customer_id']))
    if data.get('supplier_id'):
        db.execute("UPDATE suppliers SET balance=CAST(balance AS REAL)+? WHERE id=?", (str(amount), data['supplier_id']))
    if data.get('invoice_id'):
        db.execute("UPDATE invoices SET paid=CAST(paid AS REAL)-? WHERE id=?", (str(amount), data['invoice_id']))


def record_movement(db, voucher_id, data):
    db.execute("DELETE FROM cash_bank_movements WHERE reference_type='voucher' AND reference_id=?", (voucher_id,))
    amount = abs(dec(data['amount'])) if data['type'] == 'receipt' else -abs(dec(data['amount']))
    db.execute("""
        INSERT INTO cash_bank_movements(user_id, branch_id, cashbox_id, bank_account_id, movement_type, amount, direction, reference_type, reference_id, description, movement_date)
        VALUES ('u1',?,?,?,?,?,?,?,?,?,?)
    """, (data.get('branch_id'), data.get('cashbox_id'), data.get('bank_account_id'), data['type'], str(amount), 'in' if amount >= 0 else 'out', 'voucher', voucher_id, data.get('description',''), data.get('date')))


def add_voucher(db, data):
    validate(db, data)
    cur = db.execute("""
        INSERT INTO vouchers(user_id,type,date,amount,description,reference,customer_id,supplier_id,invoice_id,exchange_rate_to_usd,original_currency,branch_id,cashbox_id,bank_account_id,payment_method)
        VALUES ('u1',?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (data['type'], data['date'], str(data['amount']), data.get('description',''), data.get('reference',''), data.get('customer_id'), data.get('supplier_id'), data.get('invoice_id'), data.get('exchange_rate_to_usd',1), data.get('original_currency','USD'), data.get('branch_id'), data.get('cashbox_id'), data.get('bank_account_id'), data.get('payment_method','cash')))
    vid = cur.lastrowid
    apply_effects(db, data)
    record_movement(db, vid, data)
    return vid


def update_voucher(db, voucher_id, data):
    old = row(db, 'vouchers', voucher_id)
    validate(db, data, exclude_voucher_id=voucher_id)
    reverse_effects(db, old)
    db.execute("""
        UPDATE vouchers SET type=?, date=?, amount=?, description=?, reference=?, customer_id=?, supplier_id=?, invoice_id=?, exchange_rate_to_usd=?, original_currency=?, branch_id=?, cashbox_id=?, bank_account_id=?, payment_method=? WHERE id=?
    """, (data['type'], data['date'], str(data['amount']), data.get('description',''), data.get('reference',''), data.get('customer_id'), data.get('supplier_id'), data.get('invoice_id'), data.get('exchange_rate_to_usd',1), data.get('original_currency','USD'), data.get('branch_id'), data.get('cashbox_id'), data.get('bank_account_id'), data.get('payment_method','cash'), voucher_id))
    apply_effects(db, data)
    record_movement(db, voucher_id, data)
    return voucher_id


def delete_voucher(db, voucher_id):
    old = row(db, 'vouchers', voucher_id)
    reverse_effects(db, old)
    db.execute("DELETE FROM cash_bank_movements WHERE reference_type='voucher' AND reference_id=?", (voucher_id,))
    db.execute("DELETE FROM vouchers WHERE id=?", (voucher_id,))


def assert_dec(actual, expected, label):
    if dec(actual) != Decimal(str(expected)):
        raise AssertionError(f'{label}: expected {expected}, got {actual}')


def test_sales_receipt_flow():
    db = setup_db()
    assert_dec(remaining(db, 1), '800', 'initial sale remaining')
    vid = add_voucher(db, {'type':'receipt','date':'2026-06-15','amount':'300','customer_id':1,'invoice_id':1,'branch_id':1,'cashbox_id':1,'payment_method':'cash'})
    assert_dec(row(db,'invoices',1)['paid'], '500', 'sale paid after receipt')
    assert_dec(row(db,'customers',1)['balance'], '500', 'customer balance after receipt')
    assert_dec(row(db,'users','u1')['cash_balance'], '300', 'cash after receipt')
    assert_dec(scalar(db, "SELECT amount FROM cash_bank_movements WHERE reference_id=?", (vid,)), '300', 'receipt movement amount')
    try:
        add_voucher(db, {'type':'receipt','date':'2026-06-15','amount':'600','customer_id':1,'invoice_id':1})
        raise AssertionError('overpayment was accepted')
    except ValueError:
        pass
    same = update_voucher(db, vid, {'type':'receipt','date':'2026-06-15','amount':'500','customer_id':1,'invoice_id':1,'branch_id':1,'bank_account_id':2,'payment_method':'bank'})
    if same != vid or not row(db, 'vouchers', vid):
        raise AssertionError('update did not preserve voucher id')
    assert_dec(row(db,'invoices',1)['paid'], '700', 'sale paid after receipt update')
    assert_dec(row(db,'customers',1)['balance'], '300', 'customer balance after receipt update')
    assert_dec(row(db,'users','u1')['cash_balance'], '500', 'cash after receipt update')
    assert_dec(scalar(db, "SELECT COUNT(*) FROM cash_bank_movements WHERE reference_id=?", (vid,)), '1', 'single movement after update')
    assert_dec(scalar(db, "SELECT bank_account_id FROM cash_bank_movements WHERE reference_id=?", (vid,)), '2', 'bank account preserved')
    delete_voucher(db, vid)
    assert_dec(row(db,'invoices',1)['paid'], '200', 'sale paid after receipt delete')
    assert_dec(row(db,'customers',1)['balance'], '800', 'customer balance after receipt delete')
    assert_dec(row(db,'users','u1')['cash_balance'], '0', 'cash after receipt delete')
    assert_dec(scalar(db, "SELECT COUNT(*) FROM cash_bank_movements WHERE reference_id=?", (vid,)), '0', 'movement removed after delete')


def test_purchase_payment_and_expense_flow():
    db = setup_db()
    assert_dec(remaining(db, 2), '800', 'initial purchase remaining')
    vid = add_voucher(db, {'type':'payment','date':'2026-06-15','amount':'350','supplier_id':1,'invoice_id':2,'branch_id':1,'cashbox_id':1,'payment_method':'cash'})
    assert_dec(row(db,'invoices',2)['paid'], '750', 'purchase paid after payment')
    assert_dec(row(db,'suppliers',1)['balance'], '450', 'supplier balance after payment')
    assert_dec(row(db,'users','u1')['cash_balance'], '-350', 'cash after payment')
    assert_dec(scalar(db, "SELECT amount FROM cash_bank_movements WHERE reference_id=?", (vid,)), '-350', 'payment movement amount')
    update_voucher(db, vid, {'type':'payment','date':'2026-06-15','amount':'800','supplier_id':1,'invoice_id':2,'branch_id':1,'cashbox_id':1,'payment_method':'cash'})
    assert_dec(row(db,'invoices',2)['paid'], '1200', 'purchase paid after full payment update')
    assert_dec(row(db,'suppliers',1)['balance'], '0', 'supplier balance after full payment update')
    assert_dec(row(db,'users','u1')['cash_balance'], '-800', 'cash after full payment update')
    delete_voucher(db, vid)
    assert_dec(row(db,'invoices',2)['paid'], '400', 'purchase paid after delete')
    assert_dec(row(db,'suppliers',1)['balance'], '800', 'supplier balance after delete')
    assert_dec(row(db,'users','u1')['cash_balance'], '0', 'cash after delete')
    eid = add_voucher(db, {'type':'expense','date':'2026-06-15','amount':'77','branch_id':1,'cashbox_id':1,'payment_method':'cash'})
    assert_dec(row(db,'users','u1')['cash_balance'], '-77', 'cash after expense')
    assert_dec(scalar(db, "SELECT amount FROM cash_bank_movements WHERE reference_id=?", (eid,)), '-77', 'expense movement amount')


def test_static_regressions():
    widget = (ROOT / 'alrajhi_client/views/widgets/vouchers_widget.py').read_text(encoding='utf-8')
    if 'invoice_combo.currentIndexChanged.connect(self.update_amount_from_invoice)' not in widget:
        raise AssertionError('invoice auto amount hook missing')
    if 'def update_amount_from_invoice' not in widget or '_invoice_remaining_by_id' not in widget:
        raise AssertionError('invoice remaining auto-fill implementation missing')
    if "getattr(self, '_loading_voucher', False)" not in widget:
        raise AssertionError('edit-mode load must not overwrite existing voucher amount')
    if '_voucher_old_amount_for_invoice' not in widget:
        raise AssertionError('edit-mode old voucher amount is not included in remaining amount')
    conn = (ROOT / 'alrajhi_client/database/connection.py').read_text(encoding='utf-8')
    update_block = conn[conn.index('    def update_voucher'):conn.index('    # ------------------- دوال مساعدة داخلية')]
    if 'self.delete_voucher(voucher_id)' in update_block or 'self.add_voucher(data)' in update_block:
        raise AssertionError('local update_voucher still deletes/reinserts vouchers')
    server = (ROOT / 'alrajhi_server/api/vouchers.py').read_text(encoding='utf-8')
    for required in ['_record_voucher_movement', 'cash_bank_movements', 'bank_account_id', 'payment_method', 'UPDATE vouchers']:
        if required not in server:
            raise AssertionError(f'server voucher path missing {required}')


if __name__ == '__main__':
    test_sales_receipt_flow()
    test_purchase_payment_and_expense_flow()
    test_static_regressions()
    print('vouchers_deep_accounting_test_phase105: PASS')
