from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from alrajhi_server.database.connection import get_db

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        db = get_db()
        user = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user or user['role'] != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        return fn(*args, **kwargs)
    return wrapper




def permission_required(permission_key):
    """Require a DB-backed RBAC permission. Admin remains implicitly allowed."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = str(get_jwt_identity())
            db = get_db()
            role = db.execute('SELECT role FROM users WHERE id=?', (user_id,)).fetchone()
            if role and role['role'] == 'admin':
                return fn(*args, **kwargs)
            row = db.execute('''
                SELECT 1 FROM user_roles ur
                JOIN role_permissions rp ON rp.role_id=ur.role_id AND rp.allowed=1
                JOIN roles r ON r.id=ur.role_id AND r.is_active=1
                WHERE ur.user_id=? AND rp.permission_key=? LIMIT 1
            ''', (user_id, str(permission_key))).fetchone()
            if not row:
                return jsonify({'error': 'Permission denied', 'permission': str(permission_key)}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
