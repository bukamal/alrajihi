from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.api.audit_utils import audit_log
from alrajhi_server.database.connection import get_db
import datetime
from decimal import Decimal
import re

items_bp = Blueprint('items', __name__)


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


def _sync_opening_inventory(db, item_id, user_id, quantity, unit_cost):
    qty = Decimal(str(quantity or 0))
    cost = Decimal(str(unit_cost or 0))
    db.execute("DELETE FROM inventory_movements WHERE item_id=? AND user_id=? AND movement_type='opening' AND reference_id IS NULL",
               (item_id, user_id))
    if qty != 0:
        db.execute('''
            INSERT INTO inventory_movements (item_id, user_id, movement_type, quantity, unit_cost, reference_id, movement_date)
            VALUES (?,?,?,?,?,?,?)
        ''', (item_id, user_id, 'opening', str(qty), str(cost), None, datetime.datetime.now().isoformat()))
    _update_item_quantity(db, item_id, user_id)
    _recalculate_average_cost(db, item_id, user_id)


def _validate_barcode_format(barcode):
    if barcode is None or str(barcode).strip() == '':
        return None
    value = str(barcode).strip()
    if re.fullmatch(r"\d{13}", value):
        total = sum(int(d) if i % 2 == 0 else int(d) * 3 for i, d in enumerate(value[:12]))
        check = str((10 - (total % 10)) % 10)
        if check != value[-1]:
            raise ValueError('باركود EAN-13 غير صالح: رقم التحقق غير صحيح')
        return value
    if not re.fullmatch(r"[A-Za-z0-9._\- /]{1,64}", value):
        raise ValueError('صيغة الباركود غير صالحة')
    return value

def _assert_unique_barcode(db, user_id, barcode, item_id=None):
    value = _validate_barcode_format(barcode)
    if not value:
        return None
    params = [user_id, value]
    sql = "SELECT id, name FROM items WHERE user_id=? AND barcode=? AND deleted_at IS NULL"
    if item_id is not None:
        sql += " AND id<>?"
        params.append(item_id)
    row = db.execute(sql, params).fetchone()
    if row:
        raise ValueError(f"الباركود '{value}' مستخدم بالفعل للمادة: {row['name']}")
    return value

@items_bp.route('/items', methods=['GET'])
@jwt_required()
def get_items():
    user_id = get_jwt_identity()
    search = request.args.get('search')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)
    db = get_db()
    query = """
        SELECT i.*, c.name as category_name,
               COALESCE((
                   SELECT SUM(CASE
                       WHEN movement_type IN ('opening','purchase','adjustment','production_out') THEN CAST(quantity AS REAL)
                       WHEN movement_type IN ('sale','production_consume') THEN -CAST(quantity AS REAL)
                       ELSE 0 END)
                   FROM inventory_movements
                   WHERE item_id = i.id AND user_id = i.user_id
               ), CAST(COALESCE(i.quantity, '0') AS REAL)) AS available,
               COALESCE((
                   SELECT SUM(CAST(quantity AS REAL))
                   FROM inventory_movements
                   WHERE item_id = i.id AND user_id = i.user_id AND movement_type = 'opening'
               ), CAST(COALESCE(i.quantity, '0') AS REAL)) AS opening_quantity
        FROM items i
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE i.user_id = ? AND i.deleted_at IS NULL
    """
    params = [user_id]
    if search:
        query += " AND (i.name LIKE ? OR i.barcode LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY i.name"
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    if offset:
        query += " OFFSET ?"
        params.append(offset)
    count_query = "SELECT COUNT(*) FROM items i WHERE i.user_id = ? AND i.deleted_at IS NULL"
    count_params = [user_id]
    if search:
        count_query += " AND (i.name LIKE ? OR i.barcode LIKE ?)"
        count_params.extend([f"%{search}%", f"%{search}%"])
    total = db.execute(count_query, count_params).fetchone()[0]
    rows = db.execute(query, params).fetchall()
    return jsonify({'items': [dict(row) for row in rows], 'total': total})

