from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.api.audit_utils import audit_log
from alrajhi_server.database.connection import get_db
import datetime
from decimal import Decimal

def _has_permission(db, user_id, permission_key):
    user_id = str(user_id)
    role = db.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
    if role and role['role'] == 'admin':
        return True
    db.execute("""
        INSERT OR IGNORE INTO user_roles(user_id, role_id)
        SELECT u.id, r.id FROM users u JOIN roles r ON lower(COALESCE(u.role,'user'))=r.name WHERE u.id=?
    """, (user_id,))
    row = db.execute("""
        SELECT 1 FROM user_roles ur
        JOIN role_permissions rp ON rp.role_id=ur.role_id AND rp.allowed=1
        JOIN roles r ON r.id=ur.role_id AND r.is_active=1
        WHERE ur.user_id=? AND rp.permission_key=? LIMIT 1
    """, (user_id, permission_key)).fetchone()
    return row is not None


invoices_bp = Blueprint('invoices', __name__)


def _invoice_has_vouchers(db, invoice_id, user_id):
    row = db.execute("SELECT COUNT(*) AS cnt FROM vouchers WHERE invoice_id=? AND user_id=?", (invoice_id, user_id)).fetchone()
    return bool(row and row['cnt'])


def _invoice_has_returns(db, invoice_id, user_id):
    row = db.execute("""
        SELECT (
            SELECT COUNT(*) FROM sales_returns WHERE original_invoice_id=? AND user_id=? AND deleted_at IS NULL
        ) + (
            SELECT COUNT(*) FROM purchase_returns WHERE original_invoice_id=? AND user_id=? AND deleted_at IS NULL
        ) AS cnt
    """, (invoice_id, user_id, invoice_id, user_id)).fetchone()
    return bool(row and row['cnt'])


def _update_item_quantity(db, item_id, user_id):
    row = db.execute('''
        SELECT SUM(CASE
            WHEN movement_type IN ('opening','purchase','adjustment','production_out','sales_return') THEN CAST(quantity AS REAL)
            WHEN movement_type IN ('sale','production_consume','purchase_return') THEN -CAST(quantity AS REAL)
            ELSE 0 END) AS total_qty
        FROM inventory_movements
        WHERE item_id=? AND user_id=?
    ''', (item_id, user_id)).fetchone()
    qty = Decimal(str(row['total_qty'])) if row and row['total_qty'] is not None else Decimal('0')
    db.execute("UPDATE items SET quantity=? WHERE id=? AND user_id=?", (str(qty), item_id, user_id))


def _recalculate_average_cost(db, item_id, user_id):
    row = db.execute('''
        SELECT SUM(CAST(quantity AS REAL)) AS total_qty,
               SUM(CAST(quantity AS REAL) * CAST(unit_cost AS REAL)) AS total_cost
        FROM inventory_movements
        WHERE item_id=? AND user_id=? AND movement_type IN ('opening','purchase','adjustment','production_out')
    ''', (item_id, user_id)).fetchone()
    total_qty = Decimal(str(row['total_qty'])) if row and row['total_qty'] is not None else Decimal('0')
    total_cost = Decimal(str(row['total_cost'])) if row and row['total_cost'] is not None else Decimal('0')
    avg = total_cost / total_qty if total_qty > 0 else Decimal('0')
    db.execute("UPDATE items SET average_cost=? WHERE id=? AND user_id=?", (str(avg), item_id, user_id))


def _available_item_quantity(db, item_id, user_id):
    row = db.execute('''
        SELECT SUM(CASE
            WHEN movement_type IN ('opening','purchase','adjustment','production_out','sales_return') THEN CAST(quantity AS REAL)
            WHEN movement_type IN ('sale','production_consume','purchase_return') THEN -CAST(quantity AS REAL)
            ELSE 0 END) AS total_qty
        FROM inventory_movements
        WHERE item_id=? AND user_id=?
    ''', (item_id, user_id)).fetchone()
    return Decimal(str(row['total_qty'])) if row and row['total_qty'] is not None else Decimal('0')


def _assert_sale_stock_available(db, user_id, lines):
    required_by_item = {}
    for line in lines or []:
        item_id = line['item_id']
        conv_factor = Decimal(str(line.get('conversion_factor', 1) or 1))
        if conv_factor <= 0:
            conv_factor = Decimal('1')
        qty = Decimal(str(line.get('quantity', 0) or 0))
        base_qty = Decimal(str(line.get('base_qty', line.get('quantity_in_base', qty * conv_factor)) or 0))
        required_by_item[item_id] = required_by_item.get(item_id, Decimal('0')) + base_qty
    for item_id, required_qty in required_by_item.items():
        available = _available_item_quantity(db, item_id, user_id)
        if required_qty > available:
            item = db.execute("SELECT name FROM items WHERE id=? AND user_id=?", (item_id, user_id)).fetchone()
            name = item['name'] if item and 'name' in item.keys() else str(item_id)
            raise ValueError(f"الكمية غير كافية للمادة {name}: المطلوب {required_qty} والمتاح {available}")



