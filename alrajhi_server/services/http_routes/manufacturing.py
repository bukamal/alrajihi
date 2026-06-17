"""Thin service route boundary for manufacturing.

SQL-backed route implementation is intentionally contained in
alrajhi_server.repositories.http_route_sql.manufacturing so service/http boundary modules
remain free from SQL literals and direct data access.
"""
from alrajhi_server.repositories.http_route_sql.manufacturing import manufacturing_bp

__all__ = ["manufacturing_bp"]
