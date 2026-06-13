from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.api.audit_utils import audit_log
from alrajhi_server.database.connection import get_db
import datetime
from decimal import Decimal

manufacturing_bp = Blueprint('manufacturing', __name__)


def _dec(value, default='0'):
    try:
        return Decimal(str(value if value is not None else default))
    except Exception:
        return Decimal(str(default))

def _item_qty(db, item_id):
    row = db.execute("SELECT CAST(quantity AS REAL) as qty FROM items WHERE id=?", (item_id,)).fetchone()
    return _dec(row['qty']) if row else Decimal('0')

def _item_avg_cost(db, item_id):
    row = db.execute("SELECT CAST(average_cost AS TEXT) as avg_cost FROM items WHERE id=?", (item_id,)).fetchone()
    return _dec(row['avg_cost']) if row else Decimal('0')

def _validate_positive(value, label):
    qty = _dec(value)
    if qty <= 0:
        raise ValueError(f"{label} يجب أن تكون أكبر من صفر")
    return qty

def _update_item_quantity(db, item_id):
    row = db.execute("""
        SELECT SUM(
            CASE
                WHEN movement_type IN ('opening','purchase','adjustment','production_out','consumption_reverse') THEN CAST(quantity AS REAL)
                WHEN movement_type IN ('sale','production_consume') THEN -CAST(quantity AS REAL)
                ELSE 0
            END
        ) AS total_qty
        FROM inventory_movements WHERE item_id=?
    """, (item_id,)).fetchone()
    qty = _dec(row['total_qty']) if row and row['total_qty'] is not None else Decimal('0')
    db.execute("UPDATE items SET quantity=? WHERE id=?", (str(qty), item_id))

def _recalculate_average_cost(db, item_id):
    row = db.execute("""
        SELECT SUM(CAST(quantity AS REAL)) as total_qty,
               SUM(CAST(quantity AS REAL) * CAST(unit_cost AS REAL)) as total_cost
        FROM inventory_movements
        WHERE item_id=? AND movement_type IN ('opening','purchase','adjustment','production_out','consumption_reverse')
    """, (item_id,)).fetchone()
    total_qty = _dec(row['total_qty']) if row and row['total_qty'] is not None else Decimal('0')
    total_cost = _dec(row['total_cost']) if row and row['total_cost'] is not None else Decimal('0')
    avg = total_cost / total_qty if total_qty > 0 else Decimal('0')
    db.execute("UPDATE items SET average_cost=? WHERE id=?", (str(avg), item_id))

def _record_movement(db, user_id, item_id, movement_type, quantity, unit_cost, reference_id):
    now = datetime.datetime.now().isoformat()
    db.execute("""
        INSERT INTO inventory_movements (item_id, user_id, movement_type, quantity, unit_cost, reference_id, movement_date)
        VALUES (?,?,?,?,?,?,?)
    """, (item_id, user_id, movement_type, str(quantity), str(unit_cost), reference_id, now))
    _update_item_quantity(db, item_id)
    if movement_type in ('opening','purchase','adjustment','production_out','consumption_reverse'):
        _recalculate_average_cost(db, item_id)



