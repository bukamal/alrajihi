# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from alrajhi_server.repositories.return_repository import get_return_repository
from alrajhi_server.services.branch_access_policy import BranchAccessError, branch_access_policy

returns_bp = Blueprint('returns', __name__)


def _branch_denied(exc):
    return jsonify({'error': str(exc), 'code': 'BRANCH_ACCESS_DENIED'}), 403

def _branch_where(user_id, alias, requested_branch_id=None):
    sql, params = branch_access_policy.scope_sql(user_id, alias=alias, branch_column='branch_id', requested_branch_id=requested_branch_id)
    sql = sql.strip()
    if sql.upper().startswith('AND '):
        sql = sql[4:]
    return sql, params

def _require_branch(user_id, branch_id, context):
    return branch_access_policy.require(user_id, branch_id, context=context)


def _dec(value, default='0'):
    try:
        return Decimal(str(value if value is not None else default))
    except Exception:
        return Decimal(str(default))


def _next_no(db, table, user_id, prefix):
    year = datetime.datetime.now().strftime('%Y')
    full_prefix = f'{prefix}-{year}-'
    row = db.query(f"SELECT MAX(return_no) AS max_no FROM {table} WHERE user_id=? AND return_no LIKE ?", (user_id, full_prefix + '%')).fetchone()
    max_no = row['max_no'] if row else None
    try:
        num = int(str(max_no).split('-')[-1]) + 1 if max_no else 1
    except Exception:
        num = 1
    return f'{full_prefix}{num:04d}'


def _update_item_quantity(db, item_id, user_id):
    row = db.query("""
        SELECT SUM(CASE
            WHEN movement_type IN ('opening','purchase','adjustment','production_out','sales_return','consumption_reverse') THEN CAST(quantity AS REAL)
            WHEN movement_type IN ('sale','production_consume','purchase_return') THEN -CAST(quantity AS REAL)
            ELSE 0 END) AS total_qty
        FROM inventory_movements
        WHERE item_id=? AND user_id=?
    """, (item_id, user_id)).fetchone()
    qty = _dec(row['total_qty']) if row and row['total_qty'] is not None else Decimal('0')
    db.query("UPDATE items SET quantity=? WHERE id=? AND user_id=?", (str(qty), item_id, user_id))


def _recalculate_average_cost(db, item_id, user_id):
    row = db.query("""
        SELECT SUM(CAST(quantity AS REAL)) AS total_qty,
               SUM(CAST(quantity AS REAL) * CAST(unit_cost AS REAL)) AS total_cost
        FROM inventory_movements
        WHERE item_id=? AND user_id=? AND movement_type IN ('opening','purchase','adjustment','production_out','sales_return','consumption_reverse')
    """, (item_id, user_id)).fetchone()
    total_qty = _dec(row['total_qty']) if row and row['total_qty'] is not None else Decimal('0')
    total_cost = _dec(row['total_cost']) if row and row['total_cost'] is not None else Decimal('0')
    avg = total_cost / total_qty if total_qty > 0 else Decimal('0')
    db.query("UPDATE items SET average_cost=? WHERE id=? AND user_id=?", (str(avg), item_id, user_id))



def _warehouse_available_qty(db, user_id, item_id, warehouse_id):
    if not item_id or not warehouse_id:
        row = db.query("""
            SELECT SUM(CASE
                WHEN movement_type IN ('opening','purchase','adjustment','production_out','sales_return','consumption_reverse') THEN CAST(quantity AS REAL)
                WHEN movement_type IN ('sale','production_consume','purchase_return') THEN -CAST(quantity AS REAL)
                ELSE 0 END) AS quantity
            FROM inventory_movements
            WHERE user_id=? AND item_id=?
        """, (user_id, item_id)).fetchone()
        return _dec(row['quantity']) if row and row['quantity'] is not None else Decimal('0')
    row = db.query("""
        SELECT CAST(COALESCE(quantity,'0') AS REAL) AS quantity
        FROM item_warehouse_balances
        WHERE user_id=? AND item_id=? AND warehouse_id=?
    """, (user_id, item_id, warehouse_id)).fetchone()
    return _dec(row['quantity']) if row and row['quantity'] is not None else Decimal('0')


def _update_warehouse_balance(db, user_id, item_id, warehouse_id):
    if not item_id or not warehouse_id:
        return
    row = db.query("""
        SELECT SUM(CAST(quantity AS REAL)) AS quantity,
               SUM(CASE WHEN CAST(quantity AS REAL) > 0 THEN CAST(quantity AS REAL) * CAST(COALESCE(unit_cost,'0') AS REAL) ELSE 0 END) AS inbound_cost,
               SUM(CASE WHEN CAST(quantity AS REAL) > 0 THEN CAST(quantity AS REAL) ELSE 0 END) AS inbound_qty
        FROM warehouse_movements
        WHERE user_id=? AND item_id=? AND warehouse_id=?
    """, (user_id, item_id, warehouse_id)).fetchone()
    qty = _dec(row['quantity']) if row and row['quantity'] is not None else Decimal('0')
    inbound_qty = _dec(row['inbound_qty']) if row and row['inbound_qty'] is not None else Decimal('0')
    inbound_cost = _dec(row['inbound_cost']) if row and row['inbound_cost'] is not None else Decimal('0')
    avg = inbound_cost / inbound_qty if inbound_qty > 0 else Decimal('0')
    now = datetime.datetime.now().isoformat()
    db.query("""
        INSERT INTO item_warehouse_balances (user_id,item_id,warehouse_id,quantity,average_cost,updated_at)
        VALUES (?,?,?,?,?,?)
        ON CONFLICT(user_id,item_id,warehouse_id)
        DO UPDATE SET quantity=excluded.quantity, average_cost=excluded.average_cost, updated_at=excluded.updated_at
    """, (user_id, item_id, warehouse_id, str(qty), str(avg), now))


