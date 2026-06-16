from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.database.connection import get_db
import datetime, tempfile, shutil, os, sqlite3

enterprise_governance_bp = Blueprint('enterprise_governance', __name__)


def _is_admin(user_id):
    db = get_db()
    row = db.execute('SELECT role FROM users WHERE id=?', (str(user_id),)).fetchone()
    return bool(row and row['role'] == 'admin')


@enterprise_governance_bp.route('/governance/approval-matrix', methods=['GET'])
@jwt_required()
def approval_matrix():
    db = get_db()
    rows = db.execute('SELECT * FROM approval_matrix WHERE is_active=1 ORDER BY document_type, invoice_type, approval_order, id').fetchall()
    return jsonify([dict(r) for r in rows])


@enterprise_governance_bp.route('/governance/approval-matrix', methods=['POST'])
@jwt_required()
def add_approval_matrix():
    user_id = str(get_jwt_identity())
    if not _is_admin(user_id):
        return jsonify({'error': 'admin_required'}), 403
    data = request.get_json() or {}
    db = get_db()
    cur = db.execute("""
        INSERT INTO approval_matrix(document_type, invoice_type, min_amount, max_amount, required_role, required_permission, approval_order, is_active)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        data.get('document_type','INVOICE'), data.get('invoice_type'), str(data.get('min_amount','0')),
        None if data.get('max_amount') in (None, '') else str(data.get('max_amount')),
        data.get('required_role','manager'), data.get('required_permission','approval.approve'),
        int(data.get('approval_order',1)), int(data.get('is_active',1))
    ))
    db.commit()
    return jsonify({'id': cur.lastrowid, 'status': 'ok'})


@enterprise_governance_bp.route('/governance/health', methods=['GET'])
@jwt_required()
def system_health():
    db = get_db()
    checks = []
    def count(sql):
        try: return int(db.execute(sql).fetchone()[0] or 0)
        except Exception: return -1
    def add(key, status, message, details=None):
        checks.append({'key':key,'status':status,'message':message,'details':details or {}})
    missing = []
    for table in ['users','invoices','approval_requests','approval_steps','accounts','journal_entries','journal_lines','roles','permissions']:
        if not db.execute('SELECT 1 FROM sqlite_master WHERE type="table" AND name=?', (table,)).fetchone():
            missing.append(table)
    add('database_schema', 'GREEN' if not missing else 'RED', 'Schema OK' if not missing else 'Missing tables', {'missing': missing})
    pending = count("SELECT COUNT(*) FROM approval_requests WHERE status='PENDING'")
    add('pending_approvals', 'GREEN' if pending == 0 else 'YELLOW', f'{pending} pending approval request(s)', {'count': pending})
    unposted = count("SELECT COUNT(*) FROM invoices WHERE COALESCE(workflow_status,'DRAFT')='APPROVED'")
    add('unposted_documents', 'GREEN' if unposted == 0 else 'YELLOW', f'{unposted} approved but unposted invoice(s)', {'count': unposted})
    overall = 'GREEN'
    if any(c['status']=='RED' for c in checks): overall = 'RED'
    elif any(c['status']=='YELLOW' for c in checks): overall = 'YELLOW'
    return jsonify({'overall': overall, 'checked_at': datetime.datetime.now().isoformat(timespec='seconds'), 'checks': checks})


@enterprise_governance_bp.route('/governance/validate/backup-restore', methods=['POST'])
@jwt_required()
def validate_backup_restore():
    db = get_db()
    from alrajhi_server.database.migrations import DB_PATH
    db_path = DB_PATH
    tmp = tempfile.mkdtemp(prefix='alrajhi_srv_restore_')
    try:
        backup = os.path.join(tmp, 'backup.sqlite')
        shutil.copy2(db_path, backup)
        test = sqlite3.connect(backup)
        integrity = test.execute('PRAGMA integrity_check').fetchone()[0]
        tables = test.execute('SELECT COUNT(*) FROM sqlite_master WHERE type="table"').fetchone()[0]
        test.close()
        return jsonify({'status': 'PASSED' if integrity == 'ok' else 'FAILED', 'integrity_check': integrity, 'tables': tables})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@enterprise_governance_bp.route('/governance/validate/stress-smoke', methods=['POST'])
@jwt_required()
def stress_smoke():
    data = request.get_json() or {}
    n = int(data.get('count', 200))
    db = get_db()
    db.execute('CREATE TABLE IF NOT EXISTS stress_probe(id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, amount TEXT, created_at TEXT)')
    for i in range(n):
        db.execute('INSERT INTO stress_probe(ref, amount, created_at) VALUES (?,?,?)', (f'STRESS-{i}', str(i), datetime.datetime.now().isoformat(timespec='seconds')))
    total = db.execute('SELECT COUNT(*) FROM stress_probe').fetchone()[0]
    db.commit()
    return jsonify({'status': 'PASSED', 'inserted': n, 'total_probe_rows': total})
