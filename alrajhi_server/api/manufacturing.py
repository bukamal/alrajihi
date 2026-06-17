"""Thin API boundary for manufacturing routes.

HTTP route implementation lives in alrajhi_server.services.http_routes.manufacturing.
The api package must remain free from SQL literals and direct data access.
"""
from alrajhi_server.services.http_routes.manufacturing import manufacturing_bp

__all__ = ["manufacturing_bp"]
