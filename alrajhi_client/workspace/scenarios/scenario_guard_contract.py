# -*- coding: utf-8 -*-
"""End-to-end business scenario guard matrix (Phase 271).

This module is intentionally data-only.  It ties together the contracts created
in the previous phases so CI can catch cross-cutting gaps before a regression
reaches a user-visible workflow.

A scenario is not a UI test.  It is a governance contract for a complete
business path: which shell owns it, which API endpoint is used, which permission
is required, whether branch/currency/language/print/audit/offline behavior is
expected, and which existing contract must cover each step.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from workspace.audit.audit_contract import audit_event_descriptor_for
from workspace.branches.branch_access_contract import branch_access_descriptor_map
from workspace.documents.document_contract import (
    BRANCH_NONE,
    CURRENCY_NONE,
    NETWORK_LOCAL_ONLY,
    descriptor_for,
)
from workspace.lists.list_workspace_contract import list_descriptor_for
from workspace.operational.operational_shell_contract import operational_descriptor_for
from workspace.security.rbac_contract import OPERATION_ACTION_PERMISSION_MAP, permission_descriptor_map
from workspace.settings.settings_contract import settings_descriptor_for
from workspace.sync.offline_sync_contract import offline_descriptor_for

try:  # Report contracts live under features/ for historical reasons.
    from features.reports.report_shell_contract import report_descriptor_for_key
except Exception:  # pragma: no cover - import safety for packaging analysis.
    report_descriptor_for_key = None  # type: ignore


SURFACE_DOCUMENT = "document"
SURFACE_LIST = "list"
SURFACE_REPORT = "report"
SURFACE_OPERATIONAL = "operational"

EXPECT_CURRENCY = "currency"
EXPECT_BRANCH = "branch"
EXPECT_PRINT = "print"
EXPECT_EXPORT = "export"
EXPECT_AUDIT = "audit"
EXPECT_OFFLINE = "offline"
EXPECT_SETTINGS = "settings"
EXPECT_RBAC = "rbac"
EXPECT_API = "api"
EXPECT_I18N = "i18n"


@dataclass(frozen=True)
class ScenarioStep:
    """One guarded step inside an end-to-end scenario."""

    key: str
    surface: str
    action: str
    document_type: str = ""
    list_key: str = ""
    report_key: str = ""
    operational_shell: str = ""
    operation_key: str = ""
    api_resource: str = ""
    permission_key: str = ""
    audit_event_key: str = ""
    offline_surface_key: str = ""
    expects: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""


@dataclass(frozen=True)
class ScenarioDescriptor:
    """Complete workflow guard for a business scenario."""

    scenario_key: str
    title_key: str
    module: str
    primary_document_type: str
    steps: tuple[ScenarioStep, ...]
    language_scope: str
    settings_scope: str
    branch_sensitive: bool = True
    currency_sensitive: bool = False
    network_sensitive: bool = True
    print_sensitive: bool = False
    offline_sensitive: bool = False
    audit_sensitive: bool = True
    notes: str = ""

    def step_for(self, key: str, default: ScenarioStep | None = None) -> ScenarioStep | None:
        for step in self.steps:
            if step.key == key:
                return step
        return default


def _doc(document_type: str, action: str) -> tuple[str, str, str, str]:
    descriptor = descriptor_for(document_type)
    if descriptor is None:
        return "", "", "", ""
    permission_action = "update" if action == "save" else action
    return (
        descriptor.api_resource,
        descriptor.permission_for(permission_action) or descriptor.permission_for("create"),
        f"document.{document_type}.{action}",
        f"document.{document_type}",
    )


def _list(list_key: str, action: str) -> tuple[str, str, str, str]:
    descriptor = list_descriptor_for(list_key)
    if descriptor is None:
        return "", "", "", ""
    return (
        descriptor.api_resource,
        descriptor.permission_for(action),
        f"list.{list_key}.{action}",
        "",
    )


def _op(shell_key: str, operation_key: str) -> tuple[str, str, str, str]:
    descriptor = operational_descriptor_for(shell_key)
    if descriptor is None:
        return "", "", "", ""
    operation = descriptor.operation_for(operation_key)
    permission = ""
    if operation is not None:
        permission = OPERATION_ACTION_PERMISSION_MAP.get(operation.permission_action, operation.permission_action)
    return (
        descriptor.api_resource,
        permission,
        f"operational.{shell_key}.{operation_key}",
        f"operational.{shell_key}.{operation_key}",
    )


def _report(report_key: str, action: str) -> tuple[str, str, str, str]:
    descriptor = report_descriptor_for_key(report_key) if report_descriptor_for_key else None
    if descriptor is None:
        return "", "", "", ""
    return (
        descriptor.api_resource,
        descriptor.permission_for(action),
        f"report.{report_key}.{action}",
        f"report.{report_key}",
    )


def document_step(document_type: str, action: str, *, key: str | None = None, expects: tuple[str, ...] = (), notes: str = "") -> ScenarioStep:
    api, permission, audit, offline = _doc(document_type, action)
    return ScenarioStep(
        key=key or f"{document_type}.{action}",
        surface=SURFACE_DOCUMENT,
        action=action,
        document_type=document_type,
        api_resource=api,
        permission_key=permission,
        audit_event_key=audit,
        offline_surface_key=offline,
        expects=expects,
        notes=notes,
    )


def list_step(list_key: str, action: str, *, key: str | None = None, expects: tuple[str, ...] = (), notes: str = "") -> ScenarioStep:
    api, permission, audit, offline = _list(list_key, action)
    return ScenarioStep(
        key=key or f"{list_key}.{action}",
        surface=SURFACE_LIST,
        action=action,
        list_key=list_key,
        api_resource=api,
        permission_key=permission,
        audit_event_key=audit,
        offline_surface_key=offline,
        expects=expects,
        notes=notes,
    )


def operational_step(shell_key: str, operation_key: str, *, key: str | None = None, expects: tuple[str, ...] = (), notes: str = "") -> ScenarioStep:
    api, permission, audit, offline = _op(shell_key, operation_key)
    return ScenarioStep(
        key=key or f"{shell_key}.{operation_key}",
        surface=SURFACE_OPERATIONAL,
        action=operation_key,
        operational_shell=shell_key,
        operation_key=operation_key,
        api_resource=api,
        permission_key=permission,
        audit_event_key=audit,
        offline_surface_key=offline,
        expects=expects,
        notes=notes,
    )


def report_step(report_key: str, action: str, *, key: str | None = None, expects: tuple[str, ...] = (), notes: str = "") -> ScenarioStep:
    api, permission, audit, offline = _report(report_key, action)
    return ScenarioStep(
        key=key or f"{report_key}.{action}",
        surface=SURFACE_REPORT,
        action=action,
        report_key=report_key,
        api_resource=api,
        permission_key=permission,
        audit_event_key=audit,
        offline_surface_key=offline,
        expects=expects,
        notes=notes,
    )


def _common_write_expectations(*, print_: bool = True, offline: bool = True) -> tuple[str, ...]:
    values = [EXPECT_API, EXPECT_RBAC, EXPECT_BRANCH, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_AUDIT]
    if print_:
        values.append(EXPECT_PRINT)
    if offline:
        values.append(EXPECT_OFFLINE)
    return tuple(values)


SCENARIO_GUARD_DESCRIPTORS: tuple[ScenarioDescriptor, ...] = (
    ScenarioDescriptor(
        scenario_key="sales_invoice_full_cycle",
        title_key="scenario_sales_invoice_full_cycle",
        module="transactions",
        primary_document_type="sales_invoice",
        language_scope="transactions.sales_invoice",
        settings_scope="transactions.sales_invoice",
        currency_sensitive=True,
        print_sensitive=True,
        offline_sensitive=True,
        steps=(
            list_step("sales_invoices", "open", expects=(EXPECT_RBAC, EXPECT_BRANCH, EXPECT_AUDIT, EXPECT_I18N)),
            document_step("sales_invoice", "save", expects=_common_write_expectations()),
            document_step("sales_invoice", "print", expects=(EXPECT_PRINT, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_RBAC, EXPECT_AUDIT)),
            report_step("invoice_profit", "view", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_BRANCH, EXPECT_CURRENCY, EXPECT_AUDIT)),
        ),
    ),
    ScenarioDescriptor(
        scenario_key="purchase_invoice_full_cycle",
        title_key="scenario_purchase_invoice_full_cycle",
        module="transactions",
        primary_document_type="purchase_invoice",
        language_scope="transactions.purchase_invoice",
        settings_scope="transactions.purchase_invoice",
        currency_sensitive=True,
        print_sensitive=True,
        offline_sensitive=True,
        steps=(
            list_step("purchase_invoices", "open", expects=(EXPECT_RBAC, EXPECT_BRANCH, EXPECT_AUDIT, EXPECT_I18N)),
            document_step("purchase_invoice", "save", expects=_common_write_expectations()),
            document_step("purchase_invoice", "print", expects=(EXPECT_PRINT, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_RBAC, EXPECT_AUDIT)),
            report_step("supplier_statement", "view", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_CURRENCY, EXPECT_AUDIT)),
        ),
    ),
    ScenarioDescriptor(
        scenario_key="sales_return_edit_print",
        title_key="scenario_sales_return_edit_print",
        module="transactions",
        primary_document_type="sales_return",
        language_scope="transactions.sales_return",
        settings_scope="transactions.sales_return",
        currency_sensitive=True,
        print_sensitive=True,
        offline_sensitive=True,
        steps=(
            list_step("sales_returns", "open", expects=(EXPECT_RBAC, EXPECT_BRANCH, EXPECT_AUDIT, EXPECT_I18N)),
            document_step("sales_return", "save", expects=_common_write_expectations()),
            document_step("sales_return", "print", expects=(EXPECT_PRINT, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_RBAC, EXPECT_AUDIT)),
            report_step("customer_statement", "view", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_CURRENCY, EXPECT_AUDIT)),
        ),
        notes="Protects the return list double-click/edit/print path fixed in Phase 266.",
    ),
    ScenarioDescriptor(
        scenario_key="purchase_return_edit_print",
        title_key="scenario_purchase_return_edit_print",
        module="transactions",
        primary_document_type="purchase_return",
        language_scope="transactions.purchase_return",
        settings_scope="transactions.purchase_return",
        currency_sensitive=True,
        print_sensitive=True,
        offline_sensitive=True,
        steps=(
            list_step("purchase_returns", "open", expects=(EXPECT_RBAC, EXPECT_BRANCH, EXPECT_AUDIT, EXPECT_I18N)),
            document_step("purchase_return", "save", expects=_common_write_expectations()),
            document_step("purchase_return", "print", expects=(EXPECT_PRINT, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_RBAC, EXPECT_AUDIT)),
            report_step("supplier_statement", "view", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_CURRENCY, EXPECT_AUDIT)),
        ),
        notes="Protects the purchase return currency/print path fixed in Phase 266.",
    ),
    ScenarioDescriptor(
        scenario_key="pos_fast_sale_receipt",
        title_key="scenario_pos_fast_sale_receipt",
        module="pos",
        primary_document_type="pos",
        language_scope="pos.shell",
        settings_scope="pos",
        currency_sensitive=True,
        print_sensitive=True,
        offline_sensitive=True,
        steps=(
            operational_step("pos", "checkout", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_BRANCH, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_AUDIT, EXPECT_OFFLINE)),
            operational_step("pos", "print_receipt", expects=(EXPECT_PRINT, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_RBAC, EXPECT_AUDIT)),
            report_step("pos_shifts", "view", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_BRANCH, EXPECT_CURRENCY, EXPECT_AUDIT)),
        ),
        notes="Protects the POS thermal receipt, logo and currency path fixed in Phase 268.",
    ),
    ScenarioDescriptor(
        scenario_key="restaurant_table_order_checkout",
        title_key="scenario_restaurant_table_order_checkout",
        module="restaurant",
        primary_document_type="restaurant",
        language_scope="restaurant.shell",
        settings_scope="restaurant",
        currency_sensitive=True,
        print_sensitive=True,
        offline_sensitive=False,
        steps=(
            operational_step("restaurant", "open_session", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_BRANCH, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_AUDIT)),
            operational_step("restaurant", "send_kitchen", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_BRANCH, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_AUDIT)),
            operational_step("restaurant", "print_kitchen_ticket", expects=(EXPECT_PRINT, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_RBAC, EXPECT_AUDIT)),
            operational_step("restaurant", "checkout", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_BRANCH, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_AUDIT)),
            operational_step("restaurant", "print_receipt", expects=(EXPECT_PRINT, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_RBAC, EXPECT_AUDIT)),
        ),
    ),
    ScenarioDescriptor(
        scenario_key="bom_cost_print",
        title_key="scenario_bom_cost_print",
        module="manufacturing",
        primary_document_type="bom",
        language_scope="manufacturing.bom",
        settings_scope="manufacturing.bom",
        branch_sensitive=False,
        currency_sensitive=True,
        print_sensitive=True,
        offline_sensitive=False,
        steps=(
            document_step("bom", "save", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_AUDIT)),
            document_step("bom", "print", expects=(EXPECT_PRINT, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_RBAC, EXPECT_AUDIT)),
            report_step("product_cost", "view", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_BRANCH, EXPECT_CURRENCY, EXPECT_AUDIT)),
        ),
        notes="Protects the manufacturing cost/0E+1 print path fixed in Phase 269.",
    ),
    ScenarioDescriptor(
        scenario_key="production_order_lifecycle",
        title_key="scenario_production_order_lifecycle",
        module="manufacturing",
        primary_document_type="production_order",
        language_scope="manufacturing.production_order",
        settings_scope="manufacturing.production_orders",
        branch_sensitive=False,
        currency_sensitive=True,
        print_sensitive=True,
        offline_sensitive=False,
        steps=(
            document_step("production_order", "save", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_AUDIT)),
            document_step("production_order", "print", expects=(EXPECT_PRINT, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_RBAC, EXPECT_AUDIT)),
            report_step("manufacturing_orders", "view", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_CURRENCY, EXPECT_AUDIT)),
        ),
    ),
    ScenarioDescriptor(
        scenario_key="inventory_transfer_print",
        title_key="scenario_inventory_transfer_print",
        module="inventory",
        primary_document_type="warehouse_transfer",
        language_scope="inventory.transfer",
        settings_scope="inventory.transfers",
        currency_sensitive=False,
        print_sensitive=True,
        offline_sensitive=False,
        steps=(
            list_step("warehouse_transfers", "open", expects=(EXPECT_RBAC, EXPECT_BRANCH, EXPECT_AUDIT, EXPECT_I18N)),
            document_step("warehouse_transfer", "save", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_BRANCH, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_AUDIT)),
            document_step("warehouse_transfer", "print", expects=(EXPECT_PRINT, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_RBAC, EXPECT_AUDIT)),
            report_step("warehouse_movements", "view", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_BRANCH, EXPECT_AUDIT)),
        ),
    ),
    ScenarioDescriptor(
        scenario_key="voucher_cash_bank_flow",
        title_key="scenario_voucher_cash_bank_flow",
        module="finance",
        primary_document_type="voucher",
        language_scope="finance.voucher",
        settings_scope="finance.vouchers",
        currency_sensitive=True,
        print_sensitive=True,
        offline_sensitive=True,
        steps=(
            list_step("vouchers", "open", expects=(EXPECT_RBAC, EXPECT_BRANCH, EXPECT_AUDIT, EXPECT_I18N)),
            document_step("voucher", "save", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_AUDIT, EXPECT_OFFLINE)),
            document_step("voucher", "print", expects=(EXPECT_PRINT, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_RBAC, EXPECT_AUDIT)),
            report_step("cash_movements", "view", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_BRANCH, EXPECT_CURRENCY, EXPECT_AUDIT)),
        ),
        notes="Protects the Voucher Document Shell layout fixed in Phase 267.",
    ),
    ScenarioDescriptor(
        scenario_key="material_barcode_lookup_label",
        title_key="scenario_material_barcode_lookup_label",
        module="materials",
        primary_document_type="material",
        language_scope="materials.document",
        settings_scope="materials",
        branch_sensitive=False,
        currency_sensitive=True,
        print_sensitive=True,
        offline_sensitive=True,
        steps=(
            list_step("materials", "open", expects=(EXPECT_RBAC, EXPECT_AUDIT, EXPECT_I18N)),
            document_step("material", "save", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_AUDIT, EXPECT_OFFLINE)),
            document_step("material", "print", expects=(EXPECT_PRINT, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_RBAC, EXPECT_AUDIT)),
        ),
    ),
    ScenarioDescriptor(
        scenario_key="report_income_statement_print_export",
        title_key="scenario_report_income_statement_print_export",
        module="reports",
        primary_document_type="reports",
        language_scope="reports.shell",
        settings_scope="reports",
        branch_sensitive=False,
        currency_sensitive=True,
        print_sensitive=True,
        offline_sensitive=False,
        steps=(
            report_step("income_statement", "view", expects=(EXPECT_API, EXPECT_RBAC, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_AUDIT)),
            report_step("income_statement", "print", expects=(EXPECT_PRINT, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_RBAC, EXPECT_AUDIT)),
            report_step("income_statement", "export", expects=(EXPECT_EXPORT, EXPECT_CURRENCY, EXPECT_SETTINGS, EXPECT_I18N, EXPECT_RBAC, EXPECT_AUDIT)),
        ),
    ),
)


_SCENARIO_BY_KEY: dict[str, ScenarioDescriptor] = {s.scenario_key: s for s in SCENARIO_GUARD_DESCRIPTORS}


def scenario_descriptor_for(scenario_key: str, default: ScenarioDescriptor | None = None) -> ScenarioDescriptor | None:
    return _SCENARIO_BY_KEY.get(str(scenario_key or ""), default)


def all_scenario_descriptors() -> tuple[ScenarioDescriptor, ...]:
    return SCENARIO_GUARD_DESCRIPTORS


def _descriptor_for_step(step: ScenarioStep):
    if step.surface == SURFACE_DOCUMENT:
        return descriptor_for(step.document_type)
    if step.surface == SURFACE_LIST:
        return list_descriptor_for(step.list_key)
    if step.surface == SURFACE_OPERATIONAL:
        return operational_descriptor_for(step.operational_shell)
    if step.surface == SURFACE_REPORT and report_descriptor_for_key:
        return report_descriptor_for_key(step.report_key)
    return None


def _step_branch_policy(step: ScenarioStep) -> str:
    descriptor = _descriptor_for_step(step)
    return str(getattr(descriptor, "branch_policy", "") or "")


def _step_currency_policy(step: ScenarioStep) -> str:
    descriptor = _descriptor_for_step(step)
    return str(getattr(descriptor, "currency_policy", "") or "")


def _step_settings_scope(step: ScenarioStep) -> str:
    descriptor = _descriptor_for_step(step)
    return str(getattr(descriptor, "settings_scope", "") or "")


def _step_i18n_scope(step: ScenarioStep) -> str:
    descriptor = _descriptor_for_step(step)
    return str(getattr(descriptor, "i18n_scope", "") or "")


def _step_network_mode(step: ScenarioStep) -> str:
    descriptor = _descriptor_for_step(step)
    return str(getattr(descriptor, "network_mode", "") or "")


def _step_print_supported(step: ScenarioStep) -> bool:
    descriptor = _descriptor_for_step(step)
    if descriptor is None:
        return False
    if step.surface == SURFACE_OPERATIONAL:
        op = descriptor.operation_for(step.operation_key)
        return bool(op and (op.print_profile or "print" in op.category or "print" in op.key))
    if step.surface == SURFACE_REPORT:
        return bool(getattr(descriptor, "supports_print", False))
    capabilities = getattr(descriptor, "capabilities", None)
    return bool(getattr(capabilities, "print", False))


def _step_export_supported(step: ScenarioStep) -> bool:
    descriptor = _descriptor_for_step(step)
    if descriptor is None:
        return False
    if step.surface == SURFACE_REPORT:
        return bool(getattr(descriptor, "supports_export", False))
    capabilities = getattr(descriptor, "capabilities", None)
    return bool(getattr(capabilities, "export", False))


def validate_scenario_descriptors(descriptors: Iterable[ScenarioDescriptor] | None = None) -> list[str]:
    warnings: list[str] = []
    seen: set[str] = set()
    rbac_keys = permission_descriptor_map()

    for scenario in descriptors or SCENARIO_GUARD_DESCRIPTORS:
        if not scenario.scenario_key:
            warnings.append("scenario without scenario_key")
        if scenario.scenario_key in seen:
            warnings.append(f"duplicate scenario_key: {scenario.scenario_key}")
        seen.add(scenario.scenario_key)
        if not scenario.steps:
            warnings.append(f"{scenario.scenario_key}: no steps")
        if not scenario.language_scope:
            warnings.append(f"{scenario.scenario_key}: missing language_scope")
        if not scenario.settings_scope:
            warnings.append(f"{scenario.scenario_key}: missing settings_scope")
        if scenario.primary_document_type and descriptor_for(scenario.primary_document_type) is None:
            warnings.append(f"{scenario.scenario_key}: missing primary DocumentDescriptor {scenario.primary_document_type}")
        if scenario.settings_scope and settings_descriptor_for(scenario.settings_scope) is None:
            warnings.append(f"{scenario.scenario_key}: missing SettingsScopeDescriptor {scenario.settings_scope}")

        for step in scenario.steps:
            prefix = f"{scenario.scenario_key}.{step.key}"
            descriptor = _descriptor_for_step(step)
            if descriptor is None:
                warnings.append(f"{prefix}: missing descriptor for {step.surface}")
                continue
            if EXPECT_API in step.expects and not step.api_resource:
                warnings.append(f"{prefix}: missing api_resource")
            if EXPECT_API in step.expects and _step_network_mode(step) == NETWORK_LOCAL_ONLY:
                warnings.append(f"{prefix}: API expected but network_mode is local_only")
            if EXPECT_RBAC in step.expects:
                if not step.permission_key:
                    warnings.append(f"{prefix}: missing permission_key")
                elif step.permission_key not in rbac_keys:
                    warnings.append(f"{prefix}: permission not covered by RBAC contract: {step.permission_key}")
            if EXPECT_BRANCH in step.expects and _step_branch_policy(step) == BRANCH_NONE:
                warnings.append(f"{prefix}: branch expected but branch_policy is none")
            if EXPECT_CURRENCY in step.expects and _step_currency_policy(step) == CURRENCY_NONE:
                warnings.append(f"{prefix}: currency expected but currency_policy is none")
            if EXPECT_PRINT in step.expects and not _step_print_supported(step):
                warnings.append(f"{prefix}: print expected but descriptor does not support print")
            if EXPECT_EXPORT in step.expects and not _step_export_supported(step):
                warnings.append(f"{prefix}: export expected but descriptor does not support export")
            if EXPECT_SETTINGS in step.expects and not settings_descriptor_for(_step_settings_scope(step)):
                warnings.append(f"{prefix}: missing settings descriptor for {_step_settings_scope(step)}")
            if EXPECT_I18N in step.expects and not _step_i18n_scope(step):
                warnings.append(f"{prefix}: missing i18n scope")
            if EXPECT_AUDIT in step.expects and audit_event_descriptor_for(step.audit_event_key) is None:
                warnings.append(f"{prefix}: missing audit event {step.audit_event_key}")
            if EXPECT_OFFLINE in step.expects and not offline_descriptor_for(step.offline_surface_key):
                warnings.append(f"{prefix}: missing offline sync descriptor {step.offline_surface_key}")
            if EXPECT_BRANCH in step.expects:
                branch_key = ""
                if step.surface == SURFACE_DOCUMENT and step.document_type:
                    branch_key = f"document:{step.document_type}"
                elif step.surface == SURFACE_LIST and step.list_key:
                    branch_key = f"list:{step.list_key}"
                elif step.surface == SURFACE_REPORT and step.report_key:
                    branch_key = f"report:{step.report_key}"
                elif step.surface == SURFACE_OPERATIONAL and step.operational_shell:
                    branch_key = f"operational:{step.operational_shell}"
                if branch_key and branch_key not in branch_access_descriptor_map():
                    # Branch descriptors are stricter than document descriptors.  Do not fail branchless
                    # reference data, but flag genuinely branch-sensitive workflow surfaces.
                    if _step_branch_policy(step) != BRANCH_NONE:
                        warnings.append(f"{prefix}: missing branch access contract for {branch_key}")
    return warnings


def scenario_guard_matrix(descriptors: Iterable[ScenarioDescriptor] | None = None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for scenario in descriptors or SCENARIO_GUARD_DESCRIPTORS:
        for index, step in enumerate(scenario.steps, start=1):
            rows.append({
                "scenario_key": scenario.scenario_key,
                "module": scenario.module,
                "title_key": scenario.title_key,
                "step_index": index,
                "step_key": step.key,
                "surface": step.surface,
                "action": step.action,
                "document_type": step.document_type,
                "list_key": step.list_key,
                "report_key": step.report_key,
                "operational_shell": step.operational_shell,
                "operation_key": step.operation_key,
                "api_resource": step.api_resource,
                "network_mode": _step_network_mode(step),
                "permission_key": step.permission_key,
                "audit_event_key": step.audit_event_key,
                "offline_surface_key": step.offline_surface_key,
                "settings_scope": _step_settings_scope(step),
                "i18n_scope": _step_i18n_scope(step),
                "currency_policy": _step_currency_policy(step),
                "branch_policy": _step_branch_policy(step),
                "expects": ",".join(step.expects),
                "scenario_currency_sensitive": scenario.currency_sensitive,
                "scenario_branch_sensitive": scenario.branch_sensitive,
                "scenario_print_sensitive": scenario.print_sensitive,
                "scenario_offline_sensitive": scenario.offline_sensitive,
                "notes": step.notes or scenario.notes,
            })
    return rows


def scenario_summary_matrix(descriptors: Iterable[ScenarioDescriptor] | None = None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for scenario in descriptors or SCENARIO_GUARD_DESCRIPTORS:
        rows.append({
            "scenario_key": scenario.scenario_key,
            "module": scenario.module,
            "primary_document_type": scenario.primary_document_type,
            "steps": len(scenario.steps),
            "language_scope": scenario.language_scope,
            "settings_scope": scenario.settings_scope,
            "branch_sensitive": scenario.branch_sensitive,
            "currency_sensitive": scenario.currency_sensitive,
            "network_sensitive": scenario.network_sensitive,
            "print_sensitive": scenario.print_sensitive,
            "offline_sensitive": scenario.offline_sensitive,
            "audit_sensitive": scenario.audit_sensitive,
            "notes": scenario.notes,
        })
    return rows


def scenario_coverage_summary(descriptors: Iterable[ScenarioDescriptor] | None = None) -> Mapping[str, object]:
    scenarios = tuple(descriptors or SCENARIO_GUARD_DESCRIPTORS)
    steps = [step for scenario in scenarios for step in scenario.steps]
    return {
        "scenario_count": len(scenarios),
        "step_count": len(steps),
        "modules": tuple(sorted({scenario.module for scenario in scenarios})),
        "currency_sensitive": sum(1 for scenario in scenarios if scenario.currency_sensitive),
        "branch_sensitive": sum(1 for scenario in scenarios if scenario.branch_sensitive),
        "print_sensitive": sum(1 for scenario in scenarios if scenario.print_sensitive),
        "offline_sensitive": sum(1 for scenario in scenarios if scenario.offline_sensitive),
        "surfaces": tuple(sorted({step.surface for step in steps})),
    }
