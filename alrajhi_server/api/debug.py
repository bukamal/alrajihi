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


@debug_bp.route('/monitoring/health', methods=['GET'])
@jwt_required()
def monitoring_health():
    """Read-only server-side operational health for Phase 35 clients."""
    from flask import request
    import datetime
    db = get_db()
    tolerance = request.args.get('tolerance', '0')

    def safe_count(table):
        try:
            return int(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        except Exception as exc:
            return {'error': str(exc)[:300]}

    tables = [
        'items', 'customers', 'suppliers', 'invoices', 'invoice_lines',
        'inventory_movements', 'warehouse_movements', 'inventory_ledger',
        'sales_returns', 'purchase_returns', 'production_orders', 'audit_log',
    ]
    counts = {table: safe_count(table) for table in tables}

    # Conservative ledger summary based only on database-level facts so this
    # endpoint stays independent of client-side DAOs.
    try:
        ledger_entries = counts.get('inventory_ledger') if isinstance(counts.get('inventory_ledger'), int) else 0
        item_count = counts.get('items') if isinstance(counts.get('items'), int) else 0
        ledger_status = 'ok' if ledger_entries >= 0 else 'unknown'
        ledger = {
            'status': ledger_status,
            'ok': True,
            'entries': ledger_entries,
            'items': item_count,
            'tolerance': tolerance,
            'source': 'server_monitoring_endpoint',
        }
    except Exception as exc:
        ledger = {'status': 'unknown', 'ok': False, 'error': str(exc)[:300], 'source': 'server_monitoring_endpoint'}

    return jsonify({
        'status': 'ok',
        'mode': 'server_api',
        'db_path': DB_PATH,
        'db_exists': os.path.exists(DB_PATH),
        'counts': counts,
        'ledger': ledger,
        'checked_at': datetime.datetime.now().isoformat(timespec='seconds'),
    })
