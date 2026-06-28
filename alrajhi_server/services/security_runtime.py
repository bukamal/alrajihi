# -*- coding: utf-8 -*-
"""Phase 421 server security runtime policy.

This module keeps diagnostic endpoints useful during development and support,
but closed by default in production/release environments unless the operator
explicitly enables them.
"""
from __future__ import annotations

import os
from functools import wraps
from typing import Callable, TypeVar

try:
    from flask import jsonify
except ModuleNotFoundError:  # pragma: no cover - contract tests may run without Flask
    def jsonify(payload):
        return payload

F = TypeVar("F", bound=Callable)
PRODUCTION_ENV_VALUES = {"production", "prod", "release"}


def is_production_environment() -> bool:
    return any(
        str(os.environ.get(name, "")).strip().lower() in PRODUCTION_ENV_VALUES
        for name in ("ALRAJHI_ENV", "FLASK_ENV", "ENV", "APP_ENV")
    )


def diagnostics_enabled() -> bool:
    raw = os.environ.get("ALRAJHI_ENABLE_DIAGNOSTICS")
    if raw is not None:
        return str(raw).strip().lower() in {"1", "true", "yes", "on"}
    return not is_production_environment()


def diagnostic_denied_response():
    return jsonify({"error": "diagnostics disabled", "diagnostic_mode": False}), 404


def diagnostic_route_required(fn: F) -> F:
    """Decorator for read-only diagnostics that must not be public in production."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not diagnostics_enabled():
            return diagnostic_denied_response()
        return fn(*args, **kwargs)
    return wrapper  # type: ignore[return-value]


__all__ = [
    "diagnostic_denied_response",
    "diagnostic_route_required",
    "diagnostics_enabled",
    "is_production_environment",
]
