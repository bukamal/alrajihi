#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

OUT = ROOT / "tools" / "audit_outputs" / "api_multiuser_parity_matrix.csv"
GATEWAY_OUT = ROOT / "tools" / "audit_outputs" / "api_multiuser_gateway_parity.csv"


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def add(rows: list[dict[str, str]], key: str, category: str, path: str, ok: bool, detail: str) -> None:
    rows.append({"key": key, "category": category, "path": path, "status": "OK" if ok else "FAIL", "detail": detail})


def parses(rel: str) -> bool:
    try:
        ast.parse(read(rel))
        return True
    except SyntaxError:
        return False


def main() -> int:
    from workspace.quality.api_multiuser_parity_audit import (
        accepted_remote_gaps,
        api_route_summary,
        blocking_parity_failures,
        critical_file_checks,
        gateway_parity_rows,
    )
    from workspace.quality.api_multiuser_parity_contract import API_MULTIUSER_PARITY_CONTRACT

    rows: list[dict[str, str]] = []
    required = [
        "PHASE420_API_MULTIUSER_PARITY_AUDIT_HARDENING.md",
        "alrajhi_client/workspace/quality/api_multiuser_parity_contract.py",
        "alrajhi_client/workspace/quality/api_multiuser_parity_audit.py",
        "alrajhi_client/database/connection_rest.py",
        "alrajhi_server/services/api_request_context.py",
        "alrajhi_server/repositories/http_route_sql/invoices.py",
        "tools/phase420_api_multiuser_parity_guard.py",
        "tests/test_phase420_api_multiuser_parity.py",
    ]
    for rel in required:
        add(rows, f"exists::{rel}", "file", rel, (ROOT / rel).exists(), "required Phase420 file exists")

    for rel in (
        "alrajhi_client/workspace/quality/api_multiuser_parity_contract.py",
        "alrajhi_client/workspace/quality/api_multiuser_parity_audit.py",
        "alrajhi_client/database/connection_rest.py",
        "alrajhi_server/services/api_request_context.py",
        "alrajhi_server/repositories/http_route_sql/invoices.py",
        "tools/phase420_api_multiuser_parity_guard.py",
    ):
        add(rows, f"ast::{rel}", "syntax", rel, parses(rel), "source parses")

    contract = read("alrajhi_client/workspace/quality/api_multiuser_parity_contract.py")
    release = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    add(rows, "contract_phase", "contract", "alrajhi_client/workspace/quality/api_multiuser_parity_contract.py", "API_MULTIUSER_PARITY_CONTRACT" in contract and '"phase": 420' in contract, "Phase420 contract is declared")
    add(rows, "contract_surfaces", "contract", "alrajhi_client/workspace/quality/api_multiuser_parity_contract.py", len(API_MULTIUSER_PARITY_CONTRACT["mandatory_surfaces"]) >= 10, "mandatory API/multi-user surfaces are declared")
    add(rows, "contract_known_backlog", "contract", "alrajhi_client/workspace/quality/api_multiuser_parity_contract.py", "known_followup_backlog" in contract and "optimistic locking" in contract, "follow-up risks are explicit")

    parity = gateway_parity_rows(ROOT)
    blocking = blocking_parity_failures(parity)
    accepted = accepted_remote_gaps(parity)
    add(rows, "gateway_parity_no_blocking_failures", "gateway", "alrajhi_client/gateways", not blocking, f"blocking parity failures={len(blocking)}")
    add(rows, "gateway_parity_known_local_only_visible", "gateway", "alrajhi_client/gateways", len(accepted) >= 1, f"accepted local-only remote gaps={len(accepted)}")
    add(rows, "gateway_parity_remote_core_present", "gateway", "alrajhi_client/gateways/remote", all(row.has_remote for row in parity if row.gateway in {"invoice_gateway.py", "sales_return_gateway.py", "purchase_return_gateway.py", "warehouse_gateway.py", "restaurant_gateway.py", "manufacturing_gateway.py", "rbac_gateway.py"}), "critical remote gateways exist")

    checks = critical_file_checks(ROOT)
    for key, ok in checks.items():
        add(rows, key, "hardening", "phase420_static_surfaces", bool(ok), f"{key} is present")

    summary = api_route_summary(ROOT)
    add(rows, "server_routes_present", "server", "alrajhi_server", int(summary["route_count"]) >= 20, f"route count={summary['route_count']}")
    add(rows, "server_jwt_markers_present", "server", "alrajhi_server", int(summary["jwt_markers"]) >= 20, f"jwt markers={summary['jwt_markers']}")
    add(rows, "server_permission_markers_present", "server", "alrajhi_server", int(summary["permission_markers"]) >= 5, f"permission markers={summary['permission_markers']}")
    add(rows, "server_branch_markers_present", "server", "alrajhi_server", int(summary["branch_markers"]) >= 10, f"branch markers={summary['branch_markers']}")
    add(rows, "server_audit_markers_present", "server", "alrajhi_server", int(summary["audit_markers"]) >= 5, f"audit markers={summary['audit_markers']}")

    add(rows, "release_doc", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "PHASE420_API_MULTIUSER_PARITY_AUDIT_HARDENING" in release, "Phase420 doc registered")
    add(rows, "release_test", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "tests/test_phase420_api_multiuser_parity.py" in release, "Phase420 test registered")
    add(rows, "release_check", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "api_multiuser_parity" in release and "phase=420" in release, "Phase420 release check registered")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader(); writer.writerows(rows)

    with GATEWAY_OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["gateway", "has_local", "has_remote", "abstract_methods", "missing_local", "missing_remote", "accepted_local_only", "status"])
        writer.writeheader()
        for row in parity:
            writer.writerow({
                "gateway": row.gateway,
                "has_local": row.has_local,
                "has_remote": row.has_remote,
                "abstract_methods": ",".join(row.abstract_methods),
                "missing_local": ",".join(row.missing_local),
                "missing_remote": ",".join(row.missing_remote),
                "accepted_local_only": row.accepted_local_only,
                "status": "OK" if row.ok else "FAIL",
            })

    failures = [row for row in rows if row["status"] != "OK"]
    print(f"Phase420 API/multi-user parity checks: {len(rows)} checks, failures={len(failures)}")
    print(f"Phase420 gateway rows: {len(parity)}, accepted local-only gaps={len(accepted)}, blocking failures={len(blocking)}")
    for row in failures:
        print(f"FAIL {row['key']}: {row['detail']}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
