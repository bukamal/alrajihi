from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.database.connection import get_db
from decimal import Decimal
from datetime import datetime, date

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    user_id = get_jwt_identity()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    db = get_db()

    def safe_sum(sql, params, date_col=None):
        if start_date and end_date and date_col:
            sql += f" AND {date_col} BETWEEN ? AND ?"
            params = params + (start_date, end_date)
        res = db.execute(sql, params).fetchone()[0]
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

    cash_row = db.execute("SELECT CAST(cash_balance AS REAL) FROM users WHERE id=?", (user_id,)).fetchone()
    cash = Decimal(str(cash_row[0])) if cash_row and cash_row[0] else Decimal('0')

    receivables = db.execute("SELECT SUM(CAST(balance AS REAL)) FROM customers WHERE user_id=?", (user_id,)).fetchone()[0] or 0
    payables = db.execute("SELECT SUM(CAST(balance AS REAL)) FROM suppliers WHERE user_id=?", (user_id,)).fetchone()[0] or 0

    net_profit = sales - cogs - expenses

    return jsonify({
        'total_sales': float(sales),
        'cogs': float(cogs),
        'total_expenses': float(expenses),
        'net_profit': float(net_profit),
        'cash_balance': float(cash),
        'receivables': float(receivables),
        'payables': float(payables)
    })

@reports_bp.route('/income_statement', methods=['GET'])
@jwt_required()
def income_statement():
    user_id = get_jwt_identity()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    db = get_db()

    def safe_sum(sql, params, date_col=None):
        if start_date and end_date and date_col:
            sql += f" AND {date_col} BETWEEN ? AND ?"
            params = params + (start_date, end_date)
        res = db.execute(sql, params).fetchone()[0]
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
    db = get_db()
    cash = db.execute("SELECT CAST(cash_balance AS REAL) FROM users WHERE id=?", (user_id,)).fetchone()[0] or 0
    receivables = db.execute("SELECT SUM(CAST(balance AS REAL)) FROM customers WHERE user_id=?", (user_id,)).fetchone()[0] or 0
    payables = db.execute("SELECT SUM(CAST(balance AS REAL)) FROM suppliers WHERE user_id=?", (user_id,)).fetchone()[0] or 0
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
    rows = db.execute(" UNION ALL ".join(queries) + " ORDER BY date, source_id", tuple(params)).fetchall()
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
    db = get_db()
    rows = _statement_rows(db, get_jwt_identity(), 'customer', customer_id, request.args.get('start_date'), request.args.get('end_date'))
    return jsonify({'rows': rows})


@reports_bp.route('/suppliers/<int:supplier_id>/statement', methods=['GET'])
@jwt_required()
def supplier_statement(supplier_id):
    db = get_db()
    rows = _statement_rows(db, get_jwt_identity(), 'supplier', supplier_id, request.args.get('start_date'), request.args.get('end_date'))
    return jsonify({'rows': rows})


@reports_bp.route('/customers/balances', methods=['GET'])
@jwt_required()
def customer_balances():
    rows = get_db().execute("""
        SELECT id, name, phone, address, CAST(balance AS REAL) AS balance
        FROM customers WHERE user_id=? ORDER BY name
    """, (get_jwt_identity(),)).fetchall()
    return jsonify({'rows': [dict(r) for r in rows]})


@reports_bp.route('/suppliers/balances', methods=['GET'])
@jwt_required()
def supplier_balances():
    rows = get_db().execute("""
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
    rows = db.execute(f"SELECT id, name, phone, CAST(balance AS REAL) AS balance FROM {table} WHERE user_id=? ORDER BY name", (user_id,)).fetchall()
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
        last = db.execute(sql, (d['id'], user_id, d['id'], user_id, d['id'], user_id)).fetchone()[0]
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
    return jsonify({'rows': _aging_rows(get_db(), get_jwt_identity(), 'customers', request.args.get('as_of_date'))})


@reports_bp.route('/suppliers/aging', methods=['GET'])
@jwt_required()
def supplier_aging():
    return jsonify({'rows': _aging_rows(get_db(), get_jwt_identity(), 'suppliers', request.args.get('as_of_date'))})


@reports_bp.route('/trial_balance', methods=['GET'])
@jwt_required()
def trial_balance():
    db = get_db()
    uid = get_jwt_identity()
    def ss(sql):
        v = db.execute(sql, (uid,)).fetchone()[0]
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
