from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.repositories.governance_repository import get_governance_repository
import datetime

enterprise_governance_bp = Blueprint('enterprise_governance', __name__)


def _repo():
    return get_governance_repository()


def _is_admin(user_id):
    return _repo().is_admin(str(user_id))


@enterprise_governance_bp.route('/governance/approval-matrix', methods=['GET'])
@jwt_required()
def approval_matrix():
    return jsonify(_repo().list_active_approval_matrix())


@enterprise_governance_bp.route('/governance/approval-matrix', methods=['POST'])
@jwt_required()
def add_approval_matrix():
    user_id = str(get_jwt_identity())
    if not _is_admin(user_id):
        return jsonify({'error': 'admin_required'}), 403
    matrix_id = _repo().add_approval_matrix(request.get_json() or {})
    return jsonify({'id': matrix_id, 'status': 'ok'})


@enterprise_governance_bp.route('/governance/health', methods=['GET'])
@jwt_required()
def system_health():
    repo = _repo()
    checks = []

    def add(key, status, message, details=None):
        checks.append({'key': key, 'status': status, 'message': message, 'details': details or {}})

    required_tables = ['users', 'invoices', 'approval_requests', 'approval_steps', 'accounts', 'journal_entries', 'journal_lines', 'roles', 'permissions']
    missing = [table for table in required_tables if not repo.table_exists(table)]
    add('database_schema', 'GREEN' if not missing else 'RED', 'Schema OK' if not missing else 'Missing tables', {'missing': missing})

    pending = repo.count_pending_approvals()
    add('pending_approvals', 'GREEN' if pending == 0 else 'YELLOW', f'{pending} pending approval request(s)', {'count': pending})

    unposted = repo.count_approved_unposted_invoices()
    add('unposted_documents', 'GREEN' if unposted == 0 else 'YELLOW', f'{unposted} approved but unposted invoice(s)', {'count': unposted})

    overall = 'GREEN'
    if any(c['status'] == 'RED' for c in checks):
        overall = 'RED'
    elif any(c['status'] == 'YELLOW' for c in checks):
        overall = 'YELLOW'
    return jsonify({'overall': overall, 'checked_at': datetime.datetime.now().isoformat(timespec='seconds'), 'checks': checks})


@enterprise_governance_bp.route('/governance/validate/backup-restore', methods=['POST'])
@jwt_required()
def validate_backup_restore():
    from alrajhi_server.database.migrations import DB_PATH
    return jsonify(_repo().validate_backup_restore(DB_PATH))


@enterprise_governance_bp.route('/governance/validate/stress-smoke', methods=['POST'])
@jwt_required()
def stress_smoke():
    data = request.get_json() or {}
    n = int(data.get('count', 200))
    return jsonify(_repo().run_stress_smoke(n))
