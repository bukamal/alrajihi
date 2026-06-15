from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.api.audit_utils import audit_log
from alrajhi_server.database.connection import get_db
from decimal import Decimal

vouchers_bp = Blueprint('vouchers', __name__)


def _dec(value, default='0'):
    try:
        return Decimal(str(value if value is not None else default))
    except Exception:
        return Decimal(default)


def _entity_type(vtype):
    if vtype == 'receipt':
        return 'RECEIPT_VOUCHER'
    if vtype == 'payment':
        return 'PAYMENT_VOUCHER'
    return 'EXPENSE_VOUCHER'


def _validate_voucher_payload(db, user_id, data, exclude_voucher_id=None):
    vtype = data.get('type')
    if vtype not in ('receipt', 'payment', 'expense'):
        raise ValueError('نوع السند غير صالح')
    amount = _dec(data.get('amount'))
    if amount <= 0:
        raise ValueError('مبلغ السند يجب أن يكون أكبر من صفر')
    customer_id = data.get('customer_id')
    supplier_id = data.get('supplier_id')
    invoice_id = data.get('invoice_id')
    if vtype == 'receipt':
        if not customer_id or supplier_id:
            raise ValueError('سند القبض يجب أن يرتبط بعميل فقط')
    elif vtype == 'payment':
        if not supplier_id or customer_id:
            raise ValueError('سند الدفع يجب أن يرتبط بمورد فقط')
    elif vtype == 'expense':
        if invoice_id:
            raise ValueError('سند المصروف لا يجب ربطه بفاتورة')
        if customer_id or supplier_id:
            raise ValueError('سند المصروف لا يجب ربطه بعميل أو مورد')
    if not invoice_id:
        return
    inv = db.execute("SELECT * FROM invoices WHERE id=? AND user_id=? AND deleted_at IS NULL", (invoice_id, user_id)).fetchone()
    if not inv:
        raise ValueError('الفاتورة المرتبطة غير موجودة أو محذوفة')
    if vtype == 'receipt' and inv['type'] != 'sale':
        raise ValueError('سند القبض لا يرتبط إلا بفاتورة بيع')
    if vtype == 'payment' and inv['type'] != 'purchase':
        raise ValueError('سند الدفع لا يرتبط إلا بفاتورة شراء')
    if vtype == 'receipt' and customer_id and inv['customer_id'] != customer_id:
        raise ValueError('العميل في السند لا يطابق عميل الفاتورة')
    if vtype == 'payment' and supplier_id and inv['supplier_id'] != supplier_id:
        raise ValueError('المورد في السند لا يطابق مورد الفاتورة')
    old_amount = Decimal('0')
    if exclude_voucher_id is not None:
        old = db.execute("SELECT * FROM vouchers WHERE id=? AND user_id=?", (exclude_voucher_id, user_id)).fetchone()
        if old and old['invoice_id'] == invoice_id:
            old_amount = _dec(old['amount'])
    remaining = _dec(inv['total']) - (_dec(inv['paid']) - old_amount)
    if amount > remaining:
        raise ValueError(f'مبلغ السند يتجاوز المتبقي على الفاتورة ({remaining})')


def _apply_voucher_effects(db, user_id, voucher):
    amount = _dec(voucher.get('amount'))
    if voucher.get('type') == 'receipt':
        db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS REAL) + ? WHERE id=?", (str(amount), user_id))
    elif voucher.get('type') in ('payment', 'expense'):
        db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS REAL) - ? WHERE id=?", (str(amount), user_id))
    if voucher.get('customer_id'):
        db.execute("UPDATE customers SET balance = CAST(COALESCE(balance, '0') AS REAL) - ? WHERE id=? AND user_id=?", (str(amount), voucher['customer_id'], user_id))
    elif voucher.get('supplier_id'):
        db.execute("UPDATE suppliers SET balance = CAST(COALESCE(balance, '0') AS REAL) - ? WHERE id=? AND user_id=?", (str(amount), voucher['supplier_id'], user_id))
    if voucher.get('invoice_id'):
        db.execute("UPDATE invoices SET paid = CAST(COALESCE(paid, '0') AS REAL) + ? WHERE id=? AND user_id=?", (str(amount), voucher['invoice_id'], user_id))


