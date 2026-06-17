"""Thin API boundary for returns routes.

HTTP route implementation lives in alrajhi_server.services.http_routes.returns.
The api package must remain free from SQL literals and direct data access.
"""
from alrajhi_server.services.http_routes.returns import returns_bp

__all__ = ["returns_bp"]
