from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.api.audit_utils import audit_log
from alrajhi_server.repositories.voucher_repository import get_voucher_repository

vouchers_bp = Blueprint('vouchers', __name__)


def _entity_type(vtype):
    if vtype == 'receipt':
        return 'RECEIPT_VOUCHER'
    if vtype == 'payment':
        return 'PAYMENT_VOUCHER'
    return 'EXPENSE_VOUCHER'


def _repo():
    return get_voucher_repository()


@vouchers_bp.route('/vouchers', methods=['GET'])
@jwt_required()
def get_vouchers():
    payload = _repo().list_vouchers(
        get_jwt_identity(),
        request.args.get('type'),
        request.args.get('limit', type=int),
        request.args.get('offset', type=int),
    )
    return jsonify(payload)


@vouchers_bp.route('/vouchers/<int:voucher_id>', methods=['GET'])
@jwt_required()
def get_voucher(voucher_id):
    row = _repo().get_voucher(get_jwt_identity(), voucher_id)
    if not row:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(row)


@vouchers_bp.route('/vouchers', methods=['POST'])
@jwt_required()
def add_voucher():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    try:
        voucher_id = _repo().create_voucher(user_id, data)
        audit_log('CREATE', _entity_type(data.get('type')), voucher_id, new_values=data, details='إنشاء سند')
        return jsonify({'id': voucher_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vouchers_bp.route('/vouchers/<int:voucher_id>', methods=['PUT'])
@jwt_required()
def update_voucher(voucher_id):
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    try:
        old = _repo().update_voucher(user_id, voucher_id, data)
        if old is None:
            return jsonify({'error': 'Not found'}), 404
        audit_log('UPDATE', _entity_type(data.get('type')), voucher_id, old_values=old, new_values=data, details='تعديل سند')
        return jsonify({'id': voucher_id}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vouchers_bp.route('/vouchers/<int:voucher_id>', methods=['DELETE'])
@jwt_required()
def delete_voucher(voucher_id):
    user_id = get_jwt_identity()
    try:
        old = _repo().delete_voucher(user_id, voucher_id)
        if old is None:
            return jsonify({'error': 'Not found'}), 404
        audit_log('DELETE', _entity_type(old.get('type')), voucher_id, old_values=old, details='حذف سند')
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
