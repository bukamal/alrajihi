#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit branch-access enforcement coverage for workspace shell contracts.

The audit is source/contract based and PyQt-free.  It answers:
  * Which surfaces are branch scoped?
  * Which branch source governs each surface?
  * Which surfaces require server-side filtering or payload branch checks?
  * Is branch scope data exposed through /api/rbac/me and the remote client?
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.branches.branch_access_contract import (  # noqa: E402
    branch_access_matrix,
    branch_scoped_descriptors,
    validate_branch_access_contract,
)
from workspace.security.rbac_contract import required_permission_descriptors  # noqa: E402

OUT_DIR = ROOT / "tools" / "audit_outputs"
OUT_FILE = OUT_DIR / "branch_access_contract_matrix.csv"
RBAC_API = ROOT / "alrajhi_server" / "api" / "rbac.py"
CLIENT_REST = ROOT / "alrajhi_client" / "database" / "connection_rest.py"
BRANCH_SERVICE = ROOT / "alrajhi_client" / "core" / "services" / "branch_service.py"
SERVER_POLICY = ROOT / "alrajhi_server" / "services" / "branch_access_policy.py"
CLIENT_POLICY = ROOT / "alrajhi_client" / "workspace" / "branches" / "branch_access_policy.py"


def _source_checks() -> list[str]:
    issues: list[str] = []
    rbac_text = RBAC_API.read_text(encoding="utf-8") if RBAC_API.exists() else ""
    if "can_view_all_branches" not in rbac_text or "branch_scope_mode" not in rbac_text:
        issues.append("/api/rbac/me must expose can_view_all_branches and branch_scope_mode")
    rest_text = CLIENT_REST.read_text(encoding="utf-8") if CLIENT_REST.exists() else ""
    for needle in ("get_user_branch_access", "get_my_branch_scope", "set_user_branch_access"):
        if needle not in rest_text:
            issues.append(f"RestClient missing {needle}")
    branch_service_text = BRANCH_SERVICE.read_text(encoding="utf-8") if BRANCH_SERVICE.exists() else ""
    for needle in ("can_access_branch", "require_branch_access", "scoped_query_params"):
        if needle not in branch_service_text:
            issues.append(f"BranchService missing {needle}")
    if not CLIENT_POLICY.exists():
        issues.append("missing client BranchAccessPolicy")
    if not SERVER_POLICY.exists():
        issues.append("missing server BranchAccessPolicy")
    else:
        policy_text = SERVER_POLICY.read_text(encoding="utf-8")
        for needle in ("scope_sql", "require", "allowed_branch_ids"):
            if needle not in policy_text:
                issues.append(f"ServerBranchAccessPolicy missing {needle}")
    return issues


def write_matrix() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = branch_access_matrix()
    fieldnames = list(rows[0].keys()) if rows else []
    with OUT_FILE.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    rbac_keys = {d.key for d in required_permission_descriptors()}
    issues = validate_branch_access_contract(rbac_branch_scoped_keys=rbac_keys)
    source_issues = _source_checks()
    if source_issues:
        issues["source_checks"] = source_issues

    scoped = branch_scoped_descriptors()
    if not scoped:
        issues.setdefault("branch_scoped", []).append("no branch-scoped descriptors found")
    for expected in ("document:sales_invoice", "document:purchase_invoice", "list:sales_invoices", "operational:pos", "operational:restaurant"):
        if expected not in {d.key for d in scoped}:
            issues.setdefault("missing_expected_scope", []).append(expected)

    write_matrix()
    if issues:
        print("Branch access contract audit FAILED")
        for group, values in issues.items():
            print(f"[{group}]")
            for value in values:
                print(f"  - {value}")
        return 1
    print(f"Branch access contract audit OK: {len(scoped)} branch-scoped surfaces; matrix={OUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
