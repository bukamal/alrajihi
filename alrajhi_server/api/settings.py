from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from database.connection import get_db
from decorators import admin_required

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings/<key>', methods=['GET'])
@jwt_required()
def get_setting(key):
    db = get_db()
    row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return jsonify({'value': row['value'] if row else None})

@settings_bp.route('/settings/<key>', methods=['POST'])
@admin_required
def set_setting(key):
    data = request.get_json()
    value = data.get('value')
    db = get_db()
    db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    db.commit()
    return jsonify({'status': 'ok'})

@settings_bp.route('/exchange_rates', methods=['GET'])
@jwt_required()
def get_exchange_rates():
    db = get_db()
    rows = db.execute("SELECT currency_code, rate_to_usd, updated_at FROM exchange_rates ORDER BY currency_code").fetchall()
    return jsonify([dict(row) for row in rows])

@settings_bp.route('/exchange_rates/<currency_code>', methods=['PUT'])
@admin_required
def update_exchange_rate(currency_code):
    data = request.get_json()
    rate_to_usd = data.get('rate_to_usd')
    if rate_to_usd is None:
        return jsonify({'error': 'rate_to_usd required'}), 400
    now = __import__('datetime').datetime.now().isoformat()
    db = get_db()
    db.execute("INSERT OR REPLACE INTO exchange_rates (currency_code, rate_to_usd, updated_at) VALUES (?, ?, ?)",
               (currency_code, rate_to_usd, now))
    db.commit()
    return jsonify({'status': 'ok'})

@settings_bp.route('/exchange_rates/<currency_code>/history', methods=['GET'])
@jwt_required()
def get_historical_rate(currency_code):
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'date parameter required'}), 400
    db = get_db()
    row = db.execute("""
        SELECT rate_to_usd FROM exchange_rate_history
        WHERE currency_code = ? AND effective_date <= ?
        ORDER BY effective_date DESC LIMIT 1
    """, (currency_code, date)).fetchone()
    return jsonify({'rate_to_usd': row['rate_to_usd'] if row else 1.0})