def _record_warehouse_movement(db, user_id, item_id, warehouse_id, movement_type, signed_quantity, unit_cost, reference_type, reference_id, notes, movement_date):
    if not item_id or not warehouse_id:
        return
    now = datetime.datetime.now().isoformat()
    db.query("""
        INSERT INTO warehouse_movements
        (user_id,item_id,warehouse_id,movement_type,quantity,unit_cost,reference_type,reference_id,notes,movement_date,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (user_id, item_id, warehouse_id, movement_type, str(signed_quantity), str(_dec(unit_cost)), reference_type, reference_id, notes or '', movement_date or now, now))
    _update_warehouse_balance(db, user_id, item_id, warehouse_id)


def _delete_return_warehouse_movements(db, user_id, reference_type, return_id, lines, warehouse_id):
    db.query("DELETE FROM warehouse_movements WHERE user_id=? AND reference_type=? AND reference_id=?", (user_id, reference_type, return_id))
    for line in lines or []:
        _update_warehouse_balance(db, user_id, line.get('item_id'), warehouse_id)


def _record_cash_bank_return_refund(db, user_id, reference_type, return_id, branch_id, cashbox_id, bank_account_id, payment_method, amount, movement_date, description):
    amount = _dec(amount)
    if amount <= 0:
        return
    signed = -abs(amount) if reference_type == 'sales_return' else abs(amount)
    direction = 'out' if signed < 0 else 'in'
    now = datetime.datetime.now().isoformat()
    if payment_method == 'bank':
        cashbox_id = None
    else:
        bank_account_id = None
    db.query("DELETE FROM cash_bank_movements WHERE user_id=? AND reference_type=? AND reference_id=?", (user_id, reference_type, return_id))
    db.query("""
        INSERT INTO cash_bank_movements
        (user_id,branch_id,cashbox_id,bank_account_id,movement_type,amount,direction,shift_id,reference_type,reference_id,description,movement_date,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (user_id, branch_id, cashbox_id, bank_account_id,
          'sales_return_refund' if reference_type == 'sales_return' else 'purchase_return_refund',
          str(signed), direction, None, reference_type, return_id, description or '', movement_date or now, now))


def _delete_cash_bank_reference(db, user_id, reference_type, return_id):
    db.query("DELETE FROM cash_bank_movements WHERE user_id=? AND reference_type=? AND reference_id=?", (user_id, reference_type, return_id))




def _ensure_inventory_ledger_table(db):
    db.query("""
        CREATE TABLE IF NOT EXISTS inventory_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            warehouse_id INTEGER,
            movement_type TEXT NOT NULL,
            direction TEXT NOT NULL CHECK(direction IN ('in','out','neutral')),
            quantity TEXT NOT NULL,
            unit_cost TEXT,
            total_cost TEXT,
            reference_type TEXT,
            reference_id INTEGER,
            source_table TEXT,
            source_id INTEGER,
            notes TEXT,
            movement_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)


def _post_return_ledger_entry(db, user_id, item_id, warehouse_id, kind, direction, quantity, unit_cost, return_id, notes=''):
    if direction not in {'in', 'out', 'neutral'}:
        return
    _ensure_inventory_ledger_table(db)
    qty = abs(_dec(quantity))
    cost = _dec(unit_cost)
    total_cost = qty * cost
    if kind == 'sales':
        movement_type = 'sales_return_in' if direction == 'in' else 'sales_return_reversal'
        reference_type = 'sales_return'
        source_table = 'sales_returns'
    else:
        movement_type = 'purchase_return_out' if direction == 'out' else 'purchase_return_reversal'
        reference_type = 'purchase_return'
        source_table = 'purchase_returns'
    db.query("""
        INSERT INTO inventory_ledger (
            user_id, item_id, warehouse_id, movement_type, direction, quantity,
            unit_cost, total_cost, reference_type, reference_id, source_table,
            source_id, notes, movement_date
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        user_id, item_id, warehouse_id, movement_type, direction, str(qty),
        str(cost), str(total_cost), reference_type, return_id,
        source_table, return_id, notes, datetime.datetime.now().isoformat()
    ))


def _post_return_ledger_entries(db, user_id, kind, return_id, warehouse_id, lines):
    for line in lines or []:
        item_id = line.get('item_id')
        qty = line.get('quantity_in_base') or line.get('quantity') or 0
        cost = line.get('unit_cost') or 0
        if kind == 'sales':
            _post_return_ledger_entry(db, user_id, item_id, warehouse_id, 'sales', 'in', qty, cost, return_id, 'دفتر مخزون مرتجع بيع')
        else:
            _post_return_ledger_entry(db, user_id, item_id, warehouse_id, 'purchase', 'out', qty, cost, return_id, 'دفتر مخزون مرتجع شراء')


def _post_return_ledger_reversal(db, user_id, kind, return_id, warehouse_id, lines):
    for line in lines or []:
        item_id = line.get('item_id')
        qty = line.get('quantity_in_base') or line.get('quantity') or 0
        cost = line.get('unit_cost') or 0
        if kind == 'sales':
            _post_return_ledger_entry(db, user_id, item_id, warehouse_id, 'sales', 'out', qty, cost, return_id, 'عكس دفتر مخزون مرتجع بيع')
        else:
            _post_return_ledger_entry(db, user_id, item_id, warehouse_id, 'purchase', 'in', qty, cost, return_id, 'عكس دفتر مخزون مرتجع شراء')


def _invoice(db, invoice_id, user_id, inv_type):
    row = db.query("SELECT * FROM invoices WHERE id=? AND user_id=? AND type=? AND deleted_at IS NULL", (invoice_id, user_id, inv_type)).fetchone()
    return dict(row) if row else None


def _invoice_lines(db, invoice_id):
    return [dict(r) for r in db.query("""
        SELECT il.*, it.name AS item_name, it.unit AS base_unit
        FROM invoice_lines il
        LEFT JOIN items it ON it.id = il.item_id
        WHERE il.invoice_id=?
    """, (invoice_id,)).fetchall()]



def _resolve_return_unit_factor(db, orig, src):
    item_id = orig.get('item_id')
    orig_factor = _dec(orig.get('conversion_factor') or 1)
    if orig_factor <= 0:
        orig_factor = Decimal('1')
    unit_id = src.get('unit_id')
    unit_name = str(src.get('unit') or orig.get('unit') or '').strip()
    if item_id and unit_id not in (None, ''):
        row = db.query("SELECT id, unit_name, conversion_factor FROM item_units WHERE id=? AND item_id=?", (unit_id, item_id)).fetchone()
        if not row:
            raise ValueError('وحدة المرتجع لا تتبع المادة المحددة')
        factor = _dec(row['conversion_factor'] or 1)
        if factor <= 0:
            raise ValueError('معامل وحدة المرتجع غير صالح')
        return factor, str(row['unit_name'] or unit_name), int(row['id'])
    if item_id and unit_name:
        item = db.query("SELECT unit FROM items WHERE id=?", (item_id,)).fetchone()
        if item and str(item['unit'] or '').strip() == unit_name:
            return Decimal('1'), unit_name, None
        row = db.query("SELECT id, unit_name, conversion_factor FROM item_units WHERE item_id=? AND unit_name=?", (item_id, unit_name)).fetchone()
        if row:
            factor = _dec(row['conversion_factor'] or 1)
            if factor <= 0:
                raise ValueError('معامل وحدة المرتجع غير صالح')
            return factor, str(row['unit_name'] or unit_name), int(row['id'])
    return orig_factor, unit_name, src.get('unit_id') if src.get('unit_id') not in (None, '') else orig.get('unit_id')


def _return_unit_price(orig, factor):
    orig_factor = _dec(orig.get('conversion_factor') or 1)
    if orig_factor <= 0:
        orig_factor = Decimal('1')
    return (_dec(orig.get('unit_price') or orig.get('price') or 0) / orig_factor) * factor


def _returned_qty(db, kind, invoice_id, line_id=None, item_id=None):
    if kind == 'sales':
        ret_table, line_table, fk = 'sales_returns', 'sales_return_lines', 'sales_return_id'
    else:
        ret_table, line_table, fk = 'purchase_returns', 'purchase_return_lines', 'purchase_return_id'
    if line_id:
        row = db.query(f"""
            SELECT COALESCE(SUM(CAST(rl.quantity_in_base AS REAL)),0) AS qty
            FROM {line_table} rl JOIN {ret_table} r ON r.id=rl.{fk}
            WHERE r.original_invoice_id=? AND r.deleted_at IS NULL AND rl.original_invoice_line_id=?
        """, (invoice_id, line_id)).fetchone()
    else:
        row = db.query(f"""
            SELECT COALESCE(SUM(CAST(rl.quantity_in_base AS REAL)),0) AS qty
            FROM {line_table} rl JOIN {ret_table} r ON r.id=rl.{fk}
            WHERE r.original_invoice_id=? AND r.deleted_at IS NULL AND rl.item_id=?
        """, (invoice_id, item_id)).fetchone()
    return _dec(row['qty'] if row else 0)


@returns_bp.route('/returns/sales', methods=['GET'])
@jwt_required()
def list_sales_returns():
    user_id = get_jwt_identity()
    search = request.args.get('search')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)
    branch_id = request.args.get('branch_id', type=int)
    db = get_return_repository()
    where = ["sr.user_id=?", "sr.deleted_at IS NULL"]
    params = [user_id]
    branch_sql, branch_params = _branch_where(user_id, 'sr', branch_id)
    if branch_sql:
        where.append(branch_sql); params.extend(branch_params)
    if search:
        q = f'%{search}%'
        where.append("(sr.return_no LIKE ? OR inv.reference LIKE ? OR c.name LIKE ?)")
        params.extend([q, q, q])
    where_sql = ' AND '.join(where)
    total = db.query(f"SELECT COUNT(*) FROM sales_returns sr LEFT JOIN invoices inv ON inv.id=sr.original_invoice_id LEFT JOIN customers c ON c.id=sr.customer_id WHERE {where_sql}", params).fetchone()[0]
    sql = f"""
        SELECT sr.*, inv.reference AS invoice_reference, c.name AS customer_name,
               w.name AS warehouse_name, b.name AS branch_name
        FROM sales_returns sr
        LEFT JOIN invoices inv ON inv.id=sr.original_invoice_id
        LEFT JOIN customers c ON c.id=sr.customer_id
        LEFT JOIN warehouses w ON w.id=sr.warehouse_id
        LEFT JOIN branches b ON b.id=sr.branch_id
        WHERE {where_sql}
        ORDER BY sr.id DESC
    """
    if limit is not None:
        sql += " LIMIT ?"; params.append(limit)
    if offset is not None:
        sql += " OFFSET ?"; params.append(offset)
    rows = [dict(r) for r in db.query(sql, params).fetchall()]
    return jsonify({'returns': rows, 'total': total})


