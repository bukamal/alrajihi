# -*- coding: utf-8 -*-
"""Phase 423 golden dataset accounting/inventory scenario contract.

This module is deliberately Qt-free and database-free.  It defines a deterministic
business scenario pack that CI can run without a live installation.  Runtime DAO
and report tests can later replay the same operation ids against the application
repositories and compare the resulting balances with these expectations.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Tuple

GOLDEN_DATASET_SCENARIO_CONTRACT: Dict[str, Any] = {
    "phase": 423,
    "name": "Golden Dataset Accounting & Inventory Scenario Pack",
    "currency": "SYP",
    "precision": "0.01",
    "required_scenario_groups": (
        "master_data",
        "opening_balances",
        "purchase_invoice",
        "sales_invoice",
        "sales_return",
        "purchase_return",
        "inventory_transfer",
        "manufacturing",
        "pos_sale",
        "restaurant_order",
        "vouchers",
        "reports",
    ),
    "critical_invariants": (
        "cashbox_balance_matches_all_cash_movements",
        "customer_receivable_matches_sales_returns_and_receipts",
        "supplier_payable_matches_purchases_returns_and_payments",
        "warehouse_quantities_match_purchases_returns_sales_transfers_and_manufacturing",
        "finished_goods_cost_is_derived_from_component_consumption",
        "gross_profit_uses_document_cost_basis_not_current_price",
        "branch_scope_is_present_for_every_stock_affecting_operation",
        "every_operation_has_a_stable_operation_id_for_offline_replay_and_idempotency",
    ),
    "canonical_entities": {
        "branches": ("BR-MAIN", "BR-2"),
        "warehouses": ("WH-MAIN", "WH-BR2", "WH-KITCHEN"),
        "cashboxes": ("CASH-MAIN", "CASH-POS", "CASH-REST"),
        "customers": ("CUST-001", "CUST-RETAIL"),
        "suppliers": ("SUP-001",),
        "items": ("MAT-RAW", "MAT-RETAIL", "MAT-FINISHED", "REST-MEAL"),
    },
    "accepted_transition_risks": (
        "Phase423 validates deterministic business arithmetic in a pure Python pack; database replay is a later runtime phase.",
        "Tax is included as an explicit document amount, but jurisdiction-specific VAT posting accounts remain outside this phase.",
        "Restaurant and POS operations are represented as normalized sales events so report reconciliation can share one calculation path.",
    ),
}


def contract_summary() -> Dict[str, object]:
    contract = GOLDEN_DATASET_SCENARIO_CONTRACT
    return {
        "phase": contract["phase"],
        "name": contract["name"],
        "currency": contract["currency"],
        "scenario_group_count": len(contract["required_scenario_groups"]),
        "critical_invariant_count": len(contract["critical_invariants"]),
        "entity_group_count": len(contract["canonical_entities"]),
        "accepted_transition_risks": contract["accepted_transition_risks"],
    }


def required_scenario_groups() -> Tuple[str, ...]:
    return tuple(GOLDEN_DATASET_SCENARIO_CONTRACT["required_scenario_groups"])


def critical_invariants() -> Tuple[str, ...]:
    return tuple(GOLDEN_DATASET_SCENARIO_CONTRACT["critical_invariants"])


__all__ = [
    "GOLDEN_DATASET_SCENARIO_CONTRACT",
    "contract_summary",
    "required_scenario_groups",
    "critical_invariants",
]
