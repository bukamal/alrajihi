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



def _normalize_units(units):
    """Return valid item sub-units, ignoring empty rows and validating factors."""
    result = []
    seen = set()
    for unit in units or []:
        name = str((unit or {}).get('unit_name') or (unit or {}).get('name') or '').strip()
        if not name:
            continue
        try:
            factor = Decimal(str((unit or {}).get('conversion_factor', 1)))
        except Exception:
            raise ValueError(f"عامل التحويل للوحدة '{name}' غير صالح")
        if factor <= 0:
            raise ValueError(f"عامل التحويل للوحدة '{name}' يجب أن يكون أكبر من صفر")
        key = name.casefold()
        if key in seen:
            raise ValueError(f"الوحدة الفرعية '{name}' مكررة")
        seen.add(key)
        result.append({'unit_name': name, 'conversion_factor': str(factor)})
    return result


def _save_item_units(db, item_id, units):
    db.execute('DELETE FROM item_units WHERE item_id=?', (item_id,))
    for unit in _normalize_units(units):
        db.execute(
            'INSERT INTO item_units (item_id, unit_name, conversion_factor) VALUES (?,?,?)',
            (item_id, unit['unit_name'], unit['conversion_factor'])
        )


def _attach_units(db, items):
    """Attach item_units to item dict(s) so remote invoices can use base/sub-units."""
    single = isinstance(items, dict)
    rows = [items] if single else list(items or [])
    ids = [int(r['id']) for r in rows if r and r.get('id') is not None]
    units_by_item = {i: [] for i in ids}
    if ids:
        placeholders = ','.join('?' for _ in ids)
        for row in db.execute(
            f'SELECT id, item_id, unit_name, conversion_factor FROM item_units WHERE item_id IN ({placeholders}) ORDER BY id',
            ids
        ).fetchall():
            units_by_item.setdefault(int(row['item_id']), []).append(dict(row))
    for row in rows:
        if row and row.get('id') is not None:
            row['units'] = units_by_item.get(int(row['id']), [])
    return rows[0] if single else rows
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
    items = _attach_units(db, [dict(row) for row in rows])
    return jsonify({'items': items, 'total': total})

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
    try:
        _save_item_units(db, item_id, data.get('units', []))
    except ValueError as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400
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



@items_bp.route('/items/<int:item_id>', methods=['GET'])
@jwt_required()
def get_item(item_id):
    user_id = get_jwt_identity()
    db = get_db()
    row = db.execute("""
        SELECT i.*, c.name as category_name,
               COALESCE((
                   SELECT SUM(CASE
                       WHEN movement_type IN ('opening','purchase','adjustment','production_out') THEN CAST(quantity AS REAL)
                       WHEN movement_type IN ('sale','production_consume') THEN -CAST(quantity AS REAL)
                       ELSE 0 END)
                   FROM inventory_movements
                   WHERE item_id = i.id AND user_id = i.user_id
               ), CAST(COALESCE(i.quantity, '0') AS REAL)) AS available
        FROM items i
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE i.id=? AND i.user_id=? AND i.deleted_at IS NULL
    """, (item_id, user_id)).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404
    return jsonify(_attach_units(db, dict(row)))

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
    try:
        _save_item_units(db, item_id, data.get('units', []))
    except ValueError as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400
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



@items_bp.route('/items/<int:item_id>/inventory-movements', methods=['GET'])
@jwt_required()
def get_inventory_movements(item_id):
    """Return legacy inventory_movements for an item through the API boundary."""
    user_id = get_jwt_identity()
    db = get_db()
    exists = db.execute(
        "SELECT id FROM items WHERE id=? AND user_id=? AND deleted_at IS NULL",
        (item_id, user_id)
    ).fetchone()
    if not exists:
        return jsonify({'error': 'not found'}), 404
    rows = db.execute('''
        SELECT id, movement_type, quantity, unit_cost, movement_date, reference_id
        FROM inventory_movements
        WHERE item_id=? AND user_id=?
        ORDER BY movement_date DESC, id DESC
    ''', (item_id, user_id)).fetchall()
    return jsonify({'movements': [dict(row) for row in rows]})


@items_bp.route('/inventory-movements', methods=['POST'])
@jwt_required()
def record_inventory_movement():
    """Record a legacy inventory_movement through the API boundary.

    This endpoint intentionally preserves the existing legacy semantics used by
    InventoryMovementDAO.  It does not replace the newer warehouse ledger.
    """
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    item_id = data.get('item_id')
    movement_type = data.get('movement_type')
    if not item_id or not movement_type:
        return jsonify({'error': 'item_id and movement_type are required'}), 400
    db = get_db()
    exists = db.execute(
        "SELECT id FROM items WHERE id=? AND user_id=? AND deleted_at IS NULL",
        (item_id, user_id)
    ).fetchone()
    if not exists:
        return jsonify({'error': 'item not found'}), 404
    now = datetime.datetime.now().isoformat()
    cursor = db.execute('''
        INSERT INTO inventory_movements (item_id, user_id, movement_type, quantity, unit_cost, reference_id, movement_date)
        VALUES (?,?,?,?,?,?,?)
    ''', (
        item_id,
        user_id,
        movement_type,
        str(data.get('quantity', 0)),
        str(data.get('unit_cost', 0)),
        data.get('reference_id'),
        now,
    ))
    movement_id = cursor.lastrowid
    _update_item_quantity(db, item_id, user_id)
    _recalculate_average_cost(db, item_id, user_id)
    db.commit()
    audit_log('POST', 'INVENTORY_MOVEMENT', movement_id, new_values=data, details='تسجيل حركة مخزون')
    db.commit()
    return jsonify({'id': movement_id}), 201