@returns_bp.route('/returns/purchase', methods=['GET'])
@jwt_required()
def list_purchase_returns():
    user_id = get_jwt_identity()
    search = request.args.get('search')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)
    branch_id = request.args.get('branch_id', type=int)
    db = get_return_repository()
    where = ["pr.user_id=?", "pr.deleted_at IS NULL"]
    params = [user_id]
    branch_sql, branch_params = _branch_where(user_id, 'pr', branch_id)
    if branch_sql:
        where.append(branch_sql); params.extend(branch_params)
    if search:
        q = f'%{search}%'
        where.append("(pr.return_no LIKE ? OR inv.reference LIKE ? OR s.name LIKE ?)")
        params.extend([q, q, q])
    where_sql = ' AND '.join(where)
    total = db.query(f"SELECT COUNT(*) FROM purchase_returns pr LEFT JOIN invoices inv ON inv.id=pr.original_invoice_id LEFT JOIN suppliers s ON s.id=pr.supplier_id WHERE {where_sql}", params).fetchone()[0]
    sql = f"""
        SELECT pr.*, inv.reference AS invoice_reference, s.name AS supplier_name,
               w.name AS warehouse_name, b.name AS branch_name
        FROM purchase_returns pr
        LEFT JOIN invoices inv ON inv.id=pr.original_invoice_id
        LEFT JOIN suppliers s ON s.id=pr.supplier_id
        LEFT JOIN warehouses w ON w.id=pr.warehouse_id
        LEFT JOIN branches b ON b.id=pr.branch_id
        WHERE {where_sql}
        ORDER BY pr.id DESC
    """
    if limit is not None:
        sql += " LIMIT ?"; params.append(limit)
    if offset is not None:
        sql += " OFFSET ?"; params.append(offset)
    rows = [dict(r) for r in db.query(sql, params).fetchall()]
    return jsonify({'returns': rows, 'total': total})


