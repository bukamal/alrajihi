from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.repositories.party_repository import PartyRepository

customers_bp = Blueprint('customers', __name__)
_customer_repo = PartyRepository('customers')


@customers_bp.route('/customers', methods=['GET'])
@jwt_required()
def get_customers():
    user_id = get_jwt_identity()
    result = _customer_repo.list(
        user_id=user_id,
        search=request.args.get('search'),
        limit=request.args.get('limit', type=int),
        offset=request.args.get('offset', type=int),
    )
    return jsonify({'customers': result['rows'], 'total': result['total']})


@customers_bp.route('/customers', methods=['POST'])
@jwt_required()
def add_customer():
    customer_id = _customer_repo.create(get_jwt_identity(), request.get_json() or {})
    return jsonify({'id': customer_id}), 201


@customers_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@jwt_required()
def update_customer(customer_id):
    _customer_repo.update(customer_id, get_jwt_identity(), request.get_json() or {})
    return jsonify({'status': 'ok'})


@customers_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
@jwt_required()
def delete_customer(customer_id):
    _customer_repo.delete(customer_id, get_jwt_identity())
    return jsonify({'status': 'ok'})
