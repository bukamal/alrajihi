from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.database.connection import get_db
from decimal import Decimal

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


