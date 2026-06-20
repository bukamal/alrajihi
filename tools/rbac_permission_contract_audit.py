#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit RBAC coverage for Document/List/Report/Operational shell contracts.

The audit is source-based and PyQt-free.  It answers:
  * Which permissions are required by shell contracts?
  * Are they declared in the server migration seed?
  * Are they reachable through the client RBAC fallback role seeds?
  * Is remote RBAC available in client/server mode?
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.security.rbac_contract import (  # noqa: E402
    rbac_contract_matrix,
    required_permission_keys,
    role_seed_map,
    validate_rbac_contract,
)

OUT_DIR = ROOT / "tools" / "audit_outputs"
OUT_FILE = OUT_DIR / "rbac_permission_contract_matrix.csv"
MIGRATIONS = ROOT / "alrajhi_server" / "database" / "migrations.py"
REMOTE_GATEWAY = ROOT / "alrajhi_client" / "gateways" / "remote" / "rbac_gateway.py"
GATEWAY_FACTORY = ROOT / "alrajhi_client" / "gateways" / "rbac_gateway.py"
REST_CLIENT = ROOT / "alrajhi_client" / "database" / "connection_rest.py"


def migration_permission_keys() -> set[str]:
    text = MIGRATIONS.read_text(encoding="utf-8") if MIGRATIONS.exists() else ""
    return set(re.findall(r"permissions\(key,module,action,description\) VALUES \('([^']+)'", text)) | set(re.findall(r"\('([^']+)',\s*'[^']+',\s*'[^']+',\s*'[^']+'\)", text))


def assert_remote_rbac_ready() -> list[str]:
    issues: list[str] = []
    if not REMOTE_GATEWAY.exists():
        issues.append("missing alrajhi_client/gateways/remote/rbac_gateway.py")
    else:
        remote_text = REMOTE_GATEWAY.read_text(encoding="utf-8")
        for needle in ("class RemoteRBACGateway", "get_my_permissions", "get_rbac_roles", "get_rbac_permissions"):
            if needle not in remote_text:
                issues.append(f"remote gateway missing {needle}")
    factory_text = GATEWAY_FACTORY.read_text(encoding="utf-8") if GATEWAY_FACTORY.exists() else ""
    if "RemoteRBACGateway" not in factory_text or "get_rest_client" not in factory_text:
        issues.append("create_rbac_gateway does not instantiate RemoteRBACGateway in client mode")
    rest_text = REST_CLIENT.read_text(encoding="utf-8") if REST_CLIENT.exists() else ""
    for needle in ("get_rbac_roles", "get_rbac_permissions", "get_my_permissions", "set_role_permissions", "set_user_branch_access"):
        if needle not in rest_text:
            issues.append(f"RestClient missing {needle}")
    return issues


def write_matrix() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = rbac_contract_matrix()
    registered = migration_permission_keys()
    for row in rows:
        row["migration_seeded"] = row["key"] in registered
    fieldnames = list(rows[0].keys()) if rows else []
    with OUT_FILE.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    keys = set(required_permission_keys())
    registered = migration_permission_keys()
    issues = validate_rbac_contract(registered_keys=registered)
    remote_issues = assert_remote_rbac_ready()
    if remote_issues:
        issues["remote_rbac"] = remote_issues

    seeds = role_seed_map()
    if "admin" not in seeds or set(seeds.get("admin", ())) != keys:
        issues.setdefault("role_seed_admin", []).append("admin role seed must cover every shell permission")
    for role in ("manager", "accountant", "cashier", "viewer"):
        if role not in seeds:
            issues.setdefault("role_seed_missing", []).append(role)

    write_matrix()
    if issues:
        print("RBAC permission contract audit FAILED")
        for group, values in issues.items():
            print(f"[{group}]")
            for value in values:
                print(f"  - {value}")
        return 1
    print(f"RBAC permission contract audit OK: {len(keys)} permissions; matrix={OUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