@returns_bp.route('/returns/sales/<int:return_id>', methods=['GET'])
@jwt_required()
def get_sales_return(return_id):
    user_id = get_jwt_identity()
    db = get_return_repository()
    row = db.query("SELECT * FROM sales_returns WHERE id=? AND user_id=?", (return_id, user_id)).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404
    try:
        _require_branch(user_id, row['branch_id'] if 'branch_id' in row.keys() else None, 'sales_return.get')
    except BranchAccessError as exc:
        return _branch_denied(exc)
    ret = dict(row)
    ret['lines'] = [dict(x) for x in db.query("SELECT * FROM sales_return_lines WHERE sales_return_id=?", (return_id,)).fetchall()]
    return jsonify(ret)


@returns_bp.route('/returns/purchase/<int:return_id>', methods=['GET'])
@jwt_required()
def get_purchase_return(return_id):
    user_id = get_jwt_identity()
    db = get_return_repository()
    row = db.query("SELECT * FROM purchase_returns WHERE id=? AND user_id=?", (return_id, user_id)).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404
    try:
        _require_branch(user_id, row['branch_id'] if 'branch_id' in row.keys() else None, 'purchase_return.get')
    except BranchAccessError as exc:
        return _branch_denied(exc)
    ret = dict(row)
    ret['lines'] = [dict(x) for x in db.query("SELECT * FROM purchase_return_lines WHERE purchase_return_id=?", (return_id,)).fetchall()]
    return jsonify(ret)


@returns_bp.route('/returns/sales/invoices', methods=['GET'])
@jwt_required()
def sales_invoices_for_returns():
    user_id = get_jwt_identity()
    limit = request.args.get('limit', default=200, type=int)
    search = request.args.get('search')
    db = get_return_repository()
    sql = """
        SELECT i.*, c.name AS customer_name
        FROM invoices i LEFT JOIN customers c ON c.id=i.customer_id
        WHERE i.user_id=? AND i.type='sale' AND i.deleted_at IS NULL
    """
    params = [user_id]
    branch_sql, branch_params = branch_access_policy.scope_sql(user_id, alias='i', branch_column='branch_id', requested_branch_id=request.args.get('branch_id', type=int))
    sql += branch_sql
    params.extend(branch_params)
    if search:
        q = f'%{search}%'
        sql += " AND (i.reference LIKE ? OR c.name LIKE ?)"
        params.extend([q, q])
    sql += " ORDER BY i.id DESC LIMIT ?"; params.append(limit)
    return jsonify({'invoices': [dict(r) for r in db.query(sql, params).fetchall()]})


