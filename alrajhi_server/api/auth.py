# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from alrajhi_server.database.connection import get_db
from alrajhi_server.auth.password import verify_password
import datetime
from alrajhi_server.api.audit_utils import audit_log

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user or not verify_password(password or '', user['password_hash'], user['salt']):
        return jsonify({'error': 'Invalid credentials'}), 401

    now_login = datetime.datetime.now().isoformat()
    db.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_login, user['id']))
    db.commit()

    if user:
        token = create_access_token(identity=str(user['id']))
        # تسجيل التدقيق
        db = get_db()
        now = datetime.datetime.now().isoformat()
        db.execute('''
            INSERT INTO audit_log (user_id, username, action, table_name, record_id, details, ip_address, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user['id'], user['username'], 'تسجيل دخول', 'users', user['id'], '', request.remote_addr, now))
        db.commit()
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'role': user['role'],
                'force_password_change': user['force_password_change'] if 'force_password_change' in user.keys() else 0
            }
        })
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    db = get_db()
    now = datetime.datetime.now().isoformat()
    db.execute('INSERT INTO token_blacklist (jti, created_at) VALUES (?, ?)', (jti, now))
    user_id = get_jwt_identity()
    user = db.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    if user:
        db.execute('''
            INSERT INTO audit_log (user_id, username, action, table_name, record_id, details, ip_address, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, user['username'], 'تسجيل خروج', 'auth', 0, '', request.remote_addr, now))
    db.commit()
    return jsonify({'status': 'logged out'}), 200


