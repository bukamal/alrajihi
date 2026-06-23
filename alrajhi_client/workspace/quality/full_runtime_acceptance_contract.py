# -*- coding: utf-8 -*-
"""Full runtime acceptance and packaging smoke contract (Phase 345).

This module is intentionally PyQt-free.  It does not start the desktop UI,
open a browser, or send jobs to physical printers.  Instead it gives the
release process a deterministic acceptance matrix that combines the static
contracts, non-destructive scenario smoke plans, barcode/profile coverage,
Windows packaging readiness, and a clearly separated manual/hardware checklist.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[3]

STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_MANUAL = "manual_required"


@dataclass(frozen=True)
class RuntimeAcceptanceRow:
    key: str
    category: str
    title: str
    status: str
    required: bool = True
    domain: str = ""
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status == STATUS_PASS or (self.status == STATUS_MANUAL and not self.required)

    def as_row(self) -> dict[str, object]:
        return {
            "key": self.key,
            "category": self.category,
            "title": self.title,
            "status": self.status,
            "required": bool(self.required),
            "domain": self.domain,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class AcceptanceDomain:
    key: str
    title: str
    page_ids: tuple[str, ...] = ()
    table_contracts: tuple[str, ...] = ()
    barcode_profiles: tuple[str, ...] = ()
    scenario_keys: tuple[str, ...] = ()


ACCEPTANCE_DOMAINS: tuple[AcceptanceDomain, ...] = (
    AcceptanceDomain(
        "transactions",
        "Sales, purchase, returns and document printing",
        page_ids=("sales_invoices", "purchase_invoices", "returns", "purchase_returns"),
        table_contracts=("sales_invoices.lines", "purchase_invoices.lines", "returns.lines", "purchase_returns.lines"),
        scenario_keys=("sales_invoice_full_cycle", "purchase_invoice_full_cycle", "sales_return_edit_print", "purchase_return_edit_print"),
    ),
    AcceptanceDomain(
        "pos",
        "POS checkout and receipt printing",
        page_ids=("pos",),
        table_contracts=("pos.lines",),
        barcode_profiles=("items.default",),
        scenario_keys=("pos_fast_sale_receipt",),
    ),
    AcceptanceDomain(
        "restaurant",
        "Restaurant order, KDS, table and checkout flow",
        page_ids=("restaurant",),
        table_contracts=("restaurant.order_lines", "restaurant.kitchen_queue", "restaurant.tables", "restaurant.kds_lines"),
        barcode_profiles=("restaurant.menu_items", "restaurant.table_labels"),
        scenario_keys=("restaurant_table_order_checkout",),
    ),
    AcceptanceDomain(
        "cafe",
        "Cafe products, modifiers and preparation flow",
        page_ids=("cafe",),
        table_contracts=("cafe.order_lines", "cafe.preparation_queue", "cafe.preparation_lines", "cafe.shift_report"),
        barcode_profiles=("cafe.products", "cafe.modifier_labels"),
    ),
    AcceptanceDomain(
        "apparel",
        "Apparel variants, matrix and barcode labels",
        page_ids=("apparel",),
        table_contracts=("apparel.variants", "apparel.matrix", "apparel.reports"),
        barcode_profiles=("apparel.variant_labels",),
        scenario_keys=("material_barcode_lookup_label",),
    ),
    AcceptanceDomain(
        "inventory_manufacturing_finance",
        "Inventory, manufacturing and finance smoke scenarios",
        page_ids=("warehouses", "manufacturing", "vouchers", "cashboxes"),
        table_contracts=("warehouses.warehouses", "warehouses.balances", "warehouses.transfers", "manufacturing.orders", "vouchers.voucher_lines", "cashboxes.cashboxes"),
        scenario_keys=("inventory_transfer_print", "bom_cost_print", "production_order_lifecycle", "voucher_cash_bank_flow"),
    ),
    AcceptanceDomain(
        "reports_settings_quality",
        "Reports, settings, diagnostics and release quality",
        page_ids=("reports", "settings", "audit_log", "offline_queue", "monitoring"),
        table_contracts=("reports.result", "audit_log.events", "offline_queue.queue", "monitoring.health"),
        scenario_keys=("report_income_statement_print_export",),
    ),
)

REQUIRED_BUILD_FILES: tuple[str, ...] = (
    "requirements.txt",
    "alrajhi_client/main.py",
    "alrajhi_server/run_server.py",
    "build/build_windows.ps1",
    "build/pyinstaller_hidden_imports.py",
    ".github/workflows/build-windows-installer.yml",
)

MANUAL_ACCEPTANCE_ITEMS: tuple[RuntimeAcceptanceRow, ...] = (
    RuntimeAcceptanceRow("manual_windows_exe_launch", "manual", "Launch the real Windows EXE on a clean machine", STATUS_MANUAL, required=False, domain="packaging", detail="Requires an actual Windows build artifact and clean Windows host."),
    RuntimeAcceptanceRow("manual_a4_print", "manual", "Print A4 invoice/report sample with Arabic/English/German data", STATUS_MANUAL, required=False, domain="printing", detail="Requires a physical or virtual A4 printer."),
    RuntimeAcceptanceRow("manual_thermal_receipt", "manual", "Print POS/restaurant/cafe thermal receipt", STATUS_MANUAL, required=False, domain="printing", detail="Requires thermal receipt hardware or driver."),
    RuntimeAcceptanceRow("manual_barcode_printer", "manual", "Print item/apparel/restaurant/cafe barcode labels", STATUS_MANUAL, required=False, domain="barcode", detail="Requires label printer and final label-stock dimensions."),
    RuntimeAcceptanceRow("manual_remote_api_multi_user", "manual", "Run remote/API mode with more than one user, branch, warehouse and cashbox", STATUS_MANUAL, required=False, domain="network", detail="Requires server deployment/network session; local CI cannot prove this end-to-end."),
    RuntimeAcceptanceRow("manual_backup_restore_upgrade", "manual", "Upgrade old database, backup, restore and re-open the application", STATUS_MANUAL, required=False, domain="database", detail="Requires representative customer database snapshots."),
)


def _row(key: str, category: str, title: str, ok: bool, *, domain: str = "", detail: str = "", required: bool = True) -> RuntimeAcceptanceRow:
    return RuntimeAcceptanceRow(
        key=key,
        category=category,
        title=title,
        status=STATUS_PASS if ok else STATUS_FAIL,
        required=required,
        domain=domain,
        detail=detail,
    )


def _missing(values: Iterable[str], available: Iterable[str]) -> list[str]:
    available_set = set(available)
    return [v for v in values if v not in available_set]


def _domain_contract_rows() -> list[RuntimeAcceptanceRow]:
    from workspace.registry import BARCODE_PRINT_PROFILES, PAGE_MANIFESTS
    from workspace.scenarios.scenario_runtime_smoke import all_smoke_plans
    from workspace.tables.table_column_registry import TABLE_COLUMN_CONTRACTS

    scenario_keys = {plan.scenario_key for plan in all_smoke_plans()}
    rows: list[RuntimeAcceptanceRow] = []
    for domain in ACCEPTANCE_DOMAINS:
        missing_pages = _missing(domain.page_ids, PAGE_MANIFESTS)
        rows.append(_row(
            f"{domain.key}_pages_registered",
            "runtime_surface",
            f"{domain.title}: registered pages",
            not missing_pages,
            domain=domain.key,
            detail="missing=" + ",".join(missing_pages) if missing_pages else ",".join(domain.page_ids),
        ))

        missing_contracts = _missing(domain.table_contracts, TABLE_COLUMN_CONTRACTS)
        rows.append(_row(
            f"{domain.key}_table_contracts",
            "columns",
            f"{domain.title}: table contracts",
            not missing_contracts,
            domain=domain.key,
            detail="missing=" + ",".join(missing_contracts) if missing_contracts else ",".join(domain.table_contracts),
        ))

        missing_profiles = _missing(domain.barcode_profiles, BARCODE_PRINT_PROFILES)
        profile_details: list[str] = []
        for profile_id in domain.barcode_profiles:
            profile = BARCODE_PRINT_PROFILES.get(profile_id)
            if profile is None:
                continue
            if not profile.browser_html_only:
                profile_details.append(f"{profile_id}:not_browser_html_only")
            if not profile.supports_multi_print:
                profile_details.append(f"{profile_id}:no_multi_print")
        ok_profiles = not missing_profiles and not profile_details
        rows.append(_row(
            f"{domain.key}_barcode_profiles",
            "barcode",
            f"{domain.title}: barcode profiles",
            ok_profiles,
            domain=domain.key,
            detail="missing=" + ",".join(missing_profiles) if missing_profiles else ";".join(profile_details) or ",".join(domain.barcode_profiles),
            required=bool(domain.barcode_profiles),
        ))

        missing_scenarios = _missing(domain.scenario_keys, scenario_keys)
        rows.append(_row(
            f"{domain.key}_scenario_smoke_plans",
            "scenario",
            f"{domain.title}: non-destructive scenario smoke plans",
            not missing_scenarios,
            domain=domain.key,
            detail="missing=" + ",".join(missing_scenarios) if missing_scenarios else ",".join(domain.scenario_keys),
            required=bool(domain.scenario_keys),
        ))
    return rows


def _scenario_smoke_rows() -> list[RuntimeAcceptanceRow]:
    from workspace.scenarios.scenario_runtime_smoke import run_dry_smoke, smoke_coverage_summary, validate_runtime_smoke_hooks

    warnings = validate_runtime_smoke_hooks()
    summary = smoke_coverage_summary()
    results = run_dry_smoke()
    failed = [r for r in results if r.status == "failed"]
    passed = sum(1 for r in results if r.status == "passed")
    skipped = sum(1 for r in results if r.status == "skipped")
    return [
        _row(
            "scenario_runtime_smoke_contract_valid",
            "scenario",
            "Scenario runtime smoke hooks validate without warnings",
            not warnings,
            domain="all",
            detail="; ".join(warnings[:10]) if warnings else f"{summary['scenario_count']} scenarios / {summary['check_count']} checks",
        ),
        _row(
            "scenario_runtime_dry_run_no_failures",
            "scenario",
            "Static and dry-run scenario checks pass; UI callbacks remain explicitly skipped",
            not failed,
            domain="all",
            detail=f"passed={passed}; skipped_callbacks={skipped}; failed={len(failed)}",
        ),
    ]


def _packaging_rows(root: Path) -> list[RuntimeAcceptanceRow]:
    from workspace.packaging.windows_packaging_gate_contract import validate_windows_packaging_gate, windows_packaging_gate_summary

    rows: list[RuntimeAcceptanceRow] = []
    missing_files = [rel for rel in REQUIRED_BUILD_FILES if not (root / rel).exists()]
    rows.append(_row(
        "runtime_build_files_present",
        "packaging",
        "Runtime and Windows build entry files are present",
        not missing_files,
        domain="packaging",
        detail="missing=" + ",".join(missing_files) if missing_files else ",".join(REQUIRED_BUILD_FILES),
    ))
    packaging_issues = validate_windows_packaging_gate(root)
    packaging_summary = windows_packaging_gate_summary(root)
    rows.append(_row(
        "windows_packaging_gate_ready",
        "packaging",
        "Windows runtime packaging gate is clean before building EXE",
        not packaging_issues,
        domain="packaging",
        detail=f"checks={packaging_summary['checks']}; issue_groups={packaging_summary['issue_groups']}",
    ))
    build_text = (root / "build" / "build_windows.ps1").read_text(encoding="utf-8", errors="replace") if (root / "build" / "build_windows.ps1").exists() else ""
    required_guard_tokens = (
        "release_packaging_guard.py",
        "release_hidden_imports_guard.py",
        "windows_runtime_packaging_gate_audit.py",
        "unified_printing_guard.py",
    )
    missing_tokens = [token for token in required_guard_tokens if token not in build_text]
    rows.append(_row(
        "windows_build_runs_core_release_guards",
        "packaging",
        "Windows build script runs core release/printing/package guards",
        not missing_tokens,
        domain="packaging",
        detail="missing=" + ",".join(missing_tokens) if missing_tokens else ",".join(required_guard_tokens),
    ))
    return rows


def _release_quality_rows(root: Path) -> list[RuntimeAcceptanceRow]:
    from workspace.quality.release_gate_contract import release_gate_summary, validate_release_gate

    issues = validate_release_gate(root)
    summary = release_gate_summary(root)
    return [
        _row(
            "release_gate_ready",
            "quality",
            "Release readiness gate has no missing required phase docs/tests/tools",
            not issues,
            domain="quality",
            detail=f"checks={summary['checks']}; issue_groups={summary['issue_groups']}; issues={summary['issues']}",
        )
    ]


def runtime_acceptance_rows(root: Path | None = None, *, include_manual: bool = True) -> list[RuntimeAcceptanceRow]:
    base = root or ROOT
    rows: list[RuntimeAcceptanceRow] = []
    rows.extend(_domain_contract_rows())
    rows.extend(_scenario_smoke_rows())
    rows.extend(_packaging_rows(base))
    rows.extend(_release_quality_rows(base))
    if include_manual:
        rows.extend(MANUAL_ACCEPTANCE_ITEMS)
    return rows


def runtime_acceptance_issues(rows: Iterable[RuntimeAcceptanceRow] | None = None) -> dict[str, list[str]]:
    issues: dict[str, list[str]] = {}
    for row in rows or runtime_acceptance_rows(include_manual=False):
        if row.required and row.status == STATUS_FAIL:
            issues.setdefault(row.category, []).append(f"{row.key}: {row.detail}")
    return issues


def runtime_acceptance_summary(root: Path | None = None) -> Mapping[str, object]:
    rows = runtime_acceptance_rows(root, include_manual=True)
    issues = runtime_acceptance_issues(rows)
    categories: Dict[str, int] = {}
    status_counts: Dict[str, int] = {}
    for row in rows:
        categories[row.category] = categories.get(row.category, 0) + 1
        status_counts[row.status] = status_counts.get(row.status, 0) + 1
    return {
        "phase": 345,
        "checks": len(rows),
        "automated_checks": sum(1 for row in rows if row.status != STATUS_MANUAL),
        "manual_checks": sum(1 for row in rows if row.status == STATUS_MANUAL),
        "categories": categories,
        "statuses": status_counts,
        "issues": sum(len(v) for v in issues.values()),
        "issue_groups": len(issues),
        "ready_for_manual_hardware_pass": not issues,
    }


__all__ = [
    "ACCEPTANCE_DOMAINS",
    "MANUAL_ACCEPTANCE_ITEMS",
    "RuntimeAcceptanceRow",
    "runtime_acceptance_issues",
    "runtime_acceptance_rows",
    "runtime_acceptance_summary",
]