def _post_inventory_ledger_entry(db, user_id, item_id, warehouse_id, movement_type, direction,
                                 quantity, unit_cost, reference_type, reference_id,
                                 source_table=None, source_id=None, notes=''):
    """Shadow-post manufacturing inventory effects into inventory_ledger.

    Phase 26 keeps operational stock semantics unchanged. These entries are
    append-only audit/read-model data and are not used yet to calculate stock.
    """
    qty = abs(_dec(quantity))
    cost = _dec(unit_cost)
    total = qty * cost
    now = datetime.datetime.now().isoformat()
    db.execute("""
        INSERT INTO inventory_ledger (
            user_id, item_id, warehouse_id, movement_type, direction, quantity,
            unit_cost, total_cost, reference_type, reference_id, source_table,
            source_id, notes, movement_date
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        user_id, item_id, warehouse_id, movement_type, direction, str(qty),
        str(cost), str(total), reference_type, reference_id, source_table,
        source_id, notes, now
    ))


def _post_manufacturing_consumption_ledger(db, user_id, order, item_id, qty, unit_cost, source_id=None, notes='دفتر مخزون استهلاك إنتاج'):
    _post_inventory_ledger_entry(
        db, user_id, item_id, order['raw_warehouse_id'], 'production_consume', 'out',
        qty, unit_cost, 'production_order', order['id'], 'production_consumptions',
        source_id, notes
    )


def _post_manufacturing_output_ledger(db, user_id, order, item_id, qty, unit_cost, source_id=None, notes='دفتر مخزون إنتاج منتج نهائي'):
    _post_inventory_ledger_entry(
        db, user_id, item_id, order['output_warehouse_id'], 'production_out', 'in',
        qty, unit_cost, 'production_order', order['id'], 'production_outputs',
        source_id, notes
    )


def _post_manufacturing_consumption_reversal_ledger(db, user_id, order, item_id, qty, unit_cost, source_id=None, notes='عكس دفتر مخزون استهلاك إنتاج'):
    _post_inventory_ledger_entry(
        db, user_id, item_id, order['raw_warehouse_id'], 'production_consume_reversal', 'in',
        qty, unit_cost, 'production_order_reversal', order['id'], 'production_consumptions',
        source_id, notes
    )


def _post_manufacturing_output_reversal_ledger(db, user_id, order, item_id, qty, unit_cost, source_id=None, notes='عكس دفتر مخزون إنتاج منتج نهائي'):
    _post_inventory_ledger_entry(
        db, user_id, item_id, order['output_warehouse_id'], 'production_out_reversal', 'out',
        qty, unit_cost, 'production_order_reversal', order['id'], 'production_outputs',
        source_id, notes
    )

def _validate_bom_payload(db, data, user_id):
    product_id = data.get('product_id')
    if not product_id:
        raise ValueError('يجب اختيار المنتج النهائي')
    _validate_positive(data.get('quantity'), 'كمية BOM')
    product = db.execute("SELECT id, item_type FROM items WHERE id=? AND user_id=?", (product_id, user_id)).fetchone()
    if not product:
        raise ValueError('المنتج النهائي غير موجود')
    if product['item_type'] != 'منتج نهائي':
        raise ValueError('يجب أن يكون المنتج من نوع منتج نهائي')
    lines = data.get('lines') or []
    if not lines:
        raise ValueError('لا يمكن حفظ BOM بدون مكونات')
    seen = set()
    for line in lines:
        item_id = line.get('item_id')
        if not item_id:
            raise ValueError('يوجد مكون بدون مادة')
        if item_id == product_id:
            raise ValueError('لا يمكن أن يكون المنتج النهائي مكوناً لنفسه')
        _validate_positive(line.get('quantity'), 'كمية المكون')
        if _dec(line.get('waste_percent', 0)) < 0:
            raise ValueError('نسبة الهالك لا يمكن أن تكون سالبة')
        key = (item_id, line.get('unit_id'))
        if key in seen:
            raise ValueError('يوجد مكون مكرر في BOM')
        seen.add(key)

# ========== دوال مساعدة لتوسيع BOM ==========
def _get_bom_for_product(db, product_id, user_id):
    row = db.execute("SELECT id FROM bom WHERE product_id=? AND user_id=?", (product_id, user_id)).fetchone()
    if row:
        bom_id = row['id']
        bom = db.execute("SELECT * FROM bom WHERE id=?", (bom_id,)).fetchone()
        lines = db.execute("SELECT * FROM bom_lines WHERE bom_id=?", (bom_id,)).fetchall()
        return {'id': bom_id, 'product_id': bom['product_id'], 'quantity': bom['quantity'], 'lines': [dict(l) for l in lines]}
    return None

def _expand_bom(db, product_id, quantity, user_id, multiplier=Decimal('1'), visited=None):
    if visited is None:
        visited = set()
    if product_id in visited:
        raise Exception(f"دورة في BOM: المنتج {product_id} يظهر مرتين")
    visited.add(product_id)
    bom = _get_bom_for_product(db, product_id, user_id)
    if not bom:
        raise Exception(f"المنتج {product_id} ليس له قائمة مواد (BOM)")
    result = []
    for line in bom['lines']:
        item_id = line['item_id']
        item = db.execute("SELECT item_type FROM items WHERE id=?", (item_id,)).fetchone()
        if item and item['item_type'] == 'منتج نهائي':
            sub_items = _expand_bom(db, item_id, Decimal(str(line['quantity'])) * quantity, user_id, multiplier * Decimal(str(line.get('waste_percent', 0))), visited)
            result.extend(sub_items)
        else:
            required_qty = Decimal(str(line['quantity'])) * quantity * (Decimal('1') + Decimal(str(line.get('waste_percent', 0))))
            result.append({
                'item_id': item_id,
                'item_name': line.get('item_name', ''),
                'required_qty': required_qty,
                'waste_percent': Decimal(str(line.get('waste_percent', 0))),
                'unit_id': line.get('unit_id'),
                'unit_name': '',
                'conversion_factor': Decimal('1')
            })
    visited.remove(product_id)
    return result

def get_required_materials_recursive(db, product_id, planned_qty, user_id):
    raw_materials = _expand_bom(db, product_id, planned_qty, user_id)
    merged = {}
    for mat in raw_materials:
        key = mat['item_id']
        if key in merged:
            merged[key]['required_qty'] += mat['required_qty']
        else:
            merged[key] = mat
    result = []
    for mat in merged.values():
        item = db.execute("SELECT CAST(quantity AS REAL) as qty FROM items WHERE id=?", (mat['item_id'],)).fetchone()
        available = Decimal(str(item['qty'])) if item else Decimal('0')
        mat['available_qty'] = available
        mat['is_sufficient'] = available >= mat['required_qty']
        result.append(mat)
    return result

# ========== BOM endpoints ==========
@manufacturing_bp.route('/boms', methods=['GET'])
@jwt_required()
def get_boms():
    user_id = get_jwt_identity()
    limit = request.args.get('limit', 30, type=int)
    offset = request.args.get('offset', 0, type=int)
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM bom WHERE user_id=?", (user_id,)).fetchone()[0]
    rows = db.execute("""
        SELECT b.*, i.name as product_name 
        FROM bom b
        JOIN items i ON b.product_id = i.id
        WHERE b.user_id = ?
        ORDER BY b.id DESC
        LIMIT ? OFFSET ?
    """, (user_id, limit, offset)).fetchall()
    return jsonify({'boms': [dict(row) for row in rows], 'total': total})

@manufacturing_bp.route('/boms/<int:bom_id>', methods=['GET'])
@jwt_required()
def get_bom(bom_id):
    user_id = get_jwt_identity()
    db = get_db()
    bom = db.execute("SELECT * FROM bom WHERE id=? AND user_id=?", (bom_id, user_id)).fetchone()
    if not bom:
        return jsonify({'error': 'Not found'}), 404
    lines = db.execute("SELECT * FROM bom_lines WHERE bom_id=?", (bom_id,)).fetchall()
    result = dict(bom)
    result['lines'] = [dict(line) for line in lines]
    return jsonify(result)

@manufacturing_bp.route('/boms', methods=['POST'])
@jwt_required()
def save_bom():
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    try:
        _validate_bom_payload(db, data, user_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    now = datetime.datetime.now().isoformat()
    if data.get('id'):
        db.execute("UPDATE bom SET product_id=?, quantity=?, updated_at=? WHERE id=? AND user_id=?",
                   (data['product_id'], str(data['quantity']), now, data['id'], user_id))
        db.execute("DELETE FROM bom_lines WHERE bom_id=?", (data['id'],))
        bom_id = data['id']
    else:
        cursor = db.execute("INSERT INTO bom (product_id, quantity, user_id, created_at, updated_at) VALUES (?,?,?,?,?)",
                            (data['product_id'], str(data['quantity']), user_id, now, now))
        bom_id = cursor.lastrowid
    for line in data.get('lines', []):
        db.execute("INSERT INTO bom_lines (bom_id, item_id, quantity, unit_id, waste_percent) VALUES (?,?,?,?,?)",
                   (bom_id, line['item_id'], str(line['quantity']), line.get('unit_id'), str(line.get('waste_percent', 0))))
    audit_log('CREATE', 'BOM', bom_id, new_values=data, details='حفظ BOM')
    db.commit()
    return jsonify({'id': bom_id}), 201

@manufacturing_bp.route('/boms/<int:bom_id>', methods=['DELETE'])
@jwt_required()
def delete_bom(bom_id):
    user_id = get_jwt_identity()
    db = get_db()
    rows = db.execute("""
        SELECT id, status FROM production_orders
        WHERE product_id = (SELECT product_id FROM bom WHERE id=?)
          AND user_id=? AND status IN ('planned','in_progress')
    """, (bom_id, user_id)).fetchall()
    if rows:
        return jsonify({'error': 'لا يمكن حذف BOM لوجود أوامر إنتاج نشطة'}), 400
    db.execute("DELETE FROM bom WHERE id=? AND user_id=?", (bom_id, user_id))
    audit_log('POST', 'PRODUCTION_ORDER', order_id if 'order_id' in locals() else None, details='تغيير حالة إنتاج')
    audit_log('POST', 'PRODUCTION_ORDER', order_id if 'order_id' in locals() else None, new_values=data if 'data' in locals() else None, details='عملية إنتاج')
    audit_log('POST', 'PRODUCTION_ORDER', order_id if 'order_id' in locals() else None, details='عملية إنتاج')
    db.commit()
    return jsonify({'status': 'ok'})

# ========== أوامر الإنتاج ==========
@manufacturing_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()
    limit = request.args.get('limit', 30, type=int)
    offset = request.args.get('offset', 0, type=int)
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM production_orders WHERE user_id=?", (user_id,)).fetchone()[0]
    rows = db.execute("""
        SELECT po.*, i.name as product_name, rw.name AS raw_warehouse_name, ow.name AS output_warehouse_name 
        FROM production_orders po
        JOIN items i ON po.product_id = i.id
        LEFT JOIN warehouses rw ON rw.id = po.raw_warehouse_id
        LEFT JOIN warehouses ow ON ow.id = po.output_warehouse_id
        WHERE po.user_id = ?
        ORDER BY po.id DESC
        LIMIT ? OFFSET ?
    """, (user_id, limit, offset)).fetchall()
    return jsonify({'orders': [dict(row) for row in rows], 'total': total})

@manufacturing_bp.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    user_id = get_jwt_identity()
    db = get_db()
    order = db.execute("SELECT * FROM production_orders WHERE id=? AND user_id=?", (order_id, user_id)).fetchone()
    if not order:
        return jsonify({'error': 'Not found'}), 404
    consumptions = db.execute("SELECT * FROM production_consumptions WHERE order_id=?", (order_id,)).fetchall()
    outputs = db.execute("SELECT * FROM production_outputs WHERE order_id=?", (order_id,)).fetchall()
    reservations = db.execute("SELECT * FROM material_reservations WHERE order_id=?", (order_id,)).fetchall()
    result = dict(order)
    result['consumptions'] = [dict(c) for c in consumptions]
    result['outputs'] = [dict(o) for o in outputs]
    result['reservations'] = [dict(r) for r in reservations]
    return jsonify(result)

@manufacturing_bp.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    try:
        planned_qty = _validate_positive(data.get('planned_qty'), 'الكمية المخططة')
        product_id = data['product_id']
        bom = _get_bom_for_product(db, product_id, user_id)
        if not bom or not bom.get('lines'):
            return jsonify({'error': 'لا يمكن إنشاء أمر إنتاج دون BOM صالح يحتوي على مكونات'}), 400
        required = get_required_materials_recursive(db, product_id, planned_qty, user_id)
        insufficient = [m for m in required if not m.get('is_sufficient')]
        if insufficient:
            details = '\n'.join(f"{m.get('item_name','')}: المطلوب {m.get('required_qty')}، المتوفر {m.get('available_qty')}" for m in insufficient)
            return jsonify({'error': 'لا يمكن إنشاء أمر الإنتاج لعدم كفاية المواد:\n' + details}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    now = datetime.datetime.now().isoformat()
    year = datetime.datetime.now().strftime("%Y%m%d")
    cur = db.execute("SELECT order_number FROM production_orders ORDER BY id DESC LIMIT 1")
    last = cur.fetchone()
    if last:
        parts = last['order_number'].split('-')
        num = int(parts[1]) + 1 if len(parts) == 2 and parts[0] == year else 1
    else:
        num = 1
    order_number = f"{year}-{num:04d}"
    cursor = db.execute("""
        INSERT INTO production_orders (order_number, product_id, planned_qty, status, user_id, created_at, notes, raw_warehouse_id, output_warehouse_id)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (order_number, product_id, str(planned_qty), 'planned', user_id, now, data.get('notes', ''), data.get('raw_warehouse_id'), data.get('output_warehouse_id')))
    order_id = cursor.lastrowid
    for mat in required:
        db.execute("""
            INSERT INTO material_reservations (order_id, item_id, reserved_qty, consumed_qty)
            VALUES (?,?,?,?)
        """, (order_id, mat['item_id'], str(mat['required_qty']), '0'))
    audit_log('CREATE', 'PRODUCTION_ORDER', order_id, new_values=data, details='إنشاء أمر إنتاج')
    db.commit()
    return jsonify({'id': order_id}), 201

