# -*- coding: utf-8 -*-
import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt

from alrajhi_server.auth.password import verify_password
from alrajhi_server.repositories.auth_repository import AuthRepository

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    repo = AuthRepository()
    user = repo.get_user_by_username(username)
    if not user or not verify_password(password or '', user['password_hash'], user['salt']):
        return jsonify({'error': 'Invalid credentials'}), 401

    now = datetime.datetime.now().isoformat()
    repo.mark_last_login(user['id'], now)
    token = create_access_token(identity=str(user['id']))
    repo.record_auth_event(
        user_id=user['id'], username=user['username'], action='تسجيل دخول',
        table_name='users', record_id=user['id'], ip_address=request.remote_addr, timestamp=now,
    )
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


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    repo = AuthRepository()
    now = datetime.datetime.now().isoformat()
    jti = get_jwt()['jti']
    repo.add_token_to_blacklist(jti, now)
    user_id = get_jwt_identity()
    username = repo.get_username(user_id)
    if username:
        repo.record_auth_event(
            user_id=user_id, username=username, action='تسجيل خروج',
            table_name='auth', record_id=0, ip_address=request.remote_addr, timestamp=now,
        )
    return jsonify({'status': 'logged out'}), 200
