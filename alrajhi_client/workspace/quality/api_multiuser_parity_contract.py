# -*- coding: utf-8 -*-
"""Phase 420 API / multi-user parity contract.

This contract is intentionally static and import-light.  It defines the minimum
multi-user/API invariants that must be true before more UI work continues:
local/remote gateway parity is known, critical writes carry branch/idempotency
metadata, offline replay has conflict policy, and server routes keep branch/RBAC
checks at the server boundary.
"""
from __future__ import annotations

API_MULTIUSER_PARITY_CONTRACT = {
    "phase": 420,
    "name": "API / Multi-user Parity Audit & Hardening",
    "mandatory_surfaces": (
        "invoices",
        "sales_returns",
        "purchase_returns",
        "vouchers",
        "expenses",
        "items",
        "warehouses",
        "branches",
        "restaurant",
        "manufacturing",
        "reports",
        "rbac",
        "settings",
    ),
    "server_invariants": (
        "jwt_required_on_api_routes",
        "branch_scope_on_branch_bound_queries",
        "branch_require_on_branch_bound_mutations",
        "permission_required_or_repository_permission_check_on_sensitive_actions",
        "audit_log_on_financial_or_inventory_mutations",
    ),
    "client_invariants": (
        "rest_client_sends_authorization_header",
        "rest_client_sends_idempotency_headers_when_available",
        "rest_client_sends_branch_scope_headers_when_available",
        "offline_queue_collapse_uses_idempotency_key",
        "queueable_offline_surfaces_declare_conflict_policy",
    ),
    "accepted_local_only_gateways": (
        "accounting_gateway.py",
        "approval_gateway.py",
        "monitoring_gateway.py",
        "offline_queue_gateway.py",
        "system_gateway.py",
        "workflow_gateway.py",
    ),
    "known_followup_backlog": (
        "remote approval/workflow gateway parity is intentionally tracked but not force-failed in Phase420",
        "server-side idempotency persistence is not yet a database-level uniqueness guarantee",
        "full concurrent edit optimistic locking remains a follow-up hardening phase",
    ),
}


def contract_summary() -> dict[str, object]:
    return {
        "phase": API_MULTIUSER_PARITY_CONTRACT["phase"],
        "name": API_MULTIUSER_PARITY_CONTRACT["name"],
        "mandatory_surface_count": len(API_MULTIUSER_PARITY_CONTRACT["mandatory_surfaces"]),
        "server_invariant_count": len(API_MULTIUSER_PARITY_CONTRACT["server_invariants"]),
        "client_invariant_count": len(API_MULTIUSER_PARITY_CONTRACT["client_invariants"]),
        "accepted_local_only_gateways": tuple(API_MULTIUSER_PARITY_CONTRACT["accepted_local_only_gateways"]),
    }


__all__ = ["API_MULTIUSER_PARITY_CONTRACT", "contract_summary"]
