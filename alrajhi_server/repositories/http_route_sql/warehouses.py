# -*- coding: utf-8 -*-
from __future__ import annotations
import datetime
from decimal import Decimal
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.repositories.warehouse_repository import get_warehouse_repository
from alrajhi_server.decorators import admin_required

warehouses_bp = Blueprint('warehouses', __name__)

def _uid():
    try: return int(get_jwt_identity())
    except Exception: return get_jwt_identity()

def _now(): return datetime.datetime.now().isoformat()
def _rowdict(row): return dict(row) if row else None

def _ensure_default_branch(db, uid):
    row = db.query("SELECT id FROM branches WHERE user_id=? AND is_default=1 AND deleted_at IS NULL LIMIT 1", (uid,)).fetchone()
    if row: return int(row['id'])
    row = db.query("SELECT id FROM branches WHERE user_id=? AND deleted_at IS NULL ORDER BY id LIMIT 1", (uid,)).fetchone()
    if row: return int(row['id'])
    now = _now()
    cur = db.query("""INSERT INTO branches (user_id, name, code, is_default, is_active, created_at, updated_at)
                    VALUES (?, 'الفرع الرئيسي', 'MAIN', 1, 1, ?, ?)""", (uid, now, now))
    db.commit(); return int(cur.lastrowid)

def _ensure_default_warehouse(db, uid, branch_id=None):
    branch_id = branch_id or _ensure_default_branch(db, uid)
    row = db.query("SELECT id FROM warehouses WHERE user_id=? AND is_default=1 AND deleted_at IS NULL LIMIT 1", (uid,)).fetchone()
    if row: return int(row['id'])
    row = db.query("SELECT id FROM warehouses WHERE user_id=? AND deleted_at IS NULL ORDER BY id LIMIT 1", (uid,)).fetchone()
    if row: return int(row['id'])
    now = _now()
    cur = db.query("""
        INSERT INTO warehouses (user_id, branch_id, name, code, notes, is_default, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?)
    """, (uid, branch_id, 'المستودع الرئيسي', 'MAIN-WH', 'تم إنشاؤه تلقائياً', now, now))
    db.commit(); return int(cur.lastrowid)

def _payload(data, uid):
    data = data or {}; db = get_warehouse_repository()
    return {
        'branch_id': data.get('branch_id') or _ensure_default_branch(db, uid),
        'name': (data.get('name') or '').strip() or 'مستودع',
        'code': (data.get('code') or '').strip(),
        'notes': data.get('notes') or '',
        'is_active': 1 if data.get('is_active', 1) else 0,
    }

@warehouses_bp.route('/warehouses', methods=['GET'])
@jwt_required()
def list_warehouses():
    uid = _uid(); db = get_warehouse_repository(); include = str(request.args.get('include_archived','')).lower() in ('1','true','yes')
    _ensure_default_warehouse(db, uid)
    sql = """
        SELECT w.*, br.name AS branch_name, COUNT(DISTINCT b.item_id) AS item_count,
               COALESCE(SUM(CAST(b.quantity AS REAL)), 0) AS total_qty
        FROM warehouses w
        LEFT JOIN branches br ON br.id=w.branch_id
        LEFT JOIN item_warehouse_balances b ON b.warehouse_id=w.id
        WHERE w.user_id=?
    """
    params=[uid]
    if not include: sql += " AND w.deleted_at IS NULL AND COALESCE(w.is_active,1)=1"
    sql += " GROUP BY w.id ORDER BY w.is_default DESC, w.name"
    return jsonify({'warehouses': [_rowdict(r) for r in db.query(sql, params).fetchall()]})

@warehouses_bp.route('/warehouses/default', methods=['GET'])
@jwt_required()
def default_warehouse():
    return jsonify({'id': _ensure_default_warehouse(get_warehouse_repository(), _uid())})

