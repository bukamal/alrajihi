# -*- coding: utf-8 -*-
"""Phase 424 runtime replay bridge for the Phase423 golden dataset.

The bridge gives every runtime surface one strict contract:
consume the Phase423 operations in order and return a balance envelope identical
to ``calculate_golden_expected``.  The included in-memory adapter is the reference
adapter; DAO/API/offline adapters can be implemented later without changing the
comparison logic or the expected balances.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Protocol, Sequence, Tuple

from .golden_dataset_runtime_replay_contract import (
    GOLDEN_DATASET_RUNTIME_REPLAY_CONTRACT,
    comparison_sections,
)
from .golden_dataset_scenarios import (
    EXPECTED_GOLDEN_TOTALS,
    GoldenOperation,
    build_golden_operations,
    calculate_golden_expected,
)


@dataclass(frozen=True)
class ReplayStepResult:
    operation_id: str
    group: str
    kind: str
    branch_id: str
    idempotency_key: str
    status: str
    detail: str


@dataclass(frozen=True)
class ComparisonRow:
    section: str
    key: str
    expected: str
    actual: str
    status: str
    detail: str


@dataclass(frozen=True)
class ReplayRunResult:
    adapter_name: str
    step_results: Tuple[ReplayStepResult, ...]
    actual: Mapping[str, object]
    expected: Mapping[str, object]
    comparison_rows: Tuple[ComparisonRow, ...]
    matrix_rows: Tuple[Mapping[str, object], ...]


class GoldenReplayAdapter(Protocol):
    """Runtime adapter protocol for replaying the Phase423 operation stream."""

    adapter_name: str

    def reset(self) -> None:
        """Reset all runtime state for a clean golden replay."""

    def apply_operation(self, operation: GoldenOperation, idempotency_key: str) -> ReplayStepResult:
        """Apply a single golden operation."""

    def collect_actual_balances(self) -> Mapping[str, object]:
        """Return a balance envelope matching Phase423 expected shape."""


class InMemoryGoldenReplayAdapter:
    """Deterministic reference adapter.

    This adapter stores the replayed operation stream and delegates arithmetic to
    the Phase423 calculator.  It validates bridge metadata without importing Qt,
    a database engine or server routes.
    """

    adapter_name = "in_memory_reference"

    def __init__(self) -> None:
        self._operations: List[GoldenOperation] = []
        self._seen_ids: set[str] = set()

    def reset(self) -> None:
        self._operations.clear()
        self._seen_ids.clear()

    def apply_operation(self, operation: GoldenOperation, idempotency_key: str) -> ReplayStepResult:
        if not operation.operation_id:
            return ReplayStepResult(operation.operation_id, operation.group, operation.kind, operation.branch_id, idempotency_key, "FAIL", "missing operation id")
        if idempotency_key != operation.operation_id:
            return ReplayStepResult(operation.operation_id, operation.group, operation.kind, operation.branch_id, idempotency_key, "FAIL", "idempotency key must match operation id")
        if idempotency_key in self._seen_ids:
            return ReplayStepResult(operation.operation_id, operation.group, operation.kind, operation.branch_id, idempotency_key, "SKIP", "duplicate operation ignored by idempotency key")
        if not operation.branch_id:
            return ReplayStepResult(operation.operation_id, operation.group, operation.kind, operation.branch_id, idempotency_key, "FAIL", "branch scope missing")
        self._seen_ids.add(idempotency_key)
        self._operations.append(operation)
        return ReplayStepResult(operation.operation_id, operation.group, operation.kind, operation.branch_id, idempotency_key, "OK", "operation accepted")

    def collect_actual_balances(self) -> Mapping[str, object]:
        return calculate_golden_expected(tuple(self._operations))


def operation_to_replay_envelope(operation: GoldenOperation) -> Dict[str, object]:
    """Normalize a Phase423 operation for runtime adapters and audit output."""
    return {
        "operation_id": operation.operation_id,
        "idempotency_key": operation.operation_id,
        "group": operation.group,
        "kind": operation.kind,
        "branch_id": operation.branch_id,
        "description": operation.description,
        "payload": dict(operation.payload),
    }


def build_replay_operation_stream(operations: Sequence[GoldenOperation] | None = None) -> Tuple[Mapping[str, object], ...]:
    return tuple(operation_to_replay_envelope(op) for op in (operations or build_golden_operations()))


def _flatten_section(section: str, value: object) -> Dict[str, str]:
    if isinstance(value, Mapping):
        return {str(key): str(item) for key, item in value.items()}
    return {section: str(value)}


def compare_expected_actual(expected: Mapping[str, object], actual: Mapping[str, object]) -> Tuple[ComparisonRow, ...]:
    rows: List[ComparisonRow] = []
    for section in comparison_sections():
        expected_section = _flatten_section(section, expected.get(section, {}))
        actual_section = _flatten_section(section, actual.get(section, {}))
        keys = sorted(set(expected_section) | set(actual_section))
        if not keys:
            rows.append(ComparisonRow(section, "__section_present__", "present", "missing", "FAIL", f"{section} must be present"))
            continue
        for key in keys:
            exp = expected_section.get(key, "<missing>")
            act = actual_section.get(key, "<missing>")
            rows.append(ComparisonRow(section, key, exp, act, "OK" if exp == act else "FAIL", f"{section}.{key} matches expected golden value"))
    return tuple(rows)


def build_adapter_manifest() -> Dict[str, object]:
    contract = GOLDEN_DATASET_RUNTIME_REPLAY_CONTRACT
    return {
        "phase": contract["phase"],
        "source_phase": contract["source_phase"],
        "implemented_adapters": list(contract["implemented_adapters"]),
        "runtime_adapter_backlog": list(contract["runtime_adapter_backlog"]),
        "backlog_intent": {
            "dao_repository_runtime": "Replay against a disposable local database through repositories/DAOs and compare collected balances.",
            "http_api_runtime": "Replay through server API endpoints with JWT, branch headers and idempotency keys.",
            "offline_replay_runtime": "Replay the same operation envelopes through the offline queue and verify idempotent synchronization.",
        },
        "required_outputs": list(contract["output_files"]),
    }


def _build_matrix_rows(result: ReplayRunResult) -> Tuple[Mapping[str, object], ...]:
    rows: List[Mapping[str, object]] = []

    def add(key: str, category: str, status: bool, detail: str, actual: object = "", expected: object = "") -> None:
        rows.append({
            "key": key,
            "category": category,
            "status": "OK" if status else "FAIL",
            "detail": detail,
            "actual": actual,
            "expected": expected,
        })

    add("adapter_name", "adapter", result.adapter_name == "in_memory_reference", "reference adapter is used for CI bridge verification", result.adapter_name, "in_memory_reference")
    add("step_count", "replay", len(result.step_results) == len(build_golden_operations()), "all golden operations are replayed", len(result.step_results), len(build_golden_operations()))
    add("step_statuses", "replay", all(step.status in {"OK", "SKIP"} for step in result.step_results), "all replay steps are accepted or idempotently skipped")
    add("idempotency_keys", "replay", all(step.idempotency_key == step.operation_id for step in result.step_results), "operation ids are passed as idempotency keys")
    add("branch_scope", "replay", all(bool(step.branch_id) for step in result.step_results), "branch scope is present for every replayed operation")
    add("actual_currency", "balances", result.actual.get("currency") == "SYP", "actual balance envelope preserves currency", result.actual.get("currency"), "SYP")
    add("actual_operation_count", "balances", result.actual.get("operation_count") == len(build_golden_operations()), "actual balance envelope preserves operation count", result.actual.get("operation_count"), len(build_golden_operations()))

    for row in result.comparison_rows:
        add(f"compare::{row.section}::{row.key}", "comparison", row.status == "OK", row.detail, row.actual, row.expected)

    manifest = build_adapter_manifest()
    add("adapter_manifest_backlog_explicit", "adapter", len(manifest["runtime_adapter_backlog"]) == 3, "DAO/API/offline adapters are explicit backlog, not silent omissions", manifest["runtime_adapter_backlog"], "3 backlog adapters")
    return tuple(rows)


def replay_golden_dataset(adapter: GoldenReplayAdapter | None = None, operations: Sequence[GoldenOperation] | None = None) -> ReplayRunResult:
    runtime = adapter or InMemoryGoldenReplayAdapter()
    ops = tuple(operations or build_golden_operations())
    runtime.reset()
    steps = tuple(runtime.apply_operation(op, op.operation_id) for op in ops)
    actual = runtime.collect_actual_balances()
    expected = calculate_golden_expected(ops)
    comparison = compare_expected_actual(expected, actual)
    preliminary = ReplayRunResult(runtime.adapter_name, steps, actual, expected, comparison, tuple())
    matrix = _build_matrix_rows(preliminary)
    return ReplayRunResult(runtime.adapter_name, steps, actual, expected, comparison, matrix)


def replay_failures(result: ReplayRunResult) -> Tuple[Mapping[str, object], ...]:
    return tuple(row for row in result.matrix_rows if row.get("status") != "OK")


def replay_summary(result: ReplayRunResult | None = None) -> Dict[str, object]:
    res = result or replay_golden_dataset()
    return {
        "adapter_name": res.adapter_name,
        "step_count": len(res.step_results),
        "comparison_count": len(res.comparison_rows),
        "matrix_count": len(res.matrix_rows),
        "failures": len(replay_failures(res)),
        "gross_profit": str(res.actual.get("totals", {}).get("gross_profit", "")) if isinstance(res.actual.get("totals"), Mapping) else "",
        "total_cash": str(res.actual.get("totals", {}).get("total_cash", "")) if isinstance(res.actual.get("totals"), Mapping) else "",
        "backlog_adapters": tuple(build_adapter_manifest()["runtime_adapter_backlog"]),
    }


def export_runtime_replay_outputs(output_dir: str | Path | None = None, result: ReplayRunResult | None = None) -> Dict[str, str]:
    out = Path(output_dir or Path("tools") / "audit_outputs")
    out.mkdir(parents=True, exist_ok=True)
    res = result or replay_golden_dataset()

    matrix_file = out / "golden_dataset_runtime_replay_matrix.csv"
    comparison_file = out / "golden_dataset_runtime_replay_comparison.csv"
    steps_file = out / "golden_dataset_runtime_replay_steps.json"
    actual_file = out / "golden_dataset_runtime_replay_actual_balances.json"
    manifest_file = out / "golden_dataset_runtime_replay_adapter_manifest.json"

    with matrix_file.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "status", "detail", "actual", "expected"])
        writer.writeheader()
        writer.writerows(res.matrix_rows)

    with comparison_file.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["section", "key", "expected", "actual", "status", "detail"])
        writer.writeheader()
        writer.writerows(asdict(row) for row in res.comparison_rows)

    steps_file.write_text(json.dumps([asdict(step) for step in res.step_results], ensure_ascii=False, indent=2), encoding="utf-8")
    actual_file.write_text(json.dumps(res.actual, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_file.write_text(json.dumps(build_adapter_manifest(), ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "matrix": str(matrix_file),
        "comparison": str(comparison_file),
        "steps": str(steps_file),
        "actual": str(actual_file),
        "manifest": str(manifest_file),
    }


__all__ = [
    "GoldenReplayAdapter",
    "InMemoryGoldenReplayAdapter",
    "ReplayStepResult",
    "ComparisonRow",
    "ReplayRunResult",
    "operation_to_replay_envelope",
    "build_replay_operation_stream",
    "compare_expected_actual",
    "build_adapter_manifest",
    "replay_golden_dataset",
    "replay_failures",
    "replay_summary",
    "export_runtime_replay_outputs",
]
