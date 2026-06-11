from flask import Blueprint, request, jsonify
from alrajhi_server.database.connection import get_db
from alrajhi_server.decorators import admin_required
import datetime

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/audit_log', methods=['GET'])
@admin_required
def get_audit_log():
    db = get_db()
    limit = request.args.get('limit', 2000, type=int)
    offset = request.args.get('offset', 0, type=int)
    rows = db.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
    total = db.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    return jsonify({'logs': [dict(row) for row in rows], 'total': total})

@audit_bp.route('/audit_log/old', methods=['DELETE'])
@admin_required
def delete_old_audit_logs():
    data = request.get_json()
    days = data.get('days', 90)
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
    db = get_db()
    db.execute('DELETE FROM audit_log WHERE timestamp < ?', (cutoff,))
    db.commit()
    return jsonify({'status': 'ok'})


