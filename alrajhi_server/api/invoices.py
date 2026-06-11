from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.api.audit_utils import audit_log
from alrajhi_server.database.connection import get_db
import datetime
from decimal import Decimal

invoices_bp = Blueprint('invoices', __name__)


def _invoice_has_vouchers(db, invoice_id, user_id):
    row = db.execute("SELECT COUNT(*) AS cnt FROM vouchers WHERE invoice_id=? AND user_id=?", (invoice_id, user_id)).fetchone()
    return bool(row and row['cnt'])


def _update_item_quantity(db, item_id, user_id):
    row = db.execute('''
        SELECT SUM(CASE
            WHEN movement_type IN ('opening','purchase','adjustment','production_out') THEN CAST(quantity AS REAL)
            WHEN movement_type IN ('sale','production_consume') THEN -CAST(quantity AS REAL)
            ELSE 0 END) AS total_qty
        FROM inventory_movements
        WHERE item_id=? AND user_id=?
    ''', (item_id, user_id)).fetchone()
    qty = Decimal(str(row['total_qty'])) if row and row['total_qty'] is not None else Decimal('0')
    db.execute("UPDATE items SET quantity=? WHERE id=? AND user_id=?", (str(qty), item_id, user_id))


def _recalculate_average_cost(db, item_id, user_id):
    row = db.execute('''
        SELECT SUM(CAST(quantity AS REAL)) AS total_qty,
               SUM(CAST(quantity AS REAL) * CAST(unit_cost AS REAL)) AS total_cost
        FROM inventory_movements
        WHERE item_id=? AND user_id=? AND movement_type IN ('opening','purchase','adjustment','production_out')
    ''', (item_id, user_id)).fetchone()
    total_qty = Decimal(str(row['total_qty'])) if row and row['total_qty'] is not None else Decimal('0')
    total_cost = Decimal(str(row['total_cost'])) if row and row['total_cost'] is not None else Decimal('0')
    avg = total_cost / total_qty if total_qty > 0 else Decimal('0')
    db.execute("UPDATE items SET average_cost=? WHERE id=? AND user_id=?", (str(avg), item_id, user_id))


def _apply_invoice_financial_effect(db, invoice, sign):
    total = Decimal(str(invoice.get('total', 0)))
    paid = Decimal(str(invoice.get('paid', 0)))
    net = total - paid
    if invoice.get('type') == 'sale' and invoice.get('customer_id'):
        db.execute("UPDATE customers SET balance = CAST(COALESCE(balance, '0') AS TEXT) + ? WHERE id=?", (str(sign * net), invoice['customer_id']))
    elif invoice.get('type') == 'purchase' and invoice.get('supplier_id'):
        db.execute("UPDATE suppliers SET balance = CAST(COALESCE(balance, '0') AS TEXT) + ? WHERE id=?", (str(sign * net), invoice['supplier_id']))
    if paid > 0:
        cash_delta = paid if invoice.get('type') == 'sale' else -paid
        db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS TEXT) + ? WHERE id=?", (str(sign * cash_delta), invoice['user_id']))

@invoices_bp.route('/invoices', methods=['GET'])
@jwt_required()
def get_invoices():
    user_id = get_jwt_identity()
    inv_type = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)
    db = get_db()
    count_query = "SELECT COUNT(*) FROM invoices i WHERE i.user_id = ? AND i.deleted_at IS NULL"
    count_params = [user_id]
    query = """
        SELECT i.*, c.name as customer_name, s.name as supplier_name
        FROM invoices i
        LEFT JOIN customers c ON i.customer_id = c.id
        LEFT JOIN suppliers s ON i.supplier_id = s.id
        WHERE i.user_id = ? AND i.deleted_at IS NULL
    """
    params = [user_id]
    if inv_type in ('sale', 'purchase'):
        count_query += " AND i.type = ?"
        count_params.append(inv_type)
        query += " AND i.type = ?"
        params.append(inv_type)
    if start_date:
        count_query += " AND i.date >= ?"
        count_params.append(start_date)
        query += " AND i.date >= ?"
        params.append(start_date)
    if end_date:
        count_query += " AND i.date <= ?"
        count_params.append(end_date)
        query += " AND i.date <= ?"
        params.append(end_date)
    total = db.execute(count_query, count_params).fetchone()[0]
    query += " ORDER BY i.id DESC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    if offset is not None:
        query += " OFFSET ?"
        params.append(offset)
    rows = db.execute(query, params).fetchall()
    return jsonify({'invoices': [dict(row) for row in rows], 'total': total})

