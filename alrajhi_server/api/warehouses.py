"""Thin API boundary for warehouses routes.

HTTP route implementation lives in alrajhi_server.services.http_routes.warehouses.
The api package must remain free from SQL literals and direct data access.
"""
from alrajhi_server.services.http_routes.warehouses import warehouses_bp

__all__ = ["warehouses_bp"]
