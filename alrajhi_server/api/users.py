from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from database.connection import get_db
from decorators import admin_required
import datetime

users_bp = Blueprint('users', __name__)

@users_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    db = get_db()
    rows = db.execute("SELECT id, username, full_name, role, created_at, last_login FROM users").fetchall()
    return jsonify([dict(row) for row in rows])

@users_bp.route('/users', methods=['POST'])
@admin_required
def add_user():
    data = request.get_json()
    from auth.password import hash_password
    pwd_hash, salt = hash_password(data['password'])
    db = get_db()
    now = datetime.datetime.now().isoformat()
    cursor = db.execute('''
        INSERT INTO users (username, password_hash, salt, full_name, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data['username'], pwd_hash, salt, data.get('full_name', ''), data.get('role', 'user'), now))
    db.commit()
    return jsonify({'id': cursor.lastrowid}), 201

@users_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    data = request.get_json()
    db = get_db()
    db.execute('UPDATE users SET full_name=?, role=? WHERE id=?',
               (data.get('full_name', ''), data.get('role', 'user'), user_id))
    db.commit()
    return jsonify({'status': 'ok'})

@users_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    if user_id == 1:
        return jsonify({'error': 'Cannot delete admin'}), 400
    db = get_db()
    db.execute('DELETE FROM users WHERE id=?', (user_id,))
    db.commit()
    return jsonify({'status': 'ok'})

@users_bp.route('/users/change_password', methods=['POST'])
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    db = get_db()
    user = db.execute('SELECT password_hash, salt FROM users WHERE id=?', (user_id,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    from auth.password import verify_password
    if not verify_password(old_password, user['password_hash'], user['salt']):
        return jsonify({'error': 'Invalid old password'}), 401
    from auth.password import hash_password
    new_hash, new_salt = hash_password(new_password)
    db.execute('UPDATE users SET password_hash=?, salt=?, force_password_change=0 WHERE id=?',
               (new_hash, new_salt, user_id))
    db.commit()
    return jsonify({'status': 'ok'})


