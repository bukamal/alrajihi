# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from alrajhi_server.database.connection import get_db

returns_bp = Blueprint('returns', __name__)


def _dec(value, default='0'):
    try:
        return Decimal(str(value if value is not None else default))
    except Exception:
        return Decimal(str(default))


def _next_no(db, table, user_id, prefix):
    year = datetime.datetime.now().strftime('%Y')
    full_prefix = f'{prefix}-{year}-'
    row = db.execute(f"SELECT MAX(return_no) AS max_no FROM {table} WHERE user_id=? AND return_no LIKE ?", (user_id, full_prefix + '%')).fetchone()
    max_no = row['max_no'] if row else None
    try:
        num = int(str(max_no).split('-')[-1]) + 1 if max_no else 1
    except Exception:
        num = 1
    return f'{full_prefix}{num:04d}'


def _update_item_quantity(db, item_id, user_id):
    row = db.execute("""
        SELECT SUM(CASE
            WHEN movement_type IN ('opening','purchase','adjustment','production_out','sales_return','consumption_reverse') THEN CAST(quantity AS REAL)
            WHEN movement_type IN ('sale','production_consume','purchase_return') THEN -CAST(quantity AS REAL)
            ELSE 0 END) AS total_qty
        FROM inventory_movements
        WHERE item_id=? AND user_id=?
    """, (item_id, user_id)).fetchone()
    qty = _dec(row['total_qty']) if row and row['total_qty'] is not None else Decimal('0')
    db.execute("UPDATE items SET quantity=? WHERE id=? AND user_id=?", (str(qty), item_id, user_id))


def _recalculate_average_cost(db, item_id, user_id):
    row = db.execute("""
        SELECT SUM(CAST(quantity AS REAL)) AS total_qty,
               SUM(CAST(quantity AS REAL) * CAST(unit_cost AS REAL)) AS total_cost
        FROM inventory_movements
        WHERE item_id=? AND user_id=? AND movement_type IN ('opening','purchase','adjustment','production_out','sales_return')
    """, (item_id, user_id)).fetchone()
    total_qty = _dec(row['total_qty']) if row and row['total_qty'] is not None else Decimal('0')
    total_cost = _dec(row['total_cost']) if row and row['total_cost'] is not None else Decimal('0')
    avg = total_cost / total_qty if total_qty > 0 else Decimal('0')
    db.execute("UPDATE items SET average_cost=? WHERE id=? AND user_id=?", (str(avg), item_id, user_id))


def _invoice(db, invoice_id, user_id, inv_type):
    row = db.execute("SELECT * FROM invoices WHERE id=? AND user_id=? AND type=? AND deleted_at IS NULL", (invoice_id, user_id, inv_type)).fetchone()
    return dict(row) if row else None


def _invoice_lines(db, invoice_id):
    return [dict(r) for r in db.execute("SELECT * FROM invoice_lines WHERE invoice_id=?", (invoice_id,)).fetchall()]


