# -*- coding: utf-8 -*-
"""Project-wide release readiness gate (Phase 277).

This module intentionally avoids PyQt imports.  It is safe to run from CI,
from PyInstaller guard scripts, or from the Settings diagnostics page.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ReleaseGateCheck:
    key: str
    category: str
    title: str
    tool_path: str
    output_path: str = ""
    required: bool = True
    phase: int | None = None

    def tool_exists(self, root: Path | None = None) -> bool:
        base = root or ROOT
        return bool(self.tool_path) and (base / self.tool_path).exists()

    def output_exists(self, root: Path | None = None) -> bool:
        if not self.output_path:
            return True
        base = root or ROOT
        return (base / self.output_path).exists()


RELEASE_GATE_PHASE = 277
RELEASE_BASELINE_PHASE = 276
# PHASE286_DASHBOARD_VISIBLE_PROFESSIONAL_LAYOUT is tracked below in REQUIRED_PHASE_DOCS.

REQUIRED_PHASE_DOCS: Sequence[str] = tuple(
    f"PHASE{phase}_{suffix}.md"
    for phase, suffix in [
        (249, "DOCUMENT_SHELL_CONTRACT_AUDIT"),
        (250, "API_REMOTE_GATEWAY_PARITY"),
        (251, "UNIFIED_PERMISSION_BINDER"),
        (252, "UNIFIED_MONEY_DISPLAY_POLICY"),
        (253, "TRANSACTION_SHELL_FINALIZATION"),
        (254, "MATERIAL_SHELL_UNIFICATION"),
        (255, "PARTY_VOUCHER_DASHBOARD_SHELL_CLEANUP"),
        (256, "REPORT_SHELL_UNIFICATION"),
        (257, "LIST_WORKSPACE_UNIFICATION"),
        (258, "OPERATIONAL_SHELL_UNIFICATION"),
        (259, "SETTINGS_CONTRACT_COVERAGE_AUDIT"),
        (260, "RBAC_PERMISSION_API_COVERAGE_AUDIT"),
        (261, "BRANCH_ACCESS_ENFORCEMENT_AUDIT"),
        (262, "SERVER_BRANCH_SCOPE_ENFORCEMENT"),
        (263, "POS_RESTAURANT_BRANCH_SCOPE_ENFORCEMENT"),
        (264, "AUDIT_TRAIL_ENFORCEMENT"),
        (265, "OFFLINE_QUEUE_SYNC_CONTRACT_AUDIT"),
        (266, "RETURN_LIST_PRINT_EDIT_HOTFIX"),
        (267, "VOUCHER_DOCUMENT_SHELL_LAYOUT_HOTFIX"),
        (268, "POS_THERMAL_RECEIPT_PRINT_UNIFICATION"),
        (269, "MANUFACTURING_PRINT_CURRENCY_UNIFICATION"),
        (270, "OFFLINE_REPLAY_SAFETY"),
        (271, "END_TO_END_SCENARIO_GUARD_MATRIX"),
        (272, "SCENARIO_RUNTIME_SMOKE_HOOKS"),
        (273, "SETTINGS_NAVIGATION_DIAGNOSTICS_ALIGNMENT"),
        (274, "SETTINGS_GROUPED_NAVIGATION"),
        (275, "REPORTS_CALCULATION_CURRENCY_GROUPING"),
        (276, "REPORT_PRINTING_UNIFICATION_CONFIRMATION"),
        (277, "RELEASE_READINESS_GATE"),
        (278, "WINDOWS_RUNTIME_PACKAGING_GATE"),
        (279, "PHASE32_OFFLINE_QUEUE_GUARD_HOTFIX"),
        (280, "RELEASE_PACKAGING_GUARD_CLEANUP_HOTFIX"),
        (281, "RELEASE_BUILD_GITIGNORE_TRACKING_HOTFIX"),
        (282, "REPORT_TABLE_CALCULATION_AND_MODULE_VISIBILITY"),
        (283, "RESTAURANT_OPERATION_SHELL_UX"),
        (284, "RESTAURANT_TABLE_MAP_FILTERS"),
        (285, "DASHBOARD_IDENTITY_LAYOUT_CLEANUP"),
        (286, "DASHBOARD_VISIBLE_PROFESSIONAL_LAYOUT"),
        (287, "RESTAURANT_ORDER_STATE_MACHINE"),
        (288, "KITCHEN_DISPLAY_SYSTEM_HARDENING"),
        (289, "RESTAURANT_PAYMENT_SPLIT_HARDENING"),
        (290, "RESTAURANT_PRINTING_TEMPLATES_HARDENING"),
        (291, "RESTAURANT_INVENTORY_RECIPE_INTEGRATION"),
    ]
)

REQUIRED_PHASE_TESTS: Sequence[str] = tuple(
    f"tests/test_phase{phase}_{suffix}.py"
    for phase, suffix in [
        (249, "document_shell_contract_audit"),
        (250, "api_remote_gateway_parity"),
        (251, "unified_permission_binder"),
        (252, "unified_money_display_policy"),
        (253, "transaction_shell_finalization"),
        (254, "material_shell_unification"),
        (255, "party_voucher_dashboard_shell_cleanup"),
        (256, "report_shell_unification"),
        (257, "list_workspace_unification"),
        (258, "operational_shell_unification"),
        (259, "settings_contract_coverage_audit"),
        (260, "rbac_permission_contract_audit"),
        (261, "branch_access_enforcement_audit"),
        (262, "server_branch_scope_enforcement"),
        (263, "pos_restaurant_branch_scope_enforcement"),
        (264, "audit_trail_enforcement"),
        (265, "offline_queue_sync_contract_audit"),
        (266, "return_list_print_edit_hotfix"),
        (267, "voucher_document_shell_layout_hotfix"),
        (268, "pos_thermal_receipt_unification"),
        (269, "manufacturing_print_currency_unification"),
        (270, "offline_replay_safety"),
        (271, "end_to_end_scenario_guard_matrix"),
        (272, "scenario_runtime_smoke_hooks"),
        (273, "settings_navigation_diagnostics_alignment"),
        (274, "settings_grouped_navigation"),
        (275, "reports_calculation_currency_grouping"),
        (276, "report_printing_unification_confirmation"),
        (277, "release_readiness_gate"),
        (278, "windows_runtime_packaging_gate"),
        (279, "phase32_offline_queue_guard_hotfix"),
        (280, "release_packaging_guard_cleanup_hotfix"),
        (281, "release_build_gitignore_tracking_hotfix"),
        (282, "report_calculation_module_visibility_dashboard_cleanup"),
        (283, "restaurant_operation_shell_ux"),
        (284, "restaurant_table_map_filters"),
        (285, "dashboard_identity_layout_cleanup"),
        (286, "dashboard_visible_professional_layout"),
        (287, "restaurant_order_state_machine"),
        (288, "kitchen_display_system_hardening"),
        (289, "restaurant_payment_split_hardening"),
        (290, "restaurant_printing_templates_hardening"),
        (291, "restaurant_inventory_recipe_integration"),
    ]
)

RELEASE_GATE_CHECKS: Sequence[ReleaseGateCheck] = (
    ReleaseGateCheck("document_shell", "shell", "Document Shell contract", "tools/document_shell_contract_audit.py", "tools/audit_outputs/document_shell_contract_matrix.csv", phase=249),
    ReleaseGateCheck("report_shell", "shell", "Report Shell contract", "tools/report_shell_contract_audit.py", phase=256),
    ReleaseGateCheck("list_workspace", "shell", "List Workspace contract", "tools/list_workspace_contract_audit.py", "tools/audit_outputs/list_workspace_contract_matrix.csv", phase=257),
    ReleaseGateCheck("operational_shell", "shell", "Operational Shell contract", "tools/operational_shell_contract_audit.py", "tools/audit_outputs/operational_shell_contract_matrix.csv", phase=258),
    ReleaseGateCheck("settings_contract", "settings", "Settings contract coverage", "tools/settings_contract_coverage_audit.py", "tools/audit_outputs/settings_contract_coverage_matrix.csv", phase=259),
    ReleaseGateCheck("rbac_contract", "security", "RBAC permission coverage", "tools/rbac_permission_contract_audit.py", "tools/audit_outputs/rbac_permission_contract_matrix.csv", phase=260),
    ReleaseGateCheck("branch_contract", "security", "Branch access coverage", "tools/branch_access_contract_audit.py", "tools/audit_outputs/branch_access_contract_matrix.csv", phase=261),
    ReleaseGateCheck("audit_contract", "security", "Audit trail coverage", "tools/audit_trail_contract_audit.py", "tools/audit_outputs/audit_trail_contract_matrix.csv", phase=264),
    ReleaseGateCheck("offline_sync", "sync", "Offline sync contract", "tools/offline_sync_contract_audit.py", "tools/audit_outputs/offline_sync_contract_matrix.csv", phase=265),
    ReleaseGateCheck("offline_replay", "sync", "Offline replay safety", "tools/offline_replay_safety_audit.py", "tools/audit_outputs/offline_replay_safety_matrix.csv", phase=270),
    ReleaseGateCheck("e2e_scenarios", "scenario", "End-to-end scenario guard", "tools/end_to_end_scenario_guard_audit.py", "tools/audit_outputs/end_to_end_scenario_guard_matrix.csv", phase=271),
    ReleaseGateCheck("runtime_smoke", "scenario", "Runtime smoke hooks", "tools/scenario_runtime_smoke_audit.py", "tools/audit_outputs/scenario_runtime_smoke_matrix.csv", phase=272),
    ReleaseGateCheck("reports_currency", "reports", "Reports calculation/currency guard", "tests/test_phase275_reports_calculation_currency_grouping.py", phase=275),
    ReleaseGateCheck("reports_printing", "reports", "Reports browser printing guard", "tests/test_phase276_report_printing_unification_confirmation.py", phase=276),
    ReleaseGateCheck("printing_pyinstaller", "printing", "Printing PyInstaller loader guard", "tools/phase225_printing_pyinstaller_guard.py", phase=225),
    ReleaseGateCheck("windows_packaging", "packaging", "Windows runtime packaging gate", "tools/windows_runtime_packaging_gate_audit.py", "tools/audit_outputs/windows_runtime_packaging_gate_matrix.csv", phase=278),
    ReleaseGateCheck("release_packaging", "packaging", "Release packaging guard", "tools/release_packaging_guard.py", phase=281),
    ReleaseGateCheck("release_hidden_imports", "packaging", "Release hidden imports guard", "tools/release_hidden_imports_guard.py", phase=280),
    ReleaseGateCheck("printing_browser", "printing", "Browser HTML print guard", "tools/phase237_browser_html_print_guard.py", phase=237),
    ReleaseGateCheck("dashboard_identity", "dashboard", "Dashboard identity layout cleanup", "tests/test_phase285_dashboard_identity_layout_cleanup.py", phase=285),
    ReleaseGateCheck("dashboard_visible_layout", "dashboard", "Dashboard visible professional layout", "tests/test_phase286_dashboard_visible_professional_layout.py", phase=286),
    ReleaseGateCheck("restaurant_order_state", "restaurant", "Restaurant order state machine", "tests/test_phase287_restaurant_order_state_machine.py", phase=287),
    ReleaseGateCheck("restaurant_kds_hardening", "restaurant", "Restaurant KDS hardening", "tests/test_phase288_kitchen_display_system_hardening.py", phase=288),
    ReleaseGateCheck("restaurant_payment_split", "restaurant", "Restaurant payment and split bill hardening", "tests/test_phase289_restaurant_payment_split_hardening.py", phase=289),
    ReleaseGateCheck("restaurant_printing_templates", "restaurant", "Restaurant printing templates hardening", "tests/test_phase290_restaurant_printing_templates_hardening.py", phase=290),
    ReleaseGateCheck("restaurant_inventory_recipe", "restaurant", "Restaurant inventory recipe integration", "tests/test_phase291_restaurant_inventory_recipe_integration.py", phase=291),
    ReleaseGateCheck("print_settings", "printing", "Print settings contract", "tools/phase236_print_settings_contract_audit.py", phase=236),
)


def release_gate_checks() -> Sequence[ReleaseGateCheck]:
    return RELEASE_GATE_CHECKS


def _missing_paths(paths: Iterable[str], root: Path | None = None) -> List[str]:
    base = root or ROOT
    return [p for p in paths if not (base / p).exists()]


def release_gate_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    rows: List[Dict[str, object]] = []
    for check in RELEASE_GATE_CHECKS:
        rows.append({
            "key": check.key,
            "category": check.category,
            "title": check.title,
            "phase": check.phase or "",
            "tool_path": check.tool_path,
            "tool_exists": check.tool_exists(base),
            "output_path": check.output_path,
            "output_exists": check.output_exists(base),
            "required": check.required,
        })
    return rows


def validate_release_gate(root: Path | None = None) -> Dict[str, List[str]]:
    base = root or ROOT
    issues: Dict[str, List[str]] = {}
    missing_docs = _missing_paths(REQUIRED_PHASE_DOCS, base)
    if missing_docs:
        issues["phase_docs"] = [f"missing {path}" for path in missing_docs]
    missing_tests = _missing_paths(REQUIRED_PHASE_TESTS, base)
    if missing_tests:
        issues["phase_tests"] = [f"missing {path}" for path in missing_tests]
    for row in release_gate_matrix(base):
        if row["required"] and not row["tool_exists"]:
            issues.setdefault(str(row["key"]), []).append(f"missing tool/test {row['tool_path']}")
    return issues


def release_gate_summary(root: Path | None = None) -> Dict[str, object]:
    rows = release_gate_matrix(root)
    issues = validate_release_gate(root)
    categories: Dict[str, int] = {}
    for row in rows:
        categories[str(row["category"])] = categories.get(str(row["category"]), 0) + 1
    return {
        "phase": RELEASE_GATE_PHASE,
        "baseline_phase": RELEASE_BASELINE_PHASE,
        "checks": len(rows),
        "categories": categories,
        "issues": sum(len(v) for v in issues.values()),
        "issue_groups": len(issues),
        "ready": not issues,
    }


__all__ = [
    "ReleaseGateCheck",
    "RELEASE_GATE_PHASE",
    "RELEASE_BASELINE_PHASE",
    "REQUIRED_PHASE_DOCS",
    "REQUIRED_PHASE_TESTS",
    "release_gate_checks",
    "release_gate_matrix",
    "release_gate_summary",
    "validate_release_gate",
]
