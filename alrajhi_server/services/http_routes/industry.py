from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from alrajhi_server.decorators import admin_required
from alrajhi_server.repositories.industry_repository import get_industry_repository

industry_bp = Blueprint("industry", __name__)
_repo = get_industry_repository()


@industry_bp.route("/industry/profile", methods=["GET"])
@jwt_required()
def get_industry_profile():
    return jsonify(_repo.get_profile())


@industry_bp.route("/industry/profile", methods=["PUT"])
@admin_required
def set_industry_profile():
    data = request.get_json() or {}
    try:
        profile = _repo.set_profile(
            industry=data.get("industry", "general"),
            ui_mode=data.get("ui_mode"),
            enabled_modules=data.get("enabled_modules"),
        )
        return jsonify(profile)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
