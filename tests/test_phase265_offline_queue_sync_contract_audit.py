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


def test_offline_sync_contract_declares_queueable_and_blocked_surfaces():
    _prepare_client_import_path()
    from workspace.sync.offline_sync_contract import (
        OFFLINE_POLICY_BLOCK,
        OFFLINE_POLICY_QUEUE,
        OFFLINE_POLICY_READ_ONLY,
        offline_descriptor_for,
        offline_sync_descriptors,
        queueable_api_prefixes,
        validate_offline_sync_descriptors,
    )

    assert validate_offline_sync_descriptors() == []
    keys = {d.surface_key: d for d in offline_sync_descriptors()}
    assert keys["document.sales_invoice"].offline_policy == OFFLINE_POLICY_QUEUE
    assert keys["document.purchase_return"].offline_policy == OFFLINE_POLICY_QUEUE
    assert keys["audit.audit_log"].offline_policy == OFFLINE_POLICY_QUEUE
    assert keys["operational.restaurant.session_order_payment"].offline_policy == OFFLINE_POLICY_BLOCK
    assert keys["operational.pos.shift_cashbox"].offline_policy == OFFLINE_POLICY_BLOCK
    assert offline_descriptor_for("document.warehouse_transfer").offline_policy != OFFLINE_POLICY_QUEUE

    prefixes = set(queueable_api_prefixes())
    for prefix in ("/api/invoices", "/api/returns/sales", "/api/returns/purchase", "/api/items", "/api/audit_log"):
        assert prefix in prefixes

    report_descriptors = [d for d in offline_sync_descriptors() if d.surface_family == "report"]
    assert report_descriptors
    assert all(d.offline_policy == OFFLINE_POLICY_READ_ONLY for d in report_descriptors)


def test_offline_decision_matches_rest_client_queueable_endpoints():
    _prepare_client_import_path()
    from workspace.sync.offline_sync_contract import offline_decision_for_api

    assert offline_decision_for_api("/api/invoices", "POST").queueable is True
    assert offline_decision_for_api("/api/invoices/12", "PUT").queueable is True
    assert offline_decision_for_api("/api/returns/sales/3", "DELETE").queueable is True
    assert offline_decision_for_api("/api/audit_log", "POST").queueable is True
    assert offline_decision_for_api("/api/reports/summary", "GET").queueable is False
    assert offline_decision_for_api("/api/restaurant/sessions", "POST").queueable is False
    assert offline_decision_for_api("/api/pos_shifts", "POST").queueable is False


def test_offline_queue_manager_uses_contract_and_stores_sync_metadata():
    connection = _read("alrajhi_client/database/connection.py")
    assert "from workspace.sync.offline_sync_contract import offline_decision_for_api, queueable_api_prefixes" in connection
    assert "QUEUEABLE_PREFIXES = tuple(queueable_api_prefixes())" in connection
    assert "def queue_decision" in connection
    for marker in ("payload_hash", "idempotency_key", "sync_scope", "conflict_policy", "replay_priority", "branch_id"):
        assert marker in connection
    assert "ORDER BY COALESCE(replay_priority,50), id" in connection


def test_audit_log_is_queueable_in_rest_client_and_offline_queue_contract():
    rest = _read("alrajhi_client/database/connection_rest.py")
    contract = _read("alrajhi_client/workspace/sync/offline_sync_contract.py")
    assert "def post_audit_log" in rest
    assert "queue_on_failure=True" in rest
    assert '"/api/audit_log"' in contract
    assert "audit.audit_log" in contract


def test_offline_sync_matrix_tool_runs_and_writes_csv():
    tool = ROOT / "tools" / "offline_sync_contract_audit.py"
    assert tool.exists()
    result = subprocess.run([sys.executable, str(tool)], cwd=str(ROOT), text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    matrix = ROOT / "tools" / "audit_outputs" / "offline_sync_contract_matrix.csv"
    assert matrix.exists()
    content = matrix.read_text(encoding="utf-8-sig")
    assert "document.sales_invoice" in content
    assert "operational.restaurant.session_order_payment" in content
    assert "audit.audit_log" in content
    assert "offline_policy" in content
    assert "conflict_policy" in content