def _returned_qty(db, kind, invoice_id, line_id=None, item_id=None):
    if kind == 'sales':
        ret_table, line_table, fk = 'sales_returns', 'sales_return_lines', 'sales_return_id'
    else:
        ret_table, line_table, fk = 'purchase_returns', 'purchase_return_lines', 'purchase_return_id'
    if line_id:
        row = db.execute(f"""
            SELECT COALESCE(SUM(CAST(rl.quantity_in_base AS REAL)),0) AS qty
            FROM {line_table} rl JOIN {ret_table} r ON r.id=rl.{fk}
            WHERE r.original_invoice_id=? AND r.deleted_at IS NULL AND rl.original_invoice_line_id=?
        """, (invoice_id, line_id)).fetchone()
    else:
        row = db.execute(f"""
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
    db = get_db()
    where = ["sr.user_id=?", "sr.deleted_at IS NULL"]
    params = [user_id]
    if search:
        q = f'%{search}%'
        where.append("(sr.return_no LIKE ? OR inv.reference LIKE ? OR c.name LIKE ?)")
        params.extend([q, q, q])
    where_sql = ' AND '.join(where)
    total = db.execute(f"SELECT COUNT(*) FROM sales_returns sr LEFT JOIN invoices inv ON inv.id=sr.original_invoice_id LEFT JOIN customers c ON c.id=sr.customer_id WHERE {where_sql}", params).fetchone()[0]
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
    rows = [dict(r) for r in db.execute(sql, params).fetchall()]
    return jsonify({'returns': rows, 'total': total})


@returns_bp.route('/returns/purchase', methods=['GET'])
@jwt_required()
def list_purchase_returns():
    user_id = get_jwt_identity()
    search = request.args.get('search')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)
    db = get_db()
    where = ["pr.user_id=?", "pr.deleted_at IS NULL"]
    params = [user_id]
    if search:
        q = f'%{search}%'
        where.append("(pr.return_no LIKE ? OR inv.reference LIKE ? OR s.name LIKE ?)")
        params.extend([q, q, q])
    where_sql = ' AND '.join(where)
    total = db.execute(f"SELECT COUNT(*) FROM purchase_returns pr LEFT JOIN invoices inv ON inv.id=pr.original_invoice_id LEFT JOIN suppliers s ON s.id=pr.supplier_id WHERE {where_sql}", params).fetchone()[0]
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
    rows = [dict(r) for r in db.execute(sql, params).fetchall()]
    return jsonify({'returns': rows, 'total': total})


@returns_bp.route('/returns/sales/<int:return_id>', methods=['GET'])
@jwt_required()
def get_sales_return(return_id):
    user_id = get_jwt_identity()
    db = get_db()
    row = db.execute("SELECT * FROM sales_returns WHERE id=? AND user_id=?", (return_id, user_id)).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404
    ret = dict(row)
    ret['lines'] = [dict(x) for x in db.execute("SELECT * FROM sales_return_lines WHERE sales_return_id=?", (return_id,)).fetchall()]
    return jsonify(ret)


@returns_bp.route('/returns/purchase/<int:return_id>', methods=['GET'])
@jwt_required()
def get_purchase_return(return_id):
    user_id = get_jwt_identity()
    db = get_db()
    row = db.execute("SELECT * FROM purchase_returns WHERE id=? AND user_id=?", (return_id, user_id)).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404
    ret = dict(row)
    ret['lines'] = [dict(x) for x in db.execute("SELECT * FROM purchase_return_lines WHERE purchase_return_id=?", (return_id,)).fetchall()]
    return jsonify(ret)


@returns_bp.route('/returns/sales/invoices', methods=['GET'])
@jwt_required()
def sales_invoices_for_returns():
    user_id = get_jwt_identity()
    limit = request.args.get('limit', default=200, type=int)
    search = request.args.get('search')
    db = get_db()
    sql = """
        SELECT i.*, c.name AS customer_name
        FROM invoices i LEFT JOIN customers c ON c.id=i.customer_id
        WHERE i.user_id=? AND i.type='sale' AND i.deleted_at IS NULL
    """
    params = [user_id]
    if search:
        q = f'%{search}%'
        sql += " AND (i.reference LIKE ? OR c.name LIKE ?)"
        params.extend([q, q])
    sql += " ORDER BY i.id DESC LIMIT ?"; params.append(limit)
    return jsonify({'invoices': [dict(r) for r in db.execute(sql, params).fetchall()]})


@returns_bp.route('/returns/purchase/invoices', methods=['GET'])
@jwt_required()
def purchase_invoices_for_returns():
    user_id = get_jwt_identity()
    limit = request.args.get('limit', default=200, type=int)
    search = request.args.get('search')
    db = get_db()
    sql = """
        SELECT i.*, s.name AS supplier_name
        FROM invoices i LEFT JOIN suppliers s ON s.id=i.supplier_id
        WHERE i.user_id=? AND i.type='purchase' AND i.deleted_at IS NULL
    """
    params = [user_id]
    if search:
        q = f'%{search}%'
        sql += " AND (i.reference LIKE ? OR s.name LIKE ?)"
        params.extend([q, q])
    sql += " ORDER BY i.id DESC LIMIT ?"; params.append(limit)
    return jsonify({'invoices': [dict(r) for r in db.execute(sql, params).fetchall()]})


@returns_bp.route('/returns/sales/invoices/<int:invoice_id>/lines', methods=['GET'])
@jwt_required()
def sales_returnable_lines(invoice_id):
    user_id = get_jwt_identity()
    db = get_db()
    inv = _invoice(db, invoice_id, user_id, 'sale')
    if not inv:
        return jsonify({'error': 'invalid invoice'}), 404
    result = []
    for line in _invoice_lines(db, invoice_id):
        sold = _dec(line.get('quantity_in_base') or line.get('quantity') or 0)
        returned = _returned_qty(db, 'sales', invoice_id, line.get('id'), line.get('item_id'))
        row = dict(line)
        row.update({'sold_qty': str(sold), 'returned_qty': str(returned), 'returnable_qty': str(max(Decimal('0'), sold - returned))})
        result.append(row)
    return jsonify({'lines': result})


@returns_bp.route('/returns/purchase/invoices/<int:invoice_id>/lines', methods=['GET'])
@jwt_required()
def purchase_returnable_lines(invoice_id):
    user_id = get_jwt_identity()
    db = get_db()
    inv = _invoice(db, invoice_id, user_id, 'purchase')
    if not inv:
        return jsonify({'error': 'invalid invoice'}), 404
    result = []
    for line in _invoice_lines(db, invoice_id):
        purchased = _dec(line.get('quantity_in_base') or line.get('quantity') or 0)
        returned = _returned_qty(db, 'purchase', invoice_id, line.get('id'), line.get('item_id'))
        row = dict(line)
        row.update({'purchased_qty': str(purchased), 'returned_qty': str(returned), 'returnable_qty': str(max(Decimal('0'), purchased - returned))})
        result.append(row)
    return jsonify({'lines': result})


def _create_return(kind):
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    inv_type = 'sale' if kind == 'sales' else 'purchase'
    db = get_db()
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
        base_sold = _dec(orig.get('quantity_in_base') or orig.get('quantity') or 0)
        already = _returned_qty(db, kind, inv['id'], line_id, orig.get('item_id'))
        if qty > base_sold - already:
            return jsonify({'error': 'كمية المرتجع أكبر من الكمية المتبقية'}), 400
        price = _dec(orig.get('unit_price') or 0)
        cost = _dec(orig.get('unit_cost') or 0)
        amount = qty * price
        total += amount
        prepared.append((orig, qty, price, cost, amount))
    if not prepared:
        return jsonify({'error': 'يجب إدخال كمية مرتجع صحيحة'}), 400

    refund = _dec(data.get('refund_amount') or 0)
    if refund < 0 or refund > total:
        return jsonify({'error': 'مبلغ الرد يجب أن يكون بين صفر وإجمالي المرتجع'}), 400
    credit = total - refund
    now = datetime.datetime.now().isoformat()
    date = data.get('date') or datetime.datetime.now().strftime('%Y-%m-%d')
    wh_id = data.get('warehouse_id') or inv.get('warehouse_id')
    branch_id = data.get('branch_id') or inv.get('branch_id')
    cashbox_id = data.get('cashbox_id') or inv.get('cashbox_id')
    bank_account_id = data.get('bank_account_id') or inv.get('bank_account_id')
    payment_method = data.get('payment_method') or inv.get('payment_method') or 'cash'

    if kind == 'sales':
        ret_no = data.get('return_no') or _next_no(db, 'sales_returns', user_id, 'SR')
        cur = db.execute("""
            INSERT INTO sales_returns
            (user_id,return_no,original_invoice_id,customer_id,date,total,refund_amount,credit_amount,
             warehouse_id,branch_id,cashbox_id,bank_account_id,payment_method,notes,status,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'active', ?)
        """, (user_id, ret_no, inv['id'], inv.get('customer_id'), date, str(total), str(refund), str(credit),
              wh_id, branch_id, cashbox_id, bank_account_id, payment_method, data.get('notes') or '', now))
        rid = cur.lastrowid
        for orig, qty, price, cost, amount in prepared:
            db.execute("""
                INSERT INTO sales_return_lines
                (sales_return_id,original_invoice_line_id,item_id,quantity,unit_price,total,unit,quantity_in_base,unit_cost,cost_amount)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (rid, orig.get('id'), orig.get('item_id'), str(qty), str(price), str(amount), orig.get('unit') or '',
                  str(qty), str(cost), str(qty * cost)))
            db.execute("""
                INSERT INTO inventory_movements (user_id,item_id,movement_type,quantity,unit_cost,reference_id,date)
                VALUES (?,?,?,?,?,?,?)
            """, (user_id, orig.get('item_id'), 'sales_return', str(qty), str(cost), rid, date))
            _update_item_quantity(db, orig.get('item_id'), user_id)
            _recalculate_average_cost(db, orig.get('item_id'), user_id)
        if inv.get('customer_id') and credit > 0:
            db.execute("UPDATE customers SET balance=CAST(COALESCE(balance,'0') AS REAL)-? WHERE id=? AND user_id=?", (str(credit), inv.get('customer_id'), user_id))
        if refund > 0:
            db.execute("UPDATE users SET cash_balance=CAST(COALESCE(cash_balance,'0') AS REAL)-? WHERE id=?", (str(refund), user_id))
    else:
        ret_no = data.get('return_no') or _next_no(db, 'purchase_returns', user_id, 'PR')
        cur = db.execute("""
            INSERT INTO purchase_returns
            (user_id,return_no,original_invoice_id,supplier_id,date,total,refund_amount,credit_amount,
             warehouse_id,branch_id,cashbox_id,bank_account_id,payment_method,notes,status,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'active', ?)
        """, (user_id, ret_no, inv['id'], inv.get('supplier_id'), date, str(total), str(refund), str(credit),
              wh_id, branch_id, cashbox_id, bank_account_id, payment_method, data.get('notes') or '', now))
        rid = cur.lastrowid
        for orig, qty, price, cost, amount in prepared:
            db.execute("""
                INSERT INTO purchase_return_lines
                (purchase_return_id,original_invoice_line_id,item_id,quantity,unit_price,total,unit,quantity_in_base,unit_cost,cost_amount)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (rid, orig.get('id'), orig.get('item_id'), str(qty), str(price), str(amount), orig.get('unit') or '',
                  str(qty), str(cost), str(qty * cost)))
            db.execute("""
                INSERT INTO inventory_movements (user_id,item_id,movement_type,quantity,unit_cost,reference_id,date)
                VALUES (?,?,?,?,?,?,?)
            """, (user_id, orig.get('item_id'), 'purchase_return', str(qty), str(cost), rid, date))
            _update_item_quantity(db, orig.get('item_id'), user_id)
            _recalculate_average_cost(db, orig.get('item_id'), user_id)
        if inv.get('supplier_id') and credit > 0:
            db.execute("UPDATE suppliers SET balance=CAST(COALESCE(balance,'0') AS REAL)-? WHERE id=? AND user_id=?", (str(credit), inv.get('supplier_id'), user_id))
        if refund > 0:
            db.execute("UPDATE users SET cash_balance=CAST(COALESCE(cash_balance,'0') AS REAL)+? WHERE id=?", (str(refund), user_id))

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


@returns_bp.route('/returns/sales/<int:return_id>', methods=['DELETE'])
@jwt_required()
def delete_sales_return(return_id):
    user_id = get_jwt_identity()
    db = get_db()
    ret = db.execute("SELECT * FROM sales_returns WHERE id=? AND user_id=?", (return_id, user_id)).fetchone()
    if not ret:
        return jsonify({'ok': True})
    db.execute("UPDATE sales_returns SET deleted_at=datetime('now'), status='cancelled' WHERE id=? AND user_id=?", (return_id, user_id))
    db.commit()
    return jsonify({'ok': True})


@returns_bp.route('/returns/purchase/<int:return_id>', methods=['DELETE'])
@jwt_required()
def delete_purchase_return(return_id):
    user_id = get_jwt_identity()
    db = get_db()
    ret = db.execute("SELECT * FROM purchase_returns WHERE id=? AND user_id=?", (return_id, user_id)).fetchone()
    if not ret:
        return jsonify({'ok': True})
    db.execute("UPDATE purchase_returns SET deleted_at=datetime('now'), status='cancelled' WHERE id=? AND user_id=?", (return_id, user_id))
    db.commit()
    return jsonify({'ok': True})
