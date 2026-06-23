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
        (292, "RESTAURANT_UI_VISUAL_CLEANUP"),
        (293, "RESTAURANT_TABLE_OPERATIONS_HARDENING"),
        (294, "RESTAURANT_SETTINGS_PRINTER_ROUTING"),
        (295, "RESTAURANT_OPERATION_GOVERNANCE_ENFORCEMENT"),
        (296, "RESTAURANT_RESPONSIVE_WORKSPACE_STABILIZATION"),
        (297, "RESTAURANT_QSS_RUNTIME_HOTFIX"),
        (298, "RESTAURANT_FULLSCREEN_OPERATIONAL_SHELL"),
        (299, "RESTAURANT_ORDER_WORKSPACE_DECLUTTER"),
        (300, "RESTAURANT_ORDER_SEARCH_HEADER_COLLAPSIBLE_MENU"),
        (301, "DASHBOARD_PROFESSIONAL_EXCHANGE_SYNC"),
        (302, "DASHBOARD_PIXEL_STYLE_VISUAL_MATCHING"),
        (303, "DASHBOARD_RTL_CENTERING_ALIGNMENT"),
        (304, "RESTAURANT_RUNTIME_ACCEPTANCE"),
        (305, "RESTAURANT_UNIFIED_PRINTING_AUDIT"),
        (306, "RESTAURANT_SHIFT_REPORT_OPERATIONAL_CONTROLS"),
        (307, "CAFE_MODE_FOUNDATION"),
        (308, "CAFE_SIZES_MODIFIERS"),
        (309, "CAFE_WORKSPACE_SHELL"),
        (310, "CAFE_INVENTORY_SHIFT_REPORT"),
        (311, "CAFE_RUNTIME_ACCEPTANCE"),
        (312, "CAFE_ANALYTICS_FSTRING_HOTFIX"),
        (313, "STANDALONE_CAFE_WORKSPACE_ACTIVATION"),
        (314, "RESTAURANT_CAFE_UI_DECOUPLING_HOTFIX"),
        (315, "PRODUCT_VARIANTS_FOUNDATION"),
        (316, "APPAREL_WORKSPACE_SHELL"),
        (317, "APPAREL_VARIANT_TRANSACTION_INTEGRATION"),
        (318, "WORKSPACE_SHELL_TRANSACTION_LAYOUT_UNIFICATION"),
        (319, "APPAREL_MATRIX_BULK_VARIANT_BUILDER"),
        (320, "APPAREL_INVENTORY_OPERATIONS"),
        (321, "APPAREL_REPORTS"),
        (322, "APPAREL_RUNTIME_ACCEPTANCE"),
        (323, "STARTUP_VARIANT_SCHEMA_HOTFIX"),
        (324, "APPAREL_TRANSACTION_VARIANT_SELECTION_UX"),
        (325, "APPAREL_CATALOG_BOUNDARY_PRICING_HARDENING"),
        (326, "TRANSACTION_HEADER_FOOTER_LAYOUT_HOTFIX"),
        (327, "APPAREL_TRANSACTION_PRICE_CURRENCY_HOTFIX"),
        (328, "DASHBOARD_POS_TRANSACTION_UX_POLISH"),
        (329, "PURCHASE_VARIANT_COST_CURRENCY_HOTFIX"),
        (330, "PURCHASE_APPAREL_INHERITED_COST_RATE_FALLBACK"),
        (331, "UI_REGISTRY_AND_SHELL_MANIFEST"),
        (332, "DESIGN_TOKENS_TYPOGRAPHY_NORMALIZATION"),
        (333, "MAIN_MENU_ACTION_BAR_CONTRACT"),
        (334, "UNIVERSAL_COLUMN_CONTRACT_FOUNDATION"),
        (335, "OPERATIONAL_COLUMN_CONTRACT_INTEGRATION"),
        (336, "PRINTING_EXPORT_COLUMN_MAPPING"),
        (337, "EDITABLE_TABLE_KEYBOARD_STANDARD"),
        (338, "UNIFIED_BARCODE_PRINTING_PROFILES"),
        (339, "BARCODE_MULTI_PRINT_UI"),
        (340, "FINAL_UX_REGRESSION_GUARDS"),
        (341, "SETTINGS_SURFACE_CONTRACT"),
        (342, "SETTINGS_RUNTIME_WIRING_COLUMN_CUSTOMIZER"),
        (343, "RUNTIME_APPLICATION_SWEEP"),
        (344, "VISUAL_RUNTIME_POLISH_SWEEP"),
        (345, "FULL_RUNTIME_ACCEPTANCE_PACKAGING_SMOKE"),
        (346, "TAB_LIFECYCLE_DASHBOARD_FALLBACK"),
        (347, "SAVE_CLOSES_TAB"),
        (348, "EDITABLE_ENTRY_RETURN_UNIFICATION"),
        (349, "TRANSACTION_ENTRY_CASH_FOOTER_POLISH"),
        (350, "INTERNAL_CLOSE_BUTTON_TAB_LIFECYCLE"),
        (351, "FUNCTION_CLOSE_LIFECYCLE_UNIFICATION"),
        (352, "BRAND_IDENTITY_VISUAL_SYSTEM"),
        (353, "BRANDED_LOGIN_SPLASH_ACTIVATION_RUNTIME"),
        (354, "BRANDED_TABS_MENU_ACTION_BAR"),
        (355, "BRANDED_TABLES_TRANSACTION_FOOTER"),
        (356, "BRANDED_DIALOGS_SYSTEM_WINDOWS"),
        (358, "LOGIN_LAYOUT_STABILITY_HOTFIX"),
        (359, "LOGIN_PHASE355_DESIGN_RESTORE"),
        (360, "LOGIN_RTL_LAYOUT_REORGANIZATION"),
        (361, "LOGIN_VERTICAL_EXPANSION"),
        (362, "LOGIN_PASSWORD_OPTIONS_NO_OVERLAP"),
        (363, "LOGIN_PASSWORD_OPTIONS_GAP"),
        (364, "LOGIN_PASSWORD_VISIBILITY_RESERVED_ROW"),
        (365, "LOGIN_PHASE352_RESTORE"),
        (366, "LOGIN_PRE352_RTL_SAFE"),
        (367, "LOGIN_PRE350_RESTORE"),
        (368, "LOGIN_PASSWORD_TOGGLE_ALIGNMENT"),
        (369, "WAREHOUSE_INSTALLER_PRINTING_PATHS"),
        (370, "WAREHOUSE_EXECUTABLE_IDENTITY"),
        (371, "REUSED_WINDOWS_WORKFLOW_WAREHOUSE_ONLY"),
        (372, "WORKFLOW_DELEGATED_BRANDING_HOTFIX"),
        (373, "TAB_PLAIN_TITLE"),
        (374, "SPECIAL_INTERFACE_MENU_ENTRY_FOCUS"),
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
        (292, "restaurant_ui_visual_cleanup"),
        (293, "restaurant_table_operations_hardening"),
        (294, "restaurant_settings_printer_routing"),
        (295, "restaurant_operation_governance_enforcement"),
        (296, "restaurant_responsive_workspace_stabilization"),
        (297, "restaurant_qss_runtime_hotfix"),
        (298, "restaurant_fullscreen_operational_shell"),
        (299, "restaurant_order_workspace_declutter"),
        (300, "restaurant_order_search_header_collapsible_menu"),
        (301, "dashboard_professional_exchange_sync"),
        (302, "dashboard_pixel_style_visual_matching"),
        (303, "dashboard_rtl_centering_alignment"),
        (304, "restaurant_runtime_acceptance"),
        (305, "restaurant_unified_printing_audit"),
        (306, "restaurant_shift_report_operational_controls"),
        (307, "cafe_mode_foundation"),
        (308, "cafe_sizes_modifiers"),
        (309, "cafe_workspace_shell"),
        (310, "cafe_inventory_shift_report"),
        (311, "cafe_runtime_acceptance"),
        (312, "cafe_analytics_fstring_hotfix"),
        (313, "standalone_cafe_workspace_activation"),
        (314, "restaurant_cafe_ui_decoupling_hotfix"),
        (315, "product_variants_foundation"),
        (316, "apparel_workspace_shell"),
        (317, "apparel_variant_transaction_integration"),
        (318, "workspace_shell_transaction_layout_unification"),
        (319, "apparel_matrix_bulk_variant_builder"),
        (320, "apparel_inventory_operations"),
        (321, "apparel_reports"),
        (322, "apparel_runtime_acceptance"),
        (323, "startup_variant_schema_hotfix"),
        (324, "apparel_transaction_variant_selection_ux"),
        (325, "apparel_catalog_boundary_pricing_hardening"),
        (326, "transaction_header_footer_layout_hotfix"),
        (327, "apparel_transaction_price_currency_hotfix"),
        (328, "dashboard_pos_transaction_ux_polish"),
        (329, "purchase_variant_cost_currency_hotfix"),
        (330, "purchase_apparel_inherited_cost_rate_fallback"),
        (331, "ui_registry_shell_manifest"),
        (332, "design_tokens_typography_normalization"),
        (333, "main_menu_action_bar_contract"),
        (334, "universal_column_contract_foundation"),
        (335, "operational_column_contract_integration"),
        (336, "printing_export_column_mapping"),
        (337, "editable_table_keyboard_standard"),
        (338, "unified_barcode_printing_profiles"),
        (339, "barcode_multi_print_ui"),
        (340, "final_ux_regression_guards"),
        (341, "unified_settings_surface_contract"),
        (342, "settings_runtime_wiring_column_customizer"),
        (343, "runtime_application_sweep"),
        (344, "visual_runtime_polish_sweep"),
        (345, "full_runtime_acceptance_packaging_smoke"),
        (346, "tab_lifecycle_dashboard_fallback"),
        (347, "save_closes_tab"),
        (348, "editable_entry_return_unification"),
        (349, "transaction_entry_cash_footer"),
        (350, "internal_close_button_tab_lifecycle"),
        (351, "function_close_lifecycle_unification"),
        (352, "brand_identity_visual_system"),
        (353, "branded_login_splash_activation_runtime"),
        (354, "branded_shell_runtime"),
        (355, "branded_tables_transaction_footer"),
        (356, "branded_dialogs_system_windows"),
        (358, "login_layout_stability"),
        (359, "login_phase355_restore"),
        (360, "login_rtl_layout"),
        (361, "login_vertical_expansion"),
        (362, "login_no_overlap"),
        (363, "login_password_gap"),
        (364, "login_password_visibility"),
        (365, "login_phase352_restore"),
        (366, "login_pre352_rtl_safe"),
        (367, "login_pre350_restore"),
        (368, "login_password_toggle_alignment"),
        (369, "warehouse_installer_printing"),
        (370, "warehouse_executable_identity"),
        (371, "reused_windows_workflow"),
        (372, "workflow_delegated_branding"),
        (373, "tab_plain_title"),
        (374, "special_interface_menu_entry_focus"),
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
    ReleaseGateCheck("restaurant_ui_visual_cleanup", "restaurant", "Restaurant UI visual cleanup", "tests/test_phase292_restaurant_ui_visual_cleanup.py", phase=292),
    ReleaseGateCheck("restaurant_table_operations", "restaurant", "Restaurant table operations hardening", "tests/test_phase293_restaurant_table_operations_hardening.py", phase=293),
    ReleaseGateCheck("restaurant_settings_printer_routing", "restaurant", "Restaurant settings and printer routing", "tests/test_phase294_restaurant_settings_printer_routing.py", phase=294),
    ReleaseGateCheck("restaurant_operation_governance", "restaurant", "Restaurant operation governance enforcement", "tests/test_phase295_restaurant_operation_governance_enforcement.py", phase=295),
    ReleaseGateCheck("restaurant_responsive_workspace", "restaurant", "Restaurant responsive workspace stabilization", "tests/test_phase296_restaurant_responsive_workspace_stabilization.py", phase=296),
    ReleaseGateCheck("restaurant_qss_runtime_hotfix", "restaurant", "Restaurant QSS runtime hotfix", "tests/test_phase297_restaurant_qss_runtime_hotfix.py", phase=297),
    ReleaseGateCheck("restaurant_fullscreen_operational_shell", "restaurant", "Restaurant fullscreen operational shell", "tests/test_phase298_restaurant_fullscreen_operational_shell.py", phase=298),
    ReleaseGateCheck("restaurant_order_workspace_declutter", "restaurant", "Restaurant order workspace declutter", "tests/test_phase299_restaurant_order_workspace_declutter.py", phase=299),
    ReleaseGateCheck("restaurant_order_search_header_collapsible_menu", "restaurant", "Restaurant order search header and collapsible menu", "tests/test_phase300_restaurant_order_search_header_collapsible_menu.py", phase=300),
    ReleaseGateCheck("dashboard_professional_exchange_sync", "dashboard", "Dashboard professional layout and exchange-rate sync", "tests/test_phase301_dashboard_professional_exchange_sync.py", phase=301),
    ReleaseGateCheck("dashboard_pixel_style_visual_matching", "dashboard", "Dashboard pixel-style visual matching", "tests/test_phase302_dashboard_pixel_style_visual_matching.py", phase=302),
    ReleaseGateCheck("dashboard_rtl_centering_alignment", "dashboard", "Dashboard RTL structure and centered identity alignment", "tests/test_phase303_dashboard_rtl_centering_alignment.py", phase=303),
    ReleaseGateCheck("restaurant_runtime_acceptance", "restaurant", "Restaurant runtime acceptance scenario", "tests/test_phase304_restaurant_runtime_acceptance.py", phase=304),
    ReleaseGateCheck("restaurant_unified_printing_audit", "restaurant", "Restaurant unified printing audit", "tests/test_phase305_restaurant_unified_printing_audit.py", phase=305),
    ReleaseGateCheck("restaurant_shift_report_operational_controls", "restaurant", "Restaurant shift report and operational controls", "tests/test_phase306_restaurant_shift_report_operational_controls.py", phase=306),
    ReleaseGateCheck("cafe_mode_foundation", "restaurant", "Cafe mode foundation on restaurant shell", "tests/test_phase307_cafe_mode_foundation.py", phase=307),
    ReleaseGateCheck("cafe_sizes_modifiers", "restaurant", "Cafe sizes and modifiers on restaurant order lines", "tests/test_phase308_cafe_sizes_modifiers.py", phase=308),
    ReleaseGateCheck("cafe_workspace_shell", "restaurant", "Cafe workspace shell and barista context", "tests/test_phase309_cafe_workspace_shell.py", phase=309),
    ReleaseGateCheck("cafe_inventory_shift_report", "restaurant", "Cafe inventory and shift report", "tests/test_phase310_cafe_inventory_shift_report.py", phase=310),
    ReleaseGateCheck("cafe_runtime_acceptance", "restaurant", "Cafe runtime acceptance", "tests/test_phase311_cafe_runtime_acceptance.py", phase=311),
    ReleaseGateCheck("cafe_analytics_fstring_hotfix", "restaurant", "Cafe analytics f-string hotfix", "tests/test_phase312_cafe_analytics_fstring_hotfix.py", phase=312),
    ReleaseGateCheck("standalone_cafe_workspace_activation", "restaurant", "Standalone cafe workspace activation", "tests/test_phase313_standalone_cafe_workspace_activation.py", phase=313),
    ReleaseGateCheck("restaurant_cafe_ui_decoupling_hotfix", "restaurant", "Restaurant shell no longer embeds cafe entry", "tests/test_phase314_restaurant_cafe_ui_decoupling_hotfix.py", phase=314),
    ReleaseGateCheck("product_variants_foundation", "materials", "Product variants foundation for apparel color/size stock identity", "tests/test_phase315_product_variants_foundation.py", phase=315),
    ReleaseGateCheck("apparel_workspace_shell", "materials", "Standalone apparel workspace shell backed by product variants", "tests/test_phase316_apparel_workspace_shell.py", phase=316),
    ReleaseGateCheck("apparel_variant_transaction_integration", "materials", "Apparel variant transaction/POS stock integration", "tests/test_phase317_apparel_variant_transaction_integration.py", phase=317),
    ReleaseGateCheck("workspace_shell_transaction_layout_unification", "shell", "Workspace shell and transaction layout unification", "tests/test_phase318_workspace_shell_transaction_layout_unification.py", phase=318),
    ReleaseGateCheck("apparel_matrix_bulk_variant_builder", "materials", "Apparel color/size matrix and bulk variant builder", "tests/test_phase319_apparel_matrix_bulk_variant_builder.py", phase=319),
    ReleaseGateCheck("apparel_inventory_operations", "materials", "Apparel variant-aware inventory operations", "tests/test_phase320_apparel_inventory_operations.py", phase=320),
    ReleaseGateCheck("apparel_reports", "materials", "Apparel reports for color/size stock and sales", "tests/test_phase321_apparel_reports.py", phase=321),
    ReleaseGateCheck("apparel_runtime_acceptance", "materials", "Apparel runtime acceptance for complete color/size workflow", "tests/test_phase322_apparel_runtime_acceptance.py", phase=322),
    ReleaseGateCheck("startup_variant_schema_hotfix", "database", "Startup schema upgrade for apparel variant warehouse columns", "tests/test_phase323_startup_variant_schema_hotfix.py", phase=323),
    ReleaseGateCheck("apparel_transaction_variant_selection_ux", "materials", "Apparel variant selection UX for purchase/sales transaction rows", "tests/test_phase324_apparel_transaction_variant_selection_ux.py", phase=324),
    ReleaseGateCheck("apparel_catalog_boundary_pricing_hardening", "materials", "Apparel catalog boundary and transaction pricing hardening", "tests/test_phase325_apparel_catalog_boundary_pricing_hardening.py", phase=325),
    ReleaseGateCheck("transaction_header_footer_layout_hotfix", "ui", "One-row transaction header, horizontal invoice footer, and material editor identity-card removal", "tests/test_phase326_transaction_header_footer_layout_hotfix.py", phase=326),
    ReleaseGateCheck("apparel_transaction_price_currency_hotfix", "materials", "Apparel transaction variant lookup prices convert to display currency only once", "tests/test_phase327_apparel_transaction_price_currency_hotfix.py", phase=327),
    ReleaseGateCheck("dashboard_pos_transaction_ux_polish", "ui", "Dashboard, POS and transaction header UX polish", "tests/test_phase328_dashboard_pos_transaction_ux_polish.py", phase=328),
    ReleaseGateCheck("purchase_variant_cost_currency_hotfix", "materials", "Purchase invoice apparel variant inherited cost is not re-converted", "tests/test_phase329_purchase_variant_cost_currency_hotfix.py", phase=329),
    ReleaseGateCheck("purchase_apparel_inherited_cost_rate_fallback", "materials", "Purchase invoice apparel inherited cost uses rate fallback for SYP display", "tests/test_phase330_purchase_apparel_inherited_cost_rate_fallback.py", phase=330),
    ReleaseGateCheck("ui_registry_shell_manifest", "ui", "UI registry and shell manifest foundation", "tests/test_phase331_ui_registry_shell_manifest.py", phase=331),
    ReleaseGateCheck("design_tokens_typography_normalization", "ui", "Design tokens and typography normalization", "tests/test_phase332_design_tokens_typography_normalization.py", phase=332),
    ReleaseGateCheck("main_menu_action_bar_contract", "shell", "Main menu/action bar contract", "tests/test_phase333_main_menu_action_bar_contract.py", phase=333),
    ReleaseGateCheck("universal_column_contract_foundation", "ui", "Universal column contract foundation", "tests/test_phase334_universal_column_contract_foundation.py", phase=334),
    ReleaseGateCheck("operational_column_contract_integration", "ui", "Restaurant/Cafe/POS/Apparel column contract integration", "tests/test_phase335_operational_column_contract_integration.py", phase=335),
    ReleaseGateCheck("printing_export_column_mapping", "printing", "Print/export column mapping", "tests/test_phase336_printing_export_column_mapping.py", phase=336),
    ReleaseGateCheck("editable_table_keyboard_standard", "ui", "Editable table keyboard standard", "tests/test_phase337_editable_table_keyboard_standard.py", phase=337),
    ReleaseGateCheck("unified_barcode_printing_profiles", "printing", "Unified barcode printing profiles", "tests/test_phase338_unified_barcode_printing_profiles.py", phase=338),
    ReleaseGateCheck("barcode_multi_print_ui", "printing", "Barcode multi-print UI for items/apparel/restaurant/cafe", "tests/test_phase339_barcode_multi_print_ui.py", phase=339),
    ReleaseGateCheck("final_ux_regression_guards", "quality", "Final UX regression guard for shell/actions/columns/keyboard/barcode", "tools/phase340_final_ux_regression_guard.py", "tools/audit_outputs/final_ux_regression_matrix.csv", phase=340),
    ReleaseGateCheck("settings_surface_contract", "settings", "Unified settings surface for columns and barcode profiles", "tools/phase341_settings_surface_guard.py", "tools/audit_outputs/settings_surface_matrix.csv", phase=341),
    ReleaseGateCheck("settings_runtime_wiring", "settings", "Settings surface runtime wiring and column customizer integration", "tools/phase342_settings_runtime_wiring_guard.py", "tools/audit_outputs/settings_runtime_wiring_matrix.csv", phase=342),
    ReleaseGateCheck("runtime_application_sweep", "ui", "Runtime application sweep for remaining table contracts", "tools/phase343_runtime_application_sweep_guard.py", "tools/audit_outputs/runtime_table_contract_sweep_matrix.csv", phase=343),
    ReleaseGateCheck("visual_runtime_polish_sweep", "ui", "Visual runtime polish sweep for legacy and modern workspaces", "tools/phase344_visual_runtime_polish_guard.py", "tools/audit_outputs/visual_runtime_polish_matrix.csv", phase=344),
    ReleaseGateCheck("full_runtime_acceptance_packaging_smoke", "quality", "Full runtime acceptance and packaging smoke matrix", "tools/phase345_full_runtime_acceptance_packaging_smoke.py", "tools/audit_outputs/full_runtime_acceptance_packaging_smoke_matrix.csv", phase=345),
    ReleaseGateCheck("tab_lifecycle_dashboard_fallback", "shell", "Fixed dashboard surface and safe tab-close lifecycle", "tools/phase346_tab_lifecycle_dashboard_fallback_guard.py", "tools/audit_outputs/tab_lifecycle_dashboard_fallback_matrix.csv", phase=346),
    ReleaseGateCheck("save_closes_tab", "shell", "Successful Save closes the owning workspace tab", "tools/phase347_save_closes_tab_guard.py", "tools/audit_outputs/save_closes_tab_matrix.csv", phase=347),
    ReleaseGateCheck("editable_entry_return_unification", "ui", "Text focus, editable grid entry focus, and return document unification", "tools/phase348_editable_entry_return_unification_guard.py", "tools/audit_outputs/editable_entry_return_unification_matrix.csv", phase=348),
    ReleaseGateCheck("transaction_entry_cash_footer_polish", "ui", "Editable current-cell highlight, cash party fallback, and unified transaction footer/actions", "tools/phase349_transaction_entry_cash_footer_guard.py", "tools/audit_outputs/transaction_entry_cash_footer_matrix.csv", phase=349),
    ReleaseGateCheck("function_close_lifecycle", "shell", "Function close lifecycle unification", "tools/phase351_function_close_lifecycle_guard.py", "tools/audit_outputs/function_close_lifecycle_matrix.csv", phase=351),
    ReleaseGateCheck("brand_identity_visual_system", "ui", "Brand identity token system for logo-inspired UI", "tools/phase352_brand_identity_visual_guard.py", "tools/audit_outputs/brand_identity_visual_matrix.csv", phase=352),
    ReleaseGateCheck("branded_first_run_runtime", "ui", "Branded login/splash/activation runtime polish", "tools/phase353_branded_first_run_runtime_guard.py", "tools/audit_outputs/branded_first_run_runtime_matrix.csv", phase=353),
    ReleaseGateCheck("branded_shell_runtime", "shell", "Branded tabs, menu and action bar runtime polish", "tools/phase354_branded_shell_runtime_guard.py", "tools/audit_outputs/branded_shell_runtime_matrix.csv", phase=354),
    ReleaseGateCheck("branded_tables_transaction_footer", "ui", "Branded tables and transaction footer runtime polish", "tools/phase355_branded_tables_transaction_footer_guard.py", "tools/audit_outputs/branded_tables_transaction_footer_matrix.csv", phase=355),
    ReleaseGateCheck("branded_dialogs_system_windows", "ui", "Branded dialogs and system-window runtime polish", "tools/phase356_branded_dialogs_system_windows_guard.py", "tools/audit_outputs/branded_dialogs_system_windows_matrix.csv", phase=356),
    ReleaseGateCheck("qss_runtime_safety_hotfix", "ui", "QSS runtime f-string safety hotfix", "tools/phase357_qss_runtime_safety_hotfix_guard.py", "tools/audit_outputs/qss_runtime_safety_matrix.csv", phase=357),
    ReleaseGateCheck("login_layout_stability", "ui", "Login layout safety contract, superseded by Phase359 restore", "tools/phase358_login_layout_stability_guard.py", "tools/audit_outputs/login_layout_stability_matrix.csv", phase=358),
    ReleaseGateCheck("login_phase355_restore", "ui", "Restore LoginDialog design only to Phase355 split layout", "tools/phase359_login_phase355_restore_guard.py", "tools/audit_outputs/login_phase355_restore_matrix.csv", phase=359),
    ReleaseGateCheck("login_rtl_layout", "ui", "Organized RTL-first LoginDialog layout", "tools/phase360_login_rtl_layout_guard.py", "tools/audit_outputs/login_rtl_layout_matrix.csv", phase=360),
    ReleaseGateCheck("login_vertical_expansion", "ui", "Vertically expanded RTL LoginDialog layout", "tools/phase361_login_vertical_expansion_guard.py", "tools/audit_outputs/login_vertical_expansion_matrix.csv", phase=361),
    ReleaseGateCheck("login_no_overlap", "ui", "Login password field and remember/language panel do not overlap", "tools/phase362_login_no_overlap_guard.py", "tools/audit_outputs/login_no_overlap_matrix.csv", phase=362),
    ReleaseGateCheck("login_password_gap", "ui", "Login password field has extra vertical gap from remember/language panel", "tools/phase363_login_password_gap_guard.py", "tools/audit_outputs/login_password_gap_matrix.csv", phase=363),
    ReleaseGateCheck("login_password_visibility", "ui", "Login password field has a reserved visible row before remember/language options", "tools/phase364_login_password_visibility_guard.py", "tools/audit_outputs/login_password_visibility_matrix.csv", phase=364),
    ReleaseGateCheck("login_phase352_restore", "ui", "LoginDialog visual design restored to Phase352 single-card layout", "tools/phase365_login_phase352_restore_guard.py", "tools/audit_outputs/login_phase352_restore_matrix.csv", phase=365),
    ReleaseGateCheck("login_pre352_rtl_safe", "ui", "LoginDialog restored to pre-Phase352 layout with safe RTL ordering", "tools/phase366_login_pre352_rtl_safe_guard.py", "tools/audit_outputs/login_pre352_rtl_safe_matrix.csv", phase=366),
    ReleaseGateCheck("login_pre350_restore", "ui", "LoginDialog visual design restored to original pre-Phase350 baseline", "tools/phase367_login_pre350_restore_guard.py", "tools/audit_outputs/login_pre350_restore_matrix.csv", phase=367),
    ReleaseGateCheck("login_password_toggle_alignment", "ui", "Login password visibility button is a fixed-size peer beside the password field", "tools/phase368_login_password_toggle_alignment_guard.py", "tools/audit_outputs/login_password_toggle_alignment_matrix.csv", phase=368),
    ReleaseGateCheck("warehouse_installer_printing", "packaging", "Warehouse-only installer release and installed printing paths", "tools/phase369_warehouse_installer_printing_guard.py", "tools/audit_outputs/warehouse_installer_printing_matrix.csv", phase=369),
    ReleaseGateCheck("warehouse_executable_identity", "packaging", "Warehouse executable identity end-to-end", "tools/phase370_warehouse_executable_identity_guard.py", "tools/audit_outputs/warehouse_executable_identity_matrix.csv", phase=370),
    ReleaseGateCheck("reused_windows_workflow", "packaging", "Reused full Windows workflow with Warehouse-only release output", "tools/phase371_reused_windows_workflow_guard.py", "tools/audit_outputs/reused_windows_workflow_matrix.csv", phase=371),
    ReleaseGateCheck("workflow_delegated_branding", "packaging", "Branding verifier accepts delegated PyInstaller icon wiring", "tools/phase372_workflow_delegated_branding_guard.py", "tools/audit_outputs/workflow_delegated_branding_matrix.csv", phase=372),
    ReleaseGateCheck("tab_plain_title", "shell", "Workspace tab captions show business titles without main/sub prefixes", "tools/phase373_tab_plain_title_guard.py", "tools/audit_outputs/tab_plain_title_matrix.csv", phase=373),
    ReleaseGateCheck("special_interface_menu_entry_focus", "shell", "Restaurant, cafe and apparel move to one specialized menu while editable grids start at material", "tools/phase374_special_interface_menu_entry_focus_guard.py", "tools/audit_outputs/special_interface_menu_entry_focus_matrix.csv", phase=374),
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
