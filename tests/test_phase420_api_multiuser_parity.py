# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))
SERVER = ROOT / "alrajhi_server"
if str(SERVER.parent) not in sys.path:
    sys.path.insert(0, str(SERVER.parent))


def load_module(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_phase420_contract_summary_ready():
    module = load_module("alrajhi_client/workspace/quality/api_multiuser_parity_contract.py", "phase420_contract")
    summary = module.contract_summary()
    assert summary["phase"] == 420
    assert summary["mandatory_surface_count"] >= 10
    assert "workflow_gateway.py" in summary["accepted_local_only_gateways"]


def test_phase420_gateway_parity_has_no_blocking_failures():
    from workspace.quality.api_multiuser_parity_audit import blocking_parity_failures, gateway_parity_rows

    rows = gateway_parity_rows(ROOT)
    assert rows
    blocking = blocking_parity_failures(rows)
    assert not blocking, [row.gateway for row in blocking]
    critical = {"invoice_gateway.py", "sales_return_gateway.py", "purchase_return_gateway.py", "warehouse_gateway.py", "restaurant_gateway.py", "manufacturing_gateway.py", "rbac_gateway.py"}
    by_name = {row.gateway: row for row in rows}
    for gateway in critical:
        assert by_name[gateway].has_remote
        assert not by_name[gateway].missing_remote


def test_phase420_rest_client_and_server_context_extract_metadata_headers():
    rest_source = (ROOT / "alrajhi_client/database/connection_rest.py").read_text(encoding="utf-8", errors="ignore")
    assert "def _request_metadata_headers" in rest_source
    assert "Idempotency-Key" in rest_source
    assert "X-Alrajhi-Branch-Id" in rest_source
    assert "self._headers(request_headers)" in rest_source

    module = load_module("alrajhi_server/services/api_request_context.py", "phase420_api_request_context")
    ctx = module.build_api_request_context(
        headers={"Idempotency-Key": "abc", "X-Alrajhi-Branch-Id": "7", "X-Alrajhi-Offline-Replay": "1"},
        payload={},
        args={},
    )
    assert ctx.idempotency_key == "abc"
    assert ctx.branch_id == 7
    assert ctx.offline_replay is True


def test_phase420_critical_file_checks_are_true():
    from workspace.quality.api_multiuser_parity_audit import critical_file_checks

    checks = critical_file_checks(ROOT)
    assert checks
    assert all(checks.values()), {key: value for key, value in checks.items() if not value}


def test_phase420_guard_generates_matrices():
    result = subprocess.run([sys.executable, "tools/phase420_api_multiuser_parity_guard.py"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    matrix = ROOT / "tools/audit_outputs/api_multiuser_parity_matrix.csv"
    gateway_matrix = ROOT / "tools/audit_outputs/api_multiuser_gateway_parity.csv"
    assert matrix.exists()
    assert gateway_matrix.exists()
    with matrix.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) >= 35
    assert all(row["status"] == "OK" for row in rows)
