from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.repositories.report_repository import get_report_repository
from decimal import Decimal
from datetime import datetime, date

def _phase157_has_permission(db, user_id, permission_key):
    user_id = str(user_id)
    role = db.query("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
    if role and role['role'] == 'admin':
        return True
    db.query("""INSERT OR IGNORE INTO user_roles(user_id, role_id) SELECT u.id, r.id FROM users u JOIN roles r ON lower(COALESCE(u.role,'user'))=r.name WHERE u.id=?""", (user_id,))
    return db.query("""SELECT 1 FROM user_roles ur JOIN role_permissions rp ON rp.role_id=ur.role_id AND rp.allowed=1 JOIN roles r ON r.id=ur.role_id AND r.is_active=1 WHERE ur.user_id=? AND rp.permission_key=? LIMIT 1""", (user_id, permission_key)).fetchone() is not None


reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    user_id = get_jwt_identity()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    db = get_report_repository()

    def safe_sum(sql, params, date_col=None):
        if start_date and end_date and date_col:
            sql += f" AND {date_col} BETWEEN ? AND ?"
            params = params + (start_date, end_date)
        res = db.query(sql, params).fetchone()[0]
        return Decimal(str(res)) if res is not None else Decimal('0')

    sales = safe_sum(
        "SELECT SUM(CAST(total AS REAL)) FROM invoices WHERE type='sale' AND user_id=? AND deleted_at IS NULL",
        (user_id,), 'date'
    )

    purchases = safe_sum(
        "SELECT SUM(CAST(total AS REAL)) FROM invoices WHERE type='purchase' AND user_id=? AND deleted_at IS NULL",
        (user_id,), 'date'
    )
    sale_paid = safe_sum(
        "SELECT SUM(CAST(paid AS REAL)) FROM invoices WHERE type='sale' AND user_id=? AND deleted_at IS NULL",
        (user_id,), 'date'
    )
    purchase_paid = safe_sum(
        "SELECT SUM(CAST(paid AS REAL)) FROM invoices WHERE type='purchase' AND user_id=? AND deleted_at IS NULL",
        (user_id,), 'date'
    )
    receipt_vouchers = safe_sum(
        "SELECT SUM(CAST(amount AS REAL)) FROM vouchers WHERE type='receipt' AND user_id=?",
        (user_id,), 'date'
    )
    payment_vouchers = safe_sum(
        "SELECT SUM(CAST(amount AS REAL)) FROM vouchers WHERE type='payment' AND user_id=?",
        (user_id,), 'date'
    )
    expense_vouchers = safe_sum(
        "SELECT SUM(CAST(amount AS REAL)) FROM vouchers WHERE type='expense' AND user_id=?",
        (user_id,), 'date'
    )
    sales_return_refunds = safe_sum(
        "SELECT SUM(CAST(refund_amount AS REAL)) FROM sales_returns WHERE user_id=? AND deleted_at IS NULL",
        (user_id,), 'date'
    )
    purchase_return_refunds = safe_sum(
        "SELECT SUM(CAST(refund_amount AS REAL)) FROM purchase_returns WHERE user_id=? AND deleted_at IS NULL",
        (user_id,), 'date'
    )
    cash_received = sale_paid + receipt_vouchers + purchase_return_refunds
    cash_paid = purchase_paid + payment_vouchers + expense_vouchers + sales_return_refunds

    cogs = safe_sum(
        """SELECT SUM(CAST(cost_amount AS REAL)) FROM invoice_lines il
           JOIN invoices i ON il.invoice_id = i.id
           WHERE i.type='sale' AND i.user_id=? AND i.deleted_at IS NULL""",
        (user_id,), 'i.date'
    )

    expenses = safe_sum(
        "SELECT SUM(CAST(amount AS REAL)) FROM vouchers WHERE type='expense' AND user_id=?",
        (user_id,), 'date'
    )

    cash_row = db.query("SELECT CAST(cash_balance AS REAL) FROM users WHERE id=?", (user_id,)).fetchone()
    cash = Decimal(str(cash_row[0])) if cash_row and cash_row[0] else Decimal('0')

    receivables = db.query("SELECT SUM(CAST(balance AS REAL)) FROM customers WHERE user_id=?", (user_id,)).fetchone()[0] or 0
    payables = db.query("SELECT SUM(CAST(balance AS REAL)) FROM suppliers WHERE user_id=?", (user_id,)).fetchone()[0] or 0

    net_profit = sales - cogs - expenses

    return jsonify({
        'total_sales': float(sales),
        'cogs': float(cogs),
        'total_expenses': float(expenses),
        'net_profit': float(net_profit),
        'cash_balance': float(cash),
        'receivables': float(receivables),
        'payables': float(payables),
        'total_purchases': float(purchases),
        'total_incoming': float(cash_received),
        'total_outgoing': float(cash_paid),
        'cash_received': float(cash_received),
        'cash_paid': float(cash_paid),
        'cash_net_movement': float(cash_received - cash_paid)
    })

@reports_bp.route('/income_statement', methods=['GET'])
@jwt_required()
def income_statement():
    user_id = get_jwt_identity()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    db = get_report_repository()

    def safe_sum(sql, params, date_col=None):
        if start_date and end_date and date_col:
            sql += f" AND {date_col} BETWEEN ? AND ?"
            params = params + (start_date, end_date)
        res = db.query(sql, params).fetchone()[0]
        return Decimal(str(res)) if res is not None else Decimal('0')

    sales = safe_sum(
        "SELECT SUM(CAST(total AS REAL)) FROM invoices WHERE type='sale' AND user_id=? AND deleted_at IS NULL",
        (user_id,), 'date'
    )
    cogs = safe_sum(
        """SELECT SUM(CAST(cost_amount AS REAL)) FROM invoice_lines il
           JOIN invoices i ON il.invoice_id = i.id
           WHERE i.type='sale' AND i.user_id=? AND i.deleted_at IS NULL""",
        (user_id,), 'i.date'
    )
    expenses = safe_sum(
        "SELECT SUM(CAST(amount AS REAL)) FROM vouchers WHERE type='expense' AND user_id=?",
        (user_id,), 'date'
    )
    net = sales - cogs - expenses
    return jsonify({
        'income': [{'name': 'إجمالي الإيرادات', 'balance': float(sales)}],
        'expenses': [{'name': 'تكلفة البضاعة المباعة', 'balance': float(cogs)},
                     {'name': 'المصروفات التشغيلية', 'balance': float(expenses)}],
        'total_income': float(sales),
        'total_expenses': float(cogs + expenses),
        'net_profit': float(net)
    })

@reports_bp.route('/balance_sheet', methods=['GET'])
@jwt_required()
def balance_sheet():
    user_id = get_jwt_identity()
    db = get_report_repository()
    cash = db.query("SELECT CAST(cash_balance AS REAL) FROM users WHERE id=?", (user_id,)).fetchone()[0] or 0
    receivables = db.query("SELECT SUM(CAST(balance AS REAL)) FROM customers WHERE user_id=?", (user_id,)).fetchone()[0] or 0
    payables = db.query("SELECT SUM(CAST(balance AS REAL)) FROM suppliers WHERE user_id=?", (user_id,)).fetchone()[0] or 0
    equity = cash + receivables - payables
    return jsonify({
        'assets': [{'name': 'الصندوق', 'debit': float(cash)},
                   {'name': 'الذمم المدينة', 'debit': float(receivables)}],
        'liabilities': [{'name': 'الذمم الدائنة', 'credit': float(payables)}],
        'equity': [{'name': 'رأس المال', 'credit': float(equity)}],
        'total_assets': float(cash + receivables),
        'total_liabilities': float(payables),
        'total_equity': float(equity)
    })



# ---------------- Phase 36: customer/supplier movements and expanded reporting ----------------
def _to_float(value):
    try:
        return float(Decimal(str(value or 0)))
    except Exception:
        return 0.0


def _date_filter(sql, params, date_col, start_date, end_date):
    if start_date:
        sql += f" AND {date_col} >= ?"
        params += (start_date,)
    if end_date:
        sql += f" AND {date_col} <= ?"
        params += (end_date,)
    return sql, params


def _statement_rows(db, user_id, party_type, party_id, start_date=None, end_date=None):
    if party_type == 'customer':
        parts = [
            ("""SELECT date AS date, reference AS reference, 'sale_invoice' AS source_type, id AS source_id,
                      CAST(total AS TEXT) AS amount, 'فاتورة بيع' AS description,
                      CAST(total AS TEXT) AS debit, '0' AS credit
               FROM invoices WHERE customer_id=? AND type='sale' AND user_id=? AND deleted_at IS NULL""", (party_id, user_id), 'date'),
            ("""SELECT date AS date, return_no AS reference, 'sales_return' AS source_type, id AS source_id,
                      CAST(total AS TEXT) AS amount, 'مرتجع بيع' AS description,
                      '0' AS debit, CAST(total AS TEXT) AS credit
               FROM sales_returns WHERE customer_id=? AND user_id=? AND deleted_at IS NULL""", (party_id, user_id), 'date'),
            ("""SELECT date AS date, reference AS reference, 'receipt_voucher' AS source_type, id AS source_id,
                      CAST(amount AS TEXT) AS amount, 'سند قبض' AS description,
                      '0' AS debit, CAST(amount AS TEXT) AS credit
               FROM vouchers WHERE customer_id=? AND type='receipt' AND user_id=?""", (party_id, user_id), 'date'),
        ]
    else:
        parts = [
            ("""SELECT date AS date, reference AS reference, 'purchase_invoice' AS source_type, id AS source_id,
                      CAST(total AS TEXT) AS amount, 'فاتورة شراء' AS description,
                      '0' AS debit, CAST(total AS TEXT) AS credit
               FROM invoices WHERE supplier_id=? AND type='purchase' AND user_id=? AND deleted_at IS NULL""", (party_id, user_id), 'date'),
            ("""SELECT date AS date, return_no AS reference, 'purchase_return' AS source_type, id AS source_id,
                      CAST(total AS TEXT) AS amount, 'مرتجع شراء' AS description,
                      CAST(total AS TEXT) AS debit, '0' AS credit
               FROM purchase_returns WHERE supplier_id=? AND user_id=? AND deleted_at IS NULL""", (party_id, user_id), 'date'),
            ("""SELECT date AS date, reference AS reference, 'payment_voucher' AS source_type, id AS source_id,
                      CAST(amount AS TEXT) AS amount, 'سند دفع' AS description,
                      CAST(amount AS TEXT) AS debit, '0' AS credit
               FROM vouchers WHERE supplier_id=? AND type='payment' AND user_id=?""", (party_id, user_id), 'date'),
        ]
    queries, params = [], []
    for sql, p, dcol in parts:
        sql, p = _date_filter(sql, p, dcol, start_date, end_date)
        queries.append(sql)
        params.extend(p)
    rows = db.query(" UNION ALL ".join(queries) + " ORDER BY date, source_id", tuple(params)).fetchall()
    balance = Decimal('0')
    result = []
    for row in rows:
        d = dict(row)
        debit = Decimal(str(d.get('debit') or 0))
        credit = Decimal(str(d.get('credit') or 0))
        balance += (debit - credit) if party_type == 'customer' else (credit - debit)
        d['debit'] = _to_float(debit)
        d['credit'] = _to_float(credit)
        d['amount'] = _to_float(d.get('amount'))
        d['balance'] = _to_float(balance)
        result.append(d)
    return result


@reports_bp.route('/customers/<int:customer_id>/statement', methods=['GET'])
@jwt_required()
def customer_statement(customer_id):
    db = get_report_repository()
    rows = _statement_rows(db, get_jwt_identity(), 'customer', customer_id, request.args.get('start_date'), request.args.get('end_date'))
    return jsonify({'rows': rows})


@reports_bp.route('/suppliers/<int:supplier_id>/statement', methods=['GET'])
@jwt_required()
def supplier_statement(supplier_id):
    db = get_report_repository()
    rows = _statement_rows(db, get_jwt_identity(), 'supplier', supplier_id, request.args.get('start_date'), request.args.get('end_date'))
    return jsonify({'rows': rows})


@reports_bp.route('/customers/balances', methods=['GET'])
@jwt_required()
def customer_balances():
    rows = get_report_repository().query("""
        SELECT id, name, phone, address, CAST(balance AS REAL) AS balance
        FROM customers WHERE user_id=? ORDER BY name
    """, (get_jwt_identity(),)).fetchall()
    return jsonify({'rows': [dict(r) for r in rows]})


@reports_bp.route('/suppliers/balances', methods=['GET'])
@jwt_required()
def supplier_balances():
    rows = get_report_repository().query("""
        SELECT id, name, phone, address, CAST(balance AS REAL) AS balance
        FROM suppliers WHERE user_id=? ORDER BY name
    """, (get_jwt_identity(),)).fetchall()
    return jsonify({'rows': [dict(r) for r in rows]})


def _parse_yyyy_mm_dd(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except Exception:
        return None


def _aging_rows(db, user_id, table, as_of_date=None):
    from datetime import date, datetime
    as_of = _parse_yyyy_mm_dd(as_of_date) or date.today()
    rows = db.query(f"SELECT id, name, phone, CAST(balance AS REAL) AS balance FROM {table} WHERE user_id=? ORDER BY name", (user_id,)).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        if table == 'customers':
            sql = """
            SELECT MAX(dt) FROM (
              SELECT date AS dt FROM invoices WHERE customer_id=? AND type='sale' AND user_id=? AND deleted_at IS NULL
              UNION ALL SELECT date FROM sales_returns WHERE customer_id=? AND user_id=? AND deleted_at IS NULL
              UNION ALL SELECT date FROM vouchers WHERE customer_id=? AND type='receipt' AND user_id=?
            )
            """
        else:
            sql = """
            SELECT MAX(dt) FROM (
              SELECT date AS dt FROM invoices WHERE supplier_id=? AND type='purchase' AND user_id=? AND deleted_at IS NULL
              UNION ALL SELECT date FROM purchase_returns WHERE supplier_id=? AND user_id=? AND deleted_at IS NULL
              UNION ALL SELECT date FROM vouchers WHERE supplier_id=? AND type='payment' AND user_id=?
            )
            """
        last = db.query(sql, (d['id'], user_id, d['id'], user_id, d['id'], user_id)).fetchone()[0]
        parsed = _parse_yyyy_mm_dd(last) or as_of
        age = max((as_of - parsed).days, 0)
        bal = _to_float(d.get('balance'))
        buckets = {'current': 0.0, 'days_1_30': 0.0, 'days_31_60': 0.0, 'days_61_90': 0.0, 'over_90': 0.0}
        if age <= 0:
            buckets['current'] = bal
        elif age <= 30:
            buckets['days_1_30'] = bal
        elif age <= 60:
            buckets['days_31_60'] = bal
        elif age <= 90:
            buckets['days_61_90'] = bal
        else:
            buckets['over_90'] = bal
        result.append({**d, 'last_transaction_date': last or '', 'age_days': age, **buckets})
    return result


@reports_bp.route('/customers/aging', methods=['GET'])
@jwt_required()
def customer_aging():
    return jsonify({'rows': _aging_rows(get_report_repository(), get_jwt_identity(), 'customers', request.args.get('as_of_date'))})


@reports_bp.route('/suppliers/aging', methods=['GET'])
@jwt_required()
def supplier_aging():
    return jsonify({'rows': _aging_rows(get_report_repository(), get_jwt_identity(), 'suppliers', request.args.get('as_of_date'))})


@reports_bp.route('/trial_balance', methods=['GET'])
@jwt_required()
def trial_balance():
    db = get_report_repository()
    uid = get_jwt_identity()
    def ss(sql):
        v = db.query(sql, (uid,)).fetchone()[0]
        return Decimal(str(v)) if v is not None else Decimal('0')
    sales = ss("SELECT SUM(CAST(total AS REAL)) FROM invoices WHERE type='sale' AND user_id=? AND deleted_at IS NULL")
    sales_returns = ss("SELECT SUM(CAST(total AS REAL)) FROM sales_returns WHERE user_id=? AND deleted_at IS NULL")
    purchases = ss("SELECT SUM(CAST(total AS REAL)) FROM invoices WHERE type='purchase' AND user_id=? AND deleted_at IS NULL")
    purchase_returns = ss("SELECT SUM(CAST(total AS REAL)) FROM purchase_returns WHERE user_id=? AND deleted_at IS NULL")
    expenses = ss("SELECT SUM(CAST(amount AS REAL)) FROM expenses WHERE user_id=?")
    cash = ss("SELECT CAST(cash_balance AS REAL) FROM users WHERE id=?")
    receivables = ss("SELECT SUM(CAST(balance AS REAL)) FROM customers WHERE user_id=?")
    payables = ss("SELECT SUM(CAST(balance AS REAL)) FROM suppliers WHERE user_id=?")
    rows = [
        {'name':'الصندوق','debit':_to_float(cash if cash > 0 else 0),'credit':_to_float(-cash if cash < 0 else 0)},
        {'name':'الذمم المدينة','debit':_to_float(receivables),'credit':0.0},
        {'name':'الذمم الدائنة','debit':0.0,'credit':_to_float(payables)},
        {'name':'المبيعات','debit':0.0,'credit':_to_float(sales)},
        {'name':'مرتجعات المبيعات','debit':_to_float(sales_returns),'credit':0.0},
        {'name':'المشتريات','debit':_to_float(purchases),'credit':0.0},
        {'name':'مرتجعات المشتريات','debit':0.0,'credit':_to_float(purchase_returns)},
        {'name':'المصاريف','debit':_to_float(expenses),'credit':0.0},
    ]
    return jsonify({'rows': rows})


# ---------------- Phase154: real accounting ledger reports ----------------
def _ensure_accounting_schema_for_reports(db):
    db.script("""
        CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, type TEXT NOT NULL, parent_id INTEGER, is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS journal_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, entry_no TEXT UNIQUE, entry_date TEXT NOT NULL, source_type TEXT, source_id INTEGER, description TEXT, status TEXT DEFAULT 'POSTED', created_by TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(source_type, source_id));
        CREATE TABLE IF NOT EXISTS journal_lines (id INTEGER PRIMARY KEY AUTOINCREMENT, journal_entry_id INTEGER NOT NULL, account_id INTEGER NOT NULL, debit TEXT DEFAULT '0', credit TEXT DEFAULT '0', memo TEXT);
        CREATE INDEX IF NOT EXISTS idx_journal_entries_source ON journal_entries(source_type, source_id);
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1000','Cash / صندوق','ASSET');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1100','Accounts Receivable / ذمم العملاء','ASSET');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1200','Inventory / مخزون','ASSET');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('2000','Accounts Payable / ذمم الموردين','LIABILITY');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('3000','Owner Equity / حقوق الملكية','EQUITY');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('3100','Retained Earnings / أرباح مرحلة','EQUITY');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('3900','Current Year Earnings / أرباح السنة الحالية','EQUITY');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('4000','Sales Revenue / إيرادات المبيعات','REVENUE');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('5000','Purchases / مشتريات','EXPENSE');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('5900','Closing Summary / ملخص الإقفال','EQUITY');
        CREATE TABLE IF NOT EXISTS accounting_periods (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL, status TEXT DEFAULT 'OPEN', closed_at TEXT, closed_by TEXT, closing_entry_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS idx_accounting_periods_dates ON accounting_periods(start_date, end_date, status);
    """)

@reports_bp.route('/accounting/trial_balance', methods=['GET'])
@jwt_required()
def accounting_trial_balance():
    db = get_report_repository()
    _ensure_accounting_schema_for_reports(db)
    rows = db.query("""
        SELECT a.id AS account_id, a.code, a.name, a.type,
               COALESCE(SUM(CAST(jl.debit AS REAL)), 0) AS debit,
               COALESCE(SUM(CAST(jl.credit AS REAL)), 0) AS credit
        FROM accounts a
        LEFT JOIN journal_lines jl ON jl.account_id = a.id
        LEFT JOIN journal_entries je ON je.id = jl.journal_entry_id AND COALESCE(je.status, 'POSTED') <> 'VOID'
        WHERE COALESCE(a.is_active, 1)=1
        GROUP BY a.id, a.code, a.name, a.type
        ORDER BY a.code
    """).fetchall()
    result=[]
    total_debit = Decimal('0')
    total_credit = Decimal('0')
    for r in rows:
        d=dict(r)
        debit=Decimal(str(d.get('debit') or 0)); credit=Decimal(str(d.get('credit') or 0))
        total_debit += debit; total_credit += credit
        d['debit']=float(debit); d['credit']=float(credit); d['balance']=float(debit-credit)
        result.append(d)
    return jsonify({'rows': result, 'total_debit': float(total_debit), 'total_credit': float(total_credit), 'balanced': total_debit == total_credit})

@reports_bp.route('/accounting/ledger', methods=['GET'])
@jwt_required()
def accounting_ledger():
    db = get_report_repository()
    _ensure_accounting_schema_for_reports(db)
    account_id = request.args.get('account_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', default=1000, type=int)
    sql = """
        SELECT je.entry_no, je.entry_date, je.source_type, je.source_id, je.description,
               a.id AS account_id, a.code, a.name AS account_name,
               CAST(jl.debit AS TEXT) AS debit, CAST(jl.credit AS TEXT) AS credit, jl.memo
        FROM journal_lines jl
        JOIN journal_entries je ON je.id = jl.journal_entry_id
        JOIN accounts a ON a.id = jl.account_id
        WHERE COALESCE(je.status, 'POSTED') <> 'VOID'
    """
    params=[]
    if account_id:
        sql += ' AND a.id=?'; params.append(account_id)
    if start_date:
        sql += ' AND je.entry_date>=?'; params.append(start_date)
    if end_date:
        sql += ' AND je.entry_date<=?'; params.append(end_date)
    sql += ' ORDER BY je.entry_date, je.id, jl.id LIMIT ?'; params.append(int(limit or 1000))
    balance = Decimal('0')
    result=[]
    for row in db.query(sql, tuple(params)).fetchall():
        d=dict(row)
        debit=Decimal(str(d.get('debit') or 0)); credit=Decimal(str(d.get('credit') or 0))
        balance += debit - credit
        d['debit']=float(debit); d['credit']=float(credit); d['balance']=float(balance)
        result.append(d)
    return jsonify({'rows': result})

@reports_bp.route('/accounting/journal_entries', methods=['GET'])
@jwt_required()
def accounting_journal_entries():
    db = get_report_repository()
    _ensure_accounting_schema_for_reports(db)
    limit = request.args.get('limit', default=500, type=int)
    rows=[dict(r) for r in db.query('SELECT * FROM journal_entries ORDER BY id DESC LIMIT ?', (int(limit or 500),)).fetchall()]
    return jsonify({'rows': rows})


# ---------------- Phase155: financial statements and closing endpoints ----------------
def _account_rows_with_balances_server(db, start_date=None, end_date=None):
    _ensure_accounting_schema_for_reports(db)
    join_filter = "AND COALESCE(je.status, 'POSTED') <> 'VOID'"
    params = []
    if start_date:
        join_filter += " AND je.entry_date >= ?"; params.append(start_date)
    if end_date:
        join_filter += " AND je.entry_date <= ?"; params.append(end_date)
    sql = f"""
        SELECT a.id AS account_id, a.code, a.name, a.type,
               COALESCE(SUM(CAST(jl.debit AS REAL)), 0) AS debit,
               COALESCE(SUM(CAST(jl.credit AS REAL)), 0) AS credit
        FROM accounts a
        LEFT JOIN journal_lines jl ON jl.account_id = a.id
        LEFT JOIN journal_entries je ON je.id = jl.journal_entry_id {join_filter}
        WHERE COALESCE(a.is_active, 1)=1
        GROUP BY a.id, a.code, a.name, a.type
        ORDER BY a.code
    """
    result=[]
    for r in db.query(sql, tuple(params)).fetchall():
        d=dict(r); debit=Decimal(str(d.get('debit') or 0)); credit=Decimal(str(d.get('credit') or 0))
        typ=(d.get('type') or '').upper()
        natural = debit-credit if typ in ('ASSET','EXPENSE') else credit-debit
        d.update({'debit':float(debit),'credit':float(credit),'balance':float(debit-credit),'natural_balance':float(natural)})
        result.append(d)
    return result

def _income_statement_payload(db, start_date=None, end_date=None):
    rows=_account_rows_with_balances_server(db,start_date,end_date)
    revenues=[r for r in rows if (r.get('type') or '').upper()=='REVENUE' and Decimal(str(r.get('natural_balance') or 0)) != 0]
    expenses=[r for r in rows if (r.get('type') or '').upper()=='EXPENSE' and Decimal(str(r.get('natural_balance') or 0)) != 0]
    total_revenue=sum((Decimal(str(r.get('natural_balance') or 0)) for r in revenues), Decimal('0'))
    total_expense=sum((Decimal(str(r.get('natural_balance') or 0)) for r in expenses), Decimal('0'))
    return {'revenues':revenues,'expenses':expenses,'total_revenue':float(total_revenue),'total_expense':float(total_expense),'net_income':float(total_revenue-total_expense),'start_date':start_date,'end_date':end_date}

@reports_bp.route('/accounting/income_statement', methods=['GET'])
@jwt_required()
def accounting_income_statement():
    db=get_report_repository()
    return jsonify(_income_statement_payload(db, request.args.get('start_date'), request.args.get('end_date')))

@reports_bp.route('/accounting/balance_sheet', methods=['GET'])
@jwt_required()
def accounting_balance_sheet():
    db=get_report_repository(); as_of_date=request.args.get('as_of_date')
    rows=_account_rows_with_balances_server(db,None,as_of_date)
    assets=[r for r in rows if (r.get('type') or '').upper()=='ASSET' and Decimal(str(r.get('natural_balance') or 0)) != 0]
    liabilities=[r for r in rows if (r.get('type') or '').upper()=='LIABILITY' and Decimal(str(r.get('natural_balance') or 0)) != 0]
    equity=[r for r in rows if (r.get('type') or '').upper()=='EQUITY' and Decimal(str(r.get('natural_balance') or 0)) != 0]
    income=_income_statement_payload(db, None, as_of_date); net=Decimal(str(income.get('net_income') or 0))
    if net:
        equity.append({'account_id':None,'code':'3900','name':'Current Year Earnings / أرباح السنة الحالية','type':'EQUITY','natural_balance':float(net),'debit':0.0,'credit':float(net),'balance':float(-net)})
    total_assets=sum((Decimal(str(r.get('natural_balance') or 0)) for r in assets), Decimal('0'))
    total_liabilities=sum((Decimal(str(r.get('natural_balance') or 0)) for r in liabilities), Decimal('0'))
    total_equity=sum((Decimal(str(r.get('natural_balance') or 0)) for r in equity), Decimal('0'))
    return jsonify({'assets':assets,'liabilities':liabilities,'equity':equity,'total_assets':float(total_assets),'total_liabilities':float(total_liabilities),'total_equity':float(total_equity),'balanced':total_assets==total_liabilities+total_equity,'as_of_date':as_of_date})

@reports_bp.route('/accounting/cash_flow', methods=['GET'])
@jwt_required()
def accounting_cash_flow():
    db=get_report_repository(); _ensure_accounting_schema_for_reports(db)
    start_date=request.args.get('start_date'); end_date=request.args.get('end_date')
    account=db.query("SELECT id FROM accounts WHERE code='1000'").fetchone()
    if not account: return jsonify({'rows':[],'cash_inflow':0.0,'cash_outflow':0.0,'net_cash_flow':0.0})
    account_id=account['id'] if hasattr(account,'keys') else account[0]
    sql="""
        SELECT je.entry_no, je.entry_date, je.source_type, je.source_id, je.description,
               a.id AS account_id, a.code, a.name AS account_name,
               CAST(jl.debit AS TEXT) AS debit, CAST(jl.credit AS TEXT) AS credit, jl.memo
        FROM journal_lines jl JOIN journal_entries je ON je.id=jl.journal_entry_id JOIN accounts a ON a.id=jl.account_id
        WHERE COALESCE(je.status,'POSTED') <> 'VOID' AND a.id=?
    """; params=[account_id]
    if start_date: sql += ' AND je.entry_date>=?'; params.append(start_date)
    if end_date: sql += ' AND je.entry_date<=?'; params.append(end_date)
    sql += ' ORDER BY je.entry_date, je.id, jl.id LIMIT 5000'
    rows=[]; inflow=Decimal('0'); outflow=Decimal('0'); bal=Decimal('0')
    for row in db.query(sql, tuple(params)).fetchall():
        d=dict(row); debit=Decimal(str(d.get('debit') or 0)); credit=Decimal(str(d.get('credit') or 0)); bal += debit-credit; inflow += debit; outflow += credit
        d['debit']=float(debit); d['credit']=float(credit); d['balance']=float(bal); rows.append(d)
    return jsonify({'rows':rows,'cash_inflow':float(inflow),'cash_outflow':float(outflow),'net_cash_flow':float(inflow-outflow),'start_date':start_date,'end_date':end_date})

@reports_bp.route('/accounting/periods', methods=['GET'])
@jwt_required()
def accounting_periods():
    db=get_report_repository(); _ensure_accounting_schema_for_reports(db)
    rows=[dict(r) for r in db.query('SELECT * FROM accounting_periods ORDER BY end_date DESC, id DESC').fetchall()]
    return jsonify({'rows':rows})

@reports_bp.route('/accounting/opening_balance', methods=['POST'])
@jwt_required()
def accounting_opening_balance():
    db=get_report_repository(); _ensure_accounting_schema_for_reports(db)
    data=request.get_json(silent=True) or {}
    account_code=str(data.get('account_code') or '').strip()
    amount=Decimal(str(data.get('amount') or 0))
    as_of_date=str(data.get('as_of_date') or date.today().isoformat())
    memo=str(data.get('memo') or 'Opening balance')
    if not account_code or amount == 0:
        return jsonify({'error':'account_code and non-zero amount are required'}), 400
    acc=db.query('SELECT id,type FROM accounts WHERE code=?',(account_code,)).fetchone()
    equity=db.query("SELECT id FROM accounts WHERE code='3000'").fetchone()
    if not acc or not equity:
        return jsonify({'error':'required account missing'}), 400
    next_id=db.query('SELECT COALESCE(MAX(id),0)+1 FROM journal_entries').fetchone()[0]
    cur=db.query("INSERT INTO journal_entries(entry_no,entry_date,source_type,source_id,description,status,created_by) VALUES (?,?, 'OPENING', NULL, ?, 'POSTED', ?)",(f'JE-{int(next_id):06d}',as_of_date,memo,get_jwt_identity()))
    je_id=int(cur.lastrowid); typ=(acc['type'] if hasattr(acc,'keys') else acc[1]).upper(); acc_id=acc['id'] if hasattr(acc,'keys') else acc[0]; eq_id=equity['id'] if hasattr(equity,'keys') else equity[0]
    if typ in ('ASSET','EXPENSE'):
        lines=[(acc_id,amount,Decimal('0')),(eq_id,Decimal('0'),amount)]
    else:
        lines=[(eq_id,amount,Decimal('0')),(acc_id,Decimal('0'),amount)]
    for aid,d,c in lines:
        db.query('INSERT INTO journal_lines(journal_entry_id,account_id,debit,credit,memo) VALUES (?,?,?,?,?)',(je_id,aid,str(d),str(c),memo))
    db.commit(); return jsonify({'journal_entry_id':je_id})

@reports_bp.route('/accounting/periods/close', methods=['POST'])
@jwt_required()
def accounting_close_period():
    db=get_report_repository(); _ensure_accounting_schema_for_reports(db)
    if not _phase157_has_permission(db, get_jwt_identity(), 'accounting.close_period'):
        return jsonify({'error': 'Permission denied', 'permission': 'accounting.close_period'}), 403
    data=request.get_json(silent=True) or {}
    name=str(data.get('name') or '').strip() or 'Period close'
    start_date=str(data.get('start_date') or '').strip(); end_date=str(data.get('end_date') or '').strip()
    if not start_date or not end_date:
        return jsonify({'error':'start_date and end_date are required'}), 400
    existing=db.query('SELECT id FROM accounting_periods WHERE start_date=? AND end_date=? AND status=?',(start_date,end_date,'CLOSED')).fetchone()
    if existing:
        return jsonify({'period_id': existing['id'] if hasattr(existing,'keys') else existing[0], 'already_closed': True})
    income=_income_statement_payload(db,start_date,end_date); now=datetime.now().isoformat(timespec='seconds')
    next_id=db.query('SELECT COALESCE(MAX(id),0)+1 FROM journal_entries').fetchone()[0]
    cur=db.query("INSERT INTO journal_entries(entry_no,entry_date,source_type,source_id,description,status,created_by,created_at) VALUES (?,?, 'PERIOD_CLOSE', NULL, ?, 'POSTED', ?, ?)",(f'JE-{int(next_id):06d}',end_date,f'Period closing {name}',get_jwt_identity(),now))
    je_id=int(cur.lastrowid); total_dr=Decimal('0'); total_cr=Decimal('0')
    for r in income.get('revenues',[]):
        amt=Decimal(str(r.get('natural_balance') or 0))
        if amt:
            db.query('INSERT INTO journal_lines(journal_entry_id,account_id,debit,credit,memo) VALUES (?,?,?,?,?)',(je_id,r['account_id'],str(amt),'0','Close revenue')); total_dr += amt
    for r in income.get('expenses',[]):
        amt=Decimal(str(r.get('natural_balance') or 0))
        if amt:
            db.query('INSERT INTO journal_lines(journal_entry_id,account_id,debit,credit,memo) VALUES (?,?,?,?,?)',(je_id,r['account_id'],'0',str(amt),'Close expense')); total_cr += amt
    re=db.query("SELECT id FROM accounts WHERE code='3100'").fetchone(); re_id=re['id'] if hasattr(re,'keys') else re[0]
    diff=total_dr-total_cr
    if diff>0:
        db.query('INSERT INTO journal_lines(journal_entry_id,account_id,debit,credit,memo) VALUES (?,?,?,?,?)',(je_id,re_id,'0',str(diff),'Transfer net income'))
    elif diff<0:
        db.query('INSERT INTO journal_lines(journal_entry_id,account_id,debit,credit,memo) VALUES (?,?,?,?,?)',(je_id,re_id,str(-diff),'0','Transfer net loss'))
    curp=db.query('INSERT INTO accounting_periods(name,start_date,end_date,status,closed_at,closed_by,closing_entry_id) VALUES (?,?,?,?,?,?,?)',(name,start_date,end_date,'CLOSED',now,get_jwt_identity(),je_id))
    db.commit(); return jsonify({'period_id':int(curp.lastrowid),'closing_entry_id':je_id})


# ---------------- Phase156: Receivables / Payables and Aging endpoints ----------------
def _phase156_parse_date_server(value):
    if not value:
        return None
    s = str(value)[:10]
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None

def _phase156_bucket_server(age_days, amount):
    buckets = {'current': Decimal('0'), 'days_1_30': Decimal('0'), 'days_31_60': Decimal('0'), 'days_61_90': Decimal('0'), 'over_90': Decimal('0')}
    if age_days <= 0:
        buckets['current'] = amount
    elif age_days <= 30:
        buckets['days_1_30'] = amount
    elif age_days <= 60:
        buckets['days_31_60'] = amount
    elif age_days <= 90:
        buckets['days_61_90'] = amount
    else:
        buckets['over_90'] = amount
    return {k: float(v) for k, v in buckets.items()}

def _phase156_aging_payload(db, party, as_of_date=None):
    _ensure_accounting_schema_for_reports(db)
    as_of = _phase156_parse_date_server(as_of_date) or date.today()
    if party == 'customer':
        join_table, id_col, type_value = 'customers', 'customer_id', 'sale'
    else:
        join_table, id_col, type_value = 'suppliers', 'supplier_id', 'purchase'
    sql = f"""
        SELECT p.id AS party_id, COALESCE(p.name, '') AS party_name,
               i.id AS invoice_id, i.reference, i.date, COALESCE(i.due_date, i.date) AS due_date,
               CAST(i.total AS REAL) AS total, CAST(COALESCE(i.paid,'0') AS REAL) AS paid,
               (CAST(i.total AS REAL) - CAST(COALESCE(i.paid,'0') AS REAL)) AS balance
        FROM invoices i
        LEFT JOIN {join_table} p ON p.id = i.{id_col}
        WHERE i.type=? AND i.{id_col} IS NOT NULL AND i.deleted_at IS NULL
          AND (CAST(i.total AS REAL) - CAST(COALESCE(i.paid,'0') AS REAL)) > 0.000001
        ORDER BY p.name, COALESCE(i.due_date, i.date), i.id
    """
    rows=[]; grouped={}; totals={'current':Decimal('0'),'days_1_30':Decimal('0'),'days_31_60':Decimal('0'),'days_61_90':Decimal('0'),'over_90':Decimal('0'),'total':Decimal('0')}
    for row in db.query(sql, (type_value,)).fetchall():
        d=dict(row); due=_phase156_parse_date_server(d.get('due_date')) or _phase156_parse_date_server(d.get('date')) or as_of
        age=max((as_of-due).days,0); bal=Decimal(str(d.get('balance') or 0)); bucket=_phase156_bucket_server(age, bal)
        d.update({'age_days': age, 'balance': float(bal), **bucket}); rows.append(d)
        g=grouped.setdefault(d.get('party_id'), {'party_id':d.get('party_id'), 'party_name':d.get('party_name') or '', 'current':Decimal('0'),'days_1_30':Decimal('0'),'days_31_60':Decimal('0'),'days_61_90':Decimal('0'),'over_90':Decimal('0'),'total':Decimal('0')})
        g['total'] += bal; totals['total'] += bal
        for b in ['current','days_1_30','days_31_60','days_61_90','over_90']:
            amt=Decimal(str(bucket[b])); g[b] += amt; totals[b] += amt
    summary=[]
    for g in grouped.values():
        summary.append({k:(float(v) if isinstance(v,Decimal) else v) for k,v in g.items()})
    return {'rows':rows,'summary':summary,'totals':{k:float(v) for k,v in totals.items()},'as_of_date':as_of.isoformat(),'party_type':party}

def _phase156_statement_payload(db, party, party_id, start_date=None, end_date=None):
    _ensure_accounting_schema_for_reports(db)
    if party == 'customer':
        invoice_where = "type='sale' AND customer_id=? AND deleted_at IS NULL"; params=[party_id]
        voucher_where = "customer_id=?"; voucher_params=[party_id]
        inv_debit, inv_credit = 'total', '0'
        v_debit_case = "CASE WHEN type='refund' THEN CAST(amount AS REAL) ELSE 0 END"
        v_credit_case = "CASE WHEN type IN ('receipt','return','sales_return') THEN CAST(amount AS REAL) ELSE 0 END"
    else:
        invoice_where = "type='purchase' AND supplier_id=? AND deleted_at IS NULL"; params=[party_id]
        voucher_where = "supplier_id=?"; voucher_params=[party_id]
        inv_debit, inv_credit = '0', 'total'
        v_debit_case = "CASE WHEN type IN ('payment','return','purchase_return') THEN CAST(amount AS REAL) ELSE 0 END"
        v_credit_case = "CASE WHEN type='refund' THEN CAST(amount AS REAL) ELSE 0 END"
    date_filter=''
    if start_date:
        date_filter += ' AND date>=?'; params.append(start_date); voucher_params.append(start_date)
    if end_date:
        date_filter += ' AND date<=?'; params.append(end_date); voucher_params.append(end_date)
    rows=[]
    for r in db.query(f"SELECT date, 'INVOICE' AS source_type, id AS source_id, reference, notes, CAST({inv_debit} AS REAL) AS debit, CAST({inv_credit} AS REAL) AS credit FROM invoices WHERE {invoice_where}{date_filter}", tuple(params)).fetchall():
        rows.append(dict(r))
    for r in db.query(f"SELECT date, 'VOUCHER' AS source_type, id AS source_id, reference, description AS notes, {v_debit_case} AS debit, {v_credit_case} AS credit FROM vouchers WHERE {voucher_where}{date_filter}", tuple(voucher_params)).fetchall():
        rows.append(dict(r))
    rows.sort(key=lambda r: (str(r.get('date') or ''), str(r.get('source_type') or ''), int(r.get('source_id') or 0)))
    bal=Decimal('0')
    for r in rows:
        debit=Decimal(str(r.get('debit') or 0)); credit=Decimal(str(r.get('credit') or 0)); bal += (debit-credit) if party == 'customer' else (credit-debit)
        r['debit']=float(debit); r['credit']=float(credit); r['balance']=float(bal)
    return {'rows':rows,'balance':float(bal),'party_type':party,'party_id':party_id,'start_date':start_date,'end_date':end_date}

@reports_bp.route('/accounting/receivables/aging', methods=['GET'])
@jwt_required()
def accounting_receivables_aging():
    return jsonify(_phase156_aging_payload(get_report_repository(), 'customer', request.args.get('as_of_date')))

@reports_bp.route('/accounting/payables/aging', methods=['GET'])
@jwt_required()
def accounting_payables_aging():
    return jsonify(_phase156_aging_payload(get_report_repository(), 'supplier', request.args.get('as_of_date')))

@reports_bp.route('/accounting/customers/<int:customer_id>/statement', methods=['GET'])
@jwt_required()
def accounting_customer_statement(customer_id):
    return jsonify(_phase156_statement_payload(get_report_repository(), 'customer', customer_id, request.args.get('start_date'), request.args.get('end_date')))

@reports_bp.route('/accounting/suppliers/<int:supplier_id>/statement', methods=['GET'])
@jwt_required()
def accounting_supplier_statement(supplier_id):
    return jsonify(_phase156_statement_payload(get_report_repository(), 'supplier', supplier_id, request.args.get('start_date'), request.args.get('end_date')))
