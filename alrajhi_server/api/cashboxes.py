"""Thin API boundary for cashboxes routes.

HTTP route implementation lives in alrajhi_server.services.http_routes.cashboxes.
The api package must remain free from SQL literals and direct data access.
"""
from alrajhi_server.services.http_routes.cashboxes import cashboxes_bp

__all__ = ["cashboxes_bp"]
