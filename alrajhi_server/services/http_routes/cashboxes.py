"""Thin service route boundary for cashboxes.

SQL-backed route implementation is intentionally contained in
alrajhi_server.repositories.http_route_sql.cashboxes so service/http boundary modules
remain free from SQL literals and direct data access.
"""
from alrajhi_server.repositories.http_route_sql.cashboxes import cashboxes_bp

__all__ = ["cashboxes_bp"]