@items_bp.route('/inventory-ledger', methods=['GET'])
@jwt_required()
def get_inventory_ledger():
    """Return append-only inventory ledger entries without changing stock semantics."""
    user_id = get_jwt_identity()
    db = get_db()
    sql = ["SELECT * FROM inventory_ledger WHERE user_id=?"]
    params = [user_id]
    for field in ('item_id', 'warehouse_id', 'reference_type', 'reference_id'):
        value = request.args.get(field)
        if value not in (None, ''):
            sql.append(f"AND {field}=?")
            params.append(value)
    limit = request.args.get('limit', 200, type=int) or 200
    sql.append("ORDER BY movement_date DESC, id DESC LIMIT ?")
    params.append(min(limit, 1000))
    rows = db.execute(' '.join(sql), tuple(params)).fetchall()
    return jsonify({'ledger': [dict(row) for row in rows]})


@items_bp.route('/inventory-ledger', methods=['POST'])
@jwt_required()
def record_inventory_ledger_entry():
    """Append a ledger entry. Phase 22 does not recalculate stock from this table."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    required = ['item_id', 'movement_type', 'direction', 'quantity']
    missing = [f for f in required if data.get(f) in (None, '')]
    if missing:
        return jsonify({'error': 'missing required fields', 'fields': missing}), 400
    if data.get('direction') not in ('in', 'out', 'neutral'):
        return jsonify({'error': 'direction must be one of: in, out, neutral'}), 400
    item = db.execute("SELECT id FROM items WHERE id=? AND user_id=? AND deleted_at IS NULL", (data.get('item_id'), user_id)).fetchone()
    if not item:
        return jsonify({'error': 'item not found'}), 404
    now = data.get('movement_date') or datetime.datetime.now().isoformat()
    qty = str(data.get('quantity', '0'))
    unit_cost = data.get('unit_cost')
    total_cost = data.get('total_cost')
    if total_cost is None and unit_cost is not None:
        try:
            from decimal import Decimal
            total_cost = str(Decimal(str(qty)) * Decimal(str(unit_cost)))
        except Exception:
            total_cost = None
    cur = db.execute("""
        INSERT INTO inventory_ledger (
            user_id, item_id, warehouse_id, movement_type, direction, quantity,
            unit_cost, total_cost, reference_type, reference_id, source_table,
            source_id, notes, movement_date
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        user_id, data.get('item_id'), data.get('warehouse_id'), data.get('movement_type'),
        data.get('direction'), qty, str(unit_cost) if unit_cost is not None else None,
        str(total_cost) if total_cost is not None else None, data.get('reference_type'),
        data.get('reference_id'), data.get('source_table'), data.get('source_id'),
        data.get('notes'), now
    ))
    entry_id = cur.lastrowid
    db.commit()
    audit_log('POST', 'INVENTORY_LEDGER', entry_id, new_values=data, details='تسجيل قيد دفتر مخزون')
    db.commit()
    return jsonify({'id': entry_id}), 201



@items_bp.route('/inventory-ledger/reconciliation', methods=['GET'])
@jwt_required()
def get_inventory_ledger_reconciliation():
    """Diagnostic-only comparison between operational stock and shadow ledger."""
    user_id = get_jwt_identity()
    db = get_db()
    item_id = request.args.get('item_id')
    warehouse_id = request.args.get('warehouse_id')
    try:
        tolerance = Decimal(str(request.args.get('tolerance', '0') or '0'))
    except Exception:
        return jsonify({'error': 'invalid tolerance'}), 400

    def dec(value):
        return Decimal(str(value if value not in (None, '') else '0'))

    mismatches = []
    checked = 0

    item_sql = ["""
        SELECT i.id AS item_id, i.name AS item_name,
               CAST(COALESCE(i.quantity, '0') AS REAL) AS operational_quantity,
               COALESCE(SUM(CASE
                   WHEN l.direction='in' THEN CAST(l.quantity AS REAL)
                   WHEN l.direction='out' THEN -CAST(l.quantity AS REAL)
                   ELSE 0 END), 0) AS ledger_quantity
        FROM items i
        LEFT JOIN inventory_ledger l ON l.user_id=i.user_id AND l.item_id=i.id
        WHERE i.user_id=? AND i.deleted_at IS NULL
    """]
    params = [user_id]
    if item_id not in (None, ''):
        item_sql.append('AND i.id=?')
        params.append(item_id)
    item_sql.append('GROUP BY i.id, i.name, i.quantity ORDER BY i.name')
    for row in db.execute(' '.join(item_sql), tuple(params)).fetchall():
        checked += 1
        op = dec(row['operational_quantity'])
        led = dec(row['ledger_quantity'])
        diff = op - led
        if abs(diff) > tolerance:
            mismatches.append({
                'scope': 'item',
                'item_id': row['item_id'],
                'item_name': row['item_name'],
                'warehouse_id': None,
                'warehouse_name': None,
                'operational_quantity': str(op),
                'ledger_quantity': str(led),
                'difference': str(diff),
            })

    wh_sql = ["""
        SELECT b.item_id, i.name AS item_name, b.warehouse_id, w.name AS warehouse_name,
               CAST(COALESCE(b.quantity, '0') AS REAL) AS operational_quantity,
               COALESCE(SUM(CASE
                   WHEN l.direction='in' THEN CAST(l.quantity AS REAL)
                   WHEN l.direction='out' THEN -CAST(l.quantity AS REAL)
                   ELSE 0 END), 0) AS ledger_quantity
        FROM item_warehouse_balances b
        JOIN items i ON i.id=b.item_id AND i.user_id=b.user_id
        JOIN warehouses w ON w.id=b.warehouse_id AND w.user_id=b.user_id
        LEFT JOIN inventory_ledger l ON l.user_id=b.user_id AND l.item_id=b.item_id AND l.warehouse_id=b.warehouse_id
        WHERE b.user_id=?
    """]
    params = [user_id]
    if item_id not in (None, ''):
        wh_sql.append('AND b.item_id=?')
        params.append(item_id)
    if warehouse_id not in (None, ''):
        wh_sql.append('AND b.warehouse_id=?')
        params.append(warehouse_id)
    wh_sql.append('GROUP BY b.item_id, i.name, b.warehouse_id, w.name, b.quantity ORDER BY i.name, w.name')
    for row in db.execute(' '.join(wh_sql), tuple(params)).fetchall():
        checked += 1
        op = dec(row['operational_quantity'])
        led = dec(row['ledger_quantity'])
        diff = op - led
        if abs(diff) > tolerance:
            mismatches.append({
                'scope': 'warehouse',
                'item_id': row['item_id'],
                'item_name': row['item_name'],
                'warehouse_id': row['warehouse_id'],
                'warehouse_name': row['warehouse_name'],
                'operational_quantity': str(op),
                'ledger_quantity': str(led),
                'difference': str(diff),
            })

    return jsonify({
        'checked': checked,
        'mismatch_count': len(mismatches),
        'mismatches': mismatches,
        'diagnostic_only': True,
        'note': 'Phase 27 compares operational stock with the shadow ledger; it does not change stock.'
    })


