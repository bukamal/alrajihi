from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from alrajhi_server.repositories.category_repository import CategoryRepository

categories_bp = Blueprint('categories', __name__)
_category_repo = CategoryRepository()


@categories_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    categories = _category_repo.list(
        user_id=str(get_jwt_identity()),
        search=request.args.get('search'),
        include_inactive=request.args.get('include_inactive', default=0, type=int) == 1,
        include_deleted=request.args.get('include_deleted', default=0, type=int) == 1,
    )
    return jsonify({'categories': categories})


@categories_bp.route('/categories', methods=['POST'])
@jwt_required()
def add_category():
    try:
        category_id = _category_repo.create(str(get_jwt_identity()), request.get_json() or {})
        return jsonify({'id': category_id}), 201
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


@categories_bp.route('/categories/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    try:
        _category_repo.update(category_id, str(get_jwt_identity()), request.get_json() or {})
        return jsonify({'status': 'ok'})
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


@categories_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    try:
        _category_repo.delete(category_id, str(get_jwt_identity()))
        return jsonify({'status': 'ok'})
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


@categories_bp.route('/categories/<int:category_id>/restore', methods=['POST'])
@jwt_required()
def restore_category(category_id):
    _category_repo.restore(category_id, str(get_jwt_identity()))
    return jsonify({'status': 'ok'})
