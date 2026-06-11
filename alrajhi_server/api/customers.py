from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.api.audit_utils import audit_log
from alrajhi_server.database.connection import get_db

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/customers', methods=['GET'])
@jwt_required()
def get_customers():
    user_id = get_jwt_identity()
    search = request.args.get('search')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)
    db = get_db()
    query = "SELECT * FROM customers WHERE user_id = ?"
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
    count_query = "SELECT COUNT(*) FROM customers WHERE user_id = ?"
    count_params = [user_id]
    if search:
        count_query += " AND (name LIKE ? OR phone LIKE ?)"
        count_params.extend([f"%{search}%", f"%{search}%"])
    total = db.execute(count_query, count_params).fetchone()[0]
    rows = db.execute(query, params).fetchall()
    return jsonify({'customers': [dict(row) for row in rows], 'total': total})

@customers_bp.route('/customers', methods=['POST'])
@jwt_required()
def add_customer():
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    cursor = db.execute('''
        INSERT INTO customers (user_id, name, phone, address, balance)
        VALUES (?,?,?,?,?)
    ''', (user_id, data['name'], data.get('phone', ''), data.get('address', ''), data.get('balance', '0')))
    db.commit()
    return jsonify({'id': cursor.lastrowid}), 201

@customers_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@jwt_required()
def update_customer(customer_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    db.execute('''
        UPDATE customers SET name=?, phone=?, address=?, balance=?
        WHERE id=? AND user_id=?
    ''', (data['name'], data.get('phone', ''), data.get('address', ''), data.get('balance', '0'), customer_id, user_id))
    db.commit()
    return jsonify({'status': 'ok'})

@customers_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
@jwt_required()
def delete_customer(customer_id):
    user_id = get_jwt_identity()
    db = get_db()
    db.execute("DELETE FROM customers WHERE id=? AND user_id=?", (customer_id, user_id))
    db.commit()
    return jsonify({'status': 'ok'})


