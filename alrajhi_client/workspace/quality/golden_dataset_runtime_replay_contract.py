# -*- coding: utf-8 -*-
"""Phase 424 golden dataset runtime replay bridge contract.

This contract converts the Phase423 golden arithmetic pack into a replayable
runtime contract.  The default adapter is intentionally in-memory and Qt-free;
DAO, repository and HTTP adapters can implement the same operation interface and
must produce the exact same balance envelope.
"""
from __future__ import annotations

from typing import Any, Dict, Tuple

GOLDEN_DATASET_RUNTIME_REPLAY_CONTRACT: Dict[str, Any] = {
    "phase": 424,
    "name": "Golden Dataset Runtime Replay Bridge",
    "source_phase": 423,
    "currency": "SYP",
    "required_bridge_layers": (
        "operation_stream",
        "idempotency_keys",
        "branch_scope_metadata",
        "adapter_protocol",
        "expected_actual_comparison",
        "machine_readable_outputs",
    ),
    "required_adapters": (
        "in_memory_reference",
        "dao_repository_runtime",
        "http_api_runtime",
        "offline_replay_runtime",
    ),
    "implemented_adapters": (
        "in_memory_reference",
    ),
    "runtime_adapter_backlog": (
        "dao_repository_runtime",
        "http_api_runtime",
        "offline_replay_runtime",
    ),
    "comparison_sections": (
        "stock_by_item_warehouse",
        "cashbox_balances",
        "customer_receivables",
        "supplier_payables",
        "expenses",
        "totals",
    ),
    "critical_runtime_invariants": (
        "operation_ids_survive_replay_as_idempotency_keys",
        "branch_scope_survives_replay_for_stock_affecting_operations",
        "adapter_result_shape_matches_golden_balance_sections",
        "actual_balances_match_phase423_expected_balances",
        "replay_outputs_are_machine_readable_for_ci_and_manual_runtime_runs",
        "runtime_backlog_is_explicit_not_silent",
    ),
    "output_files": (
        "tools/audit_outputs/golden_dataset_runtime_replay_matrix.csv",
        "tools/audit_outputs/golden_dataset_runtime_replay_steps.json",
        "tools/audit_outputs/golden_dataset_runtime_replay_comparison.csv",
        "tools/audit_outputs/golden_dataset_runtime_replay_actual_balances.json",
        "tools/audit_outputs/golden_dataset_runtime_replay_adapter_manifest.json",
    ),
    "accepted_transition_risks": (
        "Phase424 proves replay protocol, operation metadata and expected/actual comparison through an in-memory reference adapter.",
        "DAO, HTTP API and offline replay adapters are declared backlog adapters and should be implemented without changing the Phase423 expected balances.",
        "The bridge is database-free by default to keep CI deterministic; production replay must run separately against a disposable database or server instance.",
    ),
}


def contract_summary() -> Dict[str, object]:
    contract = GOLDEN_DATASET_RUNTIME_REPLAY_CONTRACT
    return {
        "phase": contract["phase"],
        "name": contract["name"],
        "source_phase": contract["source_phase"],
        "currency": contract["currency"],
        "bridge_layer_count": len(contract["required_bridge_layers"]),
        "required_adapter_count": len(contract["required_adapters"]),
        "implemented_adapter_count": len(contract["implemented_adapters"]),
        "runtime_backlog_count": len(contract["runtime_adapter_backlog"]),
        "comparison_section_count": len(contract["comparison_sections"]),
        "critical_invariant_count": len(contract["critical_runtime_invariants"]),
        "output_file_count": len(contract["output_files"]),
        "accepted_transition_risks": contract["accepted_transition_risks"],
    }


def comparison_sections() -> Tuple[str, ...]:
    return tuple(GOLDEN_DATASET_RUNTIME_REPLAY_CONTRACT["comparison_sections"])


def required_bridge_layers() -> Tuple[str, ...]:
    return tuple(GOLDEN_DATASET_RUNTIME_REPLAY_CONTRACT["required_bridge_layers"])


def runtime_adapter_backlog() -> Tuple[str, ...]:
    return tuple(GOLDEN_DATASET_RUNTIME_REPLAY_CONTRACT["runtime_adapter_backlog"])


__all__ = [
    "GOLDEN_DATASET_RUNTIME_REPLAY_CONTRACT",
    "contract_summary",
    "comparison_sections",
    "required_bridge_layers",
    "runtime_adapter_backlog",
]