def _setting(db, key, default=''):
    try:
        row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row['value'] if row and row['value'] is not None else default
    except Exception:
        return default


def _setting_bool(db, key, default=False):
    value = str(_setting(db, key, 'true' if default else 'false')).strip().lower()
    return value in ('1', 'true', 'yes', 'y', 'on', 'نعم')


def _workflow_status(invoice):
    value = str((invoice or {}).get('workflow_status') or (invoice or {}).get('status') or 'DRAFT').strip().upper()
    return value if value in {'DRAFT', 'SUBMITTED', 'APPROVED', 'POSTED', 'CANCELLED'} else 'DRAFT'


def _workflow_threshold(db, inv_type):
    key = 'workflow/sales_approval_threshold' if inv_type == 'sale' else 'workflow/purchase_approval_threshold'
    try:
        return Decimal(str(_setting(db, key, '0') or '0'))
    except Exception:
        return Decimal('0')


def _initial_workflow_status(db, inv_type, total):
    try:
        amount = Decimal(str(total or '0'))
    except Exception:
        amount = Decimal('0')
    threshold = _workflow_threshold(db, inv_type)
    return 'SUBMITTED' if threshold > 0 and amount >= threshold else 'DRAFT'


def _assert_workflow_allowed(db, invoice, operation):
    status = _workflow_status(dict(invoice) if invoice else {})
    default_edit = {'DRAFT': True, 'SUBMITTED': True, 'APPROVED': False, 'POSTED': False, 'CANCELLED': False}
    default_delete = dict(default_edit)
    if operation == 'edit':
        allowed = _setting_bool(db, f'workflow/allow_edit_{status.lower()}', default_edit.get(status, False))
    else:
        allowed = _setting_bool(db, f'workflow/allow_delete_{status.lower()}', default_delete.get(status, False))
    if not allowed:
        raise ValueError(f'لا يمكن {"تعديل" if operation == "edit" else "حذف"} المستند في حالة {status} حسب سياسة سير العمل.')


def _ensure_workflow_schema(db):
    cols = {r[1] for r in db.execute('PRAGMA table_info(invoices)').fetchall()}
    for name, ddl in {
        'workflow_status': "TEXT DEFAULT 'DRAFT'",
        'submitted_at': 'TEXT', 'submitted_by': 'TEXT',
        'approved_at': 'TEXT', 'approved_by': 'TEXT',
        'posted_at': 'TEXT', 'posted_by': 'TEXT',
        'cancelled_at': 'TEXT', 'cancelled_by': 'TEXT', 'deleted_by': 'TEXT',
    }.items():
        if name not in cols:
            db.execute(f'ALTER TABLE invoices ADD COLUMN {name} {ddl}')
    db.execute("""
        CREATE TABLE IF NOT EXISTS workflow_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            action TEXT NOT NULL,
            username TEXT,
            user_id TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    db.execute('CREATE INDEX IF NOT EXISTS idx_workflow_events_entity ON workflow_events(entity_type, entity_id, created_at)')
    cols_after = {r[1] for r in db.execute('PRAGMA table_info(invoices)').fetchall()}
    if 'workflow_status' in cols_after:
        db.execute('CREATE INDEX IF NOT EXISTS idx_invoices_workflow_status ON invoices(workflow_status)')


def _apply_invoice_financial_effect(db, invoice, sign):
    total = Decimal(str(invoice.get('total', 0)))
    paid = Decimal(str(invoice.get('paid', 0)))
    net = total - paid
    if invoice.get('type') == 'sale' and invoice.get('customer_id'):
        db.execute("UPDATE customers SET balance = CAST(COALESCE(balance, '0') AS TEXT) + ? WHERE id=?", (str(sign * net), invoice['customer_id']))
    elif invoice.get('type') == 'purchase' and invoice.get('supplier_id'):
        db.execute("UPDATE suppliers SET balance = CAST(COALESCE(balance, '0') AS TEXT) + ? WHERE id=?", (str(sign * net), invoice['supplier_id']))
    if paid > 0:
        cash_delta = paid if invoice.get('type') == 'sale' else -paid
        db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS TEXT) + ? WHERE id=?", (str(sign * cash_delta), invoice['user_id']))






def _ensure_approval_accounting_schema(db):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS approval_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, entity_type TEXT NOT NULL, entity_id INTEGER NOT NULL, amount TEXT DEFAULT '0', threshold_amount TEXT DEFAULT '0', status TEXT NOT NULL DEFAULT 'PENDING', requested_by TEXT, requested_at TEXT, decided_by TEXT, decided_at TEXT, decision_notes TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT, UNIQUE(entity_type, entity_id));
        CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests(status, entity_type);
        CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, type TEXT NOT NULL, parent_id INTEGER, is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS journal_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, entry_no TEXT UNIQUE, entry_date TEXT NOT NULL, source_type TEXT, source_id INTEGER, description TEXT, status TEXT DEFAULT 'POSTED', created_by TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(source_type, source_id));
        CREATE TABLE IF NOT EXISTS journal_lines (id INTEGER PRIMARY KEY AUTOINCREMENT, journal_entry_id INTEGER NOT NULL, account_id INTEGER NOT NULL, debit TEXT DEFAULT '0', credit TEXT DEFAULT '0', memo TEXT);
        CREATE INDEX IF NOT EXISTS idx_journal_entries_source ON journal_entries(source_type, source_id);
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1000','Cash / صندوق','ASSET');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1100','Accounts Receivable / ذمم العملاء','ASSET');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1200','Inventory / مخزون','ASSET');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('2000','Accounts Payable / ذمم الموردين','LIABILITY');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('4000','Sales Revenue / إيرادات المبيعات','REVENUE');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('5000','Purchases / مشتريات','EXPENSE');
    """)