@returns_bp.route('/returns/purchase/invoices', methods=['GET'])
@jwt_required()
def purchase_invoices_for_returns():
    user_id = get_jwt_identity()
    limit = request.args.get('limit', default=200, type=int)
    search = request.args.get('search')
    db = get_return_repository()
    sql = """
        SELECT i.*, s.name AS supplier_name
        FROM invoices i LEFT JOIN suppliers s ON s.id=i.supplier_id
        WHERE i.user_id=? AND i.type='purchase' AND i.deleted_at IS NULL
    """
    params = [user_id]
    branch_sql, branch_params = branch_access_policy.scope_sql(user_id, alias='i', branch_column='branch_id', requested_branch_id=request.args.get('branch_id', type=int))
    sql += branch_sql
    params.extend(branch_params)
    if search:
        q = f'%{search}%'
        sql += " AND (i.reference LIKE ? OR s.name LIKE ?)"
        params.extend([q, q])
    sql += " ORDER BY i.id DESC LIMIT ?"; params.append(limit)
    return jsonify({'invoices': [dict(r) for r in db.query(sql, params).fetchall()]})


@returns_bp.route('/returns/sales/invoices/<int:invoice_id>/lines', methods=['GET'])
@jwt_required()
def sales_returnable_lines(invoice_id):
    user_id = get_jwt_identity()
    db = get_return_repository()
    inv = _invoice(db, invoice_id, user_id, 'sale')
    if not inv:
        return jsonify({'error': 'invalid invoice'}), 404
    try:
        _require_branch(user_id, inv.get('branch_id'), 'sales_return.invoice_lines')
    except BranchAccessError as exc:
        return _branch_denied(exc)
    result = []
    for line in _invoice_lines(db, invoice_id):
        factor = _dec(line.get('conversion_factor') or 1)
        if factor <= 0:
            factor = Decimal('1')
        sold_base = _dec(line.get('quantity_in_base') or line.get('quantity') or 0)
        returned_base = _returned_qty(db, 'sales', invoice_id, line.get('id'), line.get('item_id'))
        remaining_base = max(Decimal('0'), sold_base - returned_base)
        row = dict(line)
        row.update({'sold_qty': str(sold_base / factor), 'returned_qty': str(returned_base / factor),
                    'returnable_qty': str(remaining_base / factor), 'sold_qty_base': str(sold_base),
                    'returned_qty_base': str(returned_base), 'returnable_qty_base': str(remaining_base),
                    'conversion_factor': str(factor),
                    'invoice_currency': inv.get('original_currency') or 'USD',
                    'invoice_exchange_rate_to_usd': inv.get('exchange_rate_to_usd') or 1,
                    'line_currency': 'USD',
                    'unit_price_usd': str(line.get('unit_price') or line.get('price') or 0)})
        result.append(row)
    return jsonify({'lines': result})


@returns_bp.route('/returns/purchase/invoices/<int:invoice_id>/lines', methods=['GET'])
@jwt_required()
def purchase_returnable_lines(invoice_id):
    user_id = get_jwt_identity()
    db = get_return_repository()
    inv = _invoice(db, invoice_id, user_id, 'purchase')
    if not inv:
        return jsonify({'error': 'invalid invoice'}), 404
    try:
        _require_branch(user_id, inv.get('branch_id'), 'purchase_return.invoice_lines')
    except BranchAccessError as exc:
        return _branch_denied(exc)
    result = []
    for line in _invoice_lines(db, invoice_id):
        factor = _dec(line.get('conversion_factor') or 1)
        if factor <= 0:
            factor = Decimal('1')
        purchased_base = _dec(line.get('quantity_in_base') or line.get('quantity') or 0)
        returned_base = _returned_qty(db, 'purchase', invoice_id, line.get('id'), line.get('item_id'))
        remaining_base = max(Decimal('0'), purchased_base - returned_base)
        row = dict(line)
        row.update({'purchased_qty': str(purchased_base / factor), 'returned_qty': str(returned_base / factor),
                    'returnable_qty': str(remaining_base / factor), 'purchased_qty_base': str(purchased_base),
                    'returned_qty_base': str(returned_base), 'returnable_qty_base': str(remaining_base),
                    'conversion_factor': str(factor),
                    'invoice_currency': inv.get('original_currency') or 'USD',
                    'invoice_exchange_rate_to_usd': inv.get('exchange_rate_to_usd') or 1,
                    'line_currency': 'USD',
                    'unit_price_usd': str(line.get('unit_price') or line.get('price') or 0)})
        result.append(row)
    return jsonify({'lines': result})


