from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.audit_utils import audit_log
from database.connection import get_db
import datetime
from decimal import Decimal

vouchers_bp = Blueprint('vouchers', __name__)


def _validate_voucher_payload(db, user_id, data, exclude_voucher_id=None):
    vtype = data.get('type')
    if vtype not in ('receipt', 'payment', 'expense'):
        raise ValueError('نوع السند غير صالح')
    amount = Decimal(str(data.get('amount', 0)))
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
            old_amount = Decimal(str(old['amount']))
    remaining = Decimal(str(inv['total'])) - (Decimal(str(inv['paid'])) - old_amount)
    if amount > remaining:
        raise ValueError(f'مبلغ السند يتجاوز المتبقي على الفاتورة ({remaining})')

@vouchers_bp.route('/vouchers', methods=['GET'])
@jwt_required()
def get_vouchers():
    user_id = get_jwt_identity()
    vtype = request.args.get('type')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)
    db = get_db()
    query = "SELECT * FROM vouchers WHERE user_id = ?"
    count_query = "SELECT COUNT(*) FROM vouchers WHERE user_id = ?"
    params = [user_id]
    count_params = [user_id]
    if vtype in ('receipt', 'payment', 'expense'):
        query += " AND type = ?"
        count_query += " AND type = ?"
        params.append(vtype)
        count_params.append(vtype)
    total = db.execute(count_query, count_params).fetchone()[0]
    query += " ORDER BY id DESC"
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
    data = request.get_json()
    db = get_db()
    try:
        _validate_voucher_payload(db, user_id, data)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    db.execute("BEGIN TRANSACTION")
    try:
        cursor = db.execute('''
            INSERT INTO vouchers (user_id, type, date, amount, description, reference, customer_id, supplier_id, invoice_id, exchange_rate_to_usd, original_currency)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            user_id, data['type'], data['date'], str(data['amount']),
            data.get('description', ''), data.get('reference', ''),
            data.get('customer_id'), data.get('supplier_id'), data.get('invoice_id'),
            data.get('exchange_rate_to_usd', 1.0), data.get('original_currency', 'USD')
        ))
        voucher_id = cursor.lastrowid
        amount = Decimal(str(data['amount']))
        # تحديث رصيد الصندوق
        if data['type'] == 'receipt':
            db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS TEXT) + ? WHERE id=?", (str(amount), user_id))
        elif data['type'] in ('payment', 'expense'):
            db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS TEXT) - ? WHERE id=?", (str(amount), user_id))
        # تحديث رصيد العميل/المورد
        if data.get('customer_id'):
            db.execute("UPDATE customers SET balance = CAST(COALESCE(balance, '0') AS TEXT) - ? WHERE id=?", (str(amount), data['customer_id']))
        elif data.get('supplier_id'):
            db.execute("UPDATE suppliers SET balance = CAST(COALESCE(balance, '0') AS TEXT) - ? WHERE id=?", (str(amount), data['supplier_id']))
        # تحديث المدفوع في الفاتورة
        if data.get('invoice_id'):
            db.execute("UPDATE invoices SET paid = CAST(paid AS REAL) + ? WHERE id=?", (str(amount), data['invoice_id']))
            db.execute("UPDATE invoices SET paid = MAX(paid, 0) WHERE id=?", (data['invoice_id'],))
        audit_log('CREATE', 'RECEIPT_VOUCHER' if data.get('type') == 'receipt' else 'PAYMENT_VOUCHER' if data.get('type') == 'payment' else 'EXPENSE_VOUCHER', voucher_id, new_values=data, details='إنشاء سند')
        db.execute("COMMIT")
        return jsonify({'id': voucher_id}), 201
    except Exception as e:
        db.execute("ROLLBACK")
        return jsonify({'error': str(e)}), 500

@vouchers_bp.route('/vouchers/<int:voucher_id>', methods=['PUT'])
@jwt_required()
def update_voucher(voucher_id):
    # حذف القديم وإضافة الجديد (للبساطة)
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    db.execute("BEGIN TRANSACTION")
    try:
        # حذف السند القديم وعكس آثاره
        old = db.execute("SELECT * FROM vouchers WHERE id=? AND user_id=?", (voucher_id, user_id)).fetchone()
        if not old:
            db.execute("ROLLBACK")
            return jsonify({'error': 'Not found'}), 404
        try:
            _validate_voucher_payload(db, user_id, data, exclude_voucher_id=voucher_id)
        except ValueError as e:
            db.execute("ROLLBACK")
            return jsonify({'error': str(e)}), 400
        old_amount = Decimal(str(old['amount']))
        if old['type'] == 'receipt':
            db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS TEXT) - ? WHERE id=?", (str(old_amount), user_id))
        elif old['type'] in ('payment', 'expense'):
            db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS TEXT) + ? WHERE id=?", (str(old_amount), user_id))
        if old.get('customer_id'):
            db.execute("UPDATE customers SET balance = CAST(COALESCE(balance, '0') AS TEXT) + ? WHERE id=?", (str(old_amount), old['customer_id']))
        elif old.get('supplier_id'):
            db.execute("UPDATE suppliers SET balance = CAST(COALESCE(balance, '0') AS TEXT) + ? WHERE id=?", (str(old_amount), old['supplier_id']))
        if old.get('invoice_id'):
            db.execute("UPDATE invoices SET paid = CAST(paid AS REAL) - ? WHERE id=?", (str(old_amount), old['invoice_id']))
        db.execute("DELETE FROM vouchers WHERE id=? AND user_id=?", (voucher_id, user_id))
        # إضافة الجديد (مع تغيير البيانات)
        cursor = db.execute('''
            INSERT INTO vouchers (user_id, type, date, amount, description, reference, customer_id, supplier_id, invoice_id, exchange_rate_to_usd, original_currency)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            user_id, data['type'], data['date'], str(data['amount']),
            data.get('description', ''), data.get('reference', ''),
            data.get('customer_id'), data.get('supplier_id'), data.get('invoice_id'),
            data.get('exchange_rate_to_usd', 1.0), data.get('original_currency', 'USD')
        ))
        new_voucher_id = cursor.lastrowid
        new_amount = Decimal(str(data['amount']))
        if data['type'] == 'receipt':
            db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS TEXT) + ? WHERE id=?", (str(new_amount), user_id))
        elif data['type'] in ('payment', 'expense'):
            db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS TEXT) - ? WHERE id=?", (str(new_amount), user_id))
        if data.get('customer_id'):
            db.execute("UPDATE customers SET balance = CAST(COALESCE(balance, '0') AS TEXT) - ? WHERE id=?", (str(new_amount), data['customer_id']))
        elif data.get('supplier_id'):
            db.execute("UPDATE suppliers SET balance = CAST(COALESCE(balance, '0') AS TEXT) - ? WHERE id=?", (str(new_amount), data['supplier_id']))
        if data.get('invoice_id'):
            db.execute("UPDATE invoices SET paid = CAST(paid AS REAL) + ? WHERE id=?", (str(new_amount), data['invoice_id']))
        audit_log('UPDATE', 'RECEIPT_VOUCHER' if data.get('type') == 'receipt' else 'PAYMENT_VOUCHER' if data.get('type') == 'payment' else 'EXPENSE_VOUCHER', new_voucher_id, old_values=dict(old), new_values=data, details='تعديل سند')
        db.execute("COMMIT")
        return jsonify({'id': new_voucher_id}), 200
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
        old = db.execute("SELECT * FROM vouchers WHERE id=? AND user_id=?", (voucher_id, user_id)).fetchone()
        if not old:
            return jsonify({'error': 'Not found'}), 404
        amount = Decimal(str(old['amount']))
        if old['type'] == 'receipt':
            db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS TEXT) - ? WHERE id=?", (str(amount), user_id))
        elif old['type'] in ('payment', 'expense'):
            db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS TEXT) + ? WHERE id=?", (str(amount), user_id))
        if old.get('customer_id'):
            db.execute("UPDATE customers SET balance = CAST(COALESCE(balance, '0') AS TEXT) + ? WHERE id=?", (str(amount), old['customer_id']))
        elif old.get('supplier_id'):
            db.execute("UPDATE suppliers SET balance = CAST(COALESCE(balance, '0') AS TEXT) + ? WHERE id=?", (str(amount), old['supplier_id']))
        if old.get('invoice_id'):
            db.execute("UPDATE invoices SET paid = CAST(paid AS REAL) - ? WHERE id=?", (str(amount), old['invoice_id']))
        db.execute("DELETE FROM vouchers WHERE id=? AND user_id=?", (voucher_id, user_id))
        audit_log('DELETE', 'RECEIPT_VOUCHER' if old['type'] == 'receipt' else 'PAYMENT_VOUCHER' if old['type'] == 'payment' else 'EXPENSE_VOUCHER', voucher_id, old_values=dict(old), details='حذف سند')
        db.execute("COMMIT")
        return jsonify({'status': 'ok'})
    except Exception as e:
        db.execute("ROLLBACK")
        return jsonify({'error': str(e)}), 500


