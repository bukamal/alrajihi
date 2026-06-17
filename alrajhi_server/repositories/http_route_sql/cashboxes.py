# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from alrajhi_server.repositories.cashbox_repository import get_cashbox_repository
from alrajhi_server.decorators import admin_required

cashboxes_bp = Blueprint('cashboxes', __name__)


def _uid():
    try:
        return int(get_jwt_identity())
    except Exception:
        return get_jwt_identity()


def _now():
    return datetime.datetime.now().isoformat()


def _rowdict(row):
    return dict(row) if row else None


def _default_branch_id(db, uid):
    row = db.query("SELECT id FROM branches WHERE user_id=? AND is_default=1 AND deleted_at IS NULL LIMIT 1", (uid,)).fetchone()
    if row:
        return row['id']
    row = db.query("SELECT id FROM branches WHERE user_id=? AND deleted_at IS NULL ORDER BY id LIMIT 1", (uid,)).fetchone()
    if row:
        return row['id']
    now = _now()
    cur = db.query("""
        INSERT INTO branches (user_id, name, code, is_default, is_active, created_at, updated_at)
        VALUES (?, ?, ?, 1, 1, ?, ?)
    """, (uid, 'الفرع الرئيسي', 'MAIN', now, now))
    db.commit()
    return cur.lastrowid


def _ensure_default_cashbox(db, uid, branch_id=None):
    branch_id = branch_id or _default_branch_id(db, uid)
    row = db.query(
        "SELECT id FROM cashboxes WHERE user_id=? AND branch_id=? AND is_default=1 AND deleted_at IS NULL LIMIT 1",
        (uid, branch_id),
    ).fetchone()
    if row:
        return int(row['id'])
    row = db.query(
        "SELECT id FROM cashboxes WHERE user_id=? AND branch_id=? AND deleted_at IS NULL ORDER BY is_default DESC, id LIMIT 1",
        (uid, branch_id),
    ).fetchone()
    if row:
        return int(row['id'])
    now = _now()
    cur = db.query("""
        INSERT INTO cashboxes (user_id, branch_id, name, code, notes, is_default, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?)
    """, (uid, branch_id, 'الصندوق الرئيسي', f'CASH-{branch_id}', 'تم إنشاؤه تلقائياً', now, now))
    db.commit()
    return int(cur.lastrowid)


def _cashbox_payload(data, uid):
    db = get_cashbox_repository()
    return {
        'branch_id': data.get('branch_id') or _default_branch_id(db, uid),
        'name': (data.get('name') or '').strip() or 'صندوق',
        'code': (data.get('code') or '').strip(),
        'notes': data.get('notes') or '',
        'is_active': 1 if data.get('is_active', 1) else 0,
    }


def _bank_payload(data, uid):
    db = get_cashbox_repository()
    return {
        'branch_id': data.get('branch_id') or _default_branch_id(db, uid),
        'bank_name': (data.get('bank_name') or '').strip() or 'بنك',
        'account_name': (data.get('account_name') or '').strip() or '',
        'account_number': data.get('account_number') or '',
        'iban': data.get('iban') or '',
        'notes': data.get('notes') or '',
        'is_active': 1 if data.get('is_active', 1) else 0,
    }


@cashboxes_bp.route('/cashboxes', methods=['GET'])
@jwt_required()
def list_cashboxes():
    uid = _uid(); db = get_cashbox_repository(); include = str(request.args.get('include_archived', '')).lower() in ('1','true','yes')
    _ensure_default_cashbox(db, uid)
    sql = """
        SELECT c.*, b.name AS branch_name,
               COALESCE(SUM(CASE WHEN m.cashbox_id=c.id THEN CAST(m.amount AS REAL) ELSE 0 END),0) AS balance
        FROM cashboxes c
        LEFT JOIN branches b ON b.id=c.branch_id
        LEFT JOIN cash_bank_movements m ON m.cashbox_id=c.id
        WHERE c.user_id=?
    """
    params = [uid]
    if not include:
        sql += " AND c.deleted_at IS NULL AND COALESCE(c.is_active,1)=1"
    sql += " GROUP BY c.id ORDER BY b.name, c.is_default DESC, c.name"
    rows = [_rowdict(r) for r in db.query(sql, params).fetchall()]
    return jsonify({'cashboxes': rows})


@cashboxes_bp.route('/cashboxes/default', methods=['GET'])
@jwt_required()
def default_cashbox():
    uid = _uid(); db = get_cashbox_repository(); branch_id = request.args.get('branch_id')
    cid = _ensure_default_cashbox(db, uid, branch_id)
    return jsonify({'id': cid})


