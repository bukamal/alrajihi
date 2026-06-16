from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.database.connection import get_db
from alrajhi_server.decorators import admin_required
import datetime

users_bp = Blueprint('users', __name__)

def _sync_rbac_user_role(db, user_id, role, branch_id=None):
    try:
        role_name = str(role or 'viewer').lower()
        row = db.execute('SELECT id FROM roles WHERE name=?', (role_name,)).fetchone()
        if row:
            db.execute('DELETE FROM user_roles WHERE user_id=?', (str(user_id),))
            cols = {r[1] for r in db.execute('PRAGMA table_info(user_roles)').fetchall()}
            if 'branch_id' in cols:
                db.execute('INSERT OR IGNORE INTO user_roles(user_id, role_id, branch_id) VALUES (?,?,?)', (str(user_id), row['id'], branch_id))
            else:
                db.execute('INSERT OR IGNORE INTO user_roles(user_id, role_id) VALUES (?,?)', (str(user_id), row['id']))
        if branch_id is not None and db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='user_branch_access'").fetchone():
            db.execute('DELETE FROM user_branch_access WHERE user_id=?', (str(user_id),))
            db.execute('INSERT OR IGNORE INTO user_branch_access(user_id, branch_id) VALUES (?,?)', (str(user_id), branch_id))
    except Exception:
        pass


@users_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    db = get_db()
    
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='branches'").fetchone():
        rows = db.execute("SELECT u.id, u.username, u.full_name, u.role, u.branch_id, b.name AS branch_name, u.created_at, u.last_login FROM users u LEFT JOIN branches b ON b.id=u.branch_id").fetchall()
    else:
        rows = db.execute("SELECT id, username, full_name, role, branch_id, created_at, last_login FROM users").fetchall()
    return jsonify([dict(row) for row in rows])

@users_bp.route('/users', methods=['POST'])
@admin_required
def add_user():
    data = request.get_json()
    from alrajhi_server.auth.password import hash_password
    pwd_hash, salt = hash_password(data['password'])
    db = get_db()
    now = datetime.datetime.now().isoformat()
    
    user_cols = {r[1] for r in db.execute('PRAGMA table_info(users)').fetchall()}
    branch_id = data.get('branch_id')
    role = data.get('role', 'viewer')
    if 'branch_id' in user_cols:
        cursor = db.execute('''
            INSERT INTO users (username, password_hash, salt, full_name, role, branch_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['username'], pwd_hash, salt, data.get('full_name', ''), role, branch_id, now))
    else:
        cursor = db.execute('''
            INSERT INTO users (username, password_hash, salt, full_name, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['username'], pwd_hash, salt, data.get('full_name', ''), role, now))
    _sync_rbac_user_role(db, cursor.lastrowid, role, branch_id)
    db.commit()
    return jsonify({'id': cursor.lastrowid}), 201

@users_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    data = request.get_json()
    db = get_db()
    
    user_cols = {r[1] for r in db.execute('PRAGMA table_info(users)').fetchall()}
    branch_id = data.get('branch_id')
    role = data.get('role', 'viewer')
    if 'branch_id' in user_cols:
        db.execute('UPDATE users SET full_name=?, role=?, branch_id=? WHERE id=?',
                   (data.get('full_name', ''), role, branch_id, user_id))
    else:
        db.execute('UPDATE users SET full_name=?, role=? WHERE id=?',
                   (data.get('full_name', ''), role, user_id))
    _sync_rbac_user_role(db, user_id, role, branch_id)
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
    user_id = str(get_jwt_identity())
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    db = get_db()
    user = db.execute('SELECT password_hash, salt FROM users WHERE id=?', (user_id,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    from alrajhi_server.auth.password import verify_password
    if not verify_password(old_password, user['password_hash'], user['salt']):
        return jsonify({'error': 'Invalid old password'}), 401
    from alrajhi_server.auth.password import hash_password
    new_hash, new_salt = hash_password(new_password)
    db.execute('UPDATE users SET password_hash=?, salt=?, force_password_change=0 WHERE id=?',
               (new_hash, new_salt, user_id))
    db.commit()
    return jsonify({'status': 'ok'})