@items_bp.route('/items', methods=['POST'])
@jwt_required()
def add_item():
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    try:
        data['barcode'] = _assert_unique_barcode(db, user_id, data.get('barcode'))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    cursor = db.execute('''
        INSERT INTO items (user_id, name, category_id, item_type, purchase_price, selling_price, quantity, unit, average_cost, barcode, reorder_level)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        user_id, data['name'], data.get('category_id'), data.get('item_type', 'مخزون'),
        data.get('purchase_price', 0), data.get('selling_price', 0),
        data.get('quantity', 0), data.get('unit', ''), data.get('average_cost', 0),
        data.get('barcode'), data.get('reorder_level', 0)
    ))
    item_id = cursor.lastrowid
    _sync_opening_inventory(db, item_id, user_id, data.get('quantity', 0), data.get('average_cost', data.get('purchase_price', 0)))
    db.commit()
    audit_log('CREATE', 'ITEM', item_id, new_values=data, details='إنشاء مادة')
    db.commit()
    return jsonify({'id': item_id}), 201

def _get_opening_quantity(db, item_id, user_id):
    row = db.execute('''
        SELECT COALESCE(SUM(CAST(quantity AS REAL)), 0) AS qty
        FROM inventory_movements
        WHERE item_id=? AND user_id=? AND movement_type='opening'
    ''', (item_id, user_id)).fetchone()
    return Decimal(str(row['qty'] if row and row['qty'] is not None else 0))


def _has_non_opening_item_movements(db, item_id, user_id):
    row = db.execute('''
        SELECT COUNT(*) AS cnt
        FROM inventory_movements
        WHERE item_id=? AND user_id=? AND movement_type <> 'opening'
    ''', (item_id, user_id)).fetchone()
    return bool(row and row['cnt'])


def _count(db, sql, params):
    row = db.execute(sql, params).fetchone()
    return int(row[0] if row else 0)


def _get_item_usage_summary(db, item_id, user_id):
    summary = {
        'invoice_lines': _count(db, "SELECT COUNT(*) FROM invoice_lines WHERE item_id=?", (item_id,)),
        'inventory_movements': _count(db, "SELECT COUNT(*) FROM inventory_movements WHERE item_id=? AND user_id=? AND movement_type <> 'opening'", (item_id, user_id)),
        'bom_products': _count(db, "SELECT COUNT(*) FROM bom WHERE product_id=? AND user_id=?", (item_id, user_id)),
        'bom_lines': _count(db, "SELECT COUNT(*) FROM bom_lines WHERE item_id=?", (item_id,)),
        'production_orders': _count(db, "SELECT COUNT(*) FROM production_orders WHERE product_id=? AND user_id=?", (item_id, user_id)),
        'production_consumptions': _count(db, "SELECT COUNT(*) FROM production_consumptions WHERE item_id=?", (item_id,)),
        'production_outputs': _count(db, "SELECT COUNT(*) FROM production_outputs WHERE item_id=?", (item_id,)),
    }
    summary['blocking_total'] = sum(summary.values())
    return summary


@items_bp.route('/items/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_item(item_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    try:
        data['barcode'] = _assert_unique_barcode(db, user_id, data.get('barcode'), item_id=item_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    current_opening = _get_opening_quantity(db, item_id, user_id)
    new_opening = Decimal(str(data.get('quantity', 0) or 0))
    if current_opening != new_opening and _has_non_opening_item_movements(db, item_id, user_id):
        return jsonify({'error': 'لا يمكن تعديل الكمية الافتتاحية بعد وجود حركات بيع/شراء/تصنيع/تسوية. استخدم تسوية مخزون بدل تعديل الافتتاحي.'}), 400
    db.execute('''
        UPDATE items SET name=?, category_id=?, item_type=?, purchase_price=?, selling_price=?, quantity=?, unit=?, average_cost=?, barcode=?, reorder_level=?
        WHERE id=? AND user_id=? AND deleted_at IS NULL
    ''', (
        data['name'], data.get('category_id'), data.get('item_type'),
        data.get('purchase_price', 0), data.get('selling_price', 0),
        data.get('quantity', 0), data.get('unit', ''), data.get('average_cost', 0),
        data.get('barcode'), data.get('reorder_level', 0), item_id, user_id
    ))
    _sync_opening_inventory(db, item_id, user_id, data.get('quantity', 0), data.get('average_cost', data.get('purchase_price', 0)))
    db.commit()
    return jsonify({'status': 'ok'})

@items_bp.route('/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    user_id = get_jwt_identity()
    db = get_db()
    usage = _get_item_usage_summary(db, item_id, user_id)
    if usage['blocking_total'] > 0:
        details = ', '.join(f"{k}={v}" for k, v in usage.items() if k != 'blocking_total' and v)
        return jsonify({'error': f'لا يمكن حذف المادة لأنها مستخدمة في عمليات سابقة ({details}).'}), 400
    now = datetime.datetime.now().isoformat()
    db.execute("UPDATE items SET deleted_at=?, name = name || ' [محذوف #' || id || ']' WHERE id=? AND user_id=? AND deleted_at IS NULL", (now, item_id, user_id))
    db.commit()
    return jsonify({'status': 'ok'})