def _account_id(db, code):
    row = db.execute('SELECT id FROM accounts WHERE code=?', (code,)).fetchone()
    return row['id'] if row else None

def _ensure_approval_request(db, invoice, user_id, notes=''):
    _ensure_approval_accounting_schema(db)
    threshold = _workflow_threshold(db, invoice.get('type'))
    amount = Decimal(str(invoice.get('total', 0) or 0))
    if threshold <= 0 or amount < threshold:
        return
    now = datetime.datetime.now().isoformat(timespec='seconds')
    db.execute("""INSERT OR IGNORE INTO approval_requests(entity_type, entity_id, amount, threshold_amount, status, requested_by, requested_at, created_at, updated_at, decision_notes)
                  VALUES ('INVOICE', ?, ?, ?, 'PENDING', ?, ?, ?, ?, ?)""", (invoice['id'], str(amount), str(threshold), user_id, now, now, now, notes or ''))

def _approve_request(db, invoice, user_id, notes=''):
    _ensure_approval_request(db, invoice, user_id, notes)
    now = datetime.datetime.now().isoformat(timespec='seconds')
    db.execute("UPDATE approval_requests SET status='APPROVED', decided_by=?, decided_at=?, decision_notes=?, updated_at=? WHERE entity_type='INVOICE' AND entity_id=?", (user_id, now, notes or 'Approved', now, invoice['id']))

def _post_accounting_invoice(db, invoice, user_id, notes=''):
    _ensure_approval_accounting_schema(db)
    existing = db.execute("SELECT id FROM journal_entries WHERE source_type='INVOICE' AND source_id=?", (invoice['id'],)).fetchone()
    if existing:
        return existing['id']
    total = Decimal(str(invoice.get('total', 0) or 0)); paid = Decimal(str(invoice.get('paid', 0) or 0)); unpaid = total - paid
    if total <= 0:
        return None
    row = db.execute('SELECT COALESCE(MAX(id),0)+1 AS n FROM journal_entries').fetchone(); entry_no = f"JE-{int(row['n']):06d}"
    now = datetime.datetime.now().isoformat(timespec='seconds')
    cur = db.execute("INSERT INTO journal_entries(entry_no, entry_date, source_type, source_id, description, status, created_by, created_at) VALUES (?, ?, 'INVOICE', ?, ?, 'POSTED', ?, ?)", (entry_no, invoice.get('date') or now[:10], invoice['id'], notes or 'Invoice posting', user_id, now))
    je_id = cur.lastrowid; lines=[]
    if invoice.get('type') == 'sale':
        if paid > 0: lines.append(('1000', paid, Decimal('0'), 'قبض من فاتورة بيع'))
        if unpaid > 0: lines.append(('1100', unpaid, Decimal('0'), 'ذمم عميل'))
        lines.append(('4000', Decimal('0'), total, 'إيراد مبيعات'))
    elif invoice.get('type') == 'purchase':
        lines.append(('5000', total, Decimal('0'), 'مشتريات'))
        if paid > 0: lines.append(('1000', Decimal('0'), paid, 'دفع شراء'))
        if unpaid > 0: lines.append(('2000', Decimal('0'), unpaid, 'ذمم مورد'))
    if sum(x[1] for x in lines) != sum(x[2] for x in lines):
        raise ValueError('القيد المحاسبي غير متوازن')
    for code, debit, credit, memo in lines:
        db.execute('INSERT INTO journal_lines(journal_entry_id, account_id, debit, credit, memo) VALUES (?,?,?,?,?)', (je_id, _account_id(db, code), str(debit), str(credit), memo))
    return je_id

def _ensure_inventory_ledger_table(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS inventory_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            warehouse_id INTEGER,
            movement_type TEXT NOT NULL,
            direction TEXT NOT NULL CHECK(direction IN ('in','out','neutral')),
            quantity TEXT NOT NULL,
            unit_cost TEXT,
            total_cost TEXT,
            reference_type TEXT,
            reference_id INTEGER,
            source_table TEXT,
            source_id INTEGER,
            notes TEXT,
            movement_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)


