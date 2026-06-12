# -*- coding: utf-8 -*-
from __future__ import annotations
import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.database.connection import get_db
from alrajhi_server.decorators import admin_required

branches_bp = Blueprint('branches', __name__)

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
    cur = db.execute("""
        INSERT INTO branches (user_id, name, code, address, phone, notes, is_default, is_active, created_at, updated_at)
        VALUES (?, ?, ?, '', '', ?, 1, 1, ?, ?)
    """, (uid, 'الفرع الرئيسي', 'MAIN', 'تم إنشاؤه تلقائياً', now, now))
    db.commit(); return int(cur.lastrowid)

def _payload(data):
    data = data or {}
    name = (data.get('name') or '').strip() or 'فرع'
    return {
        'name': name,
        'code': (data.get('code') or '').strip(),
        'address': data.get('address') or '',
        'phone': data.get('phone') or '',
        'notes': data.get('notes') or '',
        'is_active': 1 if data.get('is_active', 1) else 0,
    }

@branches_bp.route('/branches', methods=['GET'])
@jwt_required()
def list_branches():
    uid = _uid(); db = get_db(); include = str(request.args.get('include_archived','')).lower() in ('1','true','yes')
    _ensure_default_branch(db, uid)
    sql = """
        SELECT b.*, COUNT(DISTINCT w.id) AS warehouse_count
        FROM branches b
        LEFT JOIN warehouses w ON w.branch_id=b.id AND w.user_id=b.user_id AND w.deleted_at IS NULL
        WHERE b.user_id=?
    """
    params=[uid]
    if not include:
        sql += " AND b.deleted_at IS NULL AND COALESCE(b.is_active,1)=1"
    sql += " GROUP BY b.id ORDER BY b.is_default DESC, b.name"
    return jsonify({'branches': [_rowdict(r) for r in db.execute(sql, params).fetchall()]})

@branches_bp.route('/branches/default', methods=['GET'])
@jwt_required()
def default_branch():
    return jsonify({'id': _ensure_default_branch(get_db(), _uid())})

@branches_bp.route('/branches/<int:branch_id>', methods=['GET'])
@jwt_required()
def get_branch(branch_id):
    row = get_db().execute('SELECT * FROM branches WHERE id=? AND user_id=?', (branch_id, _uid())).fetchone()
    if not row: return jsonify({'error': 'not found'}), 404
    return jsonify(_rowdict(row))

@branches_bp.route('/branches', methods=['POST'])
@admin_required
def add_branch():
    uid = _uid(); db = get_db(); p = _payload(request.get_json() or {}); now = _now()
    cur = db.execute("""
        INSERT INTO branches (user_id, name, code, address, phone, notes, is_default, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
    """, (uid, p['name'], p['code'], p['address'], p['phone'], p['notes'], p['is_active'], now, now))
    db.commit(); return jsonify({'id': cur.lastrowid}), 201

@branches_bp.route('/branches/<int:branch_id>', methods=['PUT'])
@admin_required
def update_branch(branch_id):
    uid = _uid(); db = get_db(); p = _payload(request.get_json() or {})
    db.execute('UPDATE branches SET name=?, code=?, address=?, phone=?, notes=?, is_active=?, updated_at=? WHERE id=? AND user_id=?',
               (p['name'], p['code'], p['address'], p['phone'], p['notes'], p['is_active'], _now(), branch_id, uid))
    db.commit(); return jsonify({'status': 'ok'})

@branches_bp.route('/branches/<int:branch_id>', methods=['DELETE'])
@admin_required
def archive_branch(branch_id):
    uid = _uid(); db = get_db(); now = _now()
    row = db.execute('SELECT is_default FROM branches WHERE id=? AND user_id=?', (branch_id, uid)).fetchone()
    if not row: return jsonify({'error': 'not found'}), 404
    if int(row['is_default'] or 0) == 1: return jsonify({'error': 'لا يمكن أرشفة الفرع الرئيسي'}), 400
    db.execute('UPDATE branches SET deleted_at=?, is_active=0, updated_at=? WHERE id=? AND user_id=?', (now, now, branch_id, uid))
    db.commit(); return jsonify({'status': 'ok'})