@cashboxes_bp.route('/cashboxes/<int:cid>', methods=['GET'])
@jwt_required()
def get_cashbox(cid):
    row = get_cashbox_repository().query('SELECT * FROM cashboxes WHERE id=? AND user_id=?', (cid, _uid())).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404
    return jsonify(_rowdict(row))


@cashboxes_bp.route('/cashboxes', methods=['POST'])
@admin_required
def add_cashbox():
    uid = _uid(); db = get_cashbox_repository(); p = _cashbox_payload(request.get_json() or {}, uid); now = _now()
    cur = db.query("""
        INSERT INTO cashboxes (user_id, branch_id, name, code, notes, is_default, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
    """, (uid, p['branch_id'], p['name'], p['code'], p['notes'], p['is_active'], now, now))
    db.commit()
    return jsonify({'id': cur.lastrowid}), 201


@cashboxes_bp.route('/cashboxes/<int:cid>', methods=['PUT'])
@admin_required
def update_cashbox(cid):
    uid = _uid(); db = get_cashbox_repository(); p = _cashbox_payload(request.get_json() or {}, uid)
    db.query('UPDATE cashboxes SET branch_id=?, name=?, code=?, notes=?, is_active=?, updated_at=? WHERE id=? AND user_id=?',
               (p['branch_id'], p['name'], p['code'], p['notes'], p['is_active'], _now(), cid, uid))
    db.commit()
    return jsonify({'status': 'ok'})


@cashboxes_bp.route('/cashboxes/<int:cid>', methods=['DELETE'])
@admin_required
def archive_cashbox(cid):
    uid = _uid(); db = get_cashbox_repository(); now = _now()
    row = db.query('SELECT is_default FROM cashboxes WHERE id=? AND user_id=?', (cid, uid)).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404
    if int(row['is_default'] or 0) == 1:
        return jsonify({'error': 'لا يمكن أرشفة الصندوق الرئيسي'}), 400
    db.query('UPDATE cashboxes SET deleted_at=?, is_active=0, updated_at=? WHERE id=? AND user_id=?', (now, now, cid, uid))
    db.commit()
    return jsonify({'status': 'ok'})


@cashboxes_bp.route('/bank_accounts', methods=['GET'])
@jwt_required()
def list_bank_accounts():
    uid = _uid(); db = get_cashbox_repository(); include = str(request.args.get('include_archived', '')).lower() in ('1','true','yes')
    sql = """
        SELECT ba.*, b.name AS branch_name,
               COALESCE(SUM(CASE WHEN m.bank_account_id=ba.id THEN CAST(m.amount AS REAL) ELSE 0 END),0) AS balance
        FROM bank_accounts ba
        LEFT JOIN branches b ON b.id=ba.branch_id
        LEFT JOIN cash_bank_movements m ON m.bank_account_id=ba.id
        WHERE ba.user_id=?
    """
    params = [uid]
    if not include:
        sql += " AND ba.deleted_at IS NULL AND COALESCE(ba.is_active,1)=1"
    sql += " GROUP BY ba.id ORDER BY b.name, ba.bank_name, ba.account_name"
    return jsonify({'bank_accounts': [_rowdict(r) for r in db.query(sql, params).fetchall()]})


@cashboxes_bp.route('/bank_accounts/<int:bid>', methods=['GET'])
@jwt_required()
def get_bank_account(bid):
    row = get_cashbox_repository().query('SELECT * FROM bank_accounts WHERE id=? AND user_id=?', (bid, _uid())).fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404
    return jsonify(_rowdict(row))


