from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.repositories.party_repository import PartyRepository

suppliers_bp = Blueprint('suppliers', __name__)
_supplier_repo = PartyRepository('suppliers')


@suppliers_bp.route('/suppliers', methods=['GET'])
@jwt_required()
def get_suppliers():
    user_id = get_jwt_identity()
    result = _supplier_repo.list(
        user_id=user_id,
        search=request.args.get('search'),
        limit=request.args.get('limit', type=int),
        offset=request.args.get('offset', type=int),
    )
    return jsonify({'suppliers': result['rows'], 'total': result['total']})


@suppliers_bp.route('/suppliers', methods=['POST'])
@jwt_required()
def add_supplier():
    supplier_id = _supplier_repo.create(get_jwt_identity(), request.get_json() or {})
    return jsonify({'id': supplier_id}), 201


@suppliers_bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
@jwt_required()
def update_supplier(supplier_id):
    _supplier_repo.update(supplier_id, get_jwt_identity(), request.get_json() or {})
    return jsonify({'status': 'ok'})


@suppliers_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
@jwt_required()
def delete_supplier(supplier_id):
    _supplier_repo.delete(supplier_id, get_jwt_identity())
    return jsonify({'status': 'ok'})
