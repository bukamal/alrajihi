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


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_audit_contract_collects_document_list_report_and_operational_events():
    _prepare_client_import_path()
    from workspace.audit.audit_contract import audit_event_descriptors, validate_audit_event_descriptors

    events = {event.event_key: event for event in audit_event_descriptors()}
    assert validate_audit_event_descriptors() == []
    for key in (
        "document.sales_invoice.print",
        "document.purchase_return.save",
        "list.materials.export",
        "report.income_statement.print",
        "operational.pos.checkout",
        "operational.restaurant.print_kitchen_ticket",
    ):
        assert key in events
    assert events["operational.pos.checkout"].permission_key == "pos.use"
    assert events["operational.restaurant.print_kitchen_ticket"].permission_key == "restaurant.kitchen_ticket.print"
    assert events["document.sales_invoice.print"].branch_scoped is True


def test_audit_trail_matrix_tool_runs_and_writes_csv():
    tool = ROOT / "tools" / "audit_trail_contract_audit.py"
    assert tool.exists()
    result = subprocess.run([sys.executable, str(tool)], cwd=str(ROOT), text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    matrix = ROOT / "tools" / "audit_outputs" / "audit_trail_contract_matrix.csv"
    assert matrix.exists()
    content = matrix.read_text(encoding="utf-8-sig")
    assert "document.sales_invoice.print" in content
    assert "operational.restaurant.print_kitchen_ticket" in content
    assert "permission_key" in content
    assert "branch_scoped" in content


def test_audit_gateways_support_structured_shell_metadata_and_remote_post():
    base = _read("alrajhi_client/gateways/audit_gateway.py")
    local = _read("alrajhi_client/gateways/local/audit_gateway.py")
    remote = _read("alrajhi_client/gateways/remote/audit_gateway.py")
    rest = _read("alrajhi_client/database/connection_rest.py")
    service = _read("alrajhi_client/core/services/audit_service.py")
    for marker in ("audit_scope", "permission_key", "branch_id", "event_category"):
        assert marker in base
        assert marker in local
        assert marker in remote
        assert marker in service
    assert "def post_audit_log" in rest
    assert "POST', '/api/audit_log'" in rest
    assert "post_audit_log" in remote


def test_server_accepts_client_audit_events_and_migrates_metadata_columns():
    api = _read("alrajhi_server/api/audit_log.py")
    utils = _read("alrajhi_server/api/audit_utils.py")
    migrations = _read("alrajhi_server/database/migrations.py")
    helper = _read("alrajhi_server/services/audit_trail_policy.py")
    assert "@audit_bp.route('/audit_log', methods=['POST'])" in api
    assert "@jwt_required()" in api
    for marker in ("audit_scope", "permission_key", "branch_id", "event_category"):
        assert marker in api
        assert marker in utils
        assert marker in migrations
    assert "def migrate_phase264_audit_contract_columns" in migrations
    assert "migrate_phase264_audit_contract_columns(conn)" in migrations
    assert "def audit_api_event" in helper
    assert "def audit_print_export" in helper


def test_workspace_and_operational_shells_emit_audit_events():
    main_window = _read("alrajhi_client/views/main_window.py")
    operational = _read("alrajhi_client/workspace/operational/operational_shell_contract.py")
    policy = _read("alrajhi_client/workspace/audit/audit_event_policy.py")
    assert "def _audit_current_tab_action" in main_window
    assert "log_workspace_event" in main_window
    assert "Workspace action denied" in main_window
    assert "Workspace action executed" in main_window
    assert "def audit_operation" in operational
    assert "OPERATIONAL_SHELL" in operational
    assert "DENIED_" in operational
    assert "def log_contract_event" in policy
