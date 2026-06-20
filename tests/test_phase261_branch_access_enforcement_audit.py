# -*- coding: utf-8 -*-
from __future__ import annotations

import pathlib
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


def test_branch_access_contract_collects_document_list_report_operational_surfaces():
    _prepare_client_import_path()
    from workspace.branches.branch_access_contract import (
        BRANCH_REQUIRED,
        branch_access_descriptor_map,
        branch_scoped_descriptors,
        validate_branch_access_contract,
    )
    from workspace.security.rbac_contract import required_permission_keys

    issues = validate_branch_access_contract(rbac_branch_scoped_keys=set(required_permission_keys()))
    assert issues == {}
    mapping = branch_access_descriptor_map()
    assert mapping["document:sales_invoice"].branch_policy == BRANCH_REQUIRED
    assert mapping["document:sales_invoice"].requires_payload_branch is True
    assert mapping["list:sales_invoices"].requires_server_filter is True
    assert mapping["operational:pos"].requires_allowed_branch_check is True
    assert mapping["operational:restaurant"].requires_payload_branch is True
    assert any(d.key.startswith("report:") for d in branch_scoped_descriptors())


def test_branch_access_policy_runtime_helper_contract():
    _prepare_client_import_path()
    from workspace.branches.branch_access_policy import BranchAccessDenied, BranchAccessPolicy

    policy = BranchAccessPolicy()
    for method in (
        "can_view_all_branches",
        "allowed_branch_ids",
        "can_access_branch",
        "effective_branch_id",
        "require_branch_access",
        "ensure_payload_branch",
        "scope_query_params",
        "filter_records",
    ):
        assert hasattr(policy, method)
    assert issubclass(BranchAccessDenied, PermissionError)


def test_server_branch_access_policy_exists_for_api_filters():
    server_policy = ROOT / "alrajhi_server/services/branch_access_policy.py"
    assert server_policy.exists()
    text = server_policy.read_text(encoding="utf-8")
    for needle in ("class ServerBranchAccessPolicy", "scope_sql", "require", "allowed_branch_ids", "branches.view_all"):
        assert needle in text


def test_rbac_me_and_rest_client_expose_branch_scope():
    rbac_api = (ROOT / "alrajhi_server/api/rbac.py").read_text(encoding="utf-8")
    assert "can_view_all_branches" in rbac_api
    assert "branch_scope_mode" in rbac_api
    rest = (ROOT / "alrajhi_client/database/connection_rest.py").read_text(encoding="utf-8")
    for method in ("get_user_branch_access", "get_my_branch_scope", "set_user_branch_access"):
        assert method in rest
    branch_service = (ROOT / "alrajhi_client/core/services/branch_service.py").read_text(encoding="utf-8")
    for needle in ("can_access_branch", "require_branch_access", "scoped_query_params", "branch_access_policy.allowed_branch_ids"):
        assert needle in branch_service


def test_branch_access_contract_audit_tool_runs_and_writes_matrix():
    tool = ROOT / "tools/branch_access_contract_audit.py"
    assert tool.exists()
    result = subprocess.run([sys.executable, str(tool)], cwd=str(ROOT), text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    matrix = ROOT / "tools/audit_outputs/branch_access_contract_matrix.csv"
    assert matrix.exists()
    content = matrix.read_text(encoding="utf-8-sig")
    assert "document:sales_invoice" in content
    assert "operational:restaurant" in content
    assert "requires_server_filter" in content
