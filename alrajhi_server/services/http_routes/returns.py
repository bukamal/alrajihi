"""Thin service route boundary for returns.

SQL-backed route implementation is intentionally contained in
alrajhi_server.repositories.http_route_sql.returns so service/http boundary modules
remain free from SQL literals and direct data access.
"""
from alrajhi_server.repositories.http_route_sql.returns import returns_bp

__all__ = ["returns_bp"]
