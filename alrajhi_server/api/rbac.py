from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.database.connection import get_db
from alrajhi_server.decorators import admin_required

rbac_bp = Blueprint('rbac', __name__)


def _is_admin(user_id):
    db = get_db()
    row = db.execute('SELECT role FROM users WHERE id=?', (str(user_id),)).fetchone()
    return bool(row and row['role'] == 'admin')


def _ensure_user_role_compat(user_id):
    db = get_db()
    db.execute('''
        INSERT OR IGNORE INTO user_roles(user_id, role_id)
        SELECT u.id, r.id FROM users u JOIN roles r ON lower(COALESCE(u.role,'user'))=r.name WHERE u.id=?
    ''', (str(user_id),))
    db.commit()


def _user_permissions(user_id):
    db = get_db()
    _ensure_user_role_compat(user_id)
    roles = [r['name'] for r in db.execute('''
        SELECT r.name FROM user_roles ur JOIN roles r ON r.id=ur.role_id
        WHERE ur.user_id=? AND r.is_active=1
    ''', (str(user_id),)).fetchall()]
    if 'admin' in roles:
        return [r['key'] for r in db.execute('SELECT key FROM permissions ORDER BY key').fetchall()]
    return [r['permission_key'] for r in db.execute('''
        SELECT DISTINCT rp.permission_key FROM user_roles ur
        JOIN role_permissions rp ON rp.role_id=ur.role_id AND rp.allowed=1
        JOIN roles r ON r.id=ur.role_id AND r.is_active=1
        WHERE ur.user_id=? ORDER BY rp.permission_key
    ''', (str(user_id),)).fetchall()]


@rbac_bp.route('/rbac/roles', methods=['GET'])
@jwt_required()
def list_roles():
    db = get_db()
    return jsonify([dict(r) for r in db.execute('SELECT * FROM roles ORDER BY is_system DESC, name').fetchall()])


@rbac_bp.route('/rbac/permissions', methods=['GET'])
@jwt_required()
def list_permissions():
    db = get_db()
    return jsonify([dict(r) for r in db.execute('SELECT * FROM permissions ORDER BY module, key').fetchall()])


@rbac_bp.route('/rbac/me', methods=['GET'])
@jwt_required()
def my_permissions():
    user_id = str(get_jwt_identity())
    db = get_db()
    _ensure_user_role_compat(user_id)
    roles = [r['name'] for r in db.execute('''
        SELECT r.name FROM user_roles ur JOIN roles r ON r.id=ur.role_id WHERE ur.user_id=? AND r.is_active=1
    ''', (user_id,)).fetchall()]
    branches = [r['branch_id'] for r in db.execute('SELECT branch_id FROM user_branch_access WHERE user_id=?', (user_id,)).fetchall()]
    return jsonify({'user_id': user_id, 'roles': roles, 'permissions': _user_permissions(user_id), 'branch_ids': branches})


@rbac_bp.route('/rbac/users/<user_id>/roles', methods=['GET'])
@admin_required
def get_user_roles(user_id):
    db = get_db()
    _ensure_user_role_compat(user_id)
    rows = db.execute('''
        SELECT r.* FROM user_roles ur JOIN roles r ON r.id=ur.role_id WHERE ur.user_id=? ORDER BY r.name
    ''', (str(user_id),)).fetchall()
    return jsonify([dict(r) for r in rows])


@rbac_bp.route('/rbac/users/<user_id>/roles', methods=['PUT'])
@admin_required
def set_user_roles(user_id):
    data = request.get_json() or {}
    names = [str(x).strip().lower() for x in data.get('roles', []) if str(x).strip()]
    db = get_db()
    db.execute('DELETE FROM user_roles WHERE user_id=?', (str(user_id),))
    for name in names:
        role = db.execute('SELECT id FROM roles WHERE name=?', (name,)).fetchone()
        if role:
            db.execute('INSERT OR IGNORE INTO user_roles(user_id, role_id) VALUES (?,?)', (str(user_id), role['id']))
    db.commit()
    return jsonify({'status': 'ok', 'user_id': str(user_id), 'roles': names})


@rbac_bp.route('/rbac/roles/<role_name>/permissions', methods=['GET'])
@jwt_required()
def get_role_permissions(role_name):
    db = get_db()
    rows = db.execute('''
        SELECT p.*, COALESCE(rp.allowed,0) AS allowed FROM permissions p
        LEFT JOIN roles r ON r.name=?
        LEFT JOIN role_permissions rp ON rp.role_id=r.id AND rp.permission_key=p.key
        ORDER BY p.module, p.key
    ''', (str(role_name).lower(),)).fetchall()
    return jsonify([dict(r) for r in rows])


@rbac_bp.route('/rbac/roles/<role_name>/permissions', methods=['PUT'])
@admin_required
def set_role_permissions(role_name):
    data = request.get_json() or {}
    keys = [str(x).strip() for x in data.get('permissions', []) if str(x).strip()]
    db = get_db()
    role = db.execute('SELECT id FROM roles WHERE name=?', (str(role_name).strip().lower(),)).fetchone()
    if not role:
        return jsonify({'error': 'Role not found'}), 404
    db.execute('DELETE FROM role_permissions WHERE role_id=?', (role['id'],))
    for key in keys:
        if db.execute('SELECT 1 FROM permissions WHERE key=?', (key,)).fetchone():
            db.execute('INSERT OR REPLACE INTO role_permissions(role_id, permission_key, allowed) VALUES (?,?,1)', (role['id'], key))
    db.commit()
    return jsonify({'status': 'ok', 'role': role_name, 'permissions': keys})


@rbac_bp.route('/rbac/users/<user_id>/branches', methods=['GET'])
@admin_required
def get_user_branches(user_id):
    db = get_db()
    rows = db.execute('''
        SELECT b.* FROM user_branch_access uba JOIN branches b ON b.id=uba.branch_id WHERE uba.user_id=? ORDER BY b.name
    ''', (str(user_id),)).fetchall()
    return jsonify([dict(r) for r in rows])


@rbac_bp.route('/rbac/users/<user_id>/branches', methods=['PUT'])
@admin_required
def set_user_branches(user_id):
    data = request.get_json() or {}
    branch_ids = data.get('branch_ids', [])
    db = get_db()
    db.execute('DELETE FROM user_branch_access WHERE user_id=?', (str(user_id),))
    for bid in branch_ids:
        try:
            db.execute('INSERT OR IGNORE INTO user_branch_access(user_id, branch_id) VALUES (?,?)', (str(user_id), int(bid)))
        except Exception:
            continue
    db.commit()
    return jsonify({'status': 'ok', 'user_id': str(user_id), 'branch_ids': branch_ids})
