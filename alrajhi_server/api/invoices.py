"""Thin API boundary for invoices routes.

HTTP route implementation lives in alrajhi_server.services.http_routes.invoices.
The api package must remain free from SQL literals and direct data access.
"""
from alrajhi_server.services.http_routes.invoices import invoices_bp

__all__ = ["invoices_bp"]
