# -*- coding: utf-8 -*-
"""Phase 423 deterministic business scenario calculator.

The pack models a compact but representative ERP day:
opening stock, purchase, sale, returns, transfer, manufacturing, POS,
restaurant sale and vouchers.  It produces balances that report/runtime tests can
use as a golden reference.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

from .golden_dataset_scenarios_contract import (
    GOLDEN_DATASET_SCENARIO_CONTRACT,
    critical_invariants,
    required_scenario_groups,
)

CENT = Decimal(str(GOLDEN_DATASET_SCENARIO_CONTRACT["precision"]))
ZERO = Decimal("0.00")


def D(value: str | int | float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def q(value: str | int | float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class GoldenOperation:
    operation_id: str
    group: str
    kind: str
    branch_id: str
    description: str
    payload: Mapping[str, object]


@dataclass(frozen=True)
class GoldenScenarioResult:
    operations: Tuple[GoldenOperation, ...]
    expected: Mapping[str, object]
    invariant_rows: Tuple[Mapping[str, object], ...]


def _money_dict(values: Mapping[str, Decimal]) -> Dict[str, str]:
    return {key: str(value.quantize(CENT, rounding=ROUND_HALF_UP)) for key, value in sorted(values.items())}


def _qty_dict(values: Mapping[Tuple[str, str], Decimal]) -> Dict[str, str]:
    return {f"{item}@{warehouse}": str(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)) for (item, warehouse), value in sorted(values.items())}


def _stock_key(item_id: str, warehouse_id: str) -> Tuple[str, str]:
    return item_id, warehouse_id


def build_golden_operations() -> Tuple[GoldenOperation, ...]:
    """Return the canonical Phase423 business day.

    Amounts are intentionally small enough to manually audit, but the scenario
    touches all financial and stock-impacting surfaces that caused regressions in
    prior phases.
    """
    return (
        GoldenOperation("GD-000", "master_data", "declare_entities", "BR-MAIN", "Canonical branches, parties, warehouses and items", {
            "currency": "SYP",
            "branches": list(GOLDEN_DATASET_SCENARIO_CONTRACT["canonical_entities"]["branches"]),
            "warehouses": list(GOLDEN_DATASET_SCENARIO_CONTRACT["canonical_entities"]["warehouses"]),
            "items": list(GOLDEN_DATASET_SCENARIO_CONTRACT["canonical_entities"]["items"]),
        }),
        GoldenOperation("GD-001", "opening_balances", "opening_stock", "BR-MAIN", "Opening stock and cash", {
            "stock": [
                {"item_id": "MAT-RAW", "warehouse_id": "WH-MAIN", "qty": "10", "cost": "100"},
                {"item_id": "MAT-RETAIL", "warehouse_id": "WH-MAIN", "qty": "5", "cost": "80"},
            ],
            "cashbox_id": "CASH-MAIN",
            "cash_in": "1000",
        }),
        GoldenOperation("GD-002", "purchase_invoice", "purchase_invoice", "BR-MAIN", "Purchase raw and retail materials from supplier", {
            "supplier_id": "SUP-001",
            "warehouse_id": "WH-MAIN",
            "lines": [
                {"item_id": "MAT-RAW", "qty": "4", "unit_cost": "110"},
                {"item_id": "MAT-RETAIL", "qty": "3", "unit_cost": "85"},
            ],
            "tax": "69.50",
        }),
        GoldenOperation("GD-003", "sales_invoice", "sales_invoice", "BR-MAIN", "Credit sale to customer from main warehouse", {
            "customer_id": "CUST-001",
            "warehouse_id": "WH-MAIN",
            "lines": [
                {"item_id": "MAT-RETAIL", "qty": "4", "unit_price": "150", "unit_cost": "80"},
            ],
            "tax": "30",
        }),
        GoldenOperation("GD-004", "sales_return", "sales_return", "BR-MAIN", "Customer returns one retail item to stock", {
            "customer_id": "CUST-001",
            "warehouse_id": "WH-MAIN",
            "restock": True,
            "lines": [
                {"item_id": "MAT-RETAIL", "qty": "1", "unit_price": "150", "unit_cost": "80"},
            ],
            "tax": "7.50",
        }),
        GoldenOperation("GD-005", "purchase_return", "purchase_return", "BR-MAIN", "Return one raw item to supplier", {
            "supplier_id": "SUP-001",
            "warehouse_id": "WH-MAIN",
            "lines": [
                {"item_id": "MAT-RAW", "qty": "1", "unit_cost": "110"},
            ],
            "tax": "5.50",
        }),
        GoldenOperation("GD-006", "inventory_transfer", "inventory_transfer", "BR-MAIN", "Transfer retail stock from main branch to branch two", {
            "source_branch_id": "BR-MAIN",
            "target_branch_id": "BR-2",
            "source_warehouse_id": "WH-MAIN",
            "target_warehouse_id": "WH-BR2",
            "lines": [
                {"item_id": "MAT-RETAIL", "qty": "2"},
            ],
        }),
        GoldenOperation("GD-007", "manufacturing", "production_order", "BR-MAIN", "Consume raw material and create finished good", {
            "source_warehouse_id": "WH-MAIN",
            "target_warehouse_id": "WH-MAIN",
            "components": [
                {"item_id": "MAT-RAW", "qty": "2", "unit_cost": "100"},
            ],
            "outputs": [
                {"item_id": "MAT-FINISHED", "qty": "1"},
            ],
        }),
        GoldenOperation("GD-008", "pos_sale", "pos_sale", "BR-2", "Cash POS sale from branch two", {
            "customer_id": "CUST-RETAIL",
            "warehouse_id": "WH-BR2",
            "cashbox_id": "CASH-POS",
            "lines": [
                {"item_id": "MAT-RETAIL", "qty": "1", "unit_price": "175", "unit_cost": "80"},
            ],
            "tax": "8.75",
        }),
        GoldenOperation("GD-009", "restaurant_order", "restaurant_order", "BR-MAIN", "Restaurant cash order with recipe stock consumption", {
            "customer_id": "CUST-RETAIL",
            "warehouse_id": "WH-KITCHEN",
            "component_warehouse_id": "WH-MAIN",
            "cashbox_id": "CASH-REST",
            "lines": [
                {"item_id": "REST-MEAL", "qty": "2", "unit_price": "120", "unit_cost": "40"},
            ],
            "components": [
                {"item_id": "MAT-RAW", "qty": "1", "unit_cost": "40"},
            ],
            "tax": "12",
        }),
        GoldenOperation("GD-010", "vouchers", "cash_receipt", "BR-MAIN", "Customer partial receipt", {
            "customer_id": "CUST-001",
            "cashbox_id": "CASH-MAIN",
            "amount": "200",
        }),
        GoldenOperation("GD-011", "vouchers", "cash_payment", "BR-MAIN", "Supplier partial payment", {
            "supplier_id": "SUP-001",
            "cashbox_id": "CASH-MAIN",
            "amount": "300",
        }),
        GoldenOperation("GD-012", "vouchers", "expense_payment", "BR-MAIN", "Office expense payment", {
            "cashbox_id": "CASH-MAIN",
            "expense_account": "EXP-OFFICE",
            "amount": "50",
        }),
        GoldenOperation("GD-013", "reports", "expected_report_cutoff", "BR-MAIN", "Report reconciliation cutoff", {
            "date": "2026-06-28",
            "scope": "full_golden_dataset",
        }),
    )


def calculate_golden_expected(operations: Sequence[GoldenOperation] | None = None) -> Dict[str, object]:
    ops = tuple(operations or build_golden_operations())
    stock: MutableMapping[Tuple[str, str], Decimal] = {}
    cashboxes: MutableMapping[str, Decimal] = {}
    receivables: MutableMapping[str, Decimal] = {}
    payables: MutableMapping[str, Decimal] = {}
    tax_collected = ZERO
    tax_paid = ZERO
    revenue = ZERO
    returns_revenue = ZERO
    cogs = ZERO
    cogs_reversal = ZERO
    purchase_total = ZERO
    purchase_return_total = ZERO
    manufacturing_cost = ZERO
    expenses: MutableMapping[str, Decimal] = {}
    stock_movement_count = 0

    def add_stock(item_id: str, warehouse_id: str, qty_value: Decimal) -> None:
        nonlocal stock_movement_count
        stock[_stock_key(item_id, warehouse_id)] = stock.get(_stock_key(item_id, warehouse_id), q(0)) + qty_value
        stock_movement_count += 1

    for op in ops:
        payload = op.payload
        if op.kind == "opening_stock":
            cashboxes[str(payload["cashbox_id"])] = cashboxes.get(str(payload["cashbox_id"]), ZERO) + D(payload["cash_in"])
            for line in payload["stock"]:  # type: ignore[index]
                add_stock(str(line["item_id"]), str(line["warehouse_id"]), q(line["qty"]))
        elif op.kind == "purchase_invoice":
            supplier = str(payload["supplier_id"])
            subtotal = ZERO
            for line in payload["lines"]:  # type: ignore[index]
                amount = D(line["qty"]) * D(line["unit_cost"])
                subtotal += amount
                add_stock(str(line["item_id"]), str(payload["warehouse_id"]), q(line["qty"]))
            tax = D(payload.get("tax", "0"))
            payables[supplier] = payables.get(supplier, ZERO) + subtotal + tax
            tax_paid += tax
            purchase_total += subtotal
        elif op.kind == "sales_invoice":
            customer = str(payload["customer_id"])
            subtotal = ZERO
            line_cost = ZERO
            for line in payload["lines"]:  # type: ignore[index]
                subtotal += D(line["qty"]) * D(line["unit_price"])
                line_cost += D(line["qty"]) * D(line["unit_cost"])
                add_stock(str(line["item_id"]), str(payload["warehouse_id"]), -q(line["qty"]))
            tax = D(payload.get("tax", "0"))
            receivables[customer] = receivables.get(customer, ZERO) + subtotal + tax
            revenue += subtotal
            tax_collected += tax
            cogs += line_cost
        elif op.kind == "sales_return":
            customer = str(payload["customer_id"])
            subtotal = ZERO
            line_cost = ZERO
            for line in payload["lines"]:  # type: ignore[index]
                subtotal += D(line["qty"]) * D(line["unit_price"])
                line_cost += D(line["qty"]) * D(line["unit_cost"])
                if bool(payload.get("restock", False)):
                    add_stock(str(line["item_id"]), str(payload["warehouse_id"]), q(line["qty"]))
            tax = D(payload.get("tax", "0"))
            receivables[customer] = receivables.get(customer, ZERO) - subtotal - tax
            returns_revenue += subtotal
            tax_collected -= tax
            cogs_reversal += line_cost
        elif op.kind == "purchase_return":
            supplier = str(payload["supplier_id"])
            subtotal = ZERO
            for line in payload["lines"]:  # type: ignore[index]
                subtotal += D(line["qty"]) * D(line["unit_cost"])
                add_stock(str(line["item_id"]), str(payload["warehouse_id"]), -q(line["qty"]))
            tax = D(payload.get("tax", "0"))
            payables[supplier] = payables.get(supplier, ZERO) - subtotal - tax
            tax_paid -= tax
            purchase_return_total += subtotal
        elif op.kind == "inventory_transfer":
            for line in payload["lines"]:  # type: ignore[index]
                add_stock(str(line["item_id"]), str(payload["source_warehouse_id"]), -q(line["qty"]))
                add_stock(str(line["item_id"]), str(payload["target_warehouse_id"]), q(line["qty"]))
        elif op.kind == "production_order":
            component_cost = ZERO
            for line in payload["components"]:  # type: ignore[index]
                component_cost += D(line["qty"]) * D(line["unit_cost"])
                add_stock(str(line["item_id"]), str(payload["source_warehouse_id"]), -q(line["qty"]))
            total_output_qty = sum((q(line["qty"]) for line in payload["outputs"]), q(0))  # type: ignore[index]
            for line in payload["outputs"]:  # type: ignore[index]
                add_stock(str(line["item_id"]), str(payload["target_warehouse_id"]), q(line["qty"]))
            manufacturing_cost += component_cost
        elif op.kind in {"pos_sale", "restaurant_order"}:
            subtotal = ZERO
            line_cost = ZERO
            for line in payload["lines"]:  # type: ignore[index]
                subtotal += D(line["qty"]) * D(line["unit_price"])
                line_cost += D(line["qty"]) * D(line["unit_cost"])
                if op.kind == "pos_sale":
                    add_stock(str(line["item_id"]), str(payload["warehouse_id"]), -q(line["qty"]))
            if op.kind == "restaurant_order":
                for component in payload.get("components", []):  # type: ignore[assignment]
                    add_stock(str(component["item_id"]), str(payload["component_warehouse_id"]), -q(component["qty"]))
            tax = D(payload.get("tax", "0"))
            cashbox = str(payload["cashbox_id"])
            cashboxes[cashbox] = cashboxes.get(cashbox, ZERO) + subtotal + tax
            revenue += subtotal
            tax_collected += tax
            cogs += line_cost
        elif op.kind == "cash_receipt":
            customer = str(payload["customer_id"])
            amount = D(payload["amount"])
            receivables[customer] = receivables.get(customer, ZERO) - amount
            cashboxes[str(payload["cashbox_id"])] = cashboxes.get(str(payload["cashbox_id"]), ZERO) + amount
        elif op.kind == "cash_payment":
            supplier = str(payload["supplier_id"])
            amount = D(payload["amount"])
            payables[supplier] = payables.get(supplier, ZERO) - amount
            cashboxes[str(payload["cashbox_id"])] = cashboxes.get(str(payload["cashbox_id"]), ZERO) - amount
        elif op.kind == "expense_payment":
            amount = D(payload["amount"])
            account = str(payload["expense_account"])
            cashboxes[str(payload["cashbox_id"])] = cashboxes.get(str(payload["cashbox_id"]), ZERO) - amount
            expenses[account] = expenses.get(account, ZERO) + amount

    net_revenue = revenue - returns_revenue
    net_cogs = cogs - cogs_reversal
    gross_profit = net_revenue - net_cogs
    vat_payable = tax_collected - tax_paid
    total_cash = sum(cashboxes.values(), ZERO)
    total_receivable = sum(receivables.values(), ZERO)
    total_payable = sum(payables.values(), ZERO)

    return {
        "currency": GOLDEN_DATASET_SCENARIO_CONTRACT["currency"],
        "operation_count": len(ops),
        "operation_ids": tuple(op.operation_id for op in ops),
        "scenario_groups": tuple(dict.fromkeys(op.group for op in ops)),
        "stock_by_item_warehouse": _qty_dict(stock),
        "cashbox_balances": _money_dict(cashboxes),
        "customer_receivables": _money_dict(receivables),
        "supplier_payables": _money_dict(payables),
        "expenses": _money_dict(expenses),
        "totals": {
            "purchase_subtotal": str(purchase_total.quantize(CENT)),
            "purchase_return_subtotal": str(purchase_return_total.quantize(CENT)),
            "sales_subtotal": str(revenue.quantize(CENT)),
            "sales_return_subtotal": str(returns_revenue.quantize(CENT)),
            "net_revenue": str(net_revenue.quantize(CENT)),
            "cogs": str(net_cogs.quantize(CENT)),
            "gross_profit": str(gross_profit.quantize(CENT)),
            "tax_collected": str(tax_collected.quantize(CENT)),
            "tax_paid": str(tax_paid.quantize(CENT)),
            "vat_payable": str(vat_payable.quantize(CENT)),
            "total_cash": str(total_cash.quantize(CENT)),
            "total_customer_receivable": str(total_receivable.quantize(CENT)),
            "total_supplier_payable": str(total_payable.quantize(CENT)),
            "manufacturing_cost": str(manufacturing_cost.quantize(CENT)),
            "stock_movement_count": str(stock_movement_count),
        },
    }


EXPECTED_GOLDEN_TOTALS: Dict[str, object] = {
    "stock_by_item_warehouse": {
        "MAT-FINISHED@WH-MAIN": "1.0000",
        "MAT-RAW@WH-MAIN": "10.0000",
        "MAT-RETAIL@WH-BR2": "1.0000",
        "MAT-RETAIL@WH-MAIN": "3.0000",
    },
    "cashbox_balances": {
        "CASH-MAIN": "850.00",
        "CASH-POS": "183.75",
        "CASH-REST": "252.00",
    },
    "customer_receivables": {"CUST-001": "272.50"},
    "supplier_payables": {"SUP-001": "349.00"},
    "expenses": {"EXP-OFFICE": "50.00"},
    "totals": {
        "purchase_subtotal": "695.00",
        "purchase_return_subtotal": "110.00",
        "sales_subtotal": "1015.00",
        "sales_return_subtotal": "150.00",
        "net_revenue": "865.00",
        "cogs": "400.00",
        "gross_profit": "465.00",
        "tax_collected": "43.25",
        "tax_paid": "64.00",
        "vat_payable": "-20.75",
        "total_cash": "1285.75",
        "total_customer_receivable": "272.50",
        "total_supplier_payable": "349.00",
        "manufacturing_cost": "200.00",
        "stock_movement_count": "13",
    },
}


def build_invariant_rows(operations: Sequence[GoldenOperation] | None = None) -> Tuple[Mapping[str, object], ...]:
    ops = tuple(operations or build_golden_operations())
    actual = calculate_golden_expected(ops)
    rows: List[Mapping[str, object]] = []

    def add(key: str, ok: bool, actual_value: object, expected_value: object, detail: str) -> None:
        rows.append({
            "key": key,
            "status": "OK" if ok else "FAIL",
            "actual": actual_value,
            "expected": expected_value,
            "detail": detail,
        })

    for group in required_scenario_groups():
        add(f"scenario_group::{group}", group in actual["scenario_groups"], actual["scenario_groups"], group, "required scenario group is present")

    ids = [op.operation_id for op in ops]
    add("operation_ids_unique", len(ids) == len(set(ids)), len(ids), len(set(ids)), "every operation has a unique idempotency/replay id")
    add("operation_count", actual["operation_count"] == 14, actual["operation_count"], 14, "canonical operation count")
    add("all_stock_ops_have_branch", all(op.branch_id for op in ops if op.group in {"opening_balances", "purchase_invoice", "sales_invoice", "sales_return", "purchase_return", "inventory_transfer", "manufacturing", "pos_sale", "restaurant_order"}), "branch_checked", "branch_checked", "stock-affecting operations declare branch scope")

    for section in ("stock_by_item_warehouse", "cashbox_balances", "customer_receivables", "supplier_payables", "expenses"):
        actual_section = actual[section]
        expected_section = EXPECTED_GOLDEN_TOTALS[section]
        add(f"section::{section}", actual_section == expected_section, actual_section, expected_section, f"{section} matches golden totals")

    for key, expected_value in EXPECTED_GOLDEN_TOTALS["totals"].items():  # type: ignore[union-attr]
        actual_value = actual["totals"][key]  # type: ignore[index]
        add(f"total::{key}", actual_value == expected_value, actual_value, expected_value, f"{key} matches golden total")

    invariant_map = {
        "cashbox_balance_matches_all_cash_movements": actual["cashbox_balances"] == EXPECTED_GOLDEN_TOTALS["cashbox_balances"],
        "customer_receivable_matches_sales_returns_and_receipts": actual["customer_receivables"] == EXPECTED_GOLDEN_TOTALS["customer_receivables"],
        "supplier_payable_matches_purchases_returns_and_payments": actual["supplier_payables"] == EXPECTED_GOLDEN_TOTALS["supplier_payables"],
        "warehouse_quantities_match_purchases_returns_sales_transfers_and_manufacturing": actual["stock_by_item_warehouse"] == EXPECTED_GOLDEN_TOTALS["stock_by_item_warehouse"],
        "finished_goods_cost_is_derived_from_component_consumption": actual["totals"]["manufacturing_cost"] == "200.00",  # type: ignore[index]
        "gross_profit_uses_document_cost_basis_not_current_price": actual["totals"]["gross_profit"] == "465.00",  # type: ignore[index]
        "branch_scope_is_present_for_every_stock_affecting_operation": all(op.branch_id for op in ops),
        "every_operation_has_a_stable_operation_id_for_offline_replay_and_idempotency": len(ids) == len(set(ids)) and all(op.operation_id.startswith("GD-") for op in ops),
    }
    for invariant in critical_invariants():
        add(f"invariant::{invariant}", bool(invariant_map.get(invariant)), bool(invariant_map.get(invariant)), True, "critical business invariant")
    return tuple(rows)


def scenario_summary() -> Dict[str, object]:
    ops = build_golden_operations()
    actual = calculate_golden_expected(ops)
    failed = [row for row in build_invariant_rows(ops) if row["status"] != "OK"]
    return {
        "phase": 423,
        "operation_count": actual["operation_count"],
        "scenario_groups": actual["scenario_groups"],
        "stock_positions": len(actual["stock_by_item_warehouse"]),
        "cashboxes": len(actual["cashbox_balances"]),
        "customer_count": len(actual["customer_receivables"]),
        "supplier_count": len(actual["supplier_payables"]),
        "gross_profit": actual["totals"]["gross_profit"],  # type: ignore[index]
        "failures": len(failed),
    }


def build_golden_scenario_result() -> GoldenScenarioResult:
    ops = build_golden_operations()
    return GoldenScenarioResult(operations=ops, expected=calculate_golden_expected(ops), invariant_rows=build_invariant_rows(ops))


def failures(rows: Iterable[Mapping[str, object]]) -> Tuple[Mapping[str, object], ...]:
    return tuple(row for row in rows if row.get("status") != "OK")


__all__ = [
    "GoldenOperation",
    "GoldenScenarioResult",
    "EXPECTED_GOLDEN_TOTALS",
    "build_golden_operations",
    "calculate_golden_expected",
    "build_invariant_rows",
    "build_golden_scenario_result",
    "scenario_summary",
    "failures",
]
