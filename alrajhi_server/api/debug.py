# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.database.connection import get_db, DB_PATH
import os


debug_bp = Blueprint('debug', __name__)


def _count(db, table):
    try:
        return int(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    except Exception as exc:
        return {'error': str(exc)}


@debug_bp.route('/debug/status', methods=['GET'])
@jwt_required()
def debug_status():
    db = get_db()
    user_id = get_jwt_identity()
    user = None
    try:
        row = db.execute('SELECT id, username, full_name, role FROM users WHERE id=?', (user_id,)).fetchone()
        user = dict(row) if row else None
    except Exception:
        user = None
    tables = [
        'users', 'items', 'categories', 'customers', 'suppliers', 'invoices',
        'invoice_lines', 'cashboxes', 'bank_accounts', 'vouchers', 'audit_log',
        'sales_returns', 'purchase_returns', 'bom', 'production_orders'
    ]
    return jsonify({
        'api_version': 2,
        'mode': 'server_api',
        'db_path': DB_PATH,
        'db_exists': os.path.exists(DB_PATH),
        'current_user_id': user_id,
        'current_user': user,
        'counts': {t: _count(db, t) for t in tables},
    })
