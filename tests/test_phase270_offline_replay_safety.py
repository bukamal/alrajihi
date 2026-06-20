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


def test_replay_safety_contract_classifies_conflicts_and_permanent_errors():
    _prepare_client_import_path()
    from workspace.sync.replay_safety import (
        REPLAY_STATUS_CONFLICT,
        REPLAY_STATUS_FAILED,
        REPLAY_STATUS_RETRY,
        build_idempotency_key,
        classify_replay_error,
        replay_headers,
    )

    key = build_idempotency_key(surface_key="document.sales_invoice", payload_hash="abc", data={"invoice_number": "SAL-1"})
    assert key == "document.sales_invoice:ref:SAL-1"
    assert build_idempotency_key(surface_key="document.material", payload_hash="abc") == "document.material:hash:abc"

    assert classify_replay_error("API error 409 at http://server: conflict", "manual_review").status == REPLAY_STATUS_CONFLICT
    assert classify_replay_error("API error 422 at http://server: invalid", "manual_review").status == REPLAY_STATUS_FAILED
    assert classify_replay_error("timeout", "manual_review").status == REPLAY_STATUS_RETRY

    headers = replay_headers({"idempotency_key": key, "sync_scope": "document.sales_invoice", "conflict_policy": "idempotent_create", "branch_id": 3})
    assert headers["Idempotency-Key"] == key
    assert headers["X-Alrajhi-Offline-Replay"] == "1"
    assert headers["X-Alrajhi-Branch-Id"] == "3"


def test_offline_queue_uses_replay_safety_and_duplicate_collapse():
    connection = _read("alrajhi_client/database/connection.py")
    assert "from workspace.sync.replay_safety import build_idempotency_key" in connection
    assert "SELECT id FROM queue WHERE session_id=? AND idempotency_key=? AND status='pending'" in connection
    assert "def mark_conflict" in connection
    assert "replay_locked_at" in connection
    assert "manual_review_reason" in connection


def test_rest_client_and_replay_gateway_send_idempotency_headers():
    rest = _read("alrajhi_client/database/connection_rest.py")
    gateway = _read("alrajhi_client/gateways/local/offline_queue_gateway.py")
    assert "def _headers(self, extra_headers=None)" in rest
    assert "extra_headers=extra_headers" not in rest  # request must call _headers(extra_headers), not forward arbitrary kwargs
    assert "headers=self._headers(extra_headers)" in rest
    assert "replay_headers(req)" in gateway
    assert "classify_replay_error" in gateway
    assert "mark_conflict" in gateway


def test_offline_replay_safety_audit_tool_runs_and_writes_csv():
    tool = ROOT / "tools" / "offline_replay_safety_audit.py"
    assert tool.exists()
    result = subprocess.run([sys.executable, str(tool)], cwd=str(ROOT), text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    matrix = ROOT / "tools" / "audit_outputs" / "offline_replay_safety_matrix.csv"
    assert matrix.exists()
    content = matrix.read_text(encoding="utf-8-sig")
    assert "idempotency_key_policy" in content
    assert "conflict_status_codes" in content
    assert "document.sales_invoice" in content
    assert "audit.audit_log" in content
