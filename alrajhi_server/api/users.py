from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from alrajhi_server.decorators import admin_required
from alrajhi_server.repositories.user_repository import UserRepository

users_bp = Blueprint('users', __name__)
_user_repo = UserRepository()


@users_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    return jsonify(_user_repo.list())


@users_bp.route('/users', methods=['POST'])
@admin_required
def add_user():
    data = request.get_json()
    from alrajhi_server.auth.password import hash_password
    pwd_hash, salt = hash_password(data['password'])
    return jsonify({'id': _user_repo.create(data, pwd_hash, salt)}), 201


@users_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    _user_repo.update(user_id, request.get_json())
    return jsonify({'status': 'ok'})


@users_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    if user_id == 1:
        return jsonify({'error': 'Cannot delete admin'}), 400
    _user_repo.delete(user_id)
    return jsonify({'status': 'ok'})


@users_bp.route('/users/change_password', methods=['POST'])
@jwt_required()
def change_password():
    user_id = str(get_jwt_identity())
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    user = _user_repo.get_password_record(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    from alrajhi_server.auth.password import verify_password
    if not verify_password(old_password, user['password_hash'], user['salt']):
        return jsonify({'error': 'Invalid old password'}), 401
    from alrajhi_server.auth.password import hash_password
    new_hash, new_salt = hash_password(new_password)
    _user_repo.update_password(user_id, new_hash, new_salt)
    return jsonify({'status': 'ok'})