@manufacturing_bp.route('/orders/<int:order_id>/start', methods=['POST'])
@jwt_required()
def start_order(order_id):
    user_id = get_jwt_identity()
    db = get_db()
    order = db.execute("SELECT * FROM production_orders WHERE id=? AND user_id=?", (order_id, user_id)).fetchone()
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    if order['status'] != 'planned':
        return jsonify({'error': f"لا يمكن بدء أمر بحالة {order['status']}"}), 400
    reservations = db.execute("SELECT * FROM material_reservations WHERE order_id=?", (order_id,)).fetchall()
    if not reservations:
        return jsonify({'error': 'لا توجد حجوزات مواد لهذا الأمر'}), 400
    insufficient = []
    for r in reservations:
        required_qty = _dec(r['reserved_qty']) - _dec(r['consumed_qty'])
        available = _item_qty(db, r['item_id'])
        if available < required_qty:
            insufficient.append(f"{r['item_id']}: المطلوب {required_qty}، المتوفر {available}")
    if insufficient:
        return jsonify({'error': 'المواد التالية غير كافية:\n' + '\n'.join(insufficient)}), 400
    db.execute("UPDATE production_orders SET status='in_progress', start_date=? WHERE id=? AND user_id=?",
               (datetime.datetime.now().isoformat(), order_id, user_id))
    audit_log('POST', 'PRODUCTION_ORDER', order_id if 'order_id' in locals() else None, new_values=data if 'data' in locals() else None, details='عملية إنتاج')
    audit_log('POST', 'PRODUCTION_ORDER', order_id if 'order_id' in locals() else None, details='عملية إنتاج')
    db.commit()
    return jsonify({'status': 'ok'})