def _create_return(kind):
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    inv_type = 'sale' if kind == 'sales' else 'purchase'
    db = get_return_repository()
    inv = _invoice(db, int(data.get('original_invoice_id') or 0), user_id, inv_type)
    if not inv:
        return jsonify({'error': 'يجب اختيار فاتورة صالحة'}), 400
    lines_in = data.get('lines') or []
    if not lines_in:
        return jsonify({'error': 'يجب اختيار بند واحد على الأقل للمرتجع'}), 400
    invoice_lines = {int(l.get('id')): l for l in _invoice_lines(db, inv['id']) if l.get('id')}
    total = Decimal('0'); prepared = []
    for src in lines_in:
        line_id = int(src.get('original_invoice_line_id') or 0)
        orig = invoice_lines.get(line_id)
        if not orig:
            return jsonify({'error': 'بند المرتجع غير موجود في الفاتورة الأصلية'}), 400
        qty = _dec(src.get('quantity'))
        if qty <= 0:
            continue
        try:
            factor, unit_name, unit_id = _resolve_return_unit_factor(db, orig, src)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400
        base_qty = qty * factor
        explicit_base = src.get('base_qty') or src.get('quantity_in_base')
        if explicit_base not in (None, ''):
            base_qty = _dec(explicit_base)
            if base_qty != qty * factor:
                base_qty = qty * factor
        base_sold = _dec(orig.get('quantity_in_base') or orig.get('quantity') or 0)
        already = _returned_qty(db, kind, inv['id'], line_id, orig.get('item_id'))
        if base_qty > base_sold - already:
            return jsonify({'error': 'كمية المرتجع أكبر من الكمية المتبقية'}), 400
        price = _return_unit_price(orig, factor)
        if kind == 'sales':
            # Use original COGS for returned sales inventory, not the selling price.
            orig_cost_amount = _dec(orig.get('cost_amount') or 0)
            cost_per_base_unit = (orig_cost_amount / base_sold) if base_sold > 0 and orig_cost_amount > 0 else (_dec(orig.get('unit_cost') or price) / factor)
        else:
            cost_per_display_unit = price
            cost_per_base_unit = cost_per_display_unit / factor
        amount = qty * price
        total += amount
        if kind == 'purchase':
            available = _warehouse_available_qty(db, user_id, orig.get('item_id'), data.get('warehouse_id') or inv.get('warehouse_id'))
            if base_qty > available:
                return jsonify({'error': 'لا توجد كمية كافية في المستودع لإرجاع هذا البند'}), 400
        prepared.append({
            'original_invoice_line_id': line_id,
            'item_id': orig.get('item_id'),
            'quantity': qty,
            'quantity_in_base': base_qty,
            'unit_price': price,
            'unit_cost': cost_per_base_unit,
            'total': amount,
            'unit': unit_name,
            'unit_id': unit_id,
            'conversion_factor': factor,
            'cost_amount': base_qty * cost_per_base_unit,
        })
    if not prepared:
        return jsonify({'error': 'يجب إدخال كمية مرتجع صحيحة'}), 400

    remaining_amount = max(Decimal('0'), _dec(inv.get('total') or 0) - _dec(inv.get('paid') or 0))
    requested_refund = data.get('refund_amount')
    refund = max(Decimal('0'), total - min(total, remaining_amount)) if requested_refund in (None, '') else _dec(requested_refund)
    if refund < 0 or refund > total:
        return jsonify({'error': 'مبلغ الرد يجب أن يكون بين صفر وإجمالي المرتجع'}), 400
    credit = total - refund
    now = datetime.datetime.now().isoformat()
    date = data.get('date') or datetime.datetime.now().strftime('%Y-%m-%d')
    wh_id = data.get('warehouse_id') or inv.get('warehouse_id')
    branch_id = data.get('branch_id') or inv.get('branch_id')
    try:
        branch_id = branch_access_policy.effective_branch_id(user_id, branch_id)
        _require_branch(user_id, branch_id, f'{kind}_return.create')
    except BranchAccessError as exc:
        return _branch_denied(exc)
    cashbox_id = data.get('cashbox_id') or inv.get('cashbox_id')
    bank_account_id = data.get('bank_account_id') or inv.get('bank_account_id')
    payment_method = data.get('payment_method') or inv.get('payment_method') or 'cash'

    if kind == 'sales':
        ret_no = data.get('return_no') or _next_no(db, 'sales_returns', user_id, 'SR')
        cur = db.query("""
            INSERT INTO sales_returns
            (user_id,return_no,original_invoice_id,customer_id,date,total,refund_amount,credit_amount,
             warehouse_id,branch_id,cashbox_id,bank_account_id,payment_method,notes,status,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'active', ?)
        """, (user_id, ret_no, inv['id'], inv.get('customer_id'), date, str(total), str(refund), str(credit),
              wh_id, branch_id, cashbox_id, bank_account_id, payment_method, data.get('notes') or '', now))
        rid = cur.lastrowid
        for line in prepared:
            db.query("""
                INSERT INTO sales_return_lines
                (sales_return_id,original_invoice_line_id,item_id,quantity,unit_price,total,unit,unit_id,conversion_factor,quantity_in_base,unit_cost,cost_amount)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (rid, line['original_invoice_line_id'], line['item_id'], str(line['quantity']), str(line['unit_price']),
                  str(line['total']), line['unit'], line.get('unit_id'), str(line.get('conversion_factor') or 1), str(line['quantity_in_base']), str(line['unit_cost']), str(line['cost_amount'])))
            db.query("""
                INSERT INTO inventory_movements (user_id,item_id,movement_type,quantity,unit_cost,reference_id,date)
                VALUES (?,?,?,?,?,?,?)
            """, (user_id, line['item_id'], 'sales_return', str(line['quantity_in_base']), str(line['unit_cost']), rid, date))
            _record_warehouse_movement(db, user_id, line['item_id'], wh_id, 'sales_return_in', line['quantity_in_base'], line['unit_cost'], 'sales_return', rid, 'إرجاع مبيعات إلى المستودع', date)
            _update_item_quantity(db, line['item_id'], user_id)
            _recalculate_average_cost(db, line['item_id'], user_id)
        if inv.get('customer_id') and credit > 0:
            db.query("UPDATE customers SET balance=CAST(COALESCE(balance,'0') AS REAL)-? WHERE id=? AND user_id=?", (str(credit), inv.get('customer_id'), user_id))
        if refund > 0:
            db.query("UPDATE users SET cash_balance=CAST(COALESCE(cash_balance,'0') AS REAL)-? WHERE id=?", (str(refund), user_id))
            _record_cash_bank_return_refund(db, user_id, 'sales_return', rid, branch_id, cashbox_id, bank_account_id, payment_method, refund, date, f'رد مرتجع مبيعات {ret_no}')
    else:
        ret_no = data.get('return_no') or _next_no(db, 'purchase_returns', user_id, 'PR')
        cur = db.query("""
            INSERT INTO purchase_returns
            (user_id,return_no,original_invoice_id,supplier_id,date,total,refund_amount,credit_amount,
             warehouse_id,branch_id,cashbox_id,bank_account_id,payment_method,notes,status,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'active', ?)
        """, (user_id, ret_no, inv['id'], inv.get('supplier_id'), date, str(total), str(refund), str(credit),
              wh_id, branch_id, cashbox_id, bank_account_id, payment_method, data.get('notes') or '', now))
        rid = cur.lastrowid
        for line in prepared:
            db.query("""
                INSERT INTO purchase_return_lines
                (purchase_return_id,original_invoice_line_id,item_id,quantity,unit_price,total,unit,unit_id,conversion_factor,quantity_in_base,unit_cost,cost_amount)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (rid, line['original_invoice_line_id'], line['item_id'], str(line['quantity']), str(line['unit_price']),
                  str(line['total']), line['unit'], line.get('unit_id'), str(line.get('conversion_factor') or 1), str(line['quantity_in_base']), str(line['unit_cost']), str(line['cost_amount'])))
            db.query("""
                INSERT INTO inventory_movements (user_id,item_id,movement_type,quantity,unit_cost,reference_id,date)
                VALUES (?,?,?,?,?,?,?)
            """, (user_id, line['item_id'], 'purchase_return', str(line['quantity_in_base']), str(line['unit_cost']), rid, date))
            _record_warehouse_movement(db, user_id, line['item_id'], wh_id, 'purchase_return_out', -abs(line['quantity_in_base']), line['unit_cost'], 'purchase_return', rid, 'مرتجع مشتريات من المستودع', date)
            _update_item_quantity(db, line['item_id'], user_id)
            _recalculate_average_cost(db, line['item_id'], user_id)
        if inv.get('supplier_id') and credit > 0:
            db.query("UPDATE suppliers SET balance=CAST(COALESCE(balance,'0') AS REAL)-? WHERE id=? AND user_id=?", (str(credit), inv.get('supplier_id'), user_id))
        if refund > 0:
            db.query("UPDATE users SET cash_balance=CAST(COALESCE(cash_balance,'0') AS REAL)+? WHERE id=?", (str(refund), user_id))
            _record_cash_bank_return_refund(db, user_id, 'purchase_return', rid, branch_id, cashbox_id, bank_account_id, payment_method, refund, date, f'استرداد مرتجع مشتريات {ret_no}')

    # Phase 24: shadow-post returns to append-only inventory_ledger.
    # This does not replace the legacy inventory_movements/item quantity semantics.
    _post_return_ledger_entries(db, user_id, kind, rid, wh_id, prepared)

    db.commit()
    return jsonify({'id': rid, 'return_no': ret_no}), 201