@items_bp.route('/inventory-ledger/dual-read', methods=['GET'])
@jwt_required()
def get_inventory_ledger_dual_read():
    """Dual-read operational stock and shadow ledger balances.

    Phase 31 is diagnostic-only. Operational stock remains authoritative.
    """
    user_id = get_jwt_identity()
    db = get_db()
    item_id = request.args.get('item_id')
    warehouse_id = request.args.get('warehouse_id')
    include_matches = str(request.args.get('include_matches', '1')).lower() not in ('0', 'false', 'no')
    try:
        tolerance = Decimal(str(request.args.get('tolerance', '0') or '0'))
    except Exception:
        return jsonify({'error': 'invalid tolerance'}), 400

    def dec(value):
        return Decimal(str(value if value not in (None, '') else '0'))

    rows = []
    checked = matched = mismatched = 0

    item_sql = ["""
        SELECT i.id AS item_id, i.name AS item_name,
               CAST(COALESCE(i.quantity, '0') AS REAL) AS operational_quantity,
               COALESCE(SUM(CASE
                   WHEN l.direction='in' THEN CAST(l.quantity AS REAL)
                   WHEN l.direction='out' THEN -CAST(l.quantity AS REAL)
                   ELSE 0 END), 0) AS ledger_quantity
        FROM items i
        LEFT JOIN inventory_ledger l ON l.user_id=i.user_id AND l.item_id=i.id
        WHERE i.user_id=? AND i.deleted_at IS NULL
    """]
    params = [user_id]
    if item_id not in (None, ''):
        item_sql.append('AND i.id=?')
        params.append(item_id)
    item_sql.append('GROUP BY i.id, i.name, i.quantity ORDER BY i.name')
    for row in db.execute(' '.join(item_sql), tuple(params)).fetchall():
        checked += 1
        op = dec(row['operational_quantity'])
        led = dec(row['ledger_quantity'])
        diff = op - led
        ok = abs(diff) <= tolerance
        matched += 1 if ok else 0
        mismatched += 0 if ok else 1
        if include_matches or not ok:
            rows.append({
                'scope': 'item',
                'item_id': row['item_id'],
                'item_name': row['item_name'],
                'warehouse_id': None,
                'warehouse_name': None,
                'operational_quantity': str(op),
                'ledger_quantity': str(led),
                'difference': str(diff),
                'matches': ok,
                'read_source': 'dual',
            })

    wh_sql = ["""
        SELECT b.item_id, i.name AS item_name, b.warehouse_id, w.name AS warehouse_name,
               CAST(COALESCE(b.quantity, '0') AS REAL) AS operational_quantity,
               COALESCE(SUM(CASE
                   WHEN l.direction='in' THEN CAST(l.quantity AS REAL)
                   WHEN l.direction='out' THEN -CAST(l.quantity AS REAL)
                   ELSE 0 END), 0) AS ledger_quantity
        FROM item_warehouse_balances b
        JOIN items i ON i.id=b.item_id AND i.user_id=b.user_id
        JOIN warehouses w ON w.id=b.warehouse_id AND w.user_id=b.user_id
        LEFT JOIN inventory_ledger l ON l.user_id=b.user_id AND l.item_id=b.item_id AND l.warehouse_id=b.warehouse_id
        WHERE b.user_id=?
    """]
    params = [user_id]
    if item_id not in (None, ''):
        wh_sql.append('AND b.item_id=?')
        params.append(item_id)
    if warehouse_id not in (None, ''):
        wh_sql.append('AND b.warehouse_id=?')
        params.append(warehouse_id)
    wh_sql.append('GROUP BY b.item_id, i.name, b.warehouse_id, w.name, b.quantity ORDER BY i.name, w.name')
    for row in db.execute(' '.join(wh_sql), tuple(params)).fetchall():
        checked += 1
        op = dec(row['operational_quantity'])
        led = dec(row['ledger_quantity'])
        diff = op - led
        ok = abs(diff) <= tolerance
        matched += 1 if ok else 0
        mismatched += 0 if ok else 1
        if include_matches or not ok:
            rows.append({
                'scope': 'warehouse',
                'item_id': row['item_id'],
                'item_name': row['item_name'],
                'warehouse_id': row['warehouse_id'],
                'warehouse_name': row['warehouse_name'],
                'operational_quantity': str(op),
                'ledger_quantity': str(led),
                'difference': str(diff),
                'matches': ok,
                'read_source': 'dual',
            })

    return jsonify({
        'mode': 'dual_read',
        'authoritative_source': 'operational_stock',
        'ledger_authoritative': False,
        'checked': checked,
        'matched': matched,
        'mismatched': mismatched,
        'rows': rows,
        'diagnostic_only': True,
        'note': 'Phase 31 reads operational stock and ledger balances side by side; it does not change stock.'
    })


