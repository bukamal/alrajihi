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

OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX = OUT_DIR / "golden_dataset_runtime_replay_matrix.csv"


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def parses(rel: str) -> bool:
    try:
        ast.parse(read(rel))
        return True
    except SyntaxError:
        return False


def add(rows: list[dict[str, str]], key: str, category: str, path: str, ok: bool, detail: str) -> None:
    rows.append({"key": key, "category": category, "path": path, "status": "OK" if ok else "FAIL", "detail": detail})


def main() -> int:
    from workspace.quality.golden_dataset_runtime_replay_contract import (
        GOLDEN_DATASET_RUNTIME_REPLAY_CONTRACT,
        contract_summary,
        required_bridge_layers,
        runtime_adapter_backlog,
    )
    from workspace.quality.golden_dataset_runtime_replay import (
        build_adapter_manifest,
        build_replay_operation_stream,
        export_runtime_replay_outputs,
        replay_failures,
        replay_golden_dataset,
        replay_summary,
    )

    rows: list[dict[str, str]] = []
    required = [
        "PHASE424_GOLDEN_DATASET_RUNTIME_REPLAY_BRIDGE.md",
        "alrajhi_client/workspace/quality/golden_dataset_runtime_replay_contract.py",
        "alrajhi_client/workspace/quality/golden_dataset_runtime_replay.py",
        "tools/phase424_golden_dataset_runtime_replay_guard.py",
        "tests/test_phase424_golden_dataset_runtime_replay.py",
    ]
    for rel in required:
        add(rows, f"exists::{rel}", "file", rel, (ROOT / rel).exists(), "required Phase424 file exists")
    for rel in required[1:4]:
        add(rows, f"ast::{rel}", "syntax", rel, parses(rel), "source parses")

    summary = contract_summary()
    add(rows, "contract_phase", "contract", required[1], summary["phase"] == 424, "Phase424 contract is declared")
    add(rows, "contract_source_phase", "contract", required[1], summary["source_phase"] == 423, "Phase424 consumes Phase423 golden dataset")
    add(rows, "contract_bridge_layers", "contract", required[1], summary["bridge_layer_count"] >= 6, "bridge layers are declared")
    add(rows, "contract_backlog_explicit", "contract", required[1], tuple(runtime_adapter_backlog()) == ("dao_repository_runtime", "http_api_runtime", "offline_replay_runtime"), "runtime adapter backlog is explicit")
    add(rows, "contract_output_files", "contract", required[1], summary["output_file_count"] >= 5, "machine-readable outputs are declared")

    stream = build_replay_operation_stream()
    add(rows, "operation_stream_count", "replay", required[2], len(stream) == 14, "operation stream has canonical golden operation count")
    add(rows, "operation_stream_idempotency", "replay", required[2], all(item["idempotency_key"] == item["operation_id"] for item in stream), "operation stream exposes idempotency keys")
    add(rows, "operation_stream_branch_scope", "replay", required[2], all(bool(item["branch_id"]) for item in stream), "operation stream carries branch scope")

    result = replay_golden_dataset()
    replay_info = replay_summary(result)
    failures = replay_failures(result)
    add(rows, "replay_adapter", "replay", required[2], replay_info["adapter_name"] == "in_memory_reference", "reference in-memory adapter executes the replay bridge")
    add(rows, "replay_step_count", "replay", required[2], replay_info["step_count"] == 14, "all golden operations are replayed")
    add(rows, "replay_failure_count", "replay", required[2], replay_info["failures"] == 0, "expected/actual replay comparison has no failures")
    add(rows, "replay_gross_profit", "replay", required[2], replay_info["gross_profit"] == "465.00", "runtime replay gross profit matches Phase423")
    add(rows, "replay_total_cash", "replay", required[2], replay_info["total_cash"] == "1285.75", "runtime replay cash total matches Phase423")

    manifest = build_adapter_manifest()
    add(rows, "manifest_implemented_adapter", "adapter", required[2], manifest["implemented_adapters"] == ["in_memory_reference"], "implemented adapter is explicit")
    add(rows, "manifest_backlog_adapter_count", "adapter", required[2], len(manifest["runtime_adapter_backlog"]) == 3, "three runtime adapters are declared as backlog")

    exported = export_runtime_replay_outputs(OUT_DIR, result)
    for key, path in exported.items():
        add(rows, f"output::{key}", "output", str(path), Path(path).exists(), f"{key} output generated")

    # Include bridge-native matrix rows after structural checks.
    for native in result.matrix_rows:
        add(rows, f"native::{native['key']}", "native", required[2], native["status"] == "OK", str(native["detail"]))

    release = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    add(rows, "release_doc", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "PHASE424_GOLDEN_DATASET_RUNTIME_REPLAY_BRIDGE" in release, "Phase424 doc registered")
    add(rows, "release_test", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "tests/test_phase424_golden_dataset_runtime_replay.py" in release, "Phase424 test registered")
    add(rows, "release_check", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "golden_dataset_runtime_replay" in release and "phase=424" in release, "Phase424 release check registered")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with MATRIX.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader(); writer.writerows(rows)

    failed = [row for row in rows if row["status"] != "OK"]
    print(f"Phase424 golden runtime replay checks: {len(rows)} checks, failures={len(failed)}")
    print(f"Matrix: {MATRIX}")
    print(f"Exported outputs: {exported}")
    for row in failed:
        print(f"FAIL {row['key']}: {row['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
