from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.decorators import admin_required
from alrajhi_server.repositories.audit_repository import AuditLogRepository
from alrajhi_server.api.audit_utils import audit_log


audit_bp = Blueprint('audit', __name__)
_audit_repo = AuditLogRepository()


@audit_bp.route('/audit_log', methods=['GET'])
@admin_required
def get_audit_log():
    return jsonify(_audit_repo.list(
        limit=request.args.get('limit', 2000, type=int),
        offset=request.args.get('offset', 0, type=int),
    ))


@audit_bp.route('/audit_log', methods=['POST'])
@jwt_required()
def post_audit_log():
    data = request.get_json() or {}
    audit_log(
        data.get('action') or 'CLIENT_EVENT',
        data.get('entity_type') or data.get('table_name') or 'CLIENT',
        data.get('entity_id') or data.get('record_id'),
        old_values=data.get('old_values'),
        new_values=data.get('new_values'),
        details=data.get('details') or '',
        source=data.get('source') or 'CLIENT',
        audit_scope=data.get('audit_scope') or '',
        permission_key=data.get('permission_key') or '',
        branch_id=data.get('branch_id'),
        event_category=data.get('event_category') or '',
    )
    return jsonify({'status': 'ok'})


@audit_bp.route('/audit_log/old', methods=['DELETE'])
@admin_required
def delete_old_audit_logs():
    data = request.get_json() or {}
    _audit_repo.delete_older_than_days(data.get('days', 90))
    return jsonify({'status': 'ok'})
