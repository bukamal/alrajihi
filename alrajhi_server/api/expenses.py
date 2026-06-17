# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from alrajhi_server.repositories.expense_repository import ExpenseRepository

expenses_bp = Blueprint('expenses', __name__)
_expense_repo = ExpenseRepository()


@expenses_bp.route('/expenses', methods=['GET'])
@jwt_required()
def get_expenses():
    return jsonify(_expense_repo.list(
        user_id=get_jwt_identity(),
        limit=request.args.get('limit', type=int),
        offset=request.args.get('offset', type=int),
    ))


@expenses_bp.route('/expenses', methods=['POST'])
@jwt_required()
def add_expense():
    expense_id = _expense_repo.create(get_jwt_identity(), request.get_json() or {})
    return jsonify({'id': expense_id}), 201


@expenses_bp.route('/expenses/<int:expense_id>', methods=['PUT'])
@jwt_required()
def update_expense(expense_id):
    _expense_repo.update(expense_id, get_jwt_identity(), request.get_json() or {})
    return jsonify({'status': 'ok'})


@expenses_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):
    _expense_repo.delete(expense_id, get_jwt_identity())
    return jsonify({'status': 'ok'})
