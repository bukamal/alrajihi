# -*- coding: utf-8 -*-
from __future__ import annotations
import datetime
from decimal import Decimal
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.repositories.warehouse_repository import get_warehouse_repository
from alrajhi_server.decorators import admin_required
from alrajhi_server.services.branch_access_policy import BranchAccessError, branch_access_policy

warehouses_bp = Blueprint('warehouses', __name__)

def _uid():
    try: return int(get_jwt_identity())
    except Exception: return get_jwt_identity()

def _now(): return datetime.datetime.now().isoformat()
def _rowdict(row): return dict(row) if row else None


def _branch_denied(exc):
    return jsonify({'error': str(exc), 'code': 'BRANCH_ACCESS_DENIED'}), 403

def _require_branch(uid, branch_id, context):
    return branch_access_policy.require(uid, branch_id, context=context)

def _require_warehouse_access(db, uid, warehouse_id, context):
    row = db.query('SELECT branch_id FROM warehouses WHERE id=? AND user_id=?', (warehouse_id, uid)).fetchone()
    if not row:
        raise ValueError('المستودع غير موجود')
    _require_branch(uid, row['branch_id'] if 'branch_id' in row.keys() else None, context)
    return row

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

def _ensure_variant_warehouse_schema(db):
    db.query("""
        CREATE TABLE IF NOT EXISTS item_warehouse_variant_balances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            variant_id INTEGER NOT NULL,
            warehouse_id INTEGER NOT NULL,
            variant_color TEXT,
            variant_size TEXT,
            variant_sku TEXT,
            quantity TEXT DEFAULT '0',
            average_cost TEXT DEFAULT '0',
            updated_at TEXT,
            UNIQUE(user_id, item_id, variant_id, warehouse_id)
        )
    """)
    for table in ('warehouse_movements', 'warehouse_transfers'):
        for col_name, col_type in (
            ('variant_id', 'INTEGER'), ('variant_color', 'TEXT'), ('variant_size', 'TEXT'), ('variant_sku', 'TEXT'),
            ('barcode_scope', 'TEXT'), ('matched_barcode', 'TEXT'),
        ):
            try:
                db.query(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
            except Exception:
                pass
    db.query("CREATE INDEX IF NOT EXISTS idx_wh_variant_balances_variant ON item_warehouse_variant_balances(variant_id)")
    db.query("CREATE INDEX IF NOT EXISTS idx_wh_variant_balances_wh ON item_warehouse_variant_balances(warehouse_id)")
    db.query("CREATE INDEX IF NOT EXISTS idx_wh_mov_variant ON warehouse_movements(variant_id)")


def _variant_payload(data=None):
    data = data or {}
    variant_id = data.get('variant_id')
    try:
        variant_id = int(variant_id) if variant_id not in (None, '', 0, '0') else None
    except Exception:
        variant_id = None
    return {
        'variant_id': variant_id,
        'variant_color': str(data.get('variant_color') or ''),
        'variant_size': str(data.get('variant_size') or ''),
        'variant_sku': str(data.get('variant_sku') or ''),
        'barcode_scope': str(data.get('barcode_scope') or ('variant' if variant_id else '')),
        'matched_barcode': str(data.get('matched_barcode') or data.get('barcode') or ''),
    }

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
    branch_sql, branch_params = branch_access_policy.scope_sql(uid, alias='w', branch_column='branch_id', requested_branch_id=request.args.get('branch_id', type=int))
    sql += branch_sql; params.extend(branch_params)
    if not include: sql += " AND w.deleted_at IS NULL AND COALESCE(w.is_active,1)=1"
    sql += " GROUP BY w.id ORDER BY w.is_default DESC, w.name"
    return jsonify({'warehouses': [_rowdict(r) for r in db.query(sql, params).fetchall()]})

@warehouses_bp.route('/warehouses/default', methods=['GET'])
@jwt_required()
def default_warehouse():
    uid = _uid(); requested = request.args.get('branch_id', type=int)
    try:
        branch_id = branch_access_policy.effective_branch_id(uid, requested)
        _require_branch(uid, branch_id, 'warehouse.default')
    except BranchAccessError as exc:
        return _branch_denied(exc)
    return jsonify({'id': _ensure_default_warehouse(get_warehouse_repository(), uid, branch_id)})

@warehouses_bp.route('/warehouses/available_qty', methods=['GET'])
@jwt_required()
def available_qty():
    uid = _uid(); db = get_warehouse_repository(); item_id = request.args.get('item_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int) or _ensure_default_warehouse(db, uid)
    variant_id = request.args.get('variant_id', type=int)
    try:
        _require_warehouse_access(db, uid, warehouse_id, 'warehouse.available_qty')
    except BranchAccessError as exc:
        return _branch_denied(exc)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 404
    if not item_id: return jsonify({'quantity': '0'})
    _ensure_variant_warehouse_schema(db)
    if variant_id:
        qty = _available_qty(db, uid, item_id, warehouse_id, variant_id=variant_id)
        return jsonify({'quantity': str(qty)})
    row = db.query('SELECT quantity FROM item_warehouse_balances WHERE user_id=? AND item_id=? AND warehouse_id=?', (uid, item_id, warehouse_id)).fetchone()
    return jsonify({'quantity': str(row['quantity']) if row and row['quantity'] is not None else '0'})

@warehouses_bp.route('/warehouses/<int:warehouse_id>', methods=['GET'])
@jwt_required()
def get_warehouse(warehouse_id):
    row = get_warehouse_repository().query('SELECT * FROM warehouses WHERE id=? AND user_id=?', (warehouse_id, _uid())).fetchone()
    if not row: return jsonify({'error': 'not found'}), 404
    try:
        _require_branch(_uid(), row['branch_id'] if 'branch_id' in row.keys() else None, 'warehouse.get')
    except BranchAccessError as exc:
        return _branch_denied(exc)
    return jsonify(_rowdict(row))

@warehouses_bp.route('/warehouses', methods=['POST'])
@admin_required
def add_warehouse():
    uid = _uid(); db = get_warehouse_repository(); p = _payload(request.get_json() or {}, uid); now = _now()
    try:
        _require_branch(uid, p['branch_id'], 'warehouse.create')
    except BranchAccessError as exc:
        return _branch_denied(exc)
    cur = db.query("""
        INSERT INTO warehouses (user_id, branch_id, name, code, notes, is_default, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
    """, (uid, p['branch_id'], p['name'], p['code'], p['notes'], p['is_active'], now, now))
    db.commit(); return jsonify({'id': cur.lastrowid}), 201

@warehouses_bp.route('/warehouses/<int:warehouse_id>', methods=['PUT'])
@admin_required
def update_warehouse(warehouse_id):
    uid = _uid(); db = get_warehouse_repository(); p = _payload(request.get_json() or {}, uid)
    try:
        _require_warehouse_access(db, uid, warehouse_id, 'warehouse.update.old')
        _require_branch(uid, p['branch_id'], 'warehouse.update.new')
    except BranchAccessError as exc:
        return _branch_denied(exc)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 404
    db.query('UPDATE warehouses SET branch_id=?, name=?, code=?, notes=?, is_active=?, updated_at=? WHERE id=? AND user_id=?',
               (p['branch_id'], p['name'], p['code'], p['notes'], p['is_active'], _now(), warehouse_id, uid))
    db.commit(); return jsonify({'status': 'ok'})

@warehouses_bp.route('/warehouses/<int:warehouse_id>', methods=['DELETE'])
@admin_required
def archive_warehouse(warehouse_id):
    uid = _uid(); db = get_warehouse_repository(); now = _now()
    row = db.query('SELECT is_default FROM warehouses WHERE id=? AND user_id=?', (warehouse_id, uid)).fetchone()
    if not row: return jsonify({'error': 'not found'}), 404
    try:
        _require_warehouse_access(db, uid, warehouse_id, 'warehouse.delete')
    except BranchAccessError as exc:
        return _branch_denied(exc)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 404
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
            base_qty TEXT,
            unit_id INTEGER,
            unit_name TEXT,
            conversion_factor TEXT DEFAULT '1',
            barcode_scope TEXT,
            matched_barcode TEXT,
            unit_cost TEXT DEFAULT '0',
            notes TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            cancelled_at TEXT,
            UNIQUE(user_id, transfer_no)
        )
    """)
    for col_name, col_type in (
        ('base_qty', 'TEXT'), ('unit_id', 'INTEGER'), ('unit_name', 'TEXT'),
        ('conversion_factor', "TEXT DEFAULT '1'"), ('barcode_scope', 'TEXT'), ('matched_barcode', 'TEXT'),
    ):
        try:
            db.query(f"ALTER TABLE warehouse_transfers ADD COLUMN {col_name} {col_type}")
        except Exception:
            pass

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

def _available_qty(db, uid, item_id, warehouse_id, variant_id=None):
    _ensure_variant_warehouse_schema(db)
    if variant_id:
        row = db.query("""
            SELECT quantity FROM item_warehouse_variant_balances
            WHERE user_id=? AND item_id=? AND variant_id=? AND warehouse_id=?
        """, (uid, item_id, variant_id, warehouse_id)).fetchone()
        return _dec(row['quantity']) if row and row['quantity'] is not None else Decimal('0')
    row = db.query("""
        SELECT quantity FROM item_warehouse_balances
        WHERE user_id=? AND item_id=? AND warehouse_id=?
    """, (uid, item_id, warehouse_id)).fetchone()
    return _dec(row['quantity']) if row and row['quantity'] is not None else Decimal('0')


def _ensure_variant_balance_row(db, uid, item_id, variant_id, warehouse_id, unit_cost='0', variant_payload=None):
    _ensure_variant_warehouse_schema(db)
    vp = _variant_payload(variant_payload)
    if db.query("""
        SELECT id FROM item_warehouse_variant_balances
        WHERE user_id=? AND item_id=? AND variant_id=? AND warehouse_id=?
    """, (uid, item_id, variant_id, warehouse_id)).fetchone():
        return
    now = _now()
    db.query("""
        INSERT INTO item_warehouse_variant_balances
        (user_id, item_id, variant_id, warehouse_id, variant_color, variant_size, variant_sku, quantity, average_cost, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, '0', ?, ?)
    """, (uid, item_id, variant_id, warehouse_id, vp['variant_color'], vp['variant_size'], vp['variant_sku'], str(unit_cost or '0'), now))

def _record_warehouse_movement(db, uid, item_id, warehouse_id, movement_type, quantity,
                               unit_cost='0', reference_type=None, reference_id=None, notes='', **variant_data):
    _ensure_variant_warehouse_schema(db)
    item_id = int(item_id or 0)
    warehouse_id = int(warehouse_id or 0)
    qty = _dec(quantity)
    cost = _dec(unit_cost)
    vp = _variant_payload(variant_data)
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
    if vp['variant_id']:
        _ensure_variant_balance_row(db, uid, item_id, vp['variant_id'], warehouse_id, cost, vp)
        current_variant = _available_qty(db, uid, item_id, warehouse_id, variant_id=vp['variant_id'])
        new_variant_qty = current_variant + qty
        if new_variant_qty < 0:
            raise ValueError('الرصيد غير كافٍ لهذا اللون/المقاس في المستودع المحدد')
        db.query("""
            UPDATE item_warehouse_variant_balances
            SET quantity=?, average_cost=?, variant_color=?, variant_size=?, variant_sku=?, updated_at=?
            WHERE user_id=? AND item_id=? AND variant_id=? AND warehouse_id=?
        """, (str(new_variant_qty), avg_cost, vp['variant_color'], vp['variant_size'], vp['variant_sku'], now, uid, item_id, vp['variant_id'], warehouse_id))
    cur = db.query("""
        INSERT INTO warehouse_movements
        (user_id, item_id, warehouse_id, movement_type, quantity, unit_cost, reference_type, reference_id, notes, movement_date, created_at,
         variant_id, variant_color, variant_size, variant_sku, barcode_scope, matched_barcode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (uid, item_id, warehouse_id, movement_type, str(qty), str(cost), reference_type, reference_id, notes or '', now, now,
          vp['variant_id'], vp['variant_color'], vp['variant_size'], vp['variant_sku'], vp['barcode_scope'], vp['matched_barcode']))
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
    branch_sql, branch_params = branch_access_policy.scope_sql(uid, alias='w', branch_column='branch_id', requested_branch_id=request.args.get('branch_id', type=int))
    sql += branch_sql; params.extend(branch_params)
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
    branch_sql, branch_params = branch_access_policy.scope_sql(uid, alias='w', branch_column='branch_id', requested_branch_id=request.args.get('branch_id', type=int))
    sql += branch_sql; params.extend(branch_params)
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
        _require_warehouse_access(db, uid, warehouse_id, 'warehouse_movement.create')
        movement_type = data.get('movement_type') or 'adjustment'
        quantity = data.get('quantity') or '0'
        unit_cost = data.get('unit_cost') or '0'
        reference_type = data.get('reference_type')
        reference_id = data.get('reference_id')
        notes = data.get('notes') or ''
        mid = _record_warehouse_movement(
            db, uid, item_id, warehouse_id, movement_type, quantity, unit_cost,
            reference_type, reference_id, notes,
            variant_id=data.get('variant_id'), variant_color=data.get('variant_color', ''),
            variant_size=data.get('variant_size', ''), variant_sku=data.get('variant_sku', ''),
            barcode_scope=data.get('barcode_scope', ''), matched_barcode=data.get('matched_barcode', '')
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
    branch_sql, branch_params = branch_access_policy.scope_sql(uid, alias='w', branch_column='branch_id', requested_branch_id=request.args.get('branch_id', type=int))
    rows = db.query("""
        SELECT m.* FROM warehouse_movements m
        JOIN warehouses w ON w.id=m.warehouse_id AND w.user_id=m.user_id
        WHERE m.user_id=? AND m.reference_id=? AND m.reference_type IN (?, ?)
    """ + branch_sql + " ORDER BY m.id ASC", tuple([uid, reference_id, reference_type, 'reverse_' + str(reference_type)] + branch_params)).fetchall()
    try:
        nets = {}
        payloads = {}
        for r in rows:
            mt = str(r['movement_type'] or '')
            base_mt = mt[8:] if mt.startswith('reverse_') else mt
            vp = _variant_payload(dict(r))
            # Phase 322: aggregate reversals per color/size variant so two
            # variants of the same material cannot collapse into a generic item
            # reversal in API/network mode.
            key = (
                r['item_id'], r['warehouse_id'], base_mt, str(r['unit_cost'] or '0'),
                vp['variant_id'], vp['variant_color'], vp['variant_size'],
                vp['variant_sku'], vp['barcode_scope'], vp['matched_barcode'],
            )
            nets[key] = nets.get(key, Decimal('0')) + _dec(r['quantity'])
            payloads[key] = vp
        reversed_count = 0
        for key, net_qty in nets.items():
            if net_qty == 0:
                continue
            item_id, warehouse_id, base_mt, unit_cost, *_ = key
            _record_warehouse_movement(
                db, uid, item_id, warehouse_id, 'reverse_' + str(base_mt),
                -net_qty, unit_cost,
                'reverse_' + str(reference_type), reference_id, 'عكس حركة مستودعية',
                **payloads.get(key, {})
            )
            reversed_count += 1
        db.commit()
        return jsonify({'status': 'ok', 'reversed': reversed_count})
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
    uid = _uid(); db = get_warehouse_repository(); _ensure_transfer_schema(db); _ensure_variant_warehouse_schema(db)
    data = request.get_json() or {}
    try:
        item_id = int(data.get('item_id') or 0)
        from_wh = int(data.get('from_warehouse_id') or 0)
        to_wh = int(data.get('to_warehouse_id') or 0)
        qty = _dec(data.get('quantity') or '0')
        conv_factor = _dec(data.get('conversion_factor') or '1')
        if conv_factor <= 0:
            conv_factor = Decimal('1')
        base_qty = _dec(data.get('base_qty') or (qty * conv_factor))
        notes = str(data.get('notes') or '').strip()
        vp = _variant_payload(data)
        if item_id <= 0:
            raise ValueError('اختر المادة')
        if from_wh <= 0 or to_wh <= 0:
            raise ValueError('اختر مستودع المصدر والوجهة')
        if from_wh == to_wh:
            raise ValueError('لا يمكن التحويل إلى نفس المستودع')
        if qty <= 0 or base_qty <= 0:
            raise ValueError('كمية التحويل يجب أن تكون أكبر من صفر')
        if not _warehouse_active(db, uid, from_wh) or not _warehouse_active(db, uid, to_wh):
            raise ValueError('لا يمكن التحويل من أو إلى مستودع مؤرشف')
        _require_warehouse_access(db, uid, from_wh, 'warehouse_transfer.from')
        _require_warehouse_access(db, uid, to_wh, 'warehouse_transfer.to')
        if _available_qty(db, uid, item_id, from_wh, variant_id=vp['variant_id']) < base_qty:
            raise ValueError('الرصيد غير كافٍ في المستودع المصدر')
        unit_cost = _item_cost(db, uid, item_id)
        now = _now()
        transfer_no = _next_transfer_no(db, uid)
        cur = db.query("""
            INSERT INTO warehouse_transfers
            (user_id, transfer_no, item_id, from_warehouse_id, to_warehouse_id, quantity, base_qty, unit_id, unit_name, conversion_factor, barcode_scope, matched_barcode,
             variant_id, variant_color, variant_size, variant_sku, unit_cost, notes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
        """, (uid, transfer_no, item_id, from_wh, to_wh, str(qty), str(base_qty), data.get('unit_id'), data.get('unit_name') or data.get('unit') or '', str(conv_factor), vp['barcode_scope'], vp['matched_barcode'], vp['variant_id'], vp['variant_color'], vp['variant_size'], vp['variant_sku'], str(unit_cost), notes, now))
        tid = int(cur.lastrowid)
        _record_warehouse_movement(db, uid, item_id, from_wh, 'transfer_out', -base_qty, unit_cost, 'warehouse_transfer', tid, f'تحويل إلى مستودع #{to_wh}: {notes}', **vp)
        _record_warehouse_movement(db, uid, item_id, to_wh, 'transfer_in', base_qty, unit_cost, 'warehouse_transfer', tid, f'تحويل من مستودع #{from_wh}: {notes}', **vp)
        _post_inventory_ledger_entry(db, uid, item_id, from_wh, 'transfer_out', 'out', base_qty, unit_cost, 'warehouse_transfer', tid, 'warehouse_transfers', tid, f'دفتر مخزون تحويل إلى مستودع #{to_wh}')
        _post_inventory_ledger_entry(db, uid, item_id, to_wh, 'transfer_in', 'in', base_qty, unit_cost, 'warehouse_transfer', tid, 'warehouse_transfers', tid, f'دفتر مخزون تحويل من مستودع #{from_wh}')
        db.commit()
        return jsonify({'id': tid}), 201
    except Exception as exc:
        db.rollback()
        return jsonify({'error': str(exc)}), 400

@warehouses_bp.route('/warehouses/transfers/<int:transfer_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_warehouse_transfer(transfer_id):
    uid = _uid(); db = get_warehouse_repository(); _ensure_transfer_schema(db); _ensure_variant_warehouse_schema(db)
    t = db.query("SELECT * FROM warehouse_transfers WHERE id=? AND user_id=?", (transfer_id, uid)).fetchone()
    if not t:
        return jsonify({'error': 'التحويل غير موجود'}), 404
    if t['status'] != 'active':
        return jsonify({'error': 'التحويل ملغى مسبقاً'}), 400
    try:
        _require_warehouse_access(db, uid, t['from_warehouse_id'], 'warehouse_transfer.cancel.from')
        _require_warehouse_access(db, uid, t['to_warehouse_id'], 'warehouse_transfer.cancel.to')
    except BranchAccessError as exc:
        return _branch_denied(exc)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 404
    qty = _dec(t['base_qty'] if 'base_qty' in t.keys() and t['base_qty'] not in (None, '') else t['quantity'])
    vp = _variant_payload(dict(t))
    if _available_qty(db, uid, t['item_id'], t['to_warehouse_id'], variant_id=vp['variant_id']) < qty:
        return jsonify({'error': 'لا يمكن إلغاء التحويل لأن رصيد المستودع المستلم غير كافٍ'}), 400
    try:
        unit_cost = _dec(t['unit_cost'])
        _record_warehouse_movement(db, uid, t['item_id'], t['to_warehouse_id'], 'transfer_cancel_out', -qty, unit_cost, 'warehouse_transfer_cancel', transfer_id, 'إلغاء تحويل مستودعي', **vp)
        _record_warehouse_movement(db, uid, t['item_id'], t['from_warehouse_id'], 'transfer_cancel_in', qty, unit_cost, 'warehouse_transfer_cancel', transfer_id, 'إلغاء تحويل مستودعي', **vp)
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
    sql = """
        SELECT t.*, i.name AS item_name, fw.name AS from_warehouse_name, tw.name AS to_warehouse_name
        FROM warehouse_transfers t
        JOIN items i ON i.id=t.item_id AND i.user_id=t.user_id
        JOIN warehouses fw ON fw.id=t.from_warehouse_id AND fw.user_id=t.user_id
        JOIN warehouses tw ON tw.id=t.to_warehouse_id AND tw.user_id=t.user_id
        WHERE t.user_id=?
    """
    params = [uid]
    requested_branch_id = request.args.get('branch_id', type=int)
    if branch_access_policy.can_view_all_branches(uid):
        if requested_branch_id:
            sql += ' AND (fw.branch_id=? OR tw.branch_id=?)'; params.extend([requested_branch_id, requested_branch_id])
    else:
        allowed = branch_access_policy.allowed_branch_ids(uid)
        if allowed:
            placeholders = ','.join('?' for _ in allowed)
            sql += f' AND (fw.branch_id IN ({placeholders}) OR tw.branch_id IN ({placeholders}))'
            params.extend(allowed + allowed)
    sql += ' ORDER BY t.id DESC LIMIT ?'; params.append(limit)
    rows = db.query(sql, tuple(params)).fetchall()
    return jsonify({'transfers': [_rowdict(r) for r in rows]})