def _reverse_voucher_effects(db, user_id, voucher):
    amount = _dec(voucher.get('amount'))
    if voucher.get('type') == 'receipt':
        db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS REAL) - ? WHERE id=?", (str(amount), user_id))
    elif voucher.get('type') in ('payment', 'expense'):
        db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS REAL) + ? WHERE id=?", (str(amount), user_id))
    if voucher.get('customer_id'):
        db.execute("UPDATE customers SET balance = CAST(COALESCE(balance, '0') AS REAL) + ? WHERE id=? AND user_id=?", (str(amount), voucher['customer_id'], user_id))
    elif voucher.get('supplier_id'):
        db.execute("UPDATE suppliers SET balance = CAST(COALESCE(balance, '0') AS REAL) + ? WHERE id=? AND user_id=?", (str(amount), voucher['supplier_id'], user_id))
    if voucher.get('invoice_id'):
        db.execute("UPDATE invoices SET paid = CAST(COALESCE(paid, '0') AS REAL) - ? WHERE id=? AND user_id=?", (str(amount), voucher['invoice_id'], user_id))


def _record_voucher_movement(db, user_id, voucher_id, voucher):
    db.execute("DELETE FROM cash_bank_movements WHERE user_id=? AND reference_type='voucher' AND reference_id=?", (user_id, voucher_id))
    amount = _dec(voucher.get('amount'))
    signed = abs(amount) if voucher.get('type') == 'receipt' else -abs(amount)
    db.execute('''
        INSERT INTO cash_bank_movements
        (user_id, branch_id, cashbox_id, bank_account_id, movement_type, amount, direction, reference_type, reference_id, description, movement_date, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
    ''', (
        user_id, voucher.get('branch_id'), voucher.get('cashbox_id'), voucher.get('bank_account_id'), voucher.get('type'),
        str(signed), 'in' if signed >= 0 else 'out', 'voucher', voucher_id,
        voucher.get('description') or voucher.get('reference') or 'سند مالي', voucher.get('date')
    ))


def _delete_voucher_movement(db, user_id, voucher_id):
    db.execute("DELETE FROM cash_bank_movements WHERE user_id=? AND reference_type='voucher' AND reference_id=?", (user_id, voucher_id))


def _row_to_dict(row):
    return dict(row) if row else None


@vouchers_bp.route('/vouchers', methods=['GET'])
@jwt_required()
def get_vouchers():
    user_id = get_jwt_identity()
    vtype = request.args.get('type')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)
    db = get_db()
    query = """
        SELECT v.*, b.name AS branch_name, c.name AS cashbox_name, ba.bank_name AS bank_name, ba.account_name AS bank_account_name
        FROM vouchers v
        LEFT JOIN branches b ON b.id=v.branch_id
        LEFT JOIN cashboxes c ON c.id=v.cashbox_id
        LEFT JOIN bank_accounts ba ON ba.id=v.bank_account_id
        WHERE v.user_id = ?
    """
    count_query = "SELECT COUNT(*) FROM vouchers WHERE user_id = ?"
    params = [user_id]
    count_params = [user_id]
    if vtype in ('receipt', 'payment', 'expense'):
        query += " AND v.type = ?"
        count_query += " AND type = ?"
        params.append(vtype)
        count_params.append(vtype)
    total = db.execute(count_query, count_params).fetchone()[0]
    query += " ORDER BY v.id DESC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    if offset is not None:
        query += " OFFSET ?"
        params.append(offset)
    rows = db.execute(query, params).fetchall()
    return jsonify({'vouchers': [dict(row) for row in rows], 'total': total})


@vouchers_bp.route('/vouchers/<int:voucher_id>', methods=['GET'])
@jwt_required()
def get_voucher(voucher_id):
    user_id = get_jwt_identity()
    db = get_db()
    row = db.execute("SELECT * FROM vouchers WHERE id=? AND user_id=?", (voucher_id, user_id)).fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dict(row))