def _post_inventory_ledger_entry(db, user_id, item_id, warehouse_id, movement_type, direction,
                                 quantity, unit_cost, invoice_id, notes=''):
    if direction not in {'in', 'out', 'neutral'}:
        return
    _ensure_inventory_ledger_table(db)
    qty = abs(Decimal(str(quantity or '0')))
    cost = Decimal(str(unit_cost or '0'))
    total_cost = qty * cost
    db.execute('''
        INSERT INTO inventory_ledger (
            user_id, item_id, warehouse_id, movement_type, direction, quantity,
            unit_cost, total_cost, reference_type, reference_id, source_table,
            source_id, notes, movement_date
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        user_id, item_id, warehouse_id, movement_type, direction, str(qty),
        str(cost), str(total_cost), 'invoice', invoice_id, 'invoices',
        invoice_id, notes, datetime.datetime.now().isoformat()
    ))


def _post_invoice_ledger_entries(db, user_id, invoice_id, invoice_data, lines=None):
    inv_type = invoice_data.get('type')
    warehouse_id = invoice_data.get('warehouse_id')
    source_lines = lines if lines is not None else invoice_data.get('lines', [])
    for line in source_lines or []:
        item_id = line['item_id'] if isinstance(line, dict) else line['item_id']
        qty = line.get('base_qty', line.get('quantity_in_base', line.get('quantity', 0))) if isinstance(line, dict) else line['quantity_in_base']
        unit_cost = line.get('unit_price', line.get('unit_cost', 0)) if isinstance(line, dict) else line['unit_cost']
        if inv_type == 'purchase':
            _post_inventory_ledger_entry(
                db, user_id, item_id, warehouse_id, 'invoice_purchase_in', 'in', qty, unit_cost,
                invoice_id, 'استلام فاتورة شراء إلى دفتر المخزون'
            )
        elif inv_type == 'sale':
            _post_inventory_ledger_entry(
                db, user_id, item_id, warehouse_id, 'invoice_sale_out', 'out', qty, unit_cost,
                invoice_id, 'صرف فاتورة بيع من دفتر المخزون'
            )


def _post_invoice_ledger_reversal(db, user_id, invoice_id, invoice_data, lines=None):
    inv_type = invoice_data.get('type')
    warehouse_id = invoice_data.get('warehouse_id')
    source_lines = lines if lines is not None else invoice_data.get('lines', [])
    for line in source_lines or []:
        item_id = line['item_id'] if isinstance(line, dict) else line['item_id']
        qty = line.get('base_qty', line.get('quantity_in_base', line.get('quantity', 0))) if isinstance(line, dict) else line['quantity_in_base']
        unit_cost = line.get('unit_price', line.get('unit_cost', 0)) if isinstance(line, dict) else line['unit_cost']
        if inv_type == 'purchase':
            _post_inventory_ledger_entry(
                db, user_id, item_id, warehouse_id, 'invoice_purchase_reversal', 'out', qty, unit_cost,
                invoice_id, 'عكس دفتر مخزون فاتورة شراء'
            )
        elif inv_type == 'sale':
            _post_inventory_ledger_entry(
                db, user_id, item_id, warehouse_id, 'invoice_sale_reversal', 'in', qty, unit_cost,
                invoice_id, 'عكس دفتر مخزون فاتورة بيع'
            )

@invoices_bp.route('/invoices', methods=['GET'])
@jwt_required()
def get_invoices():
    user_id = get_jwt_identity()
    inv_type = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)
    search = (request.args.get('search') or '').strip()
    customer_id = request.args.get('customer_id', type=int)
    supplier_id = request.args.get('supplier_id', type=int)
    db = get_db()
    count_query = "SELECT COUNT(*) FROM invoices i WHERE i.user_id = ? AND i.deleted_at IS NULL"
    count_params = [user_id]
    query = """
        SELECT i.*, c.name as customer_name, s.name as supplier_name
        FROM invoices i
        LEFT JOIN customers c ON i.customer_id = c.id
        LEFT JOIN suppliers s ON i.supplier_id = s.id
        WHERE i.user_id = ? AND i.deleted_at IS NULL
    """
    params = [user_id]
    if inv_type in ('sale', 'purchase'):
        count_query += " AND i.type = ?"
        count_params.append(inv_type)
        query += " AND i.type = ?"
        params.append(inv_type)
    if start_date:
        count_query += " AND i.date >= ?"
        count_params.append(start_date)
        query += " AND i.date >= ?"
        params.append(start_date)
    if end_date:
        count_query += " AND i.date <= ?"
        count_params.append(end_date)
        query += " AND i.date <= ?"
        params.append(end_date)
    if customer_id:
        count_query += " AND i.customer_id = ?"
        count_params.append(customer_id)
        query += " AND i.customer_id = ?"
        params.append(customer_id)
    if supplier_id:
        count_query += " AND i.supplier_id = ?"
        count_params.append(supplier_id)
        query += " AND i.supplier_id = ?"
        params.append(supplier_id)
    if search:
        like = f"%{search}%"
        count_query += """ AND (
            i.reference LIKE ? OR i.notes LIKE ?
            OR EXISTS (SELECT 1 FROM customers c2 WHERE c2.id=i.customer_id AND c2.name LIKE ?)
            OR EXISTS (SELECT 1 FROM suppliers s2 WHERE s2.id=i.supplier_id AND s2.name LIKE ?)
        )"""
        count_params.extend([like, like, like, like])
        query += " AND (i.reference LIKE ? OR i.notes LIKE ? OR c.name LIKE ? OR s.name LIKE ?)"
        params.extend([like, like, like, like])
    total = db.execute(count_query, count_params).fetchone()[0]
    query += " ORDER BY i.id DESC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    if offset is not None:
        query += " OFFSET ?"
        params.append(offset)
    rows = db.execute(query, params).fetchall()
    return jsonify({'invoices': [dict(row) for row in rows], 'total': total})


@invoices_bp.route('/invoices/next-reference', methods=['GET'])
@jwt_required()
def next_invoice_reference():
    user_id = get_jwt_identity()
    inv_type = request.args.get('type') or request.args.get('inv_type') or 'sale'
    inv_type = 'purchase' if inv_type == 'purchase' else 'sale'
    year = datetime.datetime.now().strftime('%Y')
    prefix = f"{inv_type[:3].upper()}-{year}-"
    db = get_db()
    row = db.execute(
        "SELECT MAX(reference) AS max_ref FROM invoices WHERE reference LIKE ? AND user_id=?",
        (prefix + '%', user_id)
    ).fetchone()
    max_ref = row['max_ref'] if row else None
    if max_ref:
        try:
            num = int(str(max_ref).split('-')[-1]) + 1
        except Exception:
            num = 1
    else:
        num = 1
    return jsonify({'reference': f'{prefix}{num:04d}'})

@invoices_bp.route('/invoices/<int:invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice(invoice_id):
    user_id = get_jwt_identity()
    db = get_db()
    row = db.execute("SELECT * FROM invoices WHERE id=? AND user_id=?", (invoice_id, user_id)).fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    inv = dict(row)
    lines = db.execute("SELECT * FROM invoice_lines WHERE invoice_id=?", (invoice_id,)).fetchall()
    inv['lines'] = [dict(line) for line in lines]
    return jsonify(inv)


@invoices_bp.route('/invoices/<int:invoice_id>/workflow', methods=['POST'])
@jwt_required()
def transition_invoice_workflow(invoice_id):
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    new_status = str(data.get('status') or '').strip().upper()
    if new_status not in {'DRAFT', 'SUBMITTED', 'APPROVED', 'POSTED', 'CANCELLED'}:
        return jsonify({'error': 'حالة سير العمل غير صالحة'}), 400
    action = str(data.get('action') or new_status.lower()).strip() or new_status.lower()
    notes = str(data.get('notes') or '')
    db = get_db()
    _ensure_workflow_schema(db)
    row = db.execute("SELECT * FROM invoices WHERE id=? AND user_id=? AND deleted_at IS NULL", (invoice_id, user_id)).fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    old_status = _workflow_status(dict(row))
    now = datetime.datetime.now().isoformat(timespec='seconds')
    if action == 'submit':
        _ensure_approval_request(db, dict(row), user_id, notes)
    if action == 'approve':
        if not _has_permission(db, user_id, 'approval.approve'):
            return jsonify({'error': 'Permission denied', 'permission': 'approval.approve'}), 403
        _approve_request(db, dict(row), user_id, notes)
    if action == 'reject':
        if not _has_permission(db, user_id, 'approval.reject'):
            return jsonify({'error': 'Permission denied', 'permission': 'approval.reject'}), 403
    if action == 'post' and not _has_permission(db, user_id, 'accounting.post'):
        return jsonify({'error': 'Permission denied', 'permission': 'accounting.post'}), 403
    if action == 'post' and old_status != 'APPROVED':
        return jsonify({'error': 'لا يمكن الترحيل قبل الاعتماد'}), 400
    if action == 'post':
        _post_accounting_invoice(db, dict(row), user_id, notes)
    updates = {'workflow_status': new_status}
    if new_status == 'SUBMITTED':
        updates.update({'submitted_at': now, 'submitted_by': user_id})
    elif new_status == 'APPROVED':
        updates.update({'approved_at': now, 'approved_by': user_id})
    elif new_status == 'POSTED':
        updates.update({'posted_at': now, 'posted_by': user_id})
    elif new_status == 'CANCELLED':
        updates.update({'cancelled_at': now, 'cancelled_by': user_id})
    set_sql = ', '.join([f'{k}=?' for k in updates])
    db.execute(f"UPDATE invoices SET {set_sql} WHERE id=? AND user_id=?", list(updates.values()) + [invoice_id, user_id])
    db.execute('''
        INSERT INTO workflow_events(entity_type, entity_id, old_status, new_status, action, username, user_id, notes, created_at)
        VALUES (?,?,?,?,?,?,?,?,?)
    ''', ('INVOICE', invoice_id, old_status, new_status, action, user_id, user_id, notes, now))
    audit_log(action.upper(), 'INVOICE_WORKFLOW', invoice_id,
              old_values={'workflow_status': old_status}, new_values={'workflow_status': new_status}, details=notes or action)
    db.commit()
    return jsonify({'id': invoice_id, 'workflow_status': new_status, 'old_status': old_status})

@invoices_bp.route('/invoices', methods=['POST'])
@jwt_required()
def add_invoice():
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    _ensure_workflow_schema(db)
    if not data.get('workflow_status'):
        data['workflow_status'] = _initial_workflow_status(db, data.get('type'), data.get('total'))
    if data.get('workflow_status') == 'SUBMITTED' and not data.get('submitted_at'):
        data['submitted_at'] = datetime.datetime.now().isoformat(timespec='seconds')
    if data.get('type') == 'sale':
        try:
            _assert_sale_stock_available(db, user_id, data.get('lines', []))
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    db.execute("BEGIN TRANSACTION")
    try:
        # إدراج الفاتورة
        cursor = db.execute('''
            INSERT INTO invoices (user_id, type, customer_id, supplier_id, date, reference, notes, total, paid, status, workflow_status, submitted_at, exchange_rate_to_usd, original_currency, warehouse_id, branch_id, cashbox_id, bank_account_id, payment_method, shift_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            user_id, data['type'], data.get('customer_id'), data.get('supplier_id'),
            data['date'], data.get('reference', ''), data.get('notes', ''),
            str(data['total']), str(data['paid_amount']), 'active',
            data.get('workflow_status', 'DRAFT'), data.get('submitted_at'),
            data.get('exchange_rate_to_usd', 1.0), data.get('original_currency', 'USD'),
            data.get('warehouse_id'), data.get('branch_id'), data.get('cashbox_id'),
            data.get('bank_account_id'), data.get('payment_method', 'cash'), data.get('shift_id')
        ))
        invoice_id = cursor.lastrowid
        # Phase154: create pending approval request immediately when the invoice
        # starts as SUBMITTED because it exceeded the configured threshold.
        if data.get('workflow_status') == 'SUBMITTED':
            _ensure_approval_request(db, {
                'id': invoice_id,
                'type': data.get('type'),
                'total': data.get('total'),
            }, user_id, 'طلب اعتماد تلقائي بسبب تجاوز حد الاعتماد')
        # إدراج البنود وتسجيل حركات المخزون (محاكاة منطق العميل)
        for line in data['lines']:
            conv_factor = Decimal(str(line.get('conversion_factor', 1) or 1))
            if conv_factor <= 0:
                conv_factor = Decimal('1')
            qty = Decimal(str(line.get('quantity', 0) or 0))
            base_qty = Decimal(str(line.get('base_qty', line.get('quantity_in_base', qty * conv_factor)) or 0))
            unit_cost = Decimal(str(line['unit_price']))
            db.execute('''
                INSERT INTO invoice_lines (invoice_id, item_id, quantity, unit_price, total, unit, quantity_in_base, unit_cost, cost_amount, conversion_factor)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            ''', (
                invoice_id, line['item_id'], str(line['quantity']), str(unit_cost), str(line['total']),
                line.get('unit', ''), str(base_qty), str(unit_cost), '0', str(conv_factor)
            ))
            if data['type'] == 'purchase':
                unit_cost_base = unit_cost / conv_factor
                # تسجيل حركة شراء
                db.execute('''
                    INSERT INTO inventory_movements (item_id, user_id, movement_type, quantity, unit_cost, reference_id, movement_date)
                    VALUES (?,?,?,?,?,?,?)
                ''', (line['item_id'], user_id, 'purchase', str(base_qty), str(unit_cost_base), invoice_id, datetime.datetime.now().isoformat()))
                cost_amt = unit_cost_base * base_qty
                db.execute("UPDATE invoice_lines SET cost_amount=? WHERE invoice_id=? AND item_id=?", (str(cost_amt), invoice_id, line['item_id']))
            else:  # sale
                item = db.execute("SELECT CAST(average_cost AS TEXT) as avg_cost FROM items WHERE id=?", (line['item_id'],)).fetchone()
                avg_cost = Decimal(str(item['avg_cost'])) if item else Decimal('0')
                cost_amt = base_qty * avg_cost
                db.execute("UPDATE invoice_lines SET cost_amount=? WHERE invoice_id=? AND item_id=?", (str(cost_amt), invoice_id, line['item_id']))
                db.execute('''
                    INSERT INTO inventory_movements (item_id, user_id, movement_type, quantity, unit_cost, reference_id, movement_date)
                    VALUES (?,?,?,?,?,?,?)
                ''', (line['item_id'], user_id, 'sale', str(base_qty), str(unit_cost), invoice_id, datetime.datetime.now().isoformat()))
        for item_id in {line['item_id'] for line in data['lines']}:
            _update_item_quantity(db, item_id, user_id)
            _recalculate_average_cost(db, item_id, user_id)
        _post_invoice_ledger_entries(db, user_id, invoice_id, data)
        _apply_invoice_financial_effect(db, {
            'user_id': user_id, 'type': data['type'], 'customer_id': data.get('customer_id'),
            'supplier_id': data.get('supplier_id'), 'total': data['total'],
            'paid': data.get('paid_amount', 0)
        }, Decimal('1'))
        audit_log('CREATE', 'SALE_INVOICE' if data.get('type') == 'sale' else 'PURCHASE_INVOICE', invoice_id, new_values=data, details='إنشاء فاتورة')
        db.execute("COMMIT")
        return jsonify({'id': invoice_id}), 201
    except Exception as e:
        db.execute("ROLLBACK")
        return jsonify({'error': str(e)}), 500

