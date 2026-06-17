"""Thin service route boundary for invoices.

SQL-backed route implementation is intentionally contained in
alrajhi_server.repositories.http_route_sql.invoices so service/http boundary modules
remain free from SQL literals and direct data access.
"""
from alrajhi_server.repositories.http_route_sql.invoices import invoices_bp

__all__ = ["invoices_bp"]