@vouchers_bp.route('/vouchers', methods=['POST'])
@jwt_required()
def add_voucher():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    db = get_db()
    try:
        _validate_voucher_payload(db, user_id, data)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    db.execute("BEGIN TRANSACTION")
    try:
        cursor = db.execute('''
            INSERT INTO vouchers
            (user_id, type, date, amount, description, reference, customer_id, supplier_id, invoice_id,
             exchange_rate_to_usd, original_currency, branch_id, cashbox_id, bank_account_id, payment_method)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            user_id, data['type'], data['date'], str(data['amount']),
            data.get('description', ''), data.get('reference', ''),
            data.get('customer_id'), data.get('supplier_id'), data.get('invoice_id'),
            data.get('exchange_rate_to_usd', 1.0), data.get('original_currency', 'USD'), data.get('branch_id'),
            data.get('cashbox_id'), data.get('bank_account_id'), data.get('payment_method', 'cash')
        ))
        voucher_id = cursor.lastrowid
        _apply_voucher_effects(db, user_id, data)
        _record_voucher_movement(db, user_id, voucher_id, data)
        audit_log('CREATE', _entity_type(data.get('type')), voucher_id, new_values=data, details='إنشاء سند')
        db.execute("COMMIT")
        return jsonify({'id': voucher_id}), 201
    except Exception as e:
        db.execute("ROLLBACK")
        return jsonify({'error': str(e)}), 500


@vouchers_bp.route('/vouchers/<int:voucher_id>', methods=['PUT'])
@jwt_required()
def update_voucher(voucher_id):
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    db = get_db()
    try:
        _validate_voucher_payload(db, user_id, data, exclude_voucher_id=voucher_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    db.execute("BEGIN TRANSACTION")
    try:
        old_row = db.execute("SELECT * FROM vouchers WHERE id=? AND user_id=?", (voucher_id, user_id)).fetchone()
        if not old_row:
            db.execute("ROLLBACK")
            return jsonify({'error': 'Not found'}), 404
        old = dict(old_row)
        _reverse_voucher_effects(db, user_id, old)
        db.execute('''
            UPDATE vouchers
            SET type=?, date=?, amount=?, description=?, reference=?, customer_id=?, supplier_id=?, invoice_id=?,
                exchange_rate_to_usd=?, original_currency=?, branch_id=?, cashbox_id=?, bank_account_id=?, payment_method=?
            WHERE id=? AND user_id=?
        ''', (
            data['type'], data['date'], str(data['amount']), data.get('description', ''), data.get('reference', ''),
            data.get('customer_id'), data.get('supplier_id'), data.get('invoice_id'),
            data.get('exchange_rate_to_usd', 1.0), data.get('original_currency', 'USD'), data.get('branch_id'),
            data.get('cashbox_id'), data.get('bank_account_id'), data.get('payment_method', 'cash'), voucher_id, user_id
        ))
        _apply_voucher_effects(db, user_id, data)
        _record_voucher_movement(db, user_id, voucher_id, data)
        audit_log('UPDATE', _entity_type(data.get('type')), voucher_id, old_values=old, new_values=data, details='تعديل سند')
        db.execute("COMMIT")
        return jsonify({'id': voucher_id}), 200
    except Exception as e:
        db.execute("ROLLBACK")
        return jsonify({'error': str(e)}), 500


@vouchers_bp.route('/vouchers/<int:voucher_id>', methods=['DELETE'])
@jwt_required()
def delete_voucher(voucher_id):
    user_id = get_jwt_identity()
    db = get_db()
    db.execute("BEGIN TRANSACTION")
    try:
        old_row = db.execute("SELECT * FROM vouchers WHERE id=? AND user_id=?", (voucher_id, user_id)).fetchone()
        if not old_row:
            db.execute("ROLLBACK")
            return jsonify({'error': 'Not found'}), 404
        old = dict(old_row)
        _reverse_voucher_effects(db, user_id, old)
        _delete_voucher_movement(db, user_id, voucher_id)
        db.execute("DELETE FROM vouchers WHERE id=? AND user_id=?", (voucher_id, user_id))
        audit_log('DELETE', _entity_type(old.get('type')), voucher_id, old_values=old, details='حذف سند')
        db.execute("COMMIT")
        return jsonify({'status': 'ok'})
    except Exception as e:
        db.execute("ROLLBACK")
        return jsonify({'error': str(e)}), 500