@invoices_bp.route('/invoices/<int:invoice_id>', methods=['PUT'])
@jwt_required()
def update_invoice(invoice_id):
    # تحديث محافظ على رقم الفاتورة بدل soft-delete ثم إنشاء سجل جديد.
    user_id = get_jwt_identity()
    data = request.get_json()
    db = get_db()
    _ensure_workflow_schema(db)
    old_invoice = db.execute("SELECT * FROM invoices WHERE id=? AND user_id=? AND deleted_at IS NULL", (invoice_id, user_id)).fetchone()
    if not old_invoice:
        return jsonify({'error': 'Not found'}), 404
    try:
        _assert_workflow_allowed(db, old_invoice, 'edit')
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    if _invoice_has_vouchers(db, invoice_id, user_id):
        return jsonify({'error': 'لا يمكن تعديل فاتورة مرتبطة بسندات. احذف أو عدّل السندات أولاً.'}), 400
    if _invoice_has_returns(db, invoice_id, user_id):
        return jsonify({'error': 'لا يمكن تعديل فاتورة مرتبطة بمرتجعات. ألغِ المرتجعات أولاً.'}), 400
    db.execute("BEGIN TRANSACTION")
    try:
        old_invoice_dict = dict(old_invoice)
        _apply_invoice_financial_effect(db, old_invoice_dict, Decimal('-1'))
        old_lines = db.execute("SELECT * FROM invoice_lines WHERE invoice_id=?", (invoice_id,)).fetchall()
        old_item_ids = [row['item_id'] for row in old_lines]
        _post_invoice_ledger_reversal(db, user_id, invoice_id, old_invoice_dict, old_lines)
        db.execute("DELETE FROM inventory_movements WHERE reference_id=? AND user_id=? AND movement_type IN ('purchase','sale')", (invoice_id, user_id))
        db.execute("DELETE FROM invoice_lines WHERE invoice_id=?", (invoice_id,))
        if data.get('type') == 'sale':
            _assert_sale_stock_available(db, user_id, data.get('lines', []))
        db.execute('''
            UPDATE invoices SET type=?, customer_id=?, supplier_id=?, date=?, reference=?, notes=?, total=?, paid=?,
                status='active', exchange_rate_to_usd=?, original_currency=?, warehouse_id=?, branch_id=?,
                cashbox_id=?, bank_account_id=?, payment_method=?, shift_id=?, deleted_at=NULL
            WHERE id=? AND user_id=?
        ''', (
            data['type'], data.get('customer_id'), data.get('supplier_id'), data['date'],
            data.get('reference', ''), data.get('notes', ''), str(data['total']),
            str(data.get('paid_amount', data.get('paid', 0))), data.get('exchange_rate_to_usd', 1.0),
            data.get('original_currency', 'USD'), data.get('warehouse_id'), data.get('branch_id'),
            data.get('cashbox_id'), data.get('bank_account_id'), data.get('payment_method', 'cash'), data.get('shift_id'),
            invoice_id, user_id
        ))
        for line in data['lines']:
            conv_factor = Decimal(str(line.get('conversion_factor', 1) or 1))
            if conv_factor <= 0:
                conv_factor = Decimal('1')
            qty = Decimal(str(line.get('quantity', 0) or 0))
            base_qty = Decimal(str(line.get('base_qty', line.get('quantity_in_base', qty * conv_factor)) or 0))
            unit_cost = Decimal(str(line['unit_price']))
            cursor_line = db.execute('''
                INSERT INTO invoice_lines (invoice_id, item_id, quantity, unit_price, total, unit, quantity_in_base, unit_cost, cost_amount, conversion_factor)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            ''', (
                invoice_id, line['item_id'], str(line['quantity']), str(unit_cost), str(line['total']),
                line.get('unit', ''), str(base_qty), str(unit_cost), '0', str(conv_factor)
            ))
            line_id = cursor_line.lastrowid
            if data['type'] == 'purchase':
                movement_type = 'purchase'
                movement_cost = unit_cost / conv_factor
                cost_amt = movement_cost * base_qty
            else:
                movement_type = 'sale'
                item = db.execute("SELECT CAST(average_cost AS TEXT) as avg_cost FROM items WHERE id=? AND user_id=?", (line['item_id'], user_id)).fetchone()
                avg_cost = Decimal(str(item['avg_cost'])) if item else Decimal('0')
                movement_cost = unit_cost
                cost_amt = base_qty * avg_cost
            db.execute("UPDATE invoice_lines SET cost_amount=? WHERE id=?", (str(cost_amt), line_id))
            db.execute('''
                INSERT INTO inventory_movements (item_id, user_id, movement_type, quantity, unit_cost, reference_id, movement_date)
                VALUES (?,?,?,?,?,?,?)
            ''', (line['item_id'], user_id, movement_type, str(base_qty), str(movement_cost), invoice_id, datetime.datetime.now().isoformat()))
        for item_id in set(old_item_ids + [line['item_id'] for line in data['lines']]):
            _update_item_quantity(db, item_id, user_id)
            _recalculate_average_cost(db, item_id, user_id)
        _post_invoice_ledger_entries(db, user_id, invoice_id, data)
        _apply_invoice_financial_effect(db, {
            'user_id': user_id, 'type': data['type'], 'customer_id': data.get('customer_id'),
            'supplier_id': data.get('supplier_id'), 'total': data['total'],
            'paid': data.get('paid_amount', data.get('paid', 0))
        }, Decimal('1'))
        audit_log('UPDATE', 'SALE_INVOICE' if data.get('type') == 'sale' else 'PURCHASE_INVOICE', invoice_id, old_values=old_invoice_dict, new_values=data, details='تعديل فاتورة')
        db.execute("COMMIT")
        return jsonify({'id': invoice_id, 'status': 'ok'}), 200
    except ValueError as e:
        db.execute("ROLLBACK")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.execute("ROLLBACK")
        return jsonify({'error': str(e)}), 500

