"""Thin service route boundary for warehouses.

SQL-backed route implementation is intentionally contained in
alrajhi_server.repositories.http_route_sql.warehouses so service/http boundary modules
remain free from SQL literals and direct data access.
"""
from alrajhi_server.repositories.http_route_sql.warehouses import warehouses_bp

__all__ = ["warehouses_bp"]
