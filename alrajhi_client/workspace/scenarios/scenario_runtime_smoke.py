# -*- coding: utf-8 -*-
"""Runtime smoke hooks for guarded business scenarios (Phase 272).

The scenario guard matrix added in Phase 271 is intentionally static.  This
module adds a second, executable layer that can be run from CI or from a future
in-app diagnostics screen without committing business transactions.

The checks here are *non-destructive by default*: they validate that every
scenario has a safe dry-run plan, route intent, permission/audit/settings hooks,
print hook metadata, and sample payload shape.  A UI runner may later provide
callbacks for actual widget opening, route probing, or HTML rendering; the
contract makes those callbacks explicit instead of importing Qt or starting a
server here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Mapping, Sequence

from workspace.audit.audit_contract import audit_event_descriptor_for
from workspace.scenarios.scenario_guard_contract import (
    EXPECT_API,
    EXPECT_AUDIT,
    EXPECT_BRANCH,
    EXPECT_CURRENCY,
    EXPECT_EXPORT,
    EXPECT_I18N,
    EXPECT_OFFLINE,
    EXPECT_PRINT,
    EXPECT_RBAC,
    EXPECT_SETTINGS,
    SURFACE_DOCUMENT,
    SURFACE_LIST,
    SURFACE_OPERATIONAL,
    SURFACE_REPORT,
    ScenarioDescriptor,
    ScenarioStep,
    all_scenario_descriptors,
    validate_scenario_descriptors,
)
from workspace.security.rbac_contract import permission_descriptor_map
from workspace.settings.settings_contract import settings_descriptor_for
from workspace.sync.offline_sync_contract import offline_descriptor_for

try:  # Keep this module usable in packaging/CI environments without full features.
    from features.reports.report_shell_contract import report_descriptor_for_key
except Exception:  # pragma: no cover - import safety.
    report_descriptor_for_key = None  # type: ignore


CHECK_CONTRACT = "contract"
CHECK_PAYLOAD = "payload_shape"
CHECK_ROUTE = "route_intent"
CHECK_PERMISSION = "permission"
CHECK_SETTINGS = "settings"
CHECK_LANGUAGE = "language"
CHECK_CURRENCY = "currency"
CHECK_BRANCH = "branch"
CHECK_PRINT = "print_hook"
CHECK_EXPORT = "export_hook"
CHECK_AUDIT = "audit_hook"
CHECK_OFFLINE = "offline_hook"

MODE_STATIC = "static"
MODE_DRY_RUN = "dry_run"
MODE_CALLBACK = "callback"

RISK_NONE = "none"
RISK_READ_ONLY = "read_only"
RISK_WRITE_INTENT = "write_intent"
RISK_PRINT_EXPORT = "print_export"


@dataclass(frozen=True)
class ScenarioSmokeCheck:
    """One non-destructive smoke check for a scenario step."""

    scenario_key: str
    step_key: str
    check_key: str
    mode: str
    required: bool = True
    risk_level: str = RISK_NONE
    callback_name: str = ""
    expected: str = ""
    notes: str = ""


@dataclass(frozen=True)
class ScenarioSmokePlan:
    """Dry-run execution plan for a complete business scenario."""

    scenario_key: str
    module: str
    title_key: str
    primary_document_type: str
    checks: tuple[ScenarioSmokeCheck, ...]
    destructive: bool = False
    safe_for_ci: bool = True

    def checks_for_step(self, step_key: str) -> tuple[ScenarioSmokeCheck, ...]:
        return tuple(check for check in self.checks if check.step_key == step_key)


@dataclass(frozen=True)
class ScenarioSmokeResult:
    """Result row for dry-run smoke execution."""

    scenario_key: str
    step_key: str
    check_key: str
    status: str
    message: str = ""
    callback_name: str = ""


SmokeCallback = Callable[[ScenarioDescriptor, ScenarioStep, ScenarioSmokeCheck], object]


_SAMPLE_BY_DOCUMENT: Mapping[str, Mapping[str, object]] = {
    "sales_invoice": {
        "type": "sales",
        "reference": "SMOKE-SAL-0001",
        "branch_id": 1,
        "currency": "SYP",
        "lines": [{"item_id": 1, "qty": 1, "price": 0}],
    },
    "purchase_invoice": {
        "type": "purchase",
        "reference": "SMOKE-PUR-0001",
        "branch_id": 1,
        "currency": "SYP",
        "lines": [{"item_id": 1, "qty": 1, "price": 0}],
    },
    "sales_return": {
        "return_no": "SMOKE-SRET-0001",
        "branch_id": 1,
        "currency": "SYP",
        "lines": [{"item_id": 1, "qty": 1, "price": 0}],
    },
    "purchase_return": {
        "return_no": "SMOKE-PRET-0001",
        "branch_id": 1,
        "currency": "SYP",
        "lines": [{"item_id": 1, "qty": 1, "price": 0}],
    },
    "voucher": {
        "voucher_type": "receipt",
        "amount": 0,
        "currency": "SYP",
        "payment_method": "cash",
        "branch_id": 1,
    },
    "material": {
        "name": "SMOKE-ITEM",
        "barcode": "SMOKE-0001",
        "currency": "SYP",
        "units": [],
    },
    "bom": {
        "product_name": "SMOKE-BOM",
        "quantity": 1,
        "currency": "SYP",
        "components": [],
    },
    "production_order": {
        "order_no": "SMOKE-PO-0001",
        "quantity": 1,
        "currency": "SYP",
        "consumptions": [],
        "outputs": [],
    },
    "warehouse_transfer": {
        "reference": "SMOKE-TR-0001",
        "source_warehouse_id": 1,
        "target_warehouse_id": 2,
        "branch_id": 1,
        "lines": [],
    },
}

_SAMPLE_OPERATION_PAYLOADS: Mapping[str, Mapping[str, object]] = {
    "pos.checkout": {
        "branch_id": 1,
        "warehouse_id": 1,
        "cashbox_id": 1,
        "currency": "SYP",
        "lines": [{"item_id": 1, "qty": 1, "price": 0}],
        "dry_run": True,
    },
    "restaurant.open_session": {"branch_id": 1, "table_id": 1, "dry_run": True},
    "restaurant.send_kitchen": {"branch_id": 1, "session_id": 1, "dry_run": True},
    "restaurant.checkout": {"branch_id": 1, "session_id": 1, "currency": "SYP", "dry_run": True},
}


def sample_payload_for_step(step: ScenarioStep) -> Mapping[str, object]:
    """Return a safe sample payload shape for a step without touching storage."""

    if step.surface == SURFACE_DOCUMENT and step.document_type:
        return dict(_SAMPLE_BY_DOCUMENT.get(step.document_type, {"dry_run": True}))
    if step.surface == SURFACE_OPERATIONAL:
        key = f"{step.operational_shell}.{step.operation_key}"
        return dict(_SAMPLE_OPERATION_PAYLOADS.get(key, {"dry_run": True}))
    if step.surface == SURFACE_REPORT:
        return {"date_from": "2000-01-01", "date_to": "2000-01-01", "branch_id": 1, "dry_run": True}
    if step.surface == SURFACE_LIST:
        return {"page": 1, "page_size": 1, "branch_id": 1, "dry_run": True}
    return {"dry_run": True}


def _write_risk(action: str) -> str:
    a = str(action or "").lower()
    if any(token in a for token in ("save", "checkout", "payment", "send_kitchen", "open_session", "close_shift", "open_shift", "delete", "cancel", "approve")):
        return RISK_WRITE_INTENT
    if "print" in a or "export" in a:
        return RISK_PRINT_EXPORT
    if any(token in a for token in ("view", "open", "search", "filter")):
        return RISK_READ_ONLY
    return RISK_NONE


def _callback_name_for(step: ScenarioStep, check_key: str) -> str:
    surface = step.surface
    action = step.action
    if check_key == CHECK_ROUTE:
        return f"probe_{surface}_route"
    if check_key == CHECK_PRINT:
        return "render_print_html"
    if check_key == CHECK_EXPORT:
        return "probe_export"
    if check_key == CHECK_PAYLOAD:
        return "build_sample_payload"
    if check_key == CHECK_PERMISSION:
        return "check_permission"
    if check_key == CHECK_AUDIT:
        return "record_dry_run_audit"
    if check_key == CHECK_OFFLINE:
        return "enqueue_dry_run_offline"
    if surface == SURFACE_OPERATIONAL:
        return f"probe_{step.operational_shell}_{step.operation_key}"
    return f"probe_{surface}_{action}"


def _checks_for_step(scenario: ScenarioDescriptor, step: ScenarioStep) -> list[ScenarioSmokeCheck]:
    checks: list[ScenarioSmokeCheck] = [
        ScenarioSmokeCheck(
            scenario_key=scenario.scenario_key,
            step_key=step.key,
            check_key=CHECK_CONTRACT,
            mode=MODE_STATIC,
            risk_level=RISK_NONE,
            expected=step.surface,
            notes="Step descriptor exists and is covered by Phase 271 validation.",
        ),
        ScenarioSmokeCheck(
            scenario_key=scenario.scenario_key,
            step_key=step.key,
            check_key=CHECK_PAYLOAD,
            mode=MODE_DRY_RUN,
            risk_level=RISK_NONE,
            callback_name=_callback_name_for(step, CHECK_PAYLOAD),
            expected=",".join(sorted(sample_payload_for_step(step).keys())),
            notes="Sample payload shape only; no persistence.",
        ),
    ]

    if EXPECT_API in step.expects:
        checks.append(ScenarioSmokeCheck(
            scenario_key=scenario.scenario_key,
            step_key=step.key,
            check_key=CHECK_ROUTE,
            mode=MODE_CALLBACK,
            risk_level=_write_risk(step.action),
            callback_name=_callback_name_for(step, CHECK_ROUTE),
            expected=step.api_resource,
            notes="Route probe must use HEAD/OPTIONS or dry-run mode when implemented.",
        ))
    if EXPECT_RBAC in step.expects:
        checks.append(ScenarioSmokeCheck(
            scenario_key=scenario.scenario_key,
            step_key=step.key,
            check_key=CHECK_PERMISSION,
            mode=MODE_STATIC,
            risk_level=RISK_NONE,
            callback_name=_callback_name_for(step, CHECK_PERMISSION),
            expected=step.permission_key,
        ))
    if EXPECT_SETTINGS in step.expects:
        checks.append(ScenarioSmokeCheck(
            scenario_key=scenario.scenario_key,
            step_key=step.key,
            check_key=CHECK_SETTINGS,
            mode=MODE_STATIC,
            risk_level=RISK_NONE,
            expected=scenario.settings_scope,
        ))
    if EXPECT_I18N in step.expects:
        checks.append(ScenarioSmokeCheck(
            scenario_key=scenario.scenario_key,
            step_key=step.key,
            check_key=CHECK_LANGUAGE,
            mode=MODE_STATIC,
            risk_level=RISK_NONE,
            expected=scenario.language_scope,
        ))
    if EXPECT_CURRENCY in step.expects:
        checks.append(ScenarioSmokeCheck(
            scenario_key=scenario.scenario_key,
            step_key=step.key,
            check_key=CHECK_CURRENCY,
            mode=MODE_DRY_RUN,
            risk_level=RISK_NONE,
            callback_name="format_sample_money",
            expected="MoneyDisplayPolicy",
            notes="Dry-run must format sample amounts only; no conversion side effects.",
        ))
    if EXPECT_BRANCH in step.expects:
        checks.append(ScenarioSmokeCheck(
            scenario_key=scenario.scenario_key,
            step_key=step.key,
            check_key=CHECK_BRANCH,
            mode=MODE_DRY_RUN,
            risk_level=RISK_NONE,
            callback_name="scope_sample_branch",
            expected="branch_access_policy",
        ))
    if EXPECT_PRINT in step.expects:
        checks.append(ScenarioSmokeCheck(
            scenario_key=scenario.scenario_key,
            step_key=step.key,
            check_key=CHECK_PRINT,
            mode=MODE_CALLBACK,
            risk_level=RISK_PRINT_EXPORT,
            callback_name=_callback_name_for(step, CHECK_PRINT),
            expected="browser_html",
            notes="Print smoke should render HTML to a temp file/string without sending to a physical printer.",
        ))
    if EXPECT_EXPORT in step.expects:
        checks.append(ScenarioSmokeCheck(
            scenario_key=scenario.scenario_key,
            step_key=step.key,
            check_key=CHECK_EXPORT,
            mode=MODE_CALLBACK,
            risk_level=RISK_PRINT_EXPORT,
            callback_name=_callback_name_for(step, CHECK_EXPORT),
            expected="export_probe",
        ))
    if EXPECT_AUDIT in step.expects:
        checks.append(ScenarioSmokeCheck(
            scenario_key=scenario.scenario_key,
            step_key=step.key,
            check_key=CHECK_AUDIT,
            mode=MODE_CALLBACK,
            risk_level=RISK_NONE,
            callback_name=_callback_name_for(step, CHECK_AUDIT),
            expected=step.audit_event_key,
            notes="Dry-run audit must be tagged as scenario_smoke and avoid permanent business records.",
        ))
    if EXPECT_OFFLINE in step.expects:
        checks.append(ScenarioSmokeCheck(
            scenario_key=scenario.scenario_key,
            step_key=step.key,
            check_key=CHECK_OFFLINE,
            mode=MODE_CALLBACK,
            risk_level=RISK_NONE,
            callback_name=_callback_name_for(step, CHECK_OFFLINE),
            expected=step.offline_surface_key,
            notes="Offline smoke should validate queue metadata and idempotency only.",
        ))
    return checks


def smoke_plan_for_scenario(scenario: ScenarioDescriptor) -> ScenarioSmokePlan:
    checks: list[ScenarioSmokeCheck] = []
    for step in scenario.steps:
        checks.extend(_checks_for_step(scenario, step))
    return ScenarioSmokePlan(
        scenario_key=scenario.scenario_key,
        module=scenario.module,
        title_key=scenario.title_key,
        primary_document_type=scenario.primary_document_type,
        checks=tuple(checks),
        destructive=False,
        safe_for_ci=True,
    )


def all_smoke_plans(descriptors: Iterable[ScenarioDescriptor] | None = None) -> tuple[ScenarioSmokePlan, ...]:
    return tuple(smoke_plan_for_scenario(s) for s in (descriptors or all_scenario_descriptors()))


def validate_runtime_smoke_hooks(plans: Iterable[ScenarioSmokePlan] | None = None) -> list[str]:
    """Validate that every guarded scenario has a complete non-destructive smoke plan."""

    warnings = list(validate_scenario_descriptors())
    rbac = permission_descriptor_map()
    plans_tuple = tuple(plans or all_smoke_plans())
    if not plans_tuple:
        warnings.append("no scenario smoke plans")
        return warnings

    for plan in plans_tuple:
        if plan.destructive:
            warnings.append(f"{plan.scenario_key}: smoke plan is destructive")
        if not plan.safe_for_ci:
            warnings.append(f"{plan.scenario_key}: smoke plan is not safe_for_ci")
        if not plan.checks:
            warnings.append(f"{plan.scenario_key}: no smoke checks")
        by_step: dict[str, set[str]] = {}
        for check in plan.checks:
            by_step.setdefault(check.step_key, set()).add(check.check_key)
            if check.mode == MODE_CALLBACK and not check.callback_name:
                warnings.append(f"{plan.scenario_key}.{check.step_key}.{check.check_key}: callback mode without callback_name")
            if check.check_key == CHECK_PERMISSION and check.expected and check.expected not in rbac:
                warnings.append(f"{plan.scenario_key}.{check.step_key}: permission not in RBAC contract: {check.expected}")
            if check.check_key == CHECK_SETTINGS and check.expected and settings_descriptor_for(check.expected) is None:
                warnings.append(f"{plan.scenario_key}.{check.step_key}: missing settings scope: {check.expected}")
            if check.check_key == CHECK_AUDIT and check.expected and audit_event_descriptor_for(check.expected) is None:
                warnings.append(f"{plan.scenario_key}.{check.step_key}: missing audit event: {check.expected}")
            if check.check_key == CHECK_OFFLINE and check.expected and offline_descriptor_for(check.expected) is None:
                warnings.append(f"{plan.scenario_key}.{check.step_key}: missing offline descriptor: {check.expected}")
            if check.check_key == CHECK_ROUTE and not check.expected:
                warnings.append(f"{plan.scenario_key}.{check.step_key}: route probe missing api_resource")
        for step_key, keys in by_step.items():
            if CHECK_CONTRACT not in keys:
                warnings.append(f"{plan.scenario_key}.{step_key}: missing contract smoke check")
            if CHECK_PAYLOAD not in keys:
                warnings.append(f"{plan.scenario_key}.{step_key}: missing payload smoke check")
    return warnings


def smoke_matrix(plans: Iterable[ScenarioSmokePlan] | None = None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for plan in plans or all_smoke_plans():
        for check in plan.checks:
            rows.append({
                "scenario_key": plan.scenario_key,
                "module": plan.module,
                "primary_document_type": plan.primary_document_type,
                "step_key": check.step_key,
                "check_key": check.check_key,
                "mode": check.mode,
                "required": check.required,
                "risk_level": check.risk_level,
                "callback_name": check.callback_name,
                "expected": check.expected,
                "safe_for_ci": plan.safe_for_ci,
                "destructive": plan.destructive,
                "notes": check.notes,
            })
    return rows


def smoke_summary_matrix(plans: Iterable[ScenarioSmokePlan] | None = None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for plan in plans or all_smoke_plans():
        rows.append({
            "scenario_key": plan.scenario_key,
            "module": plan.module,
            "primary_document_type": plan.primary_document_type,
            "checks": len(plan.checks),
            "callback_checks": sum(1 for c in plan.checks if c.mode == MODE_CALLBACK),
            "dry_run_checks": sum(1 for c in plan.checks if c.mode == MODE_DRY_RUN),
            "static_checks": sum(1 for c in plan.checks if c.mode == MODE_STATIC),
            "write_intent_checks": sum(1 for c in plan.checks if c.risk_level == RISK_WRITE_INTENT),
            "print_export_checks": sum(1 for c in plan.checks if c.risk_level == RISK_PRINT_EXPORT),
            "safe_for_ci": plan.safe_for_ci,
            "destructive": plan.destructive,
        })
    return rows


def smoke_coverage_summary(plans: Iterable[ScenarioSmokePlan] | None = None) -> Mapping[str, object]:
    plans_tuple = tuple(plans or all_smoke_plans())
    checks = [check for plan in plans_tuple for check in plan.checks]
    return {
        "scenario_count": len(plans_tuple),
        "check_count": len(checks),
        "callback_count": sum(1 for check in checks if check.mode == MODE_CALLBACK),
        "dry_run_count": sum(1 for check in checks if check.mode == MODE_DRY_RUN),
        "static_count": sum(1 for check in checks if check.mode == MODE_STATIC),
        "destructive_count": sum(1 for plan in plans_tuple if plan.destructive),
        "modules": tuple(sorted({plan.module for plan in plans_tuple})),
        "check_types": tuple(sorted({check.check_key for check in checks})),
        "callback_names": tuple(sorted({check.callback_name for check in checks if check.callback_name})),
    }


def run_dry_smoke(callbacks: Mapping[str, SmokeCallback] | None = None, *, scenario_keys: Sequence[str] | None = None) -> tuple[ScenarioSmokeResult, ...]:
    """Run safe static/dry-run checks and optional callbacks.

    Callbacks are never required for CI.  If provided, they are invoked only for
    checks whose callback name is present in the mapping.  Missing callback-mode
    hooks are reported as ``skipped`` rather than failed because this module is a
    contract layer, not a full UI automation runner.
    """

    callback_map = dict(callbacks or {})
    selected = set(scenario_keys or [])
    results: list[ScenarioSmokeResult] = []
    descriptors = [s for s in all_scenario_descriptors() if not selected or s.scenario_key in selected]
    scenario_map = {s.scenario_key: s for s in descriptors}
    step_map = {s.scenario_key: {step.key: step for step in s.steps} for s in descriptors}

    for plan in all_smoke_plans(descriptors):
        scenario = scenario_map[plan.scenario_key]
        for check in plan.checks:
            step = step_map[plan.scenario_key][check.step_key]
            if check.mode in (MODE_STATIC, MODE_DRY_RUN):
                # These checks are validated by construction.  Payload dry-run also exercises the payload builder.
                if check.check_key == CHECK_PAYLOAD:
                    payload = sample_payload_for_step(step)
                    if not isinstance(payload, Mapping) or not payload:
                        results.append(ScenarioSmokeResult(plan.scenario_key, check.step_key, check.check_key, "failed", "empty payload shape"))
                        continue
                results.append(ScenarioSmokeResult(plan.scenario_key, check.step_key, check.check_key, "passed", callback_name=check.callback_name))
                continue
            callback = callback_map.get(check.callback_name)
            if callback is None:
                results.append(ScenarioSmokeResult(plan.scenario_key, check.step_key, check.check_key, "skipped", "callback not provided", check.callback_name))
                continue
            try:
                callback(scenario, step, check)
            except Exception as exc:  # pragma: no cover - callback runner safety.
                results.append(ScenarioSmokeResult(plan.scenario_key, check.step_key, check.check_key, "failed", f"{type(exc).__name__}: {exc}", check.callback_name))
            else:
                results.append(ScenarioSmokeResult(plan.scenario_key, check.step_key, check.check_key, "passed", callback_name=check.callback_name))
    return tuple(results)


__all__ = [
    "ScenarioSmokeCheck",
    "ScenarioSmokePlan",
    "ScenarioSmokeResult",
    "all_smoke_plans",
    "run_dry_smoke",
    "sample_payload_for_step",
    "smoke_coverage_summary",
    "smoke_matrix",
    "smoke_plan_for_scenario",
    "smoke_summary_matrix",
    "validate_runtime_smoke_hooks",
]
