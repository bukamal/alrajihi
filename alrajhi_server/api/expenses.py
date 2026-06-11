# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.api.audit_utils import audit_log
from alrajhi_server.database.connection import get_db
import datetime

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/expenses', methods=['GET'])
@jwt_required()
def get_expenses():
    user_id = get_jwt_identity()
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM vouchers WHERE user_id=? AND type='expense'", (user_id,)).fetchone()[0]
    query = "SELECT * FROM vouchers WHERE user_id=? AND type='expense' ORDER BY id DESC"
    params = [user_id]
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    if offset is not None:
        query += " OFFSET ?"
        params.append(offset)
    rows = db.execute(query, params).fetchall()
    return jsonify({'expenses': [dict(row) for row in rows], 'total': total})

@expenses_bp.route('/expenses', methods=['POST'])
@jwt_required()
def add_expense():
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    now = datetime.datetime.now().isoformat()
    cursor = db.execute('''
        INSERT INTO vouchers (user_id, type, date, amount, description, reference, customer_id, supplier_id, invoice_id, exchange_rate_to_usd, original_currency)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        user_id, 'expense', data.get('date', now[:10]), str(data.get('amount', 0)),
        data.get('description', ''), data.get('reference', ''), None, data.get('supplier_id'), None,
        data.get('exchange_rate_to_usd', 1.0), data.get('original_currency', 'USD')
    ))
    db.commit()
    return jsonify({'id': cursor.lastrowid}), 201

@expenses_bp.route('/expenses/<int:expense_id>', methods=['PUT'])
@jwt_required()
def update_expense(expense_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    db.execute('''
        UPDATE vouchers SET date=?, amount=?, description=?, reference=?, supplier_id=?, exchange_rate_to_usd=?, original_currency=?
        WHERE id=? AND user_id=? AND type='expense'
    ''', (
        data.get('date'), str(data.get('amount', 0)), data.get('description', ''), data.get('reference', ''),
        data.get('supplier_id'), data.get('exchange_rate_to_usd', 1.0), data.get('original_currency', 'USD'),
        expense_id, user_id
    ))
    db.commit()
    return jsonify({'status': 'ok'})

@expenses_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):
    user_id = get_jwt_identity()
    db = get_db()
    db.execute("DELETE FROM vouchers WHERE id=? AND user_id=? AND type='expense'", (expense_id, user_id))
    db.commit()
    return jsonify({'status': 'ok'})
