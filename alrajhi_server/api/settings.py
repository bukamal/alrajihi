from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from alrajhi_server.decorators import admin_required
from alrajhi_server.repositories.settings_repository import SettingsRepository

settings_bp = Blueprint('settings', __name__)
_settings_repo = SettingsRepository()


@settings_bp.route('/settings/<path:key>', methods=['GET'])
@jwt_required()
def get_setting(key):
    return jsonify({'value': _settings_repo.get_setting(key)})


@settings_bp.route('/settings/<path:key>', methods=['POST'])
@admin_required
def set_setting(key):
    data = request.get_json() or {}
    _settings_repo.set_setting(key, data.get('value'))
    return jsonify({'status': 'ok'})


@settings_bp.route('/exchange_rates', methods=['GET'])
@jwt_required()
def get_exchange_rates():
    return jsonify(_settings_repo.list_exchange_rates())


@settings_bp.route('/exchange_rates/<currency_code>', methods=['PUT'])
@admin_required
def update_exchange_rate(currency_code):
    data = request.get_json() or {}
    rate_to_usd = data.get('rate_to_usd')
    if rate_to_usd is None:
        return jsonify({'error': 'rate_to_usd required'}), 400
    _settings_repo.update_exchange_rate(currency_code, rate_to_usd)
    return jsonify({'status': 'ok'})


@settings_bp.route('/exchange_rates/<currency_code>/history', methods=['GET'])
@jwt_required()
def get_historical_rate(currency_code):
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'date parameter required'}), 400
    return jsonify({'rate_to_usd': _settings_repo.historical_rate(currency_code, date)})