@manufacturing_bp.route('/orders/<int:order_id>/consume', methods=['POST'])
@jwt_required()
def consume_material(order_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    order = db.execute("SELECT * FROM production_orders WHERE id=? AND user_id=?", (order_id, user_id)).fetchone()
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    if order['status'] != 'in_progress':
        return jsonify({'error': f"لا يمكن تسجيل استهلاك لأمر بحالة {order['status']}"}), 400
    item_id = data['item_id']
    consumed_qty = _dec(data.get('consumed_qty'))
    if consumed_qty <= 0:
        return jsonify({'error': 'كمية الاستهلاك يجب أن تكون أكبر من صفر'}), 400
    unit_cost = _dec(data.get('unit_cost'))
    if unit_cost < 0:
        return jsonify({'error': 'تكلفة الوحدة لا يمكن أن تكون سالبة'}), 400
    if unit_cost == 0:
        unit_cost = _item_avg_cost(db, item_id)
    reservation = db.execute("""
        SELECT reserved_qty, consumed_qty FROM material_reservations 
        WHERE order_id = ? AND item_id = ?
    """, (order_id, item_id)).fetchone()
    if not reservation:
        return jsonify({'error': 'لا يوجد حجز لهذه المادة في هذا الأمر'}), 400
    remaining = _dec(reservation['reserved_qty']) - _dec(reservation['consumed_qty'])
    if consumed_qty > remaining:
        return jsonify({'error': f'الكمية المستهلكة ({consumed_qty}) تتجاوز المتبقي من الحجز ({remaining})'}), 400
    available = _item_qty(db, item_id)
    if available < consumed_qty:
        return jsonify({'error': f'المخزون غير كافٍ. المطلوب {consumed_qty}، المتوفر {available}'}), 400
    db.execute("""
        UPDATE material_reservations 
        SET consumed_qty = CAST(consumed_qty AS REAL) + ?
        WHERE order_id = ? AND item_id = ?
    """, (str(consumed_qty), order_id, item_id))
    now = datetime.datetime.now().isoformat()
    cur = db.execute("""
        INSERT INTO production_consumptions (order_id, item_id, consumed_qty, unit_cost, movement_date)
        VALUES (?,?,?,?,?)
    """, (order_id, item_id, str(consumed_qty), str(unit_cost), now))
    consumption_id = cur.lastrowid
    _record_movement(db, user_id, item_id, 'production_consume', consumed_qty, unit_cost, order_id)
    _post_manufacturing_consumption_ledger(db, user_id, order, item_id, consumed_qty, unit_cost, consumption_id)
    audit_log('POST', 'PRODUCTION_ORDER', order_id if 'order_id' in locals() else None, new_values=data if 'data' in locals() else None, details='عملية إنتاج')
    audit_log('POST', 'PRODUCTION_ORDER', order_id if 'order_id' in locals() else None, details='عملية إنتاج')
    db.commit()
    return jsonify({'status': 'ok'})

@manufacturing_bp.route('/orders/<int:order_id>/complete', methods=['POST'])
@jwt_required()
def complete_order(order_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    produced_qty = _dec(data.get('produced_qty'))
    if produced_qty <= 0:
        return jsonify({'error': 'كمية الإنتاج يجب أن تكون أكبر من صفر'}), 400
    db = get_db()
    order = db.execute("SELECT * FROM production_orders WHERE id=? AND user_id=?", (order_id, user_id)).fetchone()
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    if order['status'] != 'in_progress':
        return jsonify({'error': f"لا يمكن إتمام أمر بحالة {order['status']}"}), 400
    reservations = db.execute("SELECT * FROM material_reservations WHERE order_id=?", (order_id,)).fetchall()
    if not reservations:
        return jsonify({'error': 'لا توجد حجوزات مواد لهذا الأمر'}), 400
    for r in reservations:
        remaining = _dec(r['reserved_qty']) - _dec(r['consumed_qty'])
        if remaining > Decimal('0.001'):
            return jsonify({'error': f'لم يتم استهلاك كامل كمية المادة (المتبقي {remaining})'}), 400
    consumptions = db.execute("SELECT consumed_qty, unit_cost FROM production_consumptions WHERE order_id=?", (order_id,)).fetchall()
    if not consumptions:
        return jsonify({'error': 'لا يمكن إتمام الإنتاج دون تسجيل استهلاك مواد'}), 400
    total_cost = sum(_dec(c['consumed_qty']) * _dec(c['unit_cost']) for c in consumptions)
    if total_cost <= 0:
        return jsonify({'error': 'تكلفة الإنتاج يجب أن تكون أكبر من صفر'}), 400
    unit_cost = total_cost / produced_qty
    now = datetime.datetime.now().isoformat()
    cur = db.execute("""
        INSERT INTO production_outputs (order_id, item_id, produced_qty, unit_cost, output_date)
        VALUES (?,?,?,?,?)
    """, (order_id, order['product_id'], str(produced_qty), str(unit_cost), now))
    output_id = cur.lastrowid
    _record_movement(db, user_id, order['product_id'], 'production_out', produced_qty, unit_cost, order_id)
    _post_manufacturing_output_ledger(db, user_id, order, order['product_id'], produced_qty, unit_cost, output_id)
    db.execute("""
        UPDATE production_orders 
        SET produced_qty = CAST(produced_qty AS REAL) + ?, status='completed', end_date=?
        WHERE id=? AND user_id=?
    """, (str(produced_qty), now, order_id, user_id))
    audit_log('POST', 'PRODUCTION_ORDER', order_id if 'order_id' in locals() else None, new_values=data if 'data' in locals() else None, details='عملية إنتاج')
    audit_log('POST', 'PRODUCTION_ORDER', order_id if 'order_id' in locals() else None, details='عملية إنتاج')
    db.commit()
    return jsonify({'status': 'ok'})

@manufacturing_bp.route('/orders/<int:order_id>/reverse', methods=['POST'])
@jwt_required()
def reverse_order(order_id):
    user_id = get_jwt_identity()
    db = get_db()
    order = db.execute("SELECT * FROM production_orders WHERE id=? AND user_id=?", (order_id, user_id)).fetchone()
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    if order['status'] not in ('in_progress', 'completed'):
        return jsonify({'error': f"لا يمكن التراجع عن أمر بحالة {order['status']}"}), 400
    outputs = db.execute("SELECT * FROM production_outputs WHERE order_id=?", (order_id,)).fetchall()
    for o in outputs:
        available = _item_qty(db, o['item_id'])
        produced_qty = _dec(o['produced_qty'])
        if available < produced_qty:
            return jsonify({'error': f'لا يمكن التراجع لأن مخزون المنتج سيصبح سالباً. المتوفر {available}، المطلوب عكسه {produced_qty}'}), 400
    consumptions = db.execute("SELECT * FROM production_consumptions WHERE order_id=?", (order_id,)).fetchall()
    for c in consumptions:
        _record_movement(db, user_id, c['item_id'], 'adjustment', _dec(c['consumed_qty']), _dec(c['unit_cost']), None)
        _post_manufacturing_consumption_reversal_ledger(db, user_id, order, c['item_id'], _dec(c['consumed_qty']), _dec(c['unit_cost']), c['id'])
    for o in outputs:
        _record_movement(db, user_id, o['item_id'], 'adjustment', -_dec(o['produced_qty']), _dec(o['unit_cost']), None)
        _post_manufacturing_output_reversal_ledger(db, user_id, order, o['item_id'], _dec(o['produced_qty']), _dec(o['unit_cost']), o['id'])
    db.execute("DELETE FROM production_consumptions WHERE order_id=?", (order_id,))
    db.execute("DELETE FROM production_outputs WHERE order_id=?", (order_id,))
    db.execute("DELETE FROM material_reservations WHERE order_id=?", (order_id,))
    db.execute("DELETE FROM production_orders WHERE id=? AND user_id=?", (order_id, user_id))
    audit_log('POST', 'PRODUCTION_ORDER', order_id if 'order_id' in locals() else None, new_values=data if 'data' in locals() else None, details='عملية إنتاج')
    audit_log('POST', 'PRODUCTION_ORDER', order_id if 'order_id' in locals() else None, details='عملية إنتاج')
    db.commit()
    return jsonify({'status': 'ok'})



# ===== Remote coverage phase 2: detailed manufacturing endpoints =====
def _json_safe(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return value

@manufacturing_bp.route('/boms/by-product/<int:product_id>', methods=['GET'])
@jwt_required()
def get_bom_by_product(product_id):
    user_id = get_jwt_identity()
    db = get_db()
    row = db.execute('SELECT id FROM bom WHERE product_id=? AND user_id=?', (product_id, user_id)).fetchone()
    if not row:
        return jsonify({}), 404
    bom = db.execute('SELECT * FROM bom WHERE id=? AND user_id=?', (row['id'], user_id)).fetchone()
    lines = db.execute('''
        SELECT bl.*, i.name as item_name, u.unit_name, CAST(COALESCE(u.conversion_factor, 1) AS TEXT) as conversion_factor
        FROM bom_lines bl
        JOIN items i ON i.id=bl.item_id
        LEFT JOIN item_units u ON u.id=bl.unit_id
        WHERE bl.bom_id=?
    ''', (row['id'],)).fetchall()
    out = dict(bom)
    out['lines'] = [dict(l) for l in lines]
    return jsonify(_json_safe(out))

@manufacturing_bp.route('/boms/<int:bom_id>/can-edit', methods=['GET'])
@jwt_required()
def can_edit_bom_endpoint(bom_id):
    user_id = get_jwt_identity()
    db = get_db()
    bom = db.execute('SELECT * FROM bom WHERE id=? AND user_id=?', (bom_id, user_id)).fetchone()
    if not bom:
        return jsonify({'can_edit': False, 'message': 'BOM غير موجود'})
    rows = db.execute("""
        SELECT id, status FROM production_orders
        WHERE product_id=? AND user_id=? AND status IN ('planned', 'in_progress')
    """, (bom['product_id'], user_id)).fetchall()
    if rows:
        return jsonify({'can_edit': False, 'message': 'لا يمكن تعديل BOM لوجود أوامر إنتاج نشطة: ' + ', '.join(str(r['id']) for r in rows)})
    return jsonify({'can_edit': True, 'message': ''})

@manufacturing_bp.route('/boms/<int:bom_id>/required-materials', methods=['GET'])
@jwt_required()
def required_materials_endpoint(bom_id):
    user_id = get_jwt_identity()
    planned_qty = _dec(request.args.get('planned_qty', '1'))
    db = get_db()
    bom = db.execute('SELECT * FROM bom WHERE id=? AND user_id=?', (bom_id, user_id)).fetchone()
    if not bom:
        return jsonify({'materials': []})
    try:
        materials = get_required_materials_recursive(db, bom['product_id'], planned_qty, user_id)
        return jsonify({'materials': _json_safe(materials)})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400

@manufacturing_bp.route('/boms/<int:bom_id>/availability', methods=['GET'])
@jwt_required()
def availability_endpoint(bom_id):
    user_id = get_jwt_identity()
    planned_qty = _dec(request.args.get('planned_qty', '1'))
    db = get_db()
    bom = db.execute('SELECT * FROM bom WHERE id=? AND user_id=?', (bom_id, user_id)).fetchone()
    if not bom:
        return jsonify({'sufficient': False, 'materials': []})
    try:
        materials = get_required_materials_recursive(db, bom['product_id'], planned_qty, user_id)
        sufficient = all(bool(m.get('is_sufficient')) for m in materials)
        return jsonify({'sufficient': sufficient, 'materials': _json_safe(materials)})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400

@manufacturing_bp.route('/orders/<int:order_id>/reservations', methods=['GET'])
@jwt_required()
def order_reservations_endpoint(order_id):
    user_id = get_jwt_identity()
    db = get_db()
    own = db.execute('SELECT id FROM production_orders WHERE id=? AND user_id=?', (order_id, user_id)).fetchone()
    if not own:
        return jsonify({'reservations': []}), 404
    rows = db.execute('''
        SELECT mr.*, i.name as item_name
        FROM material_reservations mr
        JOIN items i ON i.id=mr.item_id
        WHERE mr.order_id=?
        ORDER BY mr.id
    ''', (order_id,)).fetchall()
    return jsonify({'reservations': [dict(r) for r in rows]})

@manufacturing_bp.route('/orders/<int:order_id>/consumptions', methods=['GET'])
@jwt_required()
def order_consumptions_endpoint(order_id):
    user_id = get_jwt_identity()
    db = get_db()
    own = db.execute('SELECT id FROM production_orders WHERE id=? AND user_id=?', (order_id, user_id)).fetchone()
    if not own:
        return jsonify({'consumptions': []}), 404
    rows = db.execute('''
        SELECT pc.*, i.name as item_name
        FROM production_consumptions pc
        JOIN items i ON i.id=pc.item_id
        WHERE pc.order_id=?
        ORDER BY pc.id
    ''', (order_id,)).fetchall()
    return jsonify({'consumptions': [dict(r) for r in rows]})

@manufacturing_bp.route('/orders/<int:order_id>/outputs', methods=['GET'])
@jwt_required()
def order_outputs_endpoint(order_id):
    user_id = get_jwt_identity()
    db = get_db()
    own = db.execute('SELECT id FROM production_orders WHERE id=? AND user_id=?', (order_id, user_id)).fetchone()
    if not own:
        return jsonify({'outputs': []}), 404
    rows = db.execute('''
        SELECT po.*, i.name as item_name
        FROM production_outputs po
        JOIN items i ON i.id=po.item_id
        WHERE po.order_id=?
        ORDER BY po.id
    ''', (order_id,)).fetchall()
    return jsonify({'outputs': [dict(r) for r in rows]})

@manufacturing_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order_endpoint(order_id):
    user_id = get_jwt_identity()
    db = get_db()
    row = db.execute('SELECT * FROM production_orders WHERE id=? AND user_id=?', (order_id, user_id)).fetchone()
    if not row:
        return jsonify({'error': 'Order not found'}), 404
    if row['status'] == 'completed':
        return jsonify({'error': 'لا يمكن إلغاء أمر مكتمل؛ استخدم العكس'}), 400
    now = datetime.datetime.now().isoformat()
    db.execute("UPDATE production_orders SET status='cancelled', end_date=? WHERE id=? AND user_id=?", (now, order_id, user_id))
    db.execute('DELETE FROM material_reservations WHERE order_id=?', (order_id,))
    audit_log('CANCEL', 'PRODUCTION_ORDER', order_id, old_values=dict(row), details='إلغاء أمر إنتاج')
    db.commit()
    return jsonify({'status': 'ok'})

@manufacturing_bp.route('/orders/<int:order_id>', methods=['DELETE'])
@jwt_required()
def delete_order_endpoint(order_id):
    user_id = get_jwt_identity()
    db = get_db()
    row = db.execute('SELECT * FROM production_orders WHERE id=? AND user_id=?', (order_id, user_id)).fetchone()
    if not row:
        return jsonify({'error': 'Order not found'}), 404
    if row['status'] not in ('planned', 'cancelled'):
        return jsonify({'error': f"لا يمكن حذف أمر بحالة {row['status']}"}), 400
    db.execute('DELETE FROM production_consumptions WHERE order_id=?', (order_id,))
    db.execute('DELETE FROM production_outputs WHERE order_id=?', (order_id,))
    db.execute('DELETE FROM material_reservations WHERE order_id=?', (order_id,))
    db.execute('DELETE FROM production_orders WHERE id=? AND user_id=?', (order_id, user_id))
    audit_log('DELETE', 'PRODUCTION_ORDER', order_id, old_values=dict(row), details='حذف أمر إنتاج')
    db.commit()
    return jsonify({'status': 'ok'})

@manufacturing_bp.route('/consumptions/<int:consumption_id>', methods=['DELETE'])
@jwt_required()
def delete_consumption_endpoint(consumption_id):
    user_id = get_jwt_identity()
    db = get_db()
    row = db.execute('''
        SELECT pc.*, po.status, po.user_id, po.raw_warehouse_id, po.output_warehouse_id, po.id AS order_ref_id FROM production_consumptions pc
        JOIN production_orders po ON po.id=pc.order_id
        WHERE pc.id=? AND po.user_id=?
    ''', (consumption_id, user_id)).fetchone()
    if not row:
        return jsonify({'error': 'الاستهلاك غير موجود'}), 404
    if row['status'] != 'in_progress':
        return jsonify({'error': f"لا يمكن حذف استهلاك من أمر {row['status']}"}), 400
    qty = _dec(row['consumed_qty']); cost = _dec(row['unit_cost'])
    db.execute('UPDATE material_reservations SET consumed_qty = CAST(consumed_qty AS REAL) - ? WHERE order_id=? AND item_id=?', (str(qty), row['order_id'], row['item_id']))
    _record_movement(db, user_id, row['item_id'], 'consumption_reverse', qty, cost, None)
    order_ctx = {'id': row['order_id'], 'raw_warehouse_id': row['raw_warehouse_id'], 'output_warehouse_id': row['output_warehouse_id']}
    _post_manufacturing_consumption_reversal_ledger(db, user_id, order_ctx, row['item_id'], qty, cost, consumption_id, 'عكس دفتر مخزون حذف استهلاك إنتاج')
    db.execute('DELETE FROM production_consumptions WHERE id=?', (consumption_id,))
    audit_log('DELETE', 'PRODUCTION_CONSUMPTION', consumption_id, old_values=dict(row), details='حذف استهلاك مادة إنتاج')
    db.commit()
    return jsonify({'status': 'ok'})

@manufacturing_bp.route('/outputs/<int:output_id>', methods=['DELETE'])
@jwt_required()
def delete_output_endpoint(output_id):
    user_id = get_jwt_identity()
    db = get_db()
    row = db.execute('''
        SELECT po2.*, po.status, po.user_id, po.raw_warehouse_id, po.output_warehouse_id, po.id AS order_ref_id FROM production_outputs po2
        JOIN production_orders po ON po.id=po2.order_id
        WHERE po2.id=? AND po.user_id=?
    ''', (output_id, user_id)).fetchone()
    if not row:
        return jsonify({'error': 'مخرج الإنتاج غير موجود'}), 404
    if row['status'] == 'completed':
        return jsonify({'error': 'لا يمكن حذف مخرج من أمر مكتمل؛ استخدم العكس'}), 400
    qty = _dec(row['produced_qty']); cost = _dec(row['unit_cost'])
    available = _item_qty(db, row['item_id'])
    if available < qty:
        return jsonify({'error': f'لا يمكن حذف المخرج لأن المخزون غير كاف. المتوفر {available}'}), 400
    _record_movement(db, user_id, row['item_id'], 'adjustment', -qty, cost, None)
    order_ctx = {'id': row['order_id'], 'raw_warehouse_id': row['raw_warehouse_id'], 'output_warehouse_id': row['output_warehouse_id']}
    _post_manufacturing_output_reversal_ledger(db, user_id, order_ctx, row['item_id'], qty, cost, output_id, 'عكس دفتر مخزون حذف مخرج إنتاج')
    db.execute('DELETE FROM production_outputs WHERE id=?', (output_id,))
    audit_log('DELETE', 'PRODUCTION_OUTPUT', output_id, old_values=dict(row), details='حذف مخرج إنتاج')
    db.commit()
    return jsonify({'status': 'ok'})
