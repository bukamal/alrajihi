# -*- coding: utf-8 -*-
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _prepare_client_import_path():
    client = ROOT / "alrajhi_client"
    if str(client) not in sys.path:
        sys.path.insert(0, str(client))
    existing = sys.modules.get("workspace")
    if existing is not None and not hasattr(existing, "__path__"):
        sys.modules.pop("workspace", None)


def test_rbac_contract_collects_shell_list_report_and_operational_permissions():
    _prepare_client_import_path()
    from workspace.security.rbac_contract import required_permission_keys, role_seed_map, validate_rbac_contract

    keys = set(required_permission_keys())
    assert validate_rbac_contract() == {}
    for expected in (
        "sales_invoices.update",
        "purchase_returns.update",
        "items.print",
        "reports.print",
        "pos.receipt.print",
        "restaurant.kitchen_ticket.print",
        "warehouses.view",
        "settings.update",
    ):
        assert expected in keys
    seeds = role_seed_map()
    assert set(seeds["admin"]) == keys
    assert "sales_invoices.update" in seeds["manager"]
    assert "pos.receipt.print" in seeds["cashier"]
    assert "reports.view" in seeds["viewer"]


def test_server_migration_seeds_every_contract_permission():
    _prepare_client_import_path()
    from workspace.security.rbac_contract import required_permission_keys

    text = (ROOT / "alrajhi_server/database/migrations.py").read_text(encoding="utf-8")
    seeded = set(re.findall(r"\('([^']+)',\s*'[^']+',\s*'[^']+',\s*'[^']+'\)", text))
    missing = sorted(set(required_permission_keys()) - seeded)
    assert missing == []
    assert "def migrate_phase260_rbac_contract_permissions" in text
    assert "migrate_phase260_rbac_contract_permissions(conn)" in text


def test_remote_rbac_gateway_is_used_in_client_mode():
    remote = ROOT / "alrajhi_client/gateways/remote/rbac_gateway.py"
    factory = ROOT / "alrajhi_client/gateways/rbac_gateway.py"
    rest = ROOT / "alrajhi_client/database/connection_rest.py"
    assert remote.exists()
    remote_text = remote.read_text(encoding="utf-8")
    assert "class RemoteRBACGateway" in remote_text
    assert "get_my_permissions" in remote_text
    assert "get_rbac_permissions" in remote_text
    factory_text = factory.read_text(encoding="utf-8")
    assert "RemoteRBACGateway" in factory_text
    assert "get_rest_client" in factory_text
    rest_text = rest.read_text(encoding="utf-8")
    for method in ("get_rbac_roles", "get_rbac_permissions", "get_my_permissions", "set_role_permissions", "set_user_branch_access"):
        assert method in rest_text


def test_client_fallback_role_defaults_merge_phase260_contract():
    text = (ROOT / "alrajhi_client/core/services/rbac_service.py").read_text(encoding="utf-8")
    assert "_phase260_role_seed_map" in text
    assert "DEFAULT_ROLE_PERMISSIONS" in text
    assert "sales_invoices.update" in (ROOT / "alrajhi_server/database/migrations.py").read_text(encoding="utf-8")


def test_rbac_permission_contract_audit_tool_runs_and_writes_matrix():
    tool = ROOT / "tools/rbac_permission_contract_audit.py"
    assert tool.exists()
    result = subprocess.run([sys.executable, str(tool)], cwd=str(ROOT), text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    matrix = ROOT / "tools/audit_outputs/rbac_permission_contract_matrix.csv"
    assert matrix.exists()
    content = matrix.read_text(encoding="utf-8-sig")
    assert "sales_invoices.update" in content
    assert "restaurant.kitchen_ticket.print" in content
    assert "migration_seeded" in content
