"""Thin service route boundary for reports.

SQL-backed route implementation is intentionally contained in
alrajhi_server.repositories.http_route_sql.reports so service/http boundary modules
remain free from SQL literals and direct data access.
"""
from alrajhi_server.repositories.http_route_sql.reports import reports_bp

__all__ = ["reports_bp"]
