# -*- coding: utf-8 -*-
"""Static API and multi-user parity audit helpers for Phase420."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from workspace.quality.api_multiuser_parity_contract import API_MULTIUSER_PARITY_CONTRACT

ROOT = Path(__file__).resolve().parents[3]
GATEWAYS = ROOT / "alrajhi_client" / "gateways"
SERVER = ROOT / "alrajhi_server"


@dataclass(frozen=True)
class GatewayParityRow:
    gateway: str
    has_local: bool
    has_remote: bool
    abstract_methods: tuple[str, ...]
    missing_local: tuple[str, ...]
    missing_remote: tuple[str, ...]
    accepted_local_only: bool = False

    @property
    def ok(self) -> bool:
        if self.missing_local:
            return False
        if self.missing_remote and not self.accepted_local_only:
            return False
        return True


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _class_methods(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    try:
        tree = ast.parse(_read(path))
    except SyntaxError:
        return ()
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                    names.append(item.name)
    return tuple(sorted(set(names)))


def gateway_parity_rows(root: Path | None = None) -> tuple[GatewayParityRow, ...]:
    base = (root or ROOT) / "alrajhi_client" / "gateways"
    accepted = set(API_MULTIUSER_PARITY_CONTRACT["accepted_local_only_gateways"])
    rows: list[GatewayParityRow] = []
    for gateway_path in sorted(base.glob("*_gateway.py")):
        gateway = gateway_path.name
        local_path = base / "local" / gateway
        remote_path = base / "remote" / gateway
        abstract_methods = _class_methods(gateway_path)
        local_methods = set(_class_methods(local_path))
        remote_methods = set(_class_methods(remote_path))
        rows.append(GatewayParityRow(
            gateway=gateway,
            has_local=local_path.exists(),
            has_remote=remote_path.exists(),
            abstract_methods=abstract_methods,
            missing_local=tuple(sorted(set(abstract_methods) - local_methods)),
            missing_remote=tuple(sorted(set(abstract_methods) - remote_methods)),
            accepted_local_only=gateway in accepted,
        ))
    return tuple(rows)


def route_files(root: Path | None = None) -> tuple[Path, ...]:
    server = (root or ROOT) / "alrajhi_server"
    files = list((server / "api").glob("*.py")) + list((server / "repositories" / "http_route_sql").glob("*.py")) + list((server / "services" / "http_routes").glob("*.py"))
    return tuple(sorted({p for p in files if p.exists()}))


def api_route_summary(root: Path | None = None) -> dict[str, object]:
    route_count = 0
    jwt_count = 0
    permission_markers = 0
    branch_markers = 0
    audit_markers = 0
    for path in route_files(root):
        src = _read(path)
        route_count += src.count("@") and src.count(".route(")
        jwt_count += src.count("@jwt_required") + src.count("jwt_required()")
        permission_markers += src.count("permission_required") + src.count("_has_permission") + src.count("Permission denied")
        branch_markers += src.count("branch_access_policy") + src.count("BranchAccessError") + src.count("scope_sql") + src.count("_require_")
        audit_markers += src.count("audit_log(") + src.count("audit_trail")
    return {
        "route_count": route_count,
        "jwt_markers": jwt_count,
        "permission_markers": permission_markers,
        "branch_markers": branch_markers,
        "audit_markers": audit_markers,
    }


def critical_file_checks(root: Path | None = None) -> dict[str, bool]:
    base = root or ROOT
    rest = _read(base / "alrajhi_client" / "database" / "connection_rest.py")
    replay = _read(base / "alrajhi_client" / "workspace" / "sync" / "replay_safety.py")
    offline = _read(base / "alrajhi_client" / "workspace" / "sync" / "offline_sync_contract.py")
    conn = _read(base / "alrajhi_client" / "database" / "connection.py")
    invoice_route = _read(base / "alrajhi_server" / "repositories" / "http_route_sql" / "invoices.py")
    request_context = _read(base / "alrajhi_server" / "services" / "api_request_context.py")
    branch_policy = _read(base / "alrajhi_server" / "services" / "branch_access_policy.py")
    return {
        "rest_authorization_header": "Authorization" in rest and "Bearer" in rest,
        "rest_metadata_headers": "_request_metadata_headers" in rest and "Idempotency-Key" in rest and "X-Alrajhi-Branch-Id" in rest,
        "rest_uses_metadata_headers": "request_headers = self._request_metadata_headers" in rest and "self._headers(request_headers)" in rest,
        "offline_replay_headers": "replay_headers" in replay and "X-Alrajhi-Offline-Replay" in replay and "Idempotency-Key" in replay,
        "offline_descriptor_validation": "validate_offline_sync_descriptors" in offline and "queueable without idempotency_key" in offline,
        "offline_queue_duplicate_collapse": "SELECT id FROM queue WHERE session_id=? AND idempotency_key=?" in conn,
        "server_request_context_helper": "ApiRequestContext" in request_context and "build_api_request_context" in request_context,
        "invoice_branch_scope": "branch_access_policy.scope_sql" in invoice_route and "_effective_payload_branch" in invoice_route and "_require_invoice_branch" in invoice_route,
        "invoice_request_context_applied": "current_api_request_context" in invoice_route and "_apply_request_context_defaults(data)" in invoice_route,
        "invoice_permissions": "_has_permission" in invoice_route and "approval.approve" in invoice_route and "accounting.post" in invoice_route,
        "invoice_audit_log": "audit_log(" in invoice_route,
        "server_branch_policy": "class ServerBranchAccessPolicy" in branch_policy and "scope_sql" in branch_policy and "require" in branch_policy,
    }


def accepted_remote_gaps(rows: Iterable[GatewayParityRow]) -> tuple[GatewayParityRow, ...]:
    return tuple(row for row in rows if row.missing_remote and row.accepted_local_only)


def blocking_parity_failures(rows: Iterable[GatewayParityRow]) -> tuple[GatewayParityRow, ...]:
    return tuple(row for row in rows if not row.ok)


__all__ = [
    "GatewayParityRow",
    "gateway_parity_rows",
    "api_route_summary",
    "critical_file_checks",
    "accepted_remote_gaps",
    "blocking_parity_failures",
]
