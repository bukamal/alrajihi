#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

OUT = ROOT / "tools" / "audit_outputs" / "golden_dataset_scenarios_matrix.csv"
EXPECTED_OUT = ROOT / "tools" / "audit_outputs" / "golden_dataset_expected_balances.json"
OPERATIONS_OUT = ROOT / "tools" / "audit_outputs" / "golden_dataset_operations.json"


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
    from workspace.quality.golden_dataset_scenarios_contract import (
        GOLDEN_DATASET_SCENARIO_CONTRACT,
        contract_summary,
    )
    from workspace.quality.golden_dataset_scenarios import (
        build_golden_operations,
        build_golden_scenario_result,
        build_invariant_rows,
        failures,
        scenario_summary,
    )

    rows: list[dict[str, str]] = []
    required = [
        "PHASE423_GOLDEN_DATASET_ACCOUNTING_INVENTORY_SCENARIO_PACK.md",
        "alrajhi_client/workspace/quality/golden_dataset_scenarios_contract.py",
        "alrajhi_client/workspace/quality/golden_dataset_scenarios.py",
        "tools/phase423_golden_dataset_scenarios_guard.py",
        "tests/test_phase423_golden_dataset_scenarios.py",
    ]
    for rel in required:
        add(rows, f"exists::{rel}", "file", rel, (ROOT / rel).exists(), "required Phase423 file exists")
    for rel in required[1:4]:
        add(rows, f"ast::{rel}", "syntax", rel, parses(rel), "source parses")

    summary = contract_summary()
    add(rows, "contract_phase", "contract", "alrajhi_client/workspace/quality/golden_dataset_scenarios_contract.py", summary["phase"] == 423, "Phase423 contract is declared")
    add(rows, "contract_currency", "contract", "alrajhi_client/workspace/quality/golden_dataset_scenarios_contract.py", GOLDEN_DATASET_SCENARIO_CONTRACT["currency"] == "SYP", "golden currency is explicit")
    add(rows, "contract_scenario_groups", "contract", "alrajhi_client/workspace/quality/golden_dataset_scenarios_contract.py", int(summary["scenario_group_count"]) >= 12, "critical scenario groups are declared")
    add(rows, "contract_invariants", "contract", "alrajhi_client/workspace/quality/golden_dataset_scenarios_contract.py", int(summary["critical_invariant_count"]) >= 8, "critical invariants are declared")

    scenario = build_golden_scenario_result()
    operations = build_golden_operations()
    scenario_info = scenario_summary()
    add(rows, "scenario_operation_count", "scenario", "alrajhi_client/workspace/quality/golden_dataset_scenarios.py", scenario_info["operation_count"] == 14, "canonical operations cover business day")
    add(rows, "scenario_failure_count", "scenario", "alrajhi_client/workspace/quality/golden_dataset_scenarios.py", scenario_info["failures"] == 0, "golden arithmetic has no invariant failures")
    add(rows, "scenario_gross_profit", "scenario", "alrajhi_client/workspace/quality/golden_dataset_scenarios.py", scenario_info["gross_profit"] == "465.00", "gross profit is stable")
    add(rows, "scenario_operation_ids_unique", "scenario", "alrajhi_client/workspace/quality/golden_dataset_scenarios.py", len({op.operation_id for op in operations}) == len(operations), "operation ids are unique")
    add(rows, "scenario_every_stock_op_branch_scoped", "scenario", "alrajhi_client/workspace/quality/golden_dataset_scenarios.py", all(op.branch_id for op in operations), "every operation carries branch scope")

    for row in build_invariant_rows():
        add(rows, str(row["key"]), "invariant", "alrajhi_client/workspace/quality/golden_dataset_scenarios.py", row["status"] == "OK", str(row["detail"]))

    release = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    add(rows, "release_doc", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "PHASE423_GOLDEN_DATASET_ACCOUNTING_INVENTORY_SCENARIO_PACK" in release, "Phase423 doc registered")
    add(rows, "release_test", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "tests/test_phase423_golden_dataset_scenarios.py" in release, "Phase423 test registered")
    add(rows, "release_check", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "golden_dataset_scenarios" in release and "phase=423" in release, "Phase423 release check registered")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader(); writer.writerows(rows)

    EXPECTED_OUT.write_text(json.dumps(scenario.expected, ensure_ascii=False, indent=2), encoding="utf-8")
    OPERATIONS_OUT.write_text(json.dumps([
        {"operation_id": op.operation_id, "group": op.group, "kind": op.kind, "branch_id": op.branch_id, "description": op.description, "payload": op.payload}
        for op in scenario.operations
    ], ensure_ascii=False, indent=2), encoding="utf-8")

    failed = [row for row in rows if row["status"] != "OK"]
    print(f"Phase423 golden dataset checks: {len(rows)} checks, failures={len(failed)}")
    print(f"Expected balances: {EXPECTED_OUT}")
    print(f"Operations: {OPERATIONS_OUT}")
    for row in failed:
        print(f"FAIL {row['key']}: {row['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
