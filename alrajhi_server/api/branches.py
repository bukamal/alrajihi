# -*- coding: utf-8 -*-
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from alrajhi_server.decorators import admin_required
from alrajhi_server.repositories.branch_repository import BranchRepository

branches_bp = Blueprint('branches', __name__)
_branch_repo = BranchRepository()


def _uid():
    try:
        return int(get_jwt_identity())
    except Exception:
        return get_jwt_identity()


def _payload(data):
    data = data or {}
    name = (data.get('name') or '').strip() or 'فرع'
    return {
        'name': name,
        'code': (data.get('code') or '').strip(),
        'address': data.get('address') or '',
        'phone': data.get('phone') or '',
        'notes': data.get('notes') or '',
        'is_active': 1 if data.get('is_active', 1) else 0,
    }


@branches_bp.route('/branches', methods=['GET'])
@jwt_required()
def list_branches():
    include = str(request.args.get('include_archived', '')).lower() in ('1', 'true', 'yes')
    return jsonify({'branches': _branch_repo.list(_uid(), include_archived=include)})


@branches_bp.route('/branches/default', methods=['GET'])
@jwt_required()
def default_branch():
    return jsonify({'id': _branch_repo.ensure_default_branch(_uid())})


@branches_bp.route('/branches/<int:branch_id>', methods=['GET'])
@jwt_required()
def get_branch(branch_id):
    row = _branch_repo.get(branch_id, _uid())
    if not row:
        return jsonify({'error': 'not found'}), 404
    return jsonify(row)


@branches_bp.route('/branches', methods=['POST'])
@admin_required
def add_branch():
    return jsonify({'id': _branch_repo.create(_uid(), _payload(request.get_json() or {}))}), 201


@branches_bp.route('/branches/<int:branch_id>', methods=['PUT'])
@admin_required
def update_branch(branch_id):
    _branch_repo.update(branch_id, _uid(), _payload(request.get_json() or {}))
    return jsonify({'status': 'ok'})


@branches_bp.route('/branches/<int:branch_id>', methods=['DELETE'])
@admin_required
def archive_branch(branch_id):
    ok, error = _branch_repo.archive(branch_id, _uid())
    if ok:
        return jsonify({'status': 'ok'})
    return jsonify({'error': error}), 404 if error == 'not found' else 400
