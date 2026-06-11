from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.api.audit_utils import audit_log
from alrajhi_server.database.connection import get_db

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/suppliers', methods=['GET'])
@jwt_required()
def get_suppliers():
    user_id = get_jwt_identity()
    search = request.args.get('search')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)
    db = get_db()
    query = "SELECT * FROM suppliers WHERE user_id = ?"
    params = [user_id]
    if search:
        query += " AND (name LIKE ? OR phone LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY name"
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    if offset:
        query += " OFFSET ?"
        params.append(offset)
    count_query = "SELECT COUNT(*) FROM suppliers WHERE user_id = ?"
    count_params = [user_id]
    if search:
        count_query += " AND (name LIKE ? OR phone LIKE ?)"
        count_params.extend([f"%{search}%", f"%{search}%"])
    total = db.execute(count_query, count_params).fetchone()[0]
    rows = db.execute(query, params).fetchall()
    return jsonify({'suppliers': [dict(row) for row in rows], 'total': total})

@suppliers_bp.route('/suppliers', methods=['POST'])
@jwt_required()
def add_supplier():
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    cursor = db.execute('''
        INSERT INTO suppliers (user_id, name, phone, address, balance)
        VALUES (?,?,?,?,?)
    ''', (user_id, data['name'], data.get('phone', ''), data.get('address', ''), data.get('balance', '0')))
    db.commit()
    return jsonify({'id': cursor.lastrowid}), 201

@suppliers_bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
@jwt_required()
def update_supplier(supplier_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    db.execute('''
        UPDATE suppliers SET name=?, phone=?, address=?, balance=?
        WHERE id=? AND user_id=?
    ''', (data['name'], data.get('phone', ''), data.get('address', ''), data.get('balance', '0'), supplier_id, user_id))
    db.commit()
    return jsonify({'status': 'ok'})

@suppliers_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
@jwt_required()
def delete_supplier(supplier_id):
    user_id = get_jwt_identity()
    db = get_db()
    db.execute("DELETE FROM suppliers WHERE id=? AND user_id=?", (supplier_id, user_id))
    db.commit()
    return jsonify({'status': 'ok'})


