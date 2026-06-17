"""Thin API boundary for reports routes.

HTTP route implementation lives in alrajhi_server.services.http_routes.reports.
The api package must remain free from SQL literals and direct data access.
"""
from alrajhi_server.services.http_routes.reports import reports_bp

__all__ = ["reports_bp"]
