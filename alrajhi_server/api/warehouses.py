# -*- coding: utf-8 -*-
from __future__ import annotations
import datetime
from decimal import Decimal
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.database.connection import get_db
from alrajhi_server.decorators import admin_required

warehouses_bp = Blueprint('warehouses', __name__)

def _uid():
    try: return int(get_jwt_identity())
    except Exception: return get_jwt_identity()

def _now(): return datetime.datetime.now().isoformat()
def _rowdict(row): return dict(row) if row else None

def _ensure_default_branch(db, uid):
    row = db.execute("SELECT id FROM branches WHERE user_id=? AND is_default=1 AND deleted_at IS NULL LIMIT 1", (uid,)).fetchone()
    if row: return int(row['id'])
    row = db.execute("SELECT id FROM branches WHERE user_id=? AND deleted_at IS NULL ORDER BY id LIMIT 1", (uid,)).fetchone()
    if row: return int(row['id'])
    now = _now()
    cur = db.execute("""INSERT INTO branches (user_id, name, code, is_default, is_active, created_at, updated_at)
                    VALUES (?, 'الفرع الرئيسي', 'MAIN', 1, 1, ?, ?)""", (uid, now, now))
    db.commit(); return int(cur.lastrowid)

def _ensure_default_warehouse(db, uid, branch_id=None):
    branch_id = branch_id or _ensure_default_branch(db, uid)
    row = db.execute("SELECT id FROM warehouses WHERE user_id=? AND is_default=1 AND deleted_at IS NULL LIMIT 1", (uid,)).fetchone()
    if row: return int(row['id'])
    row = db.execute("SELECT id FROM warehouses WHERE user_id=? AND deleted_at IS NULL ORDER BY id LIMIT 1", (uid,)).fetchone()
    if row: return int(row['id'])
    now = _now()
    cur = db.execute("""
        INSERT INTO warehouses (user_id, branch_id, name, code, notes, is_default, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?)
    """, (uid, branch_id, 'المستودع الرئيسي', 'MAIN-WH', 'تم إنشاؤه تلقائياً', now, now))
    db.commit(); return int(cur.lastrowid)

def _payload(data, uid):
    data = data or {}; db = get_db()
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
    uid = _uid(); db = get_db(); include = str(request.args.get('include_archived','')).lower() in ('1','true','yes')
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
    return jsonify({'warehouses': [_rowdict(r) for r in db.execute(sql, params).fetchall()]})

@warehouses_bp.route('/warehouses/default', methods=['GET'])
@jwt_required()
def default_warehouse():
    return jsonify({'id': _ensure_default_warehouse(get_db(), _uid())})

@warehouses_bp.route('/warehouses/available_qty', methods=['GET'])
@jwt_required()
def available_qty():
    uid = _uid(); db = get_db(); item_id = request.args.get('item_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int) or _ensure_default_warehouse(db, uid)
    if not item_id: return jsonify({'quantity': '0'})
    row = db.execute('SELECT quantity FROM item_warehouse_balances WHERE user_id=? AND item_id=? AND warehouse_id=?', (uid, item_id, warehouse_id)).fetchone()
    return jsonify({'quantity': str(row['quantity']) if row and row['quantity'] is not None else '0'})

@warehouses_bp.route('/warehouses/<int:warehouse_id>', methods=['GET'])
@jwt_required()
def get_warehouse(warehouse_id):
    row = get_db().execute('SELECT * FROM warehouses WHERE id=? AND user_id=?', (warehouse_id, _uid())).fetchone()
    if not row: return jsonify({'error': 'not found'}), 404
    return jsonify(_rowdict(row))

@warehouses_bp.route('/warehouses', methods=['POST'])
@admin_required
def add_warehouse():
    uid = _uid(); db = get_db(); p = _payload(request.get_json() or {}, uid); now = _now()
    cur = db.execute("""
        INSERT INTO warehouses (user_id, branch_id, name, code, notes, is_default, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
    """, (uid, p['branch_id'], p['name'], p['code'], p['notes'], p['is_active'], now, now))
    db.commit(); return jsonify({'id': cur.lastrowid}), 201

@warehouses_bp.route('/warehouses/<int:warehouse_id>', methods=['PUT'])
@admin_required
def update_warehouse(warehouse_id):
    uid = _uid(); db = get_db(); p = _payload(request.get_json() or {}, uid)
    db.execute('UPDATE warehouses SET branch_id=?, name=?, code=?, notes=?, is_active=?, updated_at=? WHERE id=? AND user_id=?',
               (p['branch_id'], p['name'], p['code'], p['notes'], p['is_active'], _now(), warehouse_id, uid))
    db.commit(); return jsonify({'status': 'ok'})

@warehouses_bp.route('/warehouses/<int:warehouse_id>', methods=['DELETE'])
@admin_required
def archive_warehouse(warehouse_id):
    uid = _uid(); db = get_db(); now = _now()
    row = db.execute('SELECT is_default FROM warehouses WHERE id=? AND user_id=?', (warehouse_id, uid)).fetchone()
    if not row: return jsonify({'error': 'not found'}), 404
    if int(row['is_default'] or 0) == 1: return jsonify({'error': 'لا يمكن أرشفة المستودع الرئيسي'}), 400
    db.execute('UPDATE warehouses SET deleted_at=?, is_active=0, updated_at=? WHERE id=? AND user_id=?', (now, now, warehouse_id, uid))
    db.commit(); return jsonify({'status': 'ok'})
