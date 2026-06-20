from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.repositories.rbac_repository import get_rbac_repository
from alrajhi_server.decorators import admin_required

rbac_bp = Blueprint('rbac', __name__)


def _repo():
    return get_rbac_repository()


def _is_admin(user_id):
    return _repo().is_admin(str(user_id))


def _ensure_user_role_compat(user_id):
    _repo().ensure_user_role_compat(str(user_id))


def _user_permissions(user_id):
    return _repo().list_user_permissions(str(user_id))


@rbac_bp.route('/rbac/roles', methods=['GET'])
@jwt_required()
def list_roles():
    return jsonify(_repo().list_roles())


@rbac_bp.route('/rbac/permissions', methods=['GET'])
@jwt_required()
def list_permissions():
    return jsonify(_repo().list_permissions())


@rbac_bp.route('/rbac/me', methods=['GET'])
@jwt_required()
def my_permissions():
    user_id = str(get_jwt_identity())
    repo = _repo()
    repo.ensure_user_role_compat(user_id)
    permissions = repo.list_user_permissions(user_id)
    branch_ids = repo.list_user_branch_ids(user_id)
    return jsonify({
        'user_id': user_id,
        'roles': repo.list_user_role_names(user_id),
        'permissions': permissions,
        'branch_ids': branch_ids,
        'can_view_all_branches': repo.is_admin(user_id) or 'branches.view_all' in set(permissions),
        'branch_scope_mode': 'all' if (repo.is_admin(user_id) or 'branches.view_all' in set(permissions)) else 'restricted',
    })


@rbac_bp.route('/rbac/users/<user_id>/roles', methods=['GET'])
@admin_required
def get_user_roles(user_id):
    return jsonify(_repo().list_user_roles(str(user_id)))


@rbac_bp.route('/rbac/users/<user_id>/roles', methods=['PUT'])
@admin_required
def set_user_roles(user_id):
    data = request.get_json() or {}
    names = [str(x).strip().lower() for x in data.get('roles', []) if str(x).strip()]
    _repo().replace_user_roles(str(user_id), names)
    return jsonify({'status': 'ok', 'user_id': str(user_id), 'roles': names})


@rbac_bp.route('/rbac/roles/<role_name>/permissions', methods=['GET'])
@jwt_required()
def get_role_permissions(role_name):
    return jsonify(_repo().list_role_permissions(role_name))


@rbac_bp.route('/rbac/roles/<role_name>/permissions', methods=['PUT'])
@admin_required
def set_role_permissions(role_name):
    data = request.get_json() or {}
    keys = [str(x).strip() for x in data.get('permissions', []) if str(x).strip()]
    if not _repo().replace_role_permissions(role_name, keys):
        return jsonify({'error': 'Role not found'}), 404
    return jsonify({'status': 'ok', 'role': role_name, 'permissions': keys})


@rbac_bp.route('/rbac/users/<user_id>/branches', methods=['GET'])
@admin_required
def get_user_branches(user_id):
    return jsonify(_repo().list_user_branches(str(user_id)))


@rbac_bp.route('/rbac/users/<user_id>/branches', methods=['PUT'])
@admin_required
def set_user_branches(user_id):
    data = request.get_json() or {}
    branch_ids = data.get('branch_ids', [])
    _repo().replace_user_branches(str(user_id), branch_ids)
    return jsonify({'status': 'ok', 'user_id': str(user_id), 'branch_ids': branch_ids})