@returns_bp.route('/returns/sales', methods=['POST'])
@jwt_required()
def create_sales_return():
    return _create_return('sales')


@returns_bp.route('/returns/purchase', methods=['POST'])
@jwt_required()
def create_purchase_return():
    return _create_return('purchase')


def _update_return_via_reversal(kind, return_id):
    """Update a return through the same accounting-safe reversal/recreate pipeline used locally.

    The route preserves network/API parity with the client gateways. It does not
    mutate posted historical rows in place because returns have inventory,
    customer/supplier, cash/bank and ledger effects. Instead, the old return is
    cancelled and a replacement return is created with the same return_no unless
    the client explicitly provides a different number.
    """
    user_id = get_jwt_identity()
    db = get_return_repository()
    table = 'sales_returns' if kind == 'sales' else 'purchase_returns'
    endpoint_kind = 'sales' if kind == 'sales' else 'purchase'
    old_row = db.query(f"SELECT * FROM {table} WHERE id=? AND user_id=?", (return_id, user_id)).fetchone()
    if not old_row:
        return jsonify({'error': 'not found'}), 404
    old = dict(old_row)
    try:
        _require_branch(user_id, old.get('branch_id'), f'{kind}_return.update.old')
    except BranchAccessError as exc:
        return _branch_denied(exc)
    if old.get('deleted_at') or old.get('status') == 'cancelled':
        return jsonify({'error': 'return is cancelled'}), 400
    data = dict(request.get_json() or {})
    data.setdefault('return_no', old.get('return_no'))
    data.setdefault('original_invoice_id', old.get('original_invoice_id'))
    try:
        # Reuse the exact reversal code paths to keep warehouse, cash/bank,
        # customer/supplier balances and inventory ledger semantics aligned.
        if endpoint_kind == 'sales':
            response = delete_sales_return(return_id)
        else:
            response = delete_purchase_return(return_id)
        status = getattr(response, 'status_code', None)
        if status and status >= 400:
            return response

        # The legacy create helper reads request JSON. Re-seed Flask's cached
        # JSON with the merged payload so PUT can reuse the validated create
        # contract without duplicating the accounting logic.
        request._cached_json = (data, data)  # Flask private cache; guarded by tests.
        create_response = _create_return(endpoint_kind)
        return create_response
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        return jsonify({'error': str(exc)}), 400


