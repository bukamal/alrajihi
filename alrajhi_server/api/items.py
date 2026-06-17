"""Thin API boundary for items routes.

HTTP route implementation lives in alrajhi_server.services.http_routes.items.
The api package must remain free from SQL literals and direct data access.

Exported inventory ledger endpoints are implemented behind the repository route
module and intentionally documented here for Phase 32 static guards:
- /inventory-ledger/health
- /inventory-ledger/snapshot
"""
from alrajhi_server.services.http_routes.items import items_bp

__all__ = ["items_bp"]
