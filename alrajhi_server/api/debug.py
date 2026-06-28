# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from alrajhi_server.repositories.debug_repository import DebugRepository
from alrajhi_server.services.security_runtime import diagnostic_route_required


debug_bp = Blueprint('debug', __name__)
_debug_repo = DebugRepository()


@debug_bp.route('/debug/status', methods=['GET'])
@diagnostic_route_required
@jwt_required()
def debug_status():
    return jsonify(_debug_repo.status(get_jwt_identity()))


@debug_bp.route('/monitoring/health', methods=['GET'])
@diagnostic_route_required
@jwt_required()
def monitoring_health():
    """Read-only server-side operational health for Phase 35 clients."""
    return jsonify(_debug_repo.health(request.args.get('tolerance', '0')))
