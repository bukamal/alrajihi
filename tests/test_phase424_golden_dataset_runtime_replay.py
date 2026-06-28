# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def load_module(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_phase424_contract_declares_bridge_and_backlog():
    module = load_module("alrajhi_client/workspace/quality/golden_dataset_runtime_replay_contract.py", "phase424_contract")
    summary = module.contract_summary()
    assert summary["phase"] == 424
    assert summary["source_phase"] == 423
    assert summary["bridge_layer_count"] >= 6
    assert summary["implemented_adapter_count"] == 1
    assert summary["runtime_backlog_count"] == 3
    assert "dao_repository_runtime" in module.runtime_adapter_backlog()


def test_phase424_operation_stream_preserves_runtime_metadata():
    from workspace.quality.golden_dataset_runtime_replay import build_replay_operation_stream

    stream = build_replay_operation_stream()
    assert len(stream) == 14
    assert all(item["operation_id"] == item["idempotency_key"] for item in stream)
    assert all(item["branch_id"] for item in stream)
    assert {item["kind"] for item in stream} >= {"purchase_invoice", "sales_invoice", "production_order", "restaurant_order"}


def test_phase424_in_memory_replay_matches_phase423_balances():
    from workspace.quality.golden_dataset_runtime_replay import replay_failures, replay_golden_dataset, replay_summary

    result = replay_golden_dataset()
    assert not replay_failures(result)
    summary = replay_summary(result)
    assert summary["adapter_name"] == "in_memory_reference"
    assert summary["step_count"] == 14
    assert summary["gross_profit"] == "465.00"
    assert summary["total_cash"] == "1285.75"
    assert result.actual["stock_by_item_warehouse"]["MAT-RAW@WH-MAIN"] == "10.0000"


def test_phase424_duplicate_operation_is_idempotently_skipped():
    from workspace.quality.golden_dataset_runtime_replay import InMemoryGoldenReplayAdapter
    from workspace.quality.golden_dataset_scenarios import build_golden_operations

    adapter = InMemoryGoldenReplayAdapter()
    adapter.reset()
    operation = build_golden_operations()[0]
    first = adapter.apply_operation(operation, operation.operation_id)
    second = adapter.apply_operation(operation, operation.operation_id)
    assert first.status == "OK"
    assert second.status == "SKIP"
    assert adapter.collect_actual_balances()["operation_count"] == 1


def test_phase424_guard_generates_replay_outputs_and_release_gate_registered():
    result = subprocess.run([sys.executable, "tools/phase424_golden_dataset_runtime_replay_guard.py"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr

    matrix = ROOT / "tools/audit_outputs/golden_dataset_runtime_replay_matrix.csv"
    comparison = ROOT / "tools/audit_outputs/golden_dataset_runtime_replay_comparison.csv"
    steps = ROOT / "tools/audit_outputs/golden_dataset_runtime_replay_steps.json"
    actual = ROOT / "tools/audit_outputs/golden_dataset_runtime_replay_actual_balances.json"
    manifest = ROOT / "tools/audit_outputs/golden_dataset_runtime_replay_adapter_manifest.json"
    for path in (matrix, comparison, steps, actual, manifest):
        assert path.exists(), path

    with matrix.open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) >= 55
    assert all(row["status"] == "OK" for row in rows)

    payload = json.loads(actual.read_text(encoding="utf-8"))
    assert payload["totals"]["gross_profit"] == "465.00"
    assert len(json.loads(steps.read_text(encoding="utf-8"))) == 14
    adapter_manifest = json.loads(manifest.read_text(encoding="utf-8"))
    assert adapter_manifest["runtime_adapter_backlog"] == ["dao_repository_runtime", "http_api_runtime", "offline_replay_runtime"]

    gate = (ROOT / "alrajhi_client/workspace/quality/release_gate_contract.py").read_text(encoding="utf-8")
    assert "PHASE424_GOLDEN_DATASET_RUNTIME_REPLAY_BRIDGE" in gate
    assert "tools/phase424_golden_dataset_runtime_replay_guard.py" in gate
    assert "tests/test_phase424_golden_dataset_runtime_replay.py" in gate
