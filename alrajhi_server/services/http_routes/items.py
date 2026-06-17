"""Thin service route boundary for items.

SQL-backed route implementation is intentionally contained in
alrajhi_server.repositories.http_route_sql.items so service/http boundary modules
remain free from SQL literals and direct data access.
"""
from alrajhi_server.repositories.http_route_sql.items import items_bp

__all__ = ["items_bp"]