@cashboxes_bp.route('/bank_accounts', methods=['POST'])
@admin_required
def add_bank_account():
    uid = _uid(); db = get_cashbox_repository(); p = _bank_payload(request.get_json() or {}, uid); now = _now()
    cur = db.query("""
        INSERT INTO bank_accounts (user_id, branch_id, bank_name, account_name, account_number, iban, notes, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (uid, p['branch_id'], p['bank_name'], p['account_name'], p['account_number'], p['iban'], p['notes'], p['is_active'], now, now))
    db.commit()
    return jsonify({'id': cur.lastrowid}), 201


@cashboxes_bp.route('/bank_accounts/<int:bid>', methods=['PUT'])
@admin_required
def update_bank_account(bid):
    uid = _uid(); db = get_cashbox_repository(); p = _bank_payload(request.get_json() or {}, uid)
    db.query('UPDATE bank_accounts SET branch_id=?, bank_name=?, account_name=?, account_number=?, iban=?, notes=?, is_active=?, updated_at=? WHERE id=? AND user_id=?',
               (p['branch_id'], p['bank_name'], p['account_name'], p['account_number'], p['iban'], p['notes'], p['is_active'], _now(), bid, uid))
    db.commit()
    return jsonify({'status': 'ok'})


@cashboxes_bp.route('/bank_accounts/<int:bid>', methods=['DELETE'])
@admin_required
def archive_bank_account(bid):
    uid = _uid(); db = get_cashbox_repository(); now = _now()
    db.query('UPDATE bank_accounts SET deleted_at=?, is_active=0, updated_at=? WHERE id=? AND user_id=?', (now, now, bid, uid))
    db.commit()
    return jsonify({'status': 'ok'})


@cashboxes_bp.route('/cash_bank_movements', methods=['GET'])
@jwt_required()
def movements():
    uid = _uid(); db = get_cashbox_repository(); limit = int(request.args.get('limit', 200) or 200)
    cashbox_id = request.args.get('cashbox_id'); bank_account_id = request.args.get('bank_account_id')
    sql = """
        SELECT m.*, c.name AS cashbox_name, ba.bank_name, ba.account_name, b.name AS branch_name
        FROM cash_bank_movements m
        LEFT JOIN cashboxes c ON c.id=m.cashbox_id
        LEFT JOIN bank_accounts ba ON ba.id=m.bank_account_id
        LEFT JOIN branches b ON b.id=m.branch_id
        WHERE m.user_id=?
    """
    params = [uid]
    if cashbox_id:
        sql += ' AND m.cashbox_id=?'; params.append(cashbox_id)
    if bank_account_id:
        sql += ' AND m.bank_account_id=?'; params.append(bank_account_id)
    sql += ' ORDER BY m.id DESC LIMIT ?'; params.append(limit)
    return jsonify({'movements': [_rowdict(r) for r in db.query(sql, params).fetchall()]})

@cashboxes_bp.route('/cash_bank_movements', methods=['POST'])
@jwt_required()
def add_movement():
    uid = _uid(); db = get_cashbox_repository(); data = request.get_json() or {}; now = _now()
    amount = Decimal(str(data.get('amount', 0)))
    cur = db.query('''
        INSERT INTO cash_bank_movements
        (user_id, branch_id, cashbox_id, bank_account_id, movement_type, amount, direction, shift_id,
         reference_type, reference_id, description, movement_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        uid, data.get('branch_id'), data.get('cashbox_id'), data.get('bank_account_id'),
        data.get('movement_type') or 'manual', str(amount), data.get('direction'), data.get('shift_id'),
        data.get('reference_type'), data.get('reference_id'), data.get('description') or '',
        data.get('movement_date') or now, now
    ))
    db.commit()
    return jsonify({'id': cur.lastrowid}), 201

@cashboxes_bp.route('/cash_bank_movements/by-reference', methods=['DELETE'])
@jwt_required()
def delete_movements_by_reference():
    uid = _uid(); db = get_cashbox_repository(); reference_type = request.args.get('reference_type'); reference_id = request.args.get('reference_id', type=int)
    db.query('DELETE FROM cash_bank_movements WHERE user_id=? AND reference_type=? AND reference_id=?', (uid, reference_type, reference_id))
    db.commit()
    return jsonify({'status': 'ok'})

@cashboxes_bp.route('/pos_shifts/current', methods=['GET'])
@jwt_required()
def current_shift():
    uid = _uid(); db = get_cashbox_repository(); cashbox_id = request.args.get('cashbox_id', type=int)
    sql = '''SELECT s.*, c.name AS cashbox_name, b.name AS branch_name
             FROM pos_shifts s
             LEFT JOIN cashboxes c ON c.id=s.cashbox_id
             LEFT JOIN branches b ON b.id=s.branch_id
             WHERE s.user_id=? AND s.status='open' '''
    params = [uid]
    if cashbox_id:
        sql += ' AND s.cashbox_id=?'; params.append(cashbox_id)
    sql += ' ORDER BY s.id DESC LIMIT 1'
    row = db.query(sql, params).fetchone()
    return jsonify(_rowdict(row) or {})

@cashboxes_bp.route('/pos_shifts', methods=['GET'])
@jwt_required()
def list_shifts():
    uid = _uid(); db = get_cashbox_repository(); status = request.args.get('status'); limit = request.args.get('limit', 100, type=int)
    sql = '''SELECT s.*, c.name AS cashbox_name, b.name AS branch_name
             FROM pos_shifts s
             LEFT JOIN cashboxes c ON c.id=s.cashbox_id
             LEFT JOIN branches b ON b.id=s.branch_id
             WHERE s.user_id=?'''
    params = [uid]
    if status:
        sql += ' AND s.status=?'; params.append(status)
    sql += ' ORDER BY s.id DESC LIMIT ?'; params.append(limit)
    return jsonify({'shifts': [_rowdict(r) for r in db.query(sql, params).fetchall()]})

@cashboxes_bp.route('/pos_shifts', methods=['POST'])
@jwt_required()
def open_shift():
    uid = _uid(); db = get_cashbox_repository(); data = request.get_json() or {}; now = _now()
    branch_id = data.get('branch_id')
    if not branch_id:
        branch_id = _default_branch_id(db, uid)
    cashbox_id = data.get('cashbox_id') or _ensure_default_cashbox(db, uid, branch_id)
    exists = db.query("SELECT id FROM pos_shifts WHERE user_id=? AND cashbox_id=? AND status='open' LIMIT 1", (uid, cashbox_id)).fetchone()
    if exists:
        return jsonify({'error': 'توجد وردية مفتوحة على هذا الصندوق'}), 400
    opening = Decimal(str(data.get('opening_amount') or 0))
    cur = db.query('''INSERT INTO pos_shifts
        (user_id, branch_id, cashbox_id, opening_amount, expected_amount, status, opened_at, notes)
        VALUES (?, ?, ?, ?, ?, 'open', ?, ?)''',
        (uid, branch_id, cashbox_id, str(opening), str(opening), now, data.get('notes') or ''))
    db.commit(); return jsonify({'id': cur.lastrowid}), 201

def _shift_summary_dict(db, uid, shift_id):
    shift = db.query('''SELECT s.*, c.name AS cashbox_name, b.name AS branch_name
                          FROM pos_shifts s
                          LEFT JOIN cashboxes c ON c.id=s.cashbox_id
                          LEFT JOIN branches b ON b.id=s.branch_id
                          WHERE s.id=? AND s.user_id=?''', (shift_id, uid)).fetchone()
    if not shift: return None
    d = _rowdict(shift)
    rows = db.query('SELECT movement_type, amount, direction FROM cash_bank_movements WHERE shift_id=? AND user_id=?', (shift_id, uid)).fetchall()
    total_cash = Decimal('0'); total_card = Decimal('0'); expenses = Decimal('0')
    for r in rows:
        amount = Decimal(str(r['amount'] or 0)); mtype = str(r['movement_type'] or '')
        if mtype in ('pos_sale_cash','sale_cash'):
            total_cash += amount
        elif mtype in ('pos_sale_card','sale_card'):
            total_card += amount
        elif amount < 0:
            expenses += abs(amount)
    opening = Decimal(str(d.get('opening_amount') or 0)); expected = opening + total_cash - expenses
    d.update({'total_cash': str(total_cash), 'total_card': str(total_card), 'total_sales': str(total_cash + total_card), 'expenses': str(expenses), 'expected_amount': str(expected)})
    return d

@cashboxes_bp.route('/pos_shifts/<int:shift_id>/summary', methods=['GET'])
@jwt_required()
def shift_summary(shift_id):
    summary = _shift_summary_dict(get_cashbox_repository(), _uid(), shift_id)
    if not summary: return jsonify({'error': 'not found'}), 404
    return jsonify(summary)

@cashboxes_bp.route('/pos_shifts/<int:shift_id>/close', methods=['POST'])
@jwt_required()
def close_shift(shift_id):
    uid = _uid(); db = get_cashbox_repository(); data = request.get_json() or {}; summary = _shift_summary_dict(db, uid, shift_id)
    if not summary: return jsonify({'error': 'not found'}), 404
    if summary.get('status') != 'open': return jsonify({'error': 'الوردية مغلقة بالفعل'}), 400
    actual = Decimal(str(data.get('actual_amount') or 0)); expected = Decimal(str(summary.get('expected_amount') or 0)); diff = actual - expected; now = _now()
    db.query('''UPDATE pos_shifts SET closing_amount=?, expected_amount=?, actual_amount=?, difference_amount=?,
                  total_sales=?, total_cash=?, total_card=?, status='closed', closed_at=?, notes=COALESCE(NULLIF(?,''),notes)
                  WHERE id=? AND user_id=?''',
               (str(actual), str(expected), str(actual), str(diff), summary.get('total_sales','0'), summary.get('total_cash','0'), summary.get('total_card','0'), now, data.get('notes',''), shift_id, uid))
    db.commit(); return jsonify(_shift_summary_dict(db, uid, shift_id))