@warehouses_bp.route('/warehouses/available_qty', methods=['GET'])
@jwt_required()
def available_qty():
    uid = _uid(); db = get_warehouse_repository(); item_id = request.args.get('item_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int) or _ensure_default_warehouse(db, uid)
    if not item_id: return jsonify({'quantity': '0'})
    row = db.query('SELECT quantity FROM item_warehouse_balances WHERE user_id=? AND item_id=? AND warehouse_id=?', (uid, item_id, warehouse_id)).fetchone()
    return jsonify({'quantity': str(row['quantity']) if row and row['quantity'] is not None else '0'})

@warehouses_bp.route('/warehouses/<int:warehouse_id>', methods=['GET'])
@jwt_required()
def get_warehouse(warehouse_id):
    row = get_warehouse_repository().query('SELECT * FROM warehouses WHERE id=? AND user_id=?', (warehouse_id, _uid())).fetchone()
    if not row: return jsonify({'error': 'not found'}), 404
    return jsonify(_rowdict(row))

@warehouses_bp.route('/warehouses', methods=['POST'])
@admin_required
def add_warehouse():
    uid = _uid(); db = get_warehouse_repository(); p = _payload(request.get_json() or {}, uid); now = _now()
    cur = db.query("""
        INSERT INTO warehouses (user_id, branch_id, name, code, notes, is_default, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
    """, (uid, p['branch_id'], p['name'], p['code'], p['notes'], p['is_active'], now, now))
    db.commit(); return jsonify({'id': cur.lastrowid}), 201

@warehouses_bp.route('/warehouses/<int:warehouse_id>', methods=['PUT'])
@admin_required
def update_warehouse(warehouse_id):
    uid = _uid(); db = get_warehouse_repository(); p = _payload(request.get_json() or {}, uid)
    db.query('UPDATE warehouses SET branch_id=?, name=?, code=?, notes=?, is_active=?, updated_at=? WHERE id=? AND user_id=?',
               (p['branch_id'], p['name'], p['code'], p['notes'], p['is_active'], _now(), warehouse_id, uid))
    db.commit(); return jsonify({'status': 'ok'})

@warehouses_bp.route('/warehouses/<int:warehouse_id>', methods=['DELETE'])
@admin_required
def archive_warehouse(warehouse_id):
    uid = _uid(); db = get_warehouse_repository(); now = _now()
    row = db.query('SELECT is_default FROM warehouses WHERE id=? AND user_id=?', (warehouse_id, uid)).fetchone()
    if not row: return jsonify({'error': 'not found'}), 404
    if int(row['is_default'] or 0) == 1: return jsonify({'error': 'لا يمكن أرشفة المستودع الرئيسي'}), 400
    db.query('UPDATE warehouses SET deleted_at=?, is_active=0, updated_at=? WHERE id=? AND user_id=?', (now, now, warehouse_id, uid))
    db.commit(); return jsonify({'status': 'ok'})


# ------------------- Warehouse balances, movements, and transfers for Remote Mode -------------------

def _dec(value, default='0'):
    try:
        return Decimal(str(value if value is not None else default))
    except Exception:
        return Decimal(str(default))



def _post_inventory_ledger_entry(db, user_id, item_id, warehouse_id, movement_type, direction,
                                 quantity, unit_cost=None, reference_type=None, reference_id=None,
                                 source_table=None, source_id=None, notes=''):
    """Shadow-post one warehouse event into inventory_ledger.

    Phase 25 keeps this append-only and non-authoritative: existing warehouse
    movements/balances remain the operational source for current stock.
    """
    if not item_id or not quantity:
        return None
    qty = abs(_dec(quantity))
    if qty == 0:
        return None
    if direction not in ('in', 'out', 'neutral'):
        direction = 'in' if _dec(quantity) > 0 else 'out' if _dec(quantity) < 0 else 'neutral'
    cost = _dec(unit_cost or '0') if unit_cost is not None else None
    total_cost = str(qty * cost) if cost is not None else None
    cur = db.query("""
        INSERT INTO inventory_ledger (
            user_id, item_id, warehouse_id, movement_type, direction, quantity,
            unit_cost, total_cost, reference_type, reference_id, source_table,
            source_id, notes, movement_date
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        user_id, item_id, warehouse_id, movement_type, direction, str(qty),
        str(cost) if cost is not None else None, total_cost, reference_type,
        reference_id, source_table, source_id, notes, _now()
    ))
    return int(cur.lastrowid)

def _ledger_direction_from_qty(quantity):
    q = _dec(quantity)
    return 'in' if q > 0 else 'out' if q < 0 else 'neutral'

def _ensure_transfer_schema(db):
    db.query("""
        CREATE TABLE IF NOT EXISTS warehouse_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            transfer_no TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            from_warehouse_id INTEGER NOT NULL,
            to_warehouse_id INTEGER NOT NULL,
            quantity TEXT NOT NULL,
            unit_cost TEXT DEFAULT '0',
            notes TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            cancelled_at TEXT,
            UNIQUE(user_id, transfer_no)
        )
    """)

def _warehouse_active(db, uid, warehouse_id):
    row = db.query("""
        SELECT id FROM warehouses
        WHERE id=? AND user_id=? AND deleted_at IS NULL AND COALESCE(is_active,1)=1
    """, (warehouse_id, uid)).fetchone()
    return bool(row)

def _item_cost(db, uid, item_id):
    row = db.query("SELECT COALESCE(average_cost, '0') AS average_cost FROM items WHERE id=? AND user_id=?", (item_id, uid)).fetchone()
    return _dec(row['average_cost']) if row else Decimal('0')

def _ensure_balance_row(db, uid, item_id, warehouse_id, unit_cost='0'):
    if db.query("""
        SELECT id FROM item_warehouse_balances WHERE user_id=? AND item_id=? AND warehouse_id=?
    """, (uid, item_id, warehouse_id)).fetchone():
        return
    now = _now()
    db.query("""
        INSERT INTO item_warehouse_balances
        (user_id, item_id, warehouse_id, quantity, average_cost, updated_at)
        VALUES (?, ?, ?, '0', ?, ?)
    """, (uid, item_id, warehouse_id, str(unit_cost or '0'), now))

def _available_qty(db, uid, item_id, warehouse_id):
    row = db.query("""
        SELECT quantity FROM item_warehouse_balances
        WHERE user_id=? AND item_id=? AND warehouse_id=?
    """, (uid, item_id, warehouse_id)).fetchone()
    return _dec(row['quantity']) if row and row['quantity'] is not None else Decimal('0')

def _record_warehouse_movement(db, uid, item_id, warehouse_id, movement_type, quantity,
                               unit_cost='0', reference_type=None, reference_id=None, notes=''):
    item_id = int(item_id or 0)
    warehouse_id = int(warehouse_id or 0)
    qty = _dec(quantity)
    cost = _dec(unit_cost)
    if item_id <= 0:
        raise ValueError('المادة غير صحيحة')
    if warehouse_id <= 0:
        warehouse_id = _ensure_default_warehouse(db, uid)
    if qty == 0:
        return 0
    if not _warehouse_active(db, uid, warehouse_id):
        raise ValueError('المستودع غير نشط أو غير موجود')
    _ensure_balance_row(db, uid, item_id, warehouse_id, cost)
    current = _available_qty(db, uid, item_id, warehouse_id)
    new_qty = current + qty
    if new_qty < 0:
        raise ValueError('الرصيد غير كافٍ في المستودع المحدد')
    now = _now()
    avg_cost = str(cost if cost > 0 else _item_cost(db, uid, item_id))
    db.query("""
        UPDATE item_warehouse_balances SET quantity=?, average_cost=?, updated_at=?
        WHERE user_id=? AND item_id=? AND warehouse_id=?
    """, (str(new_qty), avg_cost, now, uid, item_id, warehouse_id))
    cur = db.query("""
        INSERT INTO warehouse_movements
        (user_id, item_id, warehouse_id, movement_type, quantity, unit_cost, reference_type, reference_id, notes, movement_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (uid, item_id, warehouse_id, movement_type, str(qty), str(cost), reference_type, reference_id, notes or '', now, now))
    return int(cur.lastrowid)

@warehouses_bp.route('/warehouses/balances', methods=['GET'])
@jwt_required()
def warehouse_balances():
    uid = _uid(); db = get_warehouse_repository()
    _ensure_default_warehouse(db, uid)
    search = request.args.get('search') or None
    warehouse_id = request.args.get('warehouse_id', type=int)
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)
    sql = """
        SELECT b.id, b.item_id, i.name AS item_name, i.barcode, i.unit,
               b.warehouse_id, w.name AS warehouse_name, b.quantity, b.average_cost,
               (CAST(COALESCE(b.quantity, '0') AS REAL) * CAST(COALESCE(b.average_cost, '0') AS REAL)) AS stock_value,
               b.updated_at
        FROM item_warehouse_balances b
        JOIN items i ON i.id = b.item_id AND i.user_id=b.user_id
        JOIN warehouses w ON w.id = b.warehouse_id AND w.user_id=b.user_id
        WHERE b.user_id=? AND i.deleted_at IS NULL AND w.deleted_at IS NULL
    """
    params = [uid]
    if search:
        sql += " AND (i.name LIKE ? OR i.barcode LIKE ? OR w.name LIKE ?)"
        like = f'%{search}%'
        params.extend([like, like, like])
    if warehouse_id:
        sql += " AND b.warehouse_id=?"
        params.append(warehouse_id)
    sql += " ORDER BY w.is_default DESC, w.name, i.name"
    if limit is not None:
        sql += " LIMIT ?"; params.append(limit)
    if offset is not None:
        sql += " OFFSET ?"; params.append(offset)
    return jsonify({'balances': [_rowdict(r) for r in db.query(sql, params).fetchall()]})