@invoices_bp.route('/invoices/<int:invoice_id>', methods=['DELETE'])
@jwt_required()
def delete_invoice(invoice_id):
    user_id = get_jwt_identity()
    db = get_db()
    _ensure_workflow_schema(db)
    inv = db.execute("SELECT * FROM invoices WHERE id=? AND user_id=? AND deleted_at IS NULL", (invoice_id, user_id)).fetchone()
    if not inv:
        return jsonify({'error': 'Not found'}), 404
    try:
        _assert_workflow_allowed(db, inv, 'delete')
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    if _invoice_has_vouchers(db, invoice_id, user_id):
        return jsonify({'error': 'لا يمكن حذف فاتورة مرتبطة بسندات. احذف السندات أولاً.'}), 400
    if _invoice_has_returns(db, invoice_id, user_id):
        return jsonify({'error': 'لا يمكن حذف فاتورة مرتبطة بمرتجعات. ألغِ المرتجعات أولاً.'}), 400
    db.execute("BEGIN TRANSACTION")
    try:
        invoice_lines = db.execute("SELECT * FROM invoice_lines WHERE invoice_id=?", (invoice_id,)).fetchall()
        item_ids = [row['item_id'] for row in invoice_lines]
        _post_invoice_ledger_reversal(db, user_id, invoice_id, dict(inv), invoice_lines)
        db.execute("DELETE FROM inventory_movements WHERE reference_id=? AND user_id=? AND movement_type IN ('purchase','sale')", (invoice_id, user_id))
        for item_id in set(item_ids):
            _update_item_quantity(db, item_id, user_id)
            _recalculate_average_cost(db, item_id, user_id)
        _apply_invoice_financial_effect(db, dict(inv), Decimal('-1'))
        db.execute("UPDATE invoices SET deleted_at = datetime('now'), status='cancelled', workflow_status='CANCELLED', cancelled_at=datetime('now'), deleted_by=? WHERE id=? AND user_id=?", (user_id, invoice_id, user_id))
        audit_log('SOFT_DELETE', 'SALE_INVOICE' if inv['type'] == 'sale' else 'PURCHASE_INVOICE', invoice_id, old_values=dict(inv), details='إلغاء/حذف فاتورة')
        db.execute("COMMIT")
        return jsonify({'status': 'ok'})
    except Exception as e:
        db.execute("ROLLBACK")
        return jsonify({'error': str(e)}), 500


