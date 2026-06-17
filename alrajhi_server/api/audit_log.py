from flask import Blueprint, request, jsonify
from alrajhi_server.decorators import admin_required
from alrajhi_server.repositories.audit_repository import AuditLogRepository


audit_bp = Blueprint('audit', __name__)
_audit_repo = AuditLogRepository()


@audit_bp.route('/audit_log', methods=['GET'])
@admin_required
def get_audit_log():
    return jsonify(_audit_repo.list(
        limit=request.args.get('limit', 2000, type=int),
        offset=request.args.get('offset', 0, type=int),
    ))


@audit_bp.route('/audit_log/old', methods=['DELETE'])
@admin_required
def delete_old_audit_logs():
    data = request.get_json() or {}
    _audit_repo.delete_older_than_days(data.get('days', 90))
    return jsonify({'status': 'ok'})