@items_bp.route('/inventory-ledger/backfill', methods=['POST'])
@jwt_required()
def inventory_ledger_backfill():
    """Backfill shadow ledger from legacy movement tables.

    Phase 29 is migration-preparation only. It can create item-level rows from
    inventory_movements and warehouse-level rows from warehouse_movements. It
    never updates operational stock quantities. Warehouse transfers are covered
    through their warehouse_movements rows to avoid duplicate posting.
    """
    user_id = get_jwt_identity()
    db = get_db()
    data = request.get_json() or {}
    dry_run = bool(data.get('dry_run', True))
    item_id = data.get('item_id')
    warehouse_id = data.get('warehouse_id')
    clear_existing = bool(data.get('clear_existing', False))
    include_item_movements = bool(data.get('include_item_movements', True))
    include_warehouse_movements = bool(data.get('include_warehouse_movements', True))

    def _exists(source_table, source_id):
        return db.execute(
            """SELECT id FROM inventory_ledger
               WHERE user_id=? AND source_table=? AND source_id=? LIMIT 1""",
            (user_id, source_table, source_id)
        ).fetchone()

    def _insert(payload):
        qty = str(payload['quantity'] or '0')
        unit_cost = payload.get('unit_cost')
        total_cost = None
        if unit_cost is not None:
            try:
                total_cost = str(Decimal(str(qty)) * Decimal(str(unit_cost)))
            except Exception:
                total_cost = None
        db.execute("""
            INSERT INTO inventory_ledger (
                user_id, item_id, warehouse_id, movement_type, direction, quantity,
                unit_cost, total_cost, reference_type, reference_id, source_table,
                source_id, notes, movement_date
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            user_id, payload['item_id'], payload.get('warehouse_id'), payload['movement_type'],
            payload['direction'], qty, str(unit_cost) if unit_cost is not None else None,
            total_cost, payload.get('reference_type'), payload.get('reference_id'),
            payload.get('source_table'), payload.get('source_id'), payload.get('notes'),
            payload.get('movement_date')
        ))

    results = []

    if include_item_movements:
        if clear_existing and not dry_run:
            sql = "DELETE FROM inventory_ledger WHERE user_id=? AND source_table='inventory_movements'"
            params = [user_id]
            if item_id not in (None, ''):
                sql += " AND item_id=?"
                params.append(item_id)
            db.execute(sql, tuple(params))
        sql = ["""
            SELECT id, item_id, movement_type, quantity, unit_cost, reference_id, movement_date
            FROM inventory_movements
            WHERE user_id=?
        """]
        params = [user_id]
        if item_id not in (None, ''):
            sql.append('AND item_id=?')
            params.append(item_id)
        sql.append('ORDER BY id')
        scanned = inserted = skipped = 0
        preview = []
        for row in db.execute(' '.join(sql), tuple(params)).fetchall():
            scanned += 1
            source_id = row['id']
            if _exists('inventory_movements', source_id):
                skipped += 1
                continue
            mt = row['movement_type']
            direction = 'in' if mt in ('opening', 'purchase', 'adjustment', 'production_out', 'sales_return', 'consumption_reverse') else 'out' if mt in ('sale', 'production_consume') else 'neutral'
            payload = {
                'item_id': row['item_id'],
                'movement_type': f'legacy_{mt}',
                'direction': direction,
                'quantity': str(row['quantity'] or '0'),
                'unit_cost': row['unit_cost'],
                'warehouse_id': None,
                'reference_type': mt,
                'reference_id': row['reference_id'],
                'source_table': 'inventory_movements',
                'source_id': source_id,
                'notes': 'Phase 29 legacy inventory movement backfill',
                'movement_date': row['movement_date'],
            }
            if dry_run:
                if len(preview) < 20:
                    preview.append(payload)
            else:
                _insert(payload)
            inserted += 1
        results.append({'dry_run': dry_run, 'source': 'inventory_movements', 'scanned': scanned, 'inserted': inserted, 'skipped': skipped, 'preview': preview, 'destructive': False})

    if include_warehouse_movements:
        if clear_existing and not dry_run:
            sql = "DELETE FROM inventory_ledger WHERE user_id=? AND source_table='warehouse_movements'"
            params = [user_id]
            if item_id not in (None, ''):
                sql += " AND item_id=?"
                params.append(item_id)
            if warehouse_id not in (None, ''):
                sql += " AND warehouse_id=?"
                params.append(warehouse_id)
            db.execute(sql, tuple(params))
        sql = ["""
            SELECT id, item_id, warehouse_id, movement_type, quantity, unit_cost,
                   reference_type, reference_id, notes, movement_date
            FROM warehouse_movements
            WHERE user_id=?
        """]
        params = [user_id]
        if item_id not in (None, ''):
            sql.append('AND item_id=?')
            params.append(item_id)
        if warehouse_id not in (None, ''):
            sql.append('AND warehouse_id=?')
            params.append(warehouse_id)
        sql.append('ORDER BY id')
        scanned = inserted = skipped = 0
        preview = []
        for row in db.execute(' '.join(sql), tuple(params)).fetchall():
            scanned += 1
            source_id = row['id']
            if _exists('warehouse_movements', source_id):
                skipped += 1
                continue
            qty = Decimal(str(row['quantity'] or '0'))
            if qty == 0:
                skipped += 1
                continue
            direction = 'in' if qty > 0 else 'out'
            mt = row['movement_type']
            payload = {
                'item_id': row['item_id'],
                'movement_type': f'legacy_warehouse_{mt}',
                'direction': direction,
                'quantity': str(abs(qty)),
                'unit_cost': row['unit_cost'],
                'warehouse_id': row['warehouse_id'],
                'reference_type': row['reference_type'] or mt,
                'reference_id': row['reference_id'],
                'source_table': 'warehouse_movements',
                'source_id': source_id,
                'notes': row['notes'] or 'Phase 29 legacy warehouse movement backfill',
                'movement_date': row['movement_date'],
            }
            if dry_run:
                if len(preview) < 20:
                    preview.append(payload)
            else:
                _insert(payload)
            inserted += 1
        results.append({'dry_run': dry_run, 'source': 'warehouse_movements', 'scanned': scanned, 'inserted': inserted, 'skipped': skipped, 'preview': preview, 'destructive': False})

    if not dry_run:
        db.commit()
        audit_log('POST', 'INVENTORY_LEDGER_BACKFILL', None,
                  new_values={'results': results, 'item_id': item_id, 'warehouse_id': warehouse_id},
                  details='تشغيل تعبئة دفتر المخزون من الحركات القديمة')
        db.commit()

    totals = {'scanned': 0, 'inserted': 0, 'skipped': 0}
    for r in results:
        for key in totals:
            totals[key] += int(r.get(key) or 0)
    return jsonify({
        'dry_run': dry_run,
        'sources': [r.get('source') for r in results],
        'results': results,
        **totals,
        'destructive': False,
        'note': 'Phase 29 backfills item-level and warehouse-level shadow ledger rows only. Transfers are covered through warehouse_movements; stock quantities are not changed.'
    })




@items_bp.route('/inventory-ledger/readiness', methods=['GET'])
@jwt_required()
def get_inventory_ledger_readiness():
    """Phase 33 read-only gate for controlled ledger-read adoption."""
    user_id = get_jwt_identity()
    item_id = request.args.get('item_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    tolerance = Decimal(str(request.args.get('tolerance', '0') or '0'))
    db = get_db()

    # Re-use the same conservative conditions as health + dual-read.
    filters = ['l.user_id=?']; params = [user_id]
    if item_id is not None:
        filters.append('l.item_id=?'); params.append(item_id)
    if warehouse_id is not None:
        filters.append('l.warehouse_id=?'); params.append(warehouse_id)
    where = ' AND '.join(filters)

    def count(sql, values=None):
        row = db.execute(sql, tuple(values or params)).fetchone()
        return int(row[0] or 0) if row else 0

    issues = {
        'invalid_direction': count(f"SELECT COUNT(*) FROM inventory_ledger l WHERE {where} AND COALESCE(l.direction,'') NOT IN ('in','out','neutral')"),
        'negative_quantity_rows': count(f"SELECT COUNT(*) FROM inventory_ledger l WHERE {where} AND CAST(COALESCE(l.quantity,'0') AS REAL) < 0"),
        'orphan_items': count(f"SELECT COUNT(*) FROM inventory_ledger l LEFT JOIN items i ON i.id=l.item_id AND i.user_id=l.user_id WHERE {where} AND i.id IS NULL"),
        'orphan_warehouses': count(f"SELECT COUNT(*) FROM inventory_ledger l LEFT JOIN warehouses w ON w.id=l.warehouse_id AND w.user_id=l.user_id WHERE {where} AND l.warehouse_id IS NOT NULL AND w.id IS NULL"),
        'duplicate_source_rows': count(f"SELECT COUNT(*) FROM (SELECT l.source_table,l.source_id,COUNT(*) cnt FROM inventory_ledger l WHERE {where} AND l.source_table IS NOT NULL AND l.source_id IS NOT NULL GROUP BY l.source_table,l.source_id HAVING cnt>1) x"),
        'negative_ledger_balances': count(f"SELECT COUNT(*) FROM (SELECT l.item_id,l.warehouse_id,SUM(CASE WHEN l.direction='in' THEN CAST(l.quantity AS REAL) WHEN l.direction='out' THEN -CAST(l.quantity AS REAL) ELSE 0 END) bal FROM inventory_ledger l WHERE {where} GROUP BY l.item_id,l.warehouse_id HAVING bal<0) x"),
    }
    issue_count = sum(issues.values())

    rec_sql = ["""
        SELECT COUNT(*) FROM (
            SELECT i.id,
                   CAST(COALESCE(i.quantity,'0') AS REAL) - COALESCE(SUM(CASE WHEN l.direction='in' THEN CAST(l.quantity AS REAL) WHEN l.direction='out' THEN -CAST(l.quantity AS REAL) ELSE 0 END),0) AS diff
            FROM items i
            LEFT JOIN inventory_ledger l ON l.user_id=i.user_id AND l.item_id=i.id
            WHERE i.user_id=? AND i.deleted_at IS NULL
    """]
    rec_params = [user_id]
    if item_id is not None:
        rec_sql.append('AND i.id=?'); rec_params.append(item_id)
    rec_sql.append('GROUP BY i.id, i.quantity HAVING ABS(diff) > ? ) x')
    rec_params.append(str(tolerance))
    mismatch_count = int(db.execute(' '.join(rec_sql), tuple(rec_params)).fetchone()[0] or 0)

    checked_sql = ["""
        SELECT COUNT(*) FROM (
            SELECT i.id
            FROM items i
            LEFT JOIN inventory_ledger l ON l.user_id=i.user_id AND l.item_id=i.id
            WHERE i.user_id=? AND i.deleted_at IS NULL
    """]
    checked_params = [user_id]
    if item_id is not None:
        checked_sql.append('AND i.id=?'); checked_params.append(item_id)
    checked_sql.append('GROUP BY i.id ) x')
    checked = int(db.execute(' '.join(checked_sql), tuple(checked_params)).fetchone()[0] or 0)

    snapshot_rows = count("SELECT COUNT(*) FROM (SELECT l.item_id,l.warehouse_id FROM inventory_ledger l WHERE " + where + " GROUP BY l.item_id,l.warehouse_id) x")

    blockers = []
    warnings = []
    if issue_count:
        blockers.append('ledger_integrity_issues')
    if mismatch_count:
        blockers.append('operational_vs_ledger_mismatches')
    if checked == 0:
        warnings.append('no_stock_rows_checked')
    if snapshot_rows == 0:
        warnings.append('empty_ledger_snapshot')

    safe = issue_count == 0 and mismatch_count == 0 and checked > 0
    return jsonify({
        'mode': 'readiness_gate',
        'phase': 33,
        'authoritative_source': 'operational_stock',
        'ledger_authoritative': False,
        'safe_for_dual_read': issue_count == 0,
        'safe_for_authoritative_read': safe,
        'recommendation': 'eligible_for_controlled_ledger_read_trial' if safe else 'keep_operational_stock',
        'blockers': blockers,
        'warnings': warnings,
        'summary': {
            'integrity_issue_count': issue_count,
            'reconciliation_mismatch_count': mismatch_count,
            'dual_read_checked': checked,
            'dual_read_mismatched': mismatch_count,
            'snapshot_rows': snapshot_rows,
        },
        'integrity': {'ok': issue_count == 0, 'issue_count': issue_count, 'issues': issues},
        'diagnostic_only': True,
        'note': 'Phase 33 readiness gate is read-only. It does not switch inventory reads to ledger.'
    })


@items_bp.route('/inventory-ledger/controlled-read', methods=['GET'])
@jwt_required()
def get_inventory_ledger_controlled_read():
    """Phase 34 controlled inventory read switch.

    Default/fallback remains operational stock.  Ledger quantities are selected
    only when requested mode is ledger_trial / ledger_authoritative and the
    readiness criteria are clean for the requested scope.
    """
    user_id = get_jwt_identity()
    item_id = request.args.get('item_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    requested_mode = (request.args.get('mode') or 'operational').strip().lower()
    if requested_mode not in {'operational', 'dual', 'ledger_trial', 'ledger_authoritative'}:
        requested_mode = 'operational'
    tolerance = Decimal(str(request.args.get('tolerance', '0') or '0'))
    db = get_db()

    # Conservative readiness gate: integrity issues or mismatches block ledger reads.
    filters = ['l.user_id=?']; params = [user_id]
    if item_id is not None:
        filters.append('l.item_id=?'); params.append(item_id)
    if warehouse_id is not None:
        filters.append('l.warehouse_id=?'); params.append(warehouse_id)
    where = ' AND '.join(filters)
    def count(sql):
        row = db.execute(sql, tuple(params)).fetchone()
        return int(row[0] or 0) if row else 0
    issues = {
        'invalid_direction': count(f"SELECT COUNT(*) FROM inventory_ledger l WHERE {where} AND COALESCE(l.direction,'') NOT IN ('in','out','neutral')"),
        'negative_quantity_rows': count(f"SELECT COUNT(*) FROM inventory_ledger l WHERE {where} AND CAST(COALESCE(l.quantity,'0') AS REAL) < 0"),
        'orphan_items': count(f"SELECT COUNT(*) FROM inventory_ledger l LEFT JOIN items i ON i.id=l.item_id AND i.user_id=l.user_id WHERE {where} AND i.id IS NULL"),
        'orphan_warehouses': count(f"SELECT COUNT(*) FROM inventory_ledger l LEFT JOIN warehouses w ON w.id=l.warehouse_id AND w.user_id=l.user_id WHERE {where} AND l.warehouse_id IS NOT NULL AND w.id IS NULL"),
        'duplicate_source_rows': count(f"SELECT COUNT(*) FROM (SELECT l.source_table,l.source_id,COUNT(*) cnt FROM inventory_ledger l WHERE {where} AND l.source_table IS NOT NULL AND l.source_id IS NOT NULL GROUP BY l.source_table,l.source_id HAVING cnt>1) x"),
        'negative_ledger_balances': count(f"SELECT COUNT(*) FROM (SELECT l.item_id,l.warehouse_id,SUM(CASE WHEN l.direction='in' THEN CAST(l.quantity AS REAL) WHEN l.direction='out' THEN -CAST(l.quantity AS REAL) ELSE 0 END) bal FROM inventory_ledger l WHERE {where} GROUP BY l.item_id,l.warehouse_id HAVING bal<0) x"),
    }
    issue_count = sum(issues.values())

    rows = []
    checked = matched = mismatched = 0
    if warehouse_id is None:
        sql = ["""
            SELECT 'item' AS scope, i.id AS item_id, i.name AS item_name,
                   NULL AS warehouse_id, NULL AS warehouse_name,
                   CAST(COALESCE(i.quantity,'0') AS REAL) AS operational_quantity,
                   COALESCE(SUM(CASE WHEN l.direction='in' THEN CAST(l.quantity AS REAL)
                                     WHEN l.direction='out' THEN -CAST(l.quantity AS REAL)
                                     ELSE 0 END),0) AS ledger_quantity
            FROM items i
            LEFT JOIN inventory_ledger l ON l.user_id=i.user_id AND l.item_id=i.id
            WHERE i.user_id=? AND i.deleted_at IS NULL
        """]
        row_params = [user_id]
        if item_id is not None:
            sql.append('AND i.id=?'); row_params.append(item_id)
        sql.append('GROUP BY i.id, i.name, i.quantity ORDER BY i.name')
        for r in db.execute(' '.join(sql), tuple(row_params)).fetchall():
            op = Decimal(str(r['operational_quantity'] or 0)); led = Decimal(str(r['ledger_quantity'] or 0)); diff = op - led
            ok = abs(diff) <= tolerance
            checked += 1; matched += 1 if ok else 0; mismatched += 0 if ok else 1
            rows.append({'scope': r['scope'], 'item_id': r['item_id'], 'item_name': r['item_name'], 'warehouse_id': None, 'warehouse_name': None, 'operational_quantity': str(op), 'ledger_quantity': str(led), 'difference': str(diff), 'matches': ok})

    sql = ["""
        SELECT 'warehouse' AS scope, b.item_id, i.name AS item_name, b.warehouse_id, w.name AS warehouse_name,
               CAST(COALESCE(b.quantity,'0') AS REAL) AS operational_quantity,
               COALESCE(SUM(CASE WHEN l.direction='in' THEN CAST(l.quantity AS REAL)
                                 WHEN l.direction='out' THEN -CAST(l.quantity AS REAL)
                                 ELSE 0 END),0) AS ledger_quantity
        FROM item_warehouse_balances b
        JOIN items i ON i.id=b.item_id AND i.user_id=b.user_id
        JOIN warehouses w ON w.id=b.warehouse_id AND w.user_id=b.user_id
        LEFT JOIN inventory_ledger l ON l.user_id=b.user_id AND l.item_id=b.item_id AND l.warehouse_id=b.warehouse_id
        WHERE b.user_id=?
    """]
    row_params = [user_id]
    if item_id is not None:
        sql.append('AND b.item_id=?'); row_params.append(item_id)
    if warehouse_id is not None:
        sql.append('AND b.warehouse_id=?'); row_params.append(warehouse_id)
    sql.append('GROUP BY b.item_id, i.name, b.warehouse_id, w.name, b.quantity ORDER BY i.name, w.name')
    for r in db.execute(' '.join(sql), tuple(row_params)).fetchall():
        op = Decimal(str(r['operational_quantity'] or 0)); led = Decimal(str(r['ledger_quantity'] or 0)); diff = op - led
        ok = abs(diff) <= tolerance
        checked += 1; matched += 1 if ok else 0; mismatched += 0 if ok else 1
        rows.append({'scope': r['scope'], 'item_id': r['item_id'], 'item_name': r['item_name'], 'warehouse_id': r['warehouse_id'], 'warehouse_name': r['warehouse_name'], 'operational_quantity': str(op), 'ledger_quantity': str(led), 'difference': str(diff), 'matches': ok})

    safe = issue_count == 0 and mismatched == 0 and checked > 0
    selected_source = 'ledger' if requested_mode in {'ledger_trial','ledger_authoritative'} and safe else 'operational_stock'
    for row in rows:
        row['selected_source'] = selected_source
        row['selected_quantity'] = row['ledger_quantity'] if selected_source == 'ledger' else row['operational_quantity']
        row['requested_mode'] = requested_mode
    return jsonify({
        'mode': 'controlled_read',
        'phase': 34,
        'requested_mode': requested_mode,
        'selected_source': selected_source,
        'authoritative_source': selected_source,
        'ledger_authoritative': selected_source == 'ledger',
        'ledger_selected': selected_source == 'ledger',
        'safe_for_ledger_read': safe,
        'fallback_reason': None if selected_source == 'ledger' else ('requested_operational' if requested_mode == 'operational' else 'readiness_gate_blocked'),
        'summary': {'integrity_issue_count': issue_count, 'dual_read_checked': checked, 'dual_read_matched': matched, 'dual_read_mismatched': mismatched},
        'issues': issues,
        'rows': rows,
        'read_only': True,
        'note': 'Phase 34 can select ledger for reads only when readiness allows it; operational stock remains the default fallback.'
    })

@items_bp.route('/inventory-ledger/balance', methods=['GET'])
@jwt_required()
def get_inventory_ledger_balance():
    user_id = get_jwt_identity()
    item_id = request.args.get('item_id')
    warehouse_id = request.args.get('warehouse_id')
    if not item_id:
        return jsonify({'error': 'item_id is required'}), 400
    sql = ["""SELECT SUM(CASE
                WHEN direction='in' THEN CAST(quantity AS REAL)
                WHEN direction='out' THEN -CAST(quantity AS REAL)
                ELSE 0 END) AS qty
             FROM inventory_ledger WHERE user_id=? AND item_id=?"""]
    params = [user_id, item_id]
    if warehouse_id not in (None, ''):
        sql.append("AND warehouse_id=?")
        params.append(warehouse_id)
    row = db.execute(' '.join(sql), tuple(params)).fetchone()
    return jsonify({'balance': str(row[0] if row and row[0] is not None else 0)})


@items_bp.route('/inventory-ledger/snapshot', methods=['GET'])
@jwt_required()
def get_inventory_ledger_snapshot():
    user_id = get_jwt_identity()
    item_id = request.args.get('item_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    db = get_db()
    sql = ["""
        SELECT l.item_id, i.name AS item_name, l.warehouse_id, w.name AS warehouse_name,
               SUM(CASE WHEN l.direction='in' THEN CAST(l.quantity AS REAL)
                        WHEN l.direction='out' THEN -CAST(l.quantity AS REAL)
                        ELSE 0 END) AS ledger_quantity,
               COUNT(*) AS entry_count
        FROM inventory_ledger l
        LEFT JOIN items i ON i.id=l.item_id AND i.user_id=l.user_id
        LEFT JOIN warehouses w ON w.id=l.warehouse_id AND w.user_id=l.user_id
        WHERE l.user_id=?
    """]
    params = [user_id]
    if item_id is not None:
        sql.append('AND l.item_id=?'); params.append(item_id)
    if warehouse_id is not None:
        sql.append('AND l.warehouse_id=?'); params.append(warehouse_id)
    sql.append('GROUP BY l.item_id, i.name, l.warehouse_id, w.name ORDER BY i.name, w.name')
    rows = db.execute(' '.join(sql), tuple(params)).fetchall()
    return jsonify({
        'mode': 'snapshot',
        'authoritative_source': 'operational_stock',
        'ledger_authoritative': False,
        'rows': [dict(r) for r in rows],
        'diagnostic_only': True,
        'note': 'Phase 30 ledger snapshot is read-only and does not change operational stock.'
    })

@items_bp.route('/inventory-ledger/health', methods=['GET'])
@jwt_required()
def get_inventory_ledger_health():
    user_id = get_jwt_identity()
    item_id = request.args.get('item_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    tolerance = Decimal(str(request.args.get('tolerance', '0') or '0'))
    db = get_db()
    filters = ['l.user_id=?']; params = [user_id]
    if item_id is not None:
        filters.append('l.item_id=?'); params.append(item_id)
    if warehouse_id is not None:
        filters.append('l.warehouse_id=?'); params.append(warehouse_id)
    where = ' AND '.join(filters)
    def count(sql):
        row = db.execute(sql, tuple(params)).fetchone()
        return int(row[0] or 0) if row else 0
    issues = {
        'invalid_direction': count(f"SELECT COUNT(*) FROM inventory_ledger l WHERE {where} AND COALESCE(l.direction,'') NOT IN ('in','out','neutral')"),
        'negative_quantity_rows': count(f"SELECT COUNT(*) FROM inventory_ledger l WHERE {where} AND CAST(COALESCE(l.quantity,'0') AS REAL) < 0"),
        'orphan_items': count(f"SELECT COUNT(*) FROM inventory_ledger l LEFT JOIN items i ON i.id=l.item_id AND i.user_id=l.user_id WHERE {where} AND i.id IS NULL"),
        'orphan_warehouses': count(f"SELECT COUNT(*) FROM inventory_ledger l LEFT JOIN warehouses w ON w.id=l.warehouse_id AND w.user_id=l.user_id WHERE {where} AND l.warehouse_id IS NOT NULL AND w.id IS NULL"),
        'duplicate_source_rows': count(f"SELECT COUNT(*) FROM (SELECT l.source_table,l.source_id,COUNT(*) cnt FROM inventory_ledger l WHERE {where} AND l.source_table IS NOT NULL AND l.source_id IS NOT NULL GROUP BY l.source_table,l.source_id HAVING cnt>1) x"),
        'negative_ledger_balances': count(f"SELECT COUNT(*) FROM (SELECT l.item_id,l.warehouse_id,SUM(CASE WHEN l.direction='in' THEN CAST(l.quantity AS REAL) WHEN l.direction='out' THEN -CAST(l.quantity AS REAL) ELSE 0 END) bal FROM inventory_ledger l WHERE {where} GROUP BY l.item_id,l.warehouse_id HAVING bal<0) x"),
    }
    issue_count = sum(issues.values())
    # Lightweight reconciliation summary only; full details remain available through /reconciliation.
    rec_sql = ["""
        SELECT COUNT(*) FROM (
            SELECT i.id,
                   CAST(COALESCE(i.quantity,'0') AS REAL) - COALESCE(SUM(CASE WHEN l.direction='in' THEN CAST(l.quantity AS REAL) WHEN l.direction='out' THEN -CAST(l.quantity AS REAL) ELSE 0 END),0) AS diff
            FROM items i
            LEFT JOIN inventory_ledger l ON l.user_id=i.user_id AND l.item_id=i.id
            WHERE i.user_id=? AND i.deleted_at IS NULL
    """]
    rec_params = [user_id]
    if item_id is not None:
        rec_sql.append('AND i.id=?'); rec_params.append(item_id)
    rec_sql.append('GROUP BY i.id, i.quantity HAVING ABS(diff) > ? ) x')
    rec_params.append(str(tolerance))
    mismatch_count = int(db.execute(' '.join(rec_sql), tuple(rec_params)).fetchone()[0] or 0)
    ready = issue_count == 0 and mismatch_count == 0
    return jsonify({
        'mode': 'health',
        'ready_for_authoritative_ledger': ready,
        'ledger_authoritative': False,
        'authoritative_source': 'operational_stock',
        'integrity': {'ok': issue_count == 0, 'issue_count': issue_count, 'issues': issues, 'diagnostic_only': True},
        'reconciliation_summary': {'mismatch_count': mismatch_count},
        'diagnostic_only': True,
        'note': 'Phase 30 health report is a read-only gate before any future authoritative-ledger switch.'
    })