@returns_bp.route('/returns/sales/<int:return_id>', methods=['PUT'])
@jwt_required()
def update_sales_return(return_id):
    return _update_return_via_reversal('sales', return_id)


@returns_bp.route('/returns/purchase/<int:return_id>', methods=['PUT'])
@jwt_required()
def update_purchase_return(return_id):
    return _update_return_via_reversal('purchase', return_id)


@returns_bp.route('/returns/sales/<int:return_id>', methods=['DELETE'])
@jwt_required()
def delete_sales_return(return_id):
    user_id = get_jwt_identity()
    db = get_return_repository()
    ret = db.query("SELECT * FROM sales_returns WHERE id=? AND user_id=?", (return_id, user_id)).fetchone()
    if not ret:
        return jsonify({'ok': True})
    ret = dict(ret)
    if ret.get('deleted_at') or ret.get('status') == 'cancelled':
        return jsonify({'ok': True})
    try:
        _require_branch(user_id, ret.get('branch_id'), 'sales_return.delete')
    except BranchAccessError as exc:
        return _branch_denied(exc)
    lines = [dict(x) for x in db.query("SELECT * FROM sales_return_lines WHERE sales_return_id=?", (return_id,)).fetchall()]
    item_ids = {line.get('item_id') for line in lines if line.get('item_id')}
    _post_return_ledger_reversal(db, user_id, 'sales', return_id, ret.get('warehouse_id'), lines)
    db.query("DELETE FROM inventory_movements WHERE user_id=? AND reference_id=? AND movement_type='sales_return'", (user_id, return_id))
    _delete_return_warehouse_movements(db, user_id, 'sales_return', return_id, lines, ret.get('warehouse_id'))
    for item_id in item_ids:
        _update_item_quantity(db, item_id, user_id)
        _recalculate_average_cost(db, item_id, user_id)
    credit = _dec(ret.get('credit_amount') or 0)
    if ret.get('customer_id') and credit > 0:
        db.query("UPDATE customers SET balance=CAST(COALESCE(balance,'0') AS REAL)+? WHERE id=? AND user_id=?", (str(credit), ret.get('customer_id'), user_id))
    refund = _dec(ret.get('refund_amount') or 0)
    if refund > 0:
        db.query("UPDATE users SET cash_balance=CAST(COALESCE(cash_balance,'0') AS REAL)+? WHERE id=?", (str(refund), user_id))
        _delete_cash_bank_reference(db, user_id, 'sales_return', return_id)
    db.query("UPDATE sales_returns SET deleted_at=datetime('now'), status='cancelled' WHERE id=? AND user_id=?", (return_id, user_id))
    db.commit()
    return jsonify({'ok': True})


@returns_bp.route('/returns/purchase/<int:return_id>', methods=['DELETE'])
@jwt_required()
def delete_purchase_return(return_id):
    user_id = get_jwt_identity()
    db = get_return_repository()
    ret = db.query("SELECT * FROM purchase_returns WHERE id=? AND user_id=?", (return_id, user_id)).fetchone()
    if not ret:
        return jsonify({'ok': True})
    ret = dict(ret)
    if ret.get('deleted_at') or ret.get('status') == 'cancelled':
        return jsonify({'ok': True})
    try:
        _require_branch(user_id, ret.get('branch_id'), 'purchase_return.delete')
    except BranchAccessError as exc:
        return _branch_denied(exc)
    lines = [dict(x) for x in db.query("SELECT * FROM purchase_return_lines WHERE purchase_return_id=?", (return_id,)).fetchall()]
    item_ids = {line.get('item_id') for line in lines if line.get('item_id')}
    _post_return_ledger_reversal(db, user_id, 'purchase', return_id, ret.get('warehouse_id'), lines)
    db.query("DELETE FROM inventory_movements WHERE user_id=? AND reference_id=? AND movement_type='purchase_return'", (user_id, return_id))
    _delete_return_warehouse_movements(db, user_id, 'purchase_return', return_id, lines, ret.get('warehouse_id'))
    for item_id in item_ids:
        _update_item_quantity(db, item_id, user_id)
        _recalculate_average_cost(db, item_id, user_id)
    credit = _dec(ret.get('credit_amount') or 0)
    if ret.get('supplier_id') and credit > 0:
        db.query("UPDATE suppliers SET balance=CAST(COALESCE(balance,'0') AS REAL)+? WHERE id=? AND user_id=?", (str(credit), ret.get('supplier_id'), user_id))
    refund = _dec(ret.get('refund_amount') or 0)
    if refund > 0:
        db.query("UPDATE users SET cash_balance=CAST(COALESCE(cash_balance,'0') AS REAL)-? WHERE id=?", (str(refund), user_id))
        _delete_cash_bank_reference(db, user_id, 'purchase_return', return_id)
    db.query("UPDATE purchase_returns SET deleted_at=datetime('now'), status='cancelled' WHERE id=? AND user_id=?", (return_id, user_id))
    db.commit()
    return jsonify({'ok': True})