@warehouses_bp.route('/warehouses/balances/count', methods=['GET'])
@jwt_required()
def warehouse_balances_count():
    uid = _uid(); db = get_warehouse_repository()
    rows = warehouse_balances().json.get('balances', [])
    return jsonify({'count': len(rows)})

@warehouses_bp.route('/warehouses/movements', methods=['GET'])
@jwt_required()
def list_warehouse_movements():
    uid = _uid(); db = get_warehouse_repository()
    item_id = request.args.get('item_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    limit = request.args.get('limit', default=100, type=int) or 100
    sql = """
        SELECT m.*, i.name AS item_name, w.name AS warehouse_name
        FROM warehouse_movements m
        JOIN items i ON i.id=m.item_id AND i.user_id=m.user_id
        JOIN warehouses w ON w.id=m.warehouse_id AND w.user_id=m.user_id
        WHERE m.user_id=?
    """
    params = [uid]
    if item_id:
        sql += " AND m.item_id=?"; params.append(item_id)
    if warehouse_id:
        sql += " AND m.warehouse_id=?"; params.append(warehouse_id)
    sql += " ORDER BY m.id DESC LIMIT ?"; params.append(limit)
    return jsonify({'movements': [_rowdict(r) for r in db.query(sql, params).fetchall()]})

@warehouses_bp.route('/warehouses/movements', methods=['POST'])
@jwt_required()
def add_warehouse_movement():
    uid = _uid(); db = get_warehouse_repository(); data = request.get_json() or {}
    try:
        item_id = data.get('item_id')
        warehouse_id = data.get('warehouse_id') or _ensure_default_warehouse(db, uid)
        movement_type = data.get('movement_type') or 'adjustment'
        quantity = data.get('quantity') or '0'
        unit_cost = data.get('unit_cost') or '0'
        reference_type = data.get('reference_type')
        reference_id = data.get('reference_id')
        notes = data.get('notes') or ''
        mid = _record_warehouse_movement(
            db, uid, item_id, warehouse_id, movement_type, quantity, unit_cost,
            reference_type, reference_id, notes
        )
        # Phase 25: shadow-post direct warehouse movements, except invoice and
        # return references which already have dedicated ledger hooks.
        if reference_type not in ('invoice', 'sales_return', 'purchase_return'):
            _post_inventory_ledger_entry(
                db, uid, item_id, warehouse_id, movement_type,
                _ledger_direction_from_qty(quantity), quantity, unit_cost,
                reference_type or 'warehouse_movement', reference_id or mid,
                'warehouse_movements', mid, notes
            )
        db.commit()
        return jsonify({'id': mid}), 201
    except Exception as exc:
        db.rollback()
        return jsonify({'error': str(exc)}), 400

@warehouses_bp.route('/warehouses/reverse_reference', methods=['POST'])
@jwt_required()
def reverse_warehouse_reference():
    uid = _uid(); db = get_warehouse_repository(); data = request.get_json() or {}
    reference_type = data.get('reference_type')
    reference_id = data.get('reference_id')
    rows = db.query("""
        SELECT * FROM warehouse_movements
        WHERE user_id=? AND reference_type=? AND reference_id=?
        ORDER BY id DESC
    """, (uid, reference_type, reference_id)).fetchall()
    try:
        for r in rows:
            _record_warehouse_movement(
                db, uid, r['item_id'], r['warehouse_id'], 'reverse_' + str(r['movement_type']),
                -_dec(r['quantity']), r['unit_cost'] or '0',
                'reverse_' + str(reference_type), reference_id, 'عكس حركة مستودعية'
            )
        db.commit()
        return jsonify({'status': 'ok', 'reversed': len(rows)})
    except Exception as exc:
        db.rollback()
        return jsonify({'error': str(exc)}), 400

def _next_transfer_no(db, uid):
    _ensure_transfer_schema(db)
    today = datetime.datetime.now().strftime('%Y%m%d')
    row = db.query("SELECT COUNT(*) AS c FROM warehouse_transfers WHERE user_id=? AND transfer_no LIKE ?", (uid, f'TR-{today}-%')).fetchone()
    return f"TR-{today}-{int(row['c'] or 0) + 1:04d}"

@warehouses_bp.route('/warehouses/transfers', methods=['POST'])
@jwt_required()
def create_warehouse_transfer():
    uid = _uid(); db = get_warehouse_repository(); _ensure_transfer_schema(db)
    data = request.get_json() or {}
    try:
        item_id = int(data.get('item_id') or 0)
        from_wh = int(data.get('from_warehouse_id') or 0)
        to_wh = int(data.get('to_warehouse_id') or 0)
        qty = _dec(data.get('quantity') or '0')
        notes = str(data.get('notes') or '').strip()
        if item_id <= 0:
            raise ValueError('اختر المادة')
        if from_wh <= 0 or to_wh <= 0:
            raise ValueError('اختر مستودع المصدر والوجهة')
        if from_wh == to_wh:
            raise ValueError('لا يمكن التحويل إلى نفس المستودع')
        if qty <= 0:
            raise ValueError('كمية التحويل يجب أن تكون أكبر من صفر')
        if not _warehouse_active(db, uid, from_wh) or not _warehouse_active(db, uid, to_wh):
            raise ValueError('لا يمكن التحويل من أو إلى مستودع مؤرشف')
        if _available_qty(db, uid, item_id, from_wh) < qty:
            raise ValueError('الرصيد غير كافٍ في المستودع المصدر')
        unit_cost = _item_cost(db, uid, item_id)
        now = _now()
        transfer_no = _next_transfer_no(db, uid)
        cur = db.query("""
            INSERT INTO warehouse_transfers
            (user_id, transfer_no, item_id, from_warehouse_id, to_warehouse_id, quantity, unit_cost, notes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
        """, (uid, transfer_no, item_id, from_wh, to_wh, str(qty), str(unit_cost), notes, now))
        tid = int(cur.lastrowid)
        _record_warehouse_movement(db, uid, item_id, from_wh, 'transfer_out', -qty, unit_cost, 'warehouse_transfer', tid, f'تحويل إلى مستودع #{to_wh}: {notes}')
        _record_warehouse_movement(db, uid, item_id, to_wh, 'transfer_in', qty, unit_cost, 'warehouse_transfer', tid, f'تحويل من مستودع #{from_wh}: {notes}')
        _post_inventory_ledger_entry(db, uid, item_id, from_wh, 'transfer_out', 'out', qty, unit_cost, 'warehouse_transfer', tid, 'warehouse_transfers', tid, f'دفتر مخزون تحويل إلى مستودع #{to_wh}')
        _post_inventory_ledger_entry(db, uid, item_id, to_wh, 'transfer_in', 'in', qty, unit_cost, 'warehouse_transfer', tid, 'warehouse_transfers', tid, f'دفتر مخزون تحويل من مستودع #{from_wh}')
        db.commit()
        return jsonify({'id': tid}), 201
    except Exception as exc:
        db.rollback()
        return jsonify({'error': str(exc)}), 400

@warehouses_bp.route('/warehouses/transfers/<int:transfer_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_warehouse_transfer(transfer_id):
    uid = _uid(); db = get_warehouse_repository(); _ensure_transfer_schema(db)
    t = db.query("SELECT * FROM warehouse_transfers WHERE id=? AND user_id=?", (transfer_id, uid)).fetchone()
    if not t:
        return jsonify({'error': 'التحويل غير موجود'}), 404
    if t['status'] != 'active':
        return jsonify({'error': 'التحويل ملغى مسبقاً'}), 400
    qty = _dec(t['quantity'])
    if _available_qty(db, uid, t['item_id'], t['to_warehouse_id']) < qty:
        return jsonify({'error': 'لا يمكن إلغاء التحويل لأن رصيد المستودع المستلم غير كافٍ'}), 400
    try:
        unit_cost = _dec(t['unit_cost'])
        _record_warehouse_movement(db, uid, t['item_id'], t['to_warehouse_id'], 'transfer_cancel_out', -qty, unit_cost, 'warehouse_transfer_cancel', transfer_id, 'إلغاء تحويل مستودعي')
        _record_warehouse_movement(db, uid, t['item_id'], t['from_warehouse_id'], 'transfer_cancel_in', qty, unit_cost, 'warehouse_transfer_cancel', transfer_id, 'إلغاء تحويل مستودعي')
        _post_inventory_ledger_entry(db, uid, t['item_id'], t['to_warehouse_id'], 'transfer_cancel_out', 'out', qty, unit_cost, 'warehouse_transfer_cancel', transfer_id, 'warehouse_transfers', transfer_id, 'دفتر مخزون إلغاء تحويل مستودعي')
        _post_inventory_ledger_entry(db, uid, t['item_id'], t['from_warehouse_id'], 'transfer_cancel_in', 'in', qty, unit_cost, 'warehouse_transfer_cancel', transfer_id, 'warehouse_transfers', transfer_id, 'دفتر مخزون إلغاء تحويل مستودعي')
        db.query("UPDATE warehouse_transfers SET status='cancelled', cancelled_at=? WHERE id=? AND user_id=?", (_now(), transfer_id, uid))
        db.commit()
        return jsonify({'status': 'ok'})
    except Exception as exc:
        db.rollback()
        return jsonify({'error': str(exc)}), 400

@warehouses_bp.route('/warehouses/transfers', methods=['GET'])
@jwt_required()
def list_warehouse_transfers():
    uid = _uid(); db = get_warehouse_repository(); _ensure_transfer_schema(db)
    limit = request.args.get('limit', default=200, type=int) or 200
    rows = db.query("""
        SELECT t.*, i.name AS item_name, fw.name AS from_warehouse_name, tw.name AS to_warehouse_name
        FROM warehouse_transfers t
        JOIN items i ON i.id=t.item_id AND i.user_id=t.user_id
        JOIN warehouses fw ON fw.id=t.from_warehouse_id AND fw.user_id=t.user_id
        JOIN warehouses tw ON tw.id=t.to_warehouse_id AND tw.user_id=t.user_id
        WHERE t.user_id=?
        ORDER BY t.id DESC LIMIT ?
    """, (uid, limit)).fetchall()
    return jsonify({'transfers': [_rowdict(r) for r in rows]})