@invoices_bp.route('/invoices/<int:invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice(invoice_id):
    user_id = get_jwt_identity()
    db = get_db()
    row = db.execute("SELECT * FROM invoices WHERE id=? AND user_id=?", (invoice_id, user_id)).fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    inv = dict(row)
    lines = db.execute("SELECT * FROM invoice_lines WHERE invoice_id=?", (invoice_id,)).fetchall()
    inv['lines'] = [dict(line) for line in lines]
    return jsonify(inv)

@invoices_bp.route('/invoices', methods=['POST'])
@jwt_required()
def add_invoice():
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    db.execute("BEGIN TRANSACTION")
    try:
        # إدراج الفاتورة
        cursor = db.execute('''
            INSERT INTO invoices (user_id, type, customer_id, supplier_id, date, reference, notes, total, paid, status, exchange_rate_to_usd, original_currency, warehouse_id, branch_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            user_id, data['type'], data.get('customer_id'), data.get('supplier_id'),
            data['date'], data.get('reference', ''), data.get('notes', ''),
            str(data['total']), str(data['paid_amount']), 'active',
            data.get('exchange_rate_to_usd', 1.0), data.get('original_currency', 'USD'), data.get('warehouse_id'), data.get('branch_id')
        ))
        invoice_id = cursor.lastrowid
        # إدراج البنود وتسجيل حركات المخزون (محاكاة منطق العميل)
        for line in data['lines']:
            conv_factor = Decimal(str(line.get('conversion_factor', 1)))
            if conv_factor <= 0:
                conv_factor = Decimal('1')
            base_qty = Decimal(str(line.get('base_qty', line['quantity'])))
            unit_cost = Decimal(str(line['unit_price']))
            db.execute('''
                INSERT INTO invoice_lines (invoice_id, item_id, quantity, unit_price, total, unit, quantity_in_base, unit_cost, cost_amount, conversion_factor)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            ''', (
                invoice_id, line['item_id'], str(line['quantity']), str(unit_cost), str(line['total']),
                line.get('unit', ''), str(base_qty), str(unit_cost), '0', str(conv_factor)
            ))
            if data['type'] == 'purchase':
                unit_cost_base = unit_cost / conv_factor
                # تسجيل حركة شراء
                db.execute('''
                    INSERT INTO inventory_movements (item_id, user_id, movement_type, quantity, unit_cost, reference_id, movement_date)
                    VALUES (?,?,?,?,?,?,?)
                ''', (line['item_id'], user_id, 'purchase', str(base_qty), str(unit_cost_base), invoice_id, datetime.datetime.now().isoformat()))
                cost_amt = unit_cost_base * base_qty
                db.execute("UPDATE invoice_lines SET cost_amount=? WHERE invoice_id=? AND item_id=?", (str(cost_amt), invoice_id, line['item_id']))
            else:  # sale
                item = db.execute("SELECT CAST(average_cost AS TEXT) as avg_cost FROM items WHERE id=?", (line['item_id'],)).fetchone()
                avg_cost = Decimal(str(item['avg_cost'])) if item else Decimal('0')
                cost_amt = base_qty * avg_cost
                db.execute("UPDATE invoice_lines SET cost_amount=? WHERE invoice_id=? AND item_id=?", (str(cost_amt), invoice_id, line['item_id']))
                db.execute('''
                    INSERT INTO inventory_movements (item_id, user_id, movement_type, quantity, unit_cost, reference_id, movement_date)
                    VALUES (?,?,?,?,?,?,?)
                ''', (line['item_id'], user_id, 'sale', str(base_qty), str(unit_cost), invoice_id, datetime.datetime.now().isoformat()))
        for item_id in {line['item_id'] for line in data['lines']}:
            _update_item_quantity(db, item_id, user_id)
            _recalculate_average_cost(db, item_id, user_id)
        _apply_invoice_financial_effect(db, {
            'user_id': user_id, 'type': data['type'], 'customer_id': data.get('customer_id'),
            'supplier_id': data.get('supplier_id'), 'total': data['total'],
            'paid': data.get('paid_amount', 0)
        }, Decimal('1'))
        audit_log('CREATE', 'SALE_INVOICE' if data.get('type') == 'sale' else 'PURCHASE_INVOICE', invoice_id, new_values=data, details='إنشاء فاتورة')
        db.execute("COMMIT")
        return jsonify({'id': invoice_id}), 201
    except Exception as e:
        db.execute("ROLLBACK")
        return jsonify({'error': str(e)}), 500

@invoices_bp.route('/invoices/<int:invoice_id>', methods=['PUT'])
@jwt_required()
def update_invoice(invoice_id):
    # تحديث محافظ على رقم الفاتورة بدل soft-delete ثم إنشاء سجل جديد.
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    old_invoice = db.execute("SELECT * FROM invoices WHERE id=? AND user_id=? AND deleted_at IS NULL", (invoice_id, user_id)).fetchone()
    if not old_invoice:
        return jsonify({'error': 'Not found'}), 404
    if _invoice_has_vouchers(db, invoice_id, user_id):
        return jsonify({'error': 'لا يمكن تعديل فاتورة مرتبطة بسندات. احذف أو عدّل السندات أولاً.'}), 400
    db.execute("BEGIN TRANSACTION")
    try:
        old_invoice_dict = dict(old_invoice)
        _apply_invoice_financial_effect(db, old_invoice_dict, Decimal('-1'))
        old_item_ids = [row['item_id'] for row in db.execute("SELECT item_id FROM invoice_lines WHERE invoice_id=?", (invoice_id,)).fetchall()]
        db.execute("DELETE FROM inventory_movements WHERE reference_id=? AND user_id=? AND movement_type IN ('purchase','sale')", (invoice_id, user_id))
        db.execute("DELETE FROM invoice_lines WHERE invoice_id=?", (invoice_id,))
        db.execute('''
            UPDATE invoices SET type=?, customer_id=?, supplier_id=?, date=?, reference=?, notes=?, total=?, paid=?,
                status='active', exchange_rate_to_usd=?, original_currency=?, warehouse_id=?, branch_id=?, deleted_at=NULL
            WHERE id=? AND user_id=?
        ''', (
            data['type'], data.get('customer_id'), data.get('supplier_id'), data['date'],
            data.get('reference', ''), data.get('notes', ''), str(data['total']),
            str(data.get('paid_amount', data.get('paid', 0))), data.get('exchange_rate_to_usd', 1.0),
            data.get('original_currency', 'USD'), data.get('warehouse_id'), data.get('branch_id'), invoice_id, user_id
        ))
        for line in data['lines']:
            conv_factor = Decimal(str(line.get('conversion_factor', 1)))
            if conv_factor <= 0:
                conv_factor = Decimal('1')
            base_qty = Decimal(str(line.get('base_qty', line['quantity'])))
            unit_cost = Decimal(str(line['unit_price']))
            cursor_line = db.execute('''
                INSERT INTO invoice_lines (invoice_id, item_id, quantity, unit_price, total, unit, quantity_in_base, unit_cost, cost_amount, conversion_factor)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            ''', (
                invoice_id, line['item_id'], str(line['quantity']), str(unit_cost), str(line['total']),
                line.get('unit', ''), str(base_qty), str(unit_cost), '0', str(conv_factor)
            ))
            line_id = cursor_line.lastrowid
            if data['type'] == 'purchase':
                movement_type = 'purchase'
                movement_cost = unit_cost / conv_factor
                cost_amt = movement_cost * base_qty
            else:
                movement_type = 'sale'
                item = db.execute("SELECT CAST(average_cost AS TEXT) as avg_cost FROM items WHERE id=? AND user_id=?", (line['item_id'], user_id)).fetchone()
                avg_cost = Decimal(str(item['avg_cost'])) if item else Decimal('0')
                movement_cost = unit_cost
                cost_amt = base_qty * avg_cost
            db.execute("UPDATE invoice_lines SET cost_amount=? WHERE id=?", (str(cost_amt), line_id))
            db.execute('''
                INSERT INTO inventory_movements (item_id, user_id, movement_type, quantity, unit_cost, reference_id, movement_date)
                VALUES (?,?,?,?,?,?,?)
            ''', (line['item_id'], user_id, movement_type, str(base_qty), str(movement_cost), invoice_id, datetime.datetime.now().isoformat()))
        for item_id in set(old_item_ids + [line['item_id'] for line in data['lines']]):
            _update_item_quantity(db, item_id, user_id)
            _recalculate_average_cost(db, item_id, user_id)
        _apply_invoice_financial_effect(db, {
            'user_id': user_id, 'type': data['type'], 'customer_id': data.get('customer_id'),
            'supplier_id': data.get('supplier_id'), 'total': data['total'],
            'paid': data.get('paid_amount', data.get('paid', 0))
        }, Decimal('1'))
        audit_log('UPDATE', 'SALE_INVOICE' if data.get('type') == 'sale' else 'PURCHASE_INVOICE', invoice_id, old_values=old_invoice_dict, new_values=data, details='تعديل فاتورة')
        db.execute("COMMIT")
        return jsonify({'id': invoice_id, 'status': 'ok'}), 200
    except Exception as e:
        db.execute("ROLLBACK")
        return jsonify({'error': str(e)}), 500

@invoices_bp.route('/invoices/<int:invoice_id>', methods=['DELETE'])
@jwt_required()
def delete_invoice(invoice_id):
    user_id = get_jwt_identity()
    db = get_db()
    inv = db.execute("SELECT * FROM invoices WHERE id=? AND user_id=? AND deleted_at IS NULL", (invoice_id, user_id)).fetchone()
    if not inv:
        return jsonify({'error': 'Not found'}), 404
    if _invoice_has_vouchers(db, invoice_id, user_id):
        return jsonify({'error': 'لا يمكن حذف فاتورة مرتبطة بسندات. احذف السندات أولاً.'}), 400
    db.execute("BEGIN TRANSACTION")
    try:
        item_ids = [row['item_id'] for row in db.execute("SELECT item_id FROM invoice_lines WHERE invoice_id=?", (invoice_id,)).fetchall()]
        db.execute("DELETE FROM inventory_movements WHERE reference_id=? AND user_id=? AND movement_type IN ('purchase','sale')", (invoice_id, user_id))
        for item_id in set(item_ids):
            _update_item_quantity(db, item_id, user_id)
            _recalculate_average_cost(db, item_id, user_id)
        _apply_invoice_financial_effect(db, dict(inv), Decimal('-1'))
        db.execute("UPDATE invoices SET deleted_at = datetime('now') WHERE id=? AND user_id=?", (invoice_id, user_id))
        audit_log('SOFT_DELETE', 'SALE_INVOICE' if inv['type'] == 'sale' else 'PURCHASE_INVOICE', invoice_id, old_values=dict(inv), details='إلغاء/حذف فاتورة')
        db.execute("COMMIT")
        return jsonify({'status': 'ok'})
    except Exception as e:
        db.execute("ROLLBACK")
        return jsonify({'error': str(e)}), 500


