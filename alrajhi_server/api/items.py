"""Thin API boundary for items routes.

HTTP route implementation lives in alrajhi_server.services.http_routes.items.
The api package must remain free from SQL literals and direct data access.
"""
from alrajhi_server.services.http_routes.items import items_bp

__all__ = ["items_bp"]
