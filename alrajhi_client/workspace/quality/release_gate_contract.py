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
# PHASE409_BASIT_FINAL_ACCEPTANCE_AUDIT is tracked below in REQUIRED_PHASE_DOCS.
# PHASE410_BASIT_RELEASE_CANDIDATE_FREEZE is tracked below in REQUIRED_PHASE_DOCS.
# PHASE411_BASIT_SHELL_MENU_REBUILD_HOTFIX is tracked below in REQUIRED_PHASE_DOCS.
# PHASE412_EDITABLE_GRID_NAVIGATION_ENGINE is tracked below in REQUIRED_PHASE_DOCS.
# PHASE413_USER_PREFERENCES_PERSISTENCE is tracked below in REQUIRED_PHASE_DOCS.
# PHASE414_LEGACY_ELIMINATION_FOUNDATION is tracked below in REQUIRED_PHASE_DOCS.
# PHASE415_UNIFIED_SALES_INVOICE_GRID_RUNTIME is tracked below in REQUIRED_PHASE_DOCS.
# PHASE416_RUNTIME_ACCEPTANCE_HARNESS is tracked below in REQUIRED_PHASE_DOCS.
# PHASE417_LEGACY_TRANSACTION_QUARANTINE is tracked below in REQUIRED_PHASE_DOCS.
# PHASE418_EDITABLE_GRID_LIFECYCLE_UNIFICATION is tracked below in REQUIRED_PHASE_DOCS.
# PHASE419_PREFERENCES_REGISTRY_CONSOLIDATION is tracked below in REQUIRED_PHASE_DOCS.
# PHASE420_API_MULTIUSER_PARITY_AUDIT_HARDENING is tracked below in REQUIRED_PHASE_DOCS.
# PHASE421_ACTIVATION_SECURITY_HARDENING is tracked below in REQUIRED_PHASE_DOCS.
# PHASE422_I18N_RTL_QUALITY_GATE is tracked below in REQUIRED_PHASE_DOCS.
# PHASE423_GOLDEN_DATASET_ACCOUNTING_INVENTORY_SCENARIO_PACK is tracked below in REQUIRED_PHASE_DOCS.
# PHASE424_GOLDEN_DATASET_RUNTIME_REPLAY_BRIDGE is tracked below in REQUIRED_PHASE_DOCS.
# PHASE425_EDITABLE_GRID_ENTER_PRESERVE_HOTFIX is tracked below in REQUIRED_PHASE_DOCS.
# PHASE426_EDITABLE_GRID_ENTER_DESTINATION_FOCUS_HOTFIX is tracked below in REQUIRED_PHASE_DOCS.
# PHASE427_DIRECT_QTABLEWIDGET_EDITABLE_SWEEP is tracked below in REQUIRED_PHASE_DOCS.
# PHASE428_OPERATIONAL_ITEM_CARD_GRID_UNIFICATION is tracked below in REQUIRED_PHASE_DOCS.
# PHASE429_SHARED_OPERATIONAL_FULLSCREEN_MODE is tracked below in REQUIRED_PHASE_DOCS.
# PHASE430_POS_BARCODE_TABLE_FIRST_LAYOUT is tracked below in REQUIRED_PHASE_DOCS.
# tests/test_phase409_basit_final_acceptance_audit.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase410_basit_release_candidate_freeze.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase411_basit_shell_menu_rebuild_hotfix.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase412_editable_grid_navigation_engine.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase413_user_preferences_persistence.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase414_legacy_elimination_foundation.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase415_unified_sales_invoice_grid_runtime.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase416_runtime_acceptance_harness.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase417_legacy_transaction_quarantine.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase418_editable_grid_lifecycle_unification.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase419_preferences_registry_consolidation.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase420_api_multiuser_parity.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase421_activation_security.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase422_i18n_rtl_quality.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase423_golden_dataset_scenarios.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase424_golden_dataset_runtime_replay.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase425_editable_grid_enter_preserve.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase426_editable_grid_enter_destination_focus.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase427_direct_qtablewidget_editable_sweep.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase428_operational_item_card_grid.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase429_operational_fullscreen.py is generated from REQUIRED_PHASE_TESTS.
# tests/test_phase430_pos_barcode_table_first.py is generated from REQUIRED_PHASE_TESTS.

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
        (375, "INLINE_PARTY_VOUCHER_EDITOR"),
        (376, "VOUCHER_MASTER_DETAIL_INLINE"),
        (377, "INLINE_MANAGEMENT_EDITOR"),
        (378, "INLINE_RUNTIME_HOTFIX"),
        (379, "INLINE_PARTY_LAYOUT_UNIFICATION"),
        (380, "UNIFIED_INLINE_WORKSPACE"),
        (381, "DOCUMENT_LAYOUT_FAMILY_CONTRACT"),
        (382, "EDITABLE_GRID_RUNTIME_POLISH"),
        (383, "MENU_INLINE_ACTION_ROUTING"),
        (384, "DASHBOARD_TABLE_RUNTIME_POLISH"),
        (385, "EDITABLE_GRID_UNIT_ENTER"),
        (386, "EDITABLE_GRID_INVOICE_ENTER_ROUTE"),
        (387, "INVOICE_RETURN_LIST_ACTIONS"),
        (388, "EDITABLE_GRID_MOUSE_ACTION_BOUNDARY"),
        (389, "EDITABLE_GRID_ROW_ACTION_BOUNDARY"),
        (390, "ITEM_DELETE_ACTIVE_USAGE"),
        (391, "ITEM_DELETE_BOM_USAGE_RESOLVER"),
        (392, "FRENCH_LANGUAGE"),
        (393, "LANGUAGE_RUNTIME_SWITCH_HOTFIX"),
        (394, "RESTAURANT_SIMPLE_POS"),
        (395, "TABLE_LANGUAGE_DIRECTION"),
        (396, "RESTAURANT_ITEM_CARD_SURFACE"),
        (397, "FEATURE_ACTIVATION_GATE"),
        (398, "CATEGORY_INLINE_SAVE_BUTTON"),
        (401, "BASIT_INSPIRED_VISUAL_SYSTEM"),
        (402, "BASIT_DASHBOARD_SURFACE"),
        (403, "BASIT_TRANSACTION_SURFACE"),
        (404, "BASIT_MANAGEMENT_SURFACE"),
        (405, "BASIT_REPORTS_SETTINGS_SURFACE"),
        (406, "BASIT_SHELL_CHROME"),
        (407, "BASIT_STARTUP_DIALOGS_SURFACE"),
        (408, "BASIT_PRINTING_SURFACE"),
        (409, "BASIT_FINAL_ACCEPTANCE_AUDIT"),
        (410, "BASIT_RELEASE_CANDIDATE_FREEZE"),
        (411, "BASIT_SHELL_MENU_REBUILD_HOTFIX"),
        (412, "EDITABLE_GRID_NAVIGATION_ENGINE"),
        (413, "USER_PREFERENCES_PERSISTENCE"),
        (414, "LEGACY_ELIMINATION_FOUNDATION"),
        (415, "UNIFIED_SALES_INVOICE_GRID_RUNTIME"),
        (416, "RUNTIME_ACCEPTANCE_HARNESS"),
        (417, "LEGACY_TRANSACTION_QUARANTINE"),
        (418, "EDITABLE_GRID_LIFECYCLE_UNIFICATION"),
        (419, "PREFERENCES_REGISTRY_CONSOLIDATION"),
        (420, "API_MULTIUSER_PARITY_AUDIT_HARDENING"),
        (421, "ACTIVATION_SECURITY_HARDENING"),
        (422, "I18N_RTL_QUALITY_GATE"),
        (423, "GOLDEN_DATASET_ACCOUNTING_INVENTORY_SCENARIO_PACK"),
        (424, "GOLDEN_DATASET_RUNTIME_REPLAY_BRIDGE"),
        (425, "EDITABLE_GRID_ENTER_PRESERVE_HOTFIX"),
        (426, "EDITABLE_GRID_ENTER_DESTINATION_FOCUS_HOTFIX"),
        (427, "DIRECT_QTABLEWIDGET_EDITABLE_SWEEP"),
        (428, "OPERATIONAL_ITEM_CARD_GRID_UNIFICATION"),
        (429, "SHARED_OPERATIONAL_FULLSCREEN_MODE"),
        (430, "POS_BARCODE_TABLE_FIRST_LAYOUT"),
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
        (375, "inline_party_voucher_editor"),
        (376, "voucher_master_detail_inline"),
        (377, "inline_management_editor"),
        (378, "inline_runtime_hotfix"),
        (379, "inline_party_layout_unification"),
        (380, "unified_inline_workspace"),
        (381, "document_layout_family_contract"),
        (382, "editable_grid_runtime_polish"),
        (383, "menu_inline_action_routing"),
        (384, "dashboard_table_runtime_polish"),
        (385, "editable_grid_unit_enter"),
        (386, "editable_grid_invoice_enter_route"),
        (387, "invoice_return_list_actions"),
        (388, "editable_grid_mouse_action_boundary"),
        (389, "editable_grid_row_action_boundary"),
        (390, "item_delete_active_usage"),
        (391, "item_delete_bom_usage_resolver"),
        (392, "french_language"),
        (393, "language_runtime_switch"),
        (394, "restaurant_simple_pos"),
        (395, "table_language_direction"),
        (396, "restaurant_item_card_surface"),
        (397, "feature_activation_gate"),
        (398, "category_inline_save"),
        (401, "basit_visual_system"),
        (402, "basit_dashboard_surface"),
        (403, "basit_transaction_surface"),
        (404, "basit_management_surface"),
        (405, "basit_reports_settings_surface"),
        (406, "basit_shell_chrome"),
        (407, "basit_startup_dialogs_surface"),
        (408, "basit_printing_surface"),
        (409, "basit_final_acceptance_audit"),
        (410, "basit_release_candidate_freeze"),
        (411, "basit_shell_menu_rebuild_hotfix"),
        (412, "editable_grid_navigation_engine"),
        (413, "user_preferences_persistence"),
        (414, "legacy_elimination_foundation"),
        (415, "unified_sales_invoice_grid_runtime"),
        (416, "runtime_acceptance_harness"),
        (417, "legacy_transaction_quarantine"),
        (418, "editable_grid_lifecycle_unification"),
        (419, "preferences_registry_consolidation"),
        (420, "api_multiuser_parity"),
        (421, "activation_security"),
        (422, "i18n_rtl_quality"),
        (423, "golden_dataset_scenarios"),
        (424, "golden_dataset_runtime_replay"),
        (425, "editable_grid_enter_preserve"),
        (426, "editable_grid_enter_destination_focus"),
        (427, "direct_qtablewidget_editable_sweep"),
        (428, "operational_item_card_grid"),
        (429, "operational_fullscreen"),
        (430, "pos_barcode_table_first"),
        (431, "horizontal_branded_login_layout"),
        (432, "horizontal_login_runtime_stabilization"),
        (433, "login_password_row_visibility_fix"),
        (434, "branded_prelogin_startup_splash"),
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
    ReleaseGateCheck("inline_party_voucher_editor", "shell", "Customer, supplier and voucher lists open Add/Edit inline instead of spawning tabs", "tools/phase375_inline_party_voucher_editor_guard.py", "tools/audit_outputs/inline_party_voucher_editor_matrix.csv", phase=375),
    ReleaseGateCheck("voucher_master_detail_inline", "shell", "Voucher list uses the same master-detail inline editor structure as customers and suppliers", "tools/phase376_voucher_master_detail_inline_guard.py", "tools/audit_outputs/voucher_master_detail_inline_matrix.csv", phase=376),
    ReleaseGateCheck("inline_management_editor", "shell", "Users, categories, warehouses and branches add/edit inline instead of spawning sub-tabs", "tools/phase377_inline_management_editor_guard.py", "tools/audit_outputs/inline_management_editor_matrix.csv", phase=377),
    ReleaseGateCheck("inline_runtime_hotfix", "shell", "Inline runtime hotfix for users, vouchers, cashboxes and menu routes", "tools/phase378_inline_runtime_hotfix_guard.py", "tools/audit_outputs/inline_runtime_hotfix_matrix.csv", phase=378),
    ReleaseGateCheck("inline_party_layout_unification", "shell", "Customer and supplier inline editors share one wide layout without duplicate title cards", "tools/phase379_inline_party_layout_unification_guard.py", "tools/audit_outputs/inline_party_layout_unification_matrix.csv", phase=379),
    ReleaseGateCheck("unified_inline_workspace", "shell", "All inline master-detail editors share one wide layout and minimal outer chrome", "tools/phase380_unified_inline_workspace_guard.py", "tools/audit_outputs/unified_inline_workspace_matrix.csv", phase=380),
    ReleaseGateCheck("document_layout_family_contract", "shell", "Document editors declare card, financial, or tabular layout families for inline and standalone use", "tools/phase381_document_layout_family_contract_guard.py", "tools/audit_outputs/document_layout_family_contract_matrix.csv", phase=381),
    ReleaseGateCheck("editable_grid_runtime_polish", "ui", "Editable grids resolve barcode/material cells, jump to quantity, and focus newly inserted lines", "tools/phase382_editable_grid_runtime_polish_guard.py", "tools/audit_outputs/editable_grid_runtime_polish_matrix.csv", phase=382),
    ReleaseGateCheck("menu_inline_action_routing", "shell", "Main menu and action-bar New route management creation into inline workspaces", "tools/phase383_menu_inline_action_routing_guard.py", "tools/audit_outputs/menu_inline_action_routing_matrix.csv", phase=383),
    ReleaseGateCheck("dashboard_table_runtime_polish", "ui", "Dashboard labels, daily actions, and table Enter/centering polish", "tools/phase384_dashboard_table_runtime_polish_guard.py", "tools/audit_outputs/phase384_dashboard_table_runtime_polish_matrix.csv", phase=384),
    ReleaseGateCheck("editable_grid_unit_enter", "ui", "Editable grids move from material/barcode to unit before quantity", "tools/phase385_editable_grid_unit_enter_guard.py", "tools/audit_outputs/editable_grid_unit_enter_matrix.csv", phase=385),
    ReleaseGateCheck("editable_grid_invoice_enter_route", "ui", "Sales and purchase invoice Enter traversal follows business column order without clearing data", "tools/phase386_editable_grid_invoice_enter_route_guard.py", "tools/audit_outputs/editable_grid_invoice_enter_route_matrix.csv", phase=386),
    ReleaseGateCheck("invoice_return_list_actions", "transactions", "Sales/purchase invoice and return list Edit/Delete actions resolve source rows and enforce dependencies", "tools/phase387_invoice_return_list_actions_guard.py", "tools/audit_outputs/invoice_return_list_actions_matrix.csv", phase=387),
    ReleaseGateCheck("editable_grid_mouse_action_boundary", "ui", "Editable grid Enter navigation does not steal mouse clicks from side action buttons", "tools/phase388_editable_grid_mouse_action_boundary_guard.py", "tools/audit_outputs/editable_grid_mouse_action_boundary_matrix.csv", phase=388),
    ReleaseGateCheck("editable_grid_row_action_boundary", "ui", "List tables keep row selection while editable grids keep Enter cell traversal", "tools/phase389_editable_grid_row_action_boundary_guard.py", "tools/audit_outputs/editable_grid_row_action_boundary_matrix.csv", phase=389),
    ReleaseGateCheck("item_delete_active_usage", "materials", "Item delete/archive guard counts only active dependencies and ignores deleted invoices/cancelled production orders", "tools/phase390_item_delete_active_usage_guard.py", "tools/audit_outputs/item_delete_active_usage_matrix.csv", phase=390),
    ReleaseGateCheck("item_delete_bom_usage_resolver", "materials", "Item delete explains active BOM blockers by recipe/product name and resolution path", "tools/phase391_item_delete_bom_usage_resolver_guard.py", "tools/audit_outputs/item_delete_bom_usage_resolver_matrix.csv", phase=391),
    ReleaseGateCheck("french_language", "i18n", "French language covers UI, print and report translation surfaces", "tools/phase392_french_language_guard.py", "tools/audit_outputs/french_language_matrix.csv", phase=392),
    ReleaseGateCheck("language_runtime_switch", "i18n", "Language runtime switch cannot recurse during UI refresh", "tools/phase393_language_runtime_switch_guard.py", "tools/audit_outputs/language_runtime_switch_matrix.csv", phase=393),
    ReleaseGateCheck("restaurant_simple_pos", "restaurant", "Restaurant workspace is a simple POS with categories, items and invoice table", "tools/phase394_restaurant_simple_pos_guard.py", "tools/audit_outputs/restaurant_simple_pos_matrix.csv", phase=394),
    ReleaseGateCheck("table_language_direction", "i18n", "Tables follow UI language direction: Arabic RTL and non-Arabic LTR", "tools/phase395_table_language_direction_guard.py", "tools/audit_outputs/table_language_direction_matrix.csv", phase=395),
    ReleaseGateCheck("restaurant_item_card_surface", "restaurant", "Restaurant POS item browser uses the same rectangular card surface as categories", "tools/phase396_restaurant_item_card_surface_guard.py", "tools/audit_outputs/restaurant_item_card_surface_matrix.csv", phase=396),
    ReleaseGateCheck("feature_activation_gate", "activation", "Manufacturing, restaurant, cafe and apparel require a unified activation key before entry", "tools/phase397_feature_activation_gate_guard.py", "tools/audit_outputs/feature_activation_gate_matrix.csv", phase=397),
    ReleaseGateCheck("category_inline_save", "categories", "Category inline creation keeps a visible Save button outside hidden header cards", "tools/phase398_category_inline_save_guard.py", "tools/audit_outputs/category_inline_save_matrix.csv", phase=398),
    ReleaseGateCheck("basit_visual_system", "theme", "Basit-inspired operational palette, sizing and POS/dashboard visual skin", "tools/phase401_basit_visual_system_guard.py", "tools/audit_outputs/basit_visual_system_matrix.csv", phase=401),
    ReleaseGateCheck("basit_dashboard_surface", "dashboard", "Dashboard shortcuts, panels and cash surfaces use the Basit-inspired visual system", "tools/phase402_basit_dashboard_surface_guard.py", "tools/audit_outputs/basit_dashboard_surface_matrix.csv", phase=402),
    ReleaseGateCheck("basit_transaction_surface", "transactions", "Sales/purchase invoices and returns use Basit-inspired toolbar, grid and totals surfaces", "tools/phase403_basit_transaction_surface_guard.py", "tools/audit_outputs/basit_transaction_surface_matrix.csv", phase=403),
    ReleaseGateCheck("basit_management_surface", "management", "Materials, parties, categories, vouchers and inline master-detail lists use the Basit-inspired list surface", "tools/phase404_basit_management_surface_guard.py", phase=404),
    ReleaseGateCheck("basit_reports_settings_surface", "reports_settings", "Reports and Settings use the Basit-inspired filter, tab, card and summary surfaces", "tools/phase405_basit_reports_settings_surface_guard.py", "tools/audit_outputs/basit_reports_settings_surface_matrix.csv", phase=405),
    ReleaseGateCheck("basit_shell_chrome", "shell", "Main menu, shared action bar and workspace tabs use the Basit-inspired shell chrome", "tools/phase406_basit_shell_chrome_guard.py", "tools/audit_outputs/basit_shell_chrome_matrix.csv", phase=406),
    ReleaseGateCheck("basit_startup_dialogs_surface", "dialogs", "Startup, login, activation and system dialogs use the Basit-inspired entry surface", "tools/phase407_basit_startup_dialogs_surface_guard.py", "tools/audit_outputs/basit_startup_dialogs_surface_matrix.csv", phase=407),
    ReleaseGateCheck("basit_printing_surface", "printing", "Invoices, receipts, reports, manufacturing and inventory browser HTML prints use the Basit-inspired print palette", "tools/phase408_basit_printing_surface_guard.py", "tools/audit_outputs/basit_printing_surface_matrix.csv", phase=408),
    ReleaseGateCheck("basit_final_acceptance", "acceptance", "Final Basit-inspired visual acceptance gate across runtime, printing, startup and shell surfaces", "tools/phase409_basit_final_acceptance_audit.py", "tools/audit_outputs/basit_final_acceptance_matrix.csv", phase=409),
    ReleaseGateCheck("basit_release_candidate_freeze", "acceptance", "Freeze the Phase401-409 Basit-inspired visual stack as RC1 after final acceptance and release gates", "tools/phase410_basit_release_candidate_freeze.py", "tools/audit_outputs/basit_release_candidate_matrix.csv", phase=410),
    ReleaseGateCheck("basit_shell_menu_rebuild_hotfix", "shell", "Main IconMenuBar rebuilds cleanly across RTL/LTR and suppresses native QToolButton menu artefacts", "tools/phase411_basit_shell_menu_rebuild_hotfix.py", "tools/audit_outputs/basit_shell_menu_rebuild_matrix.csv", phase=411),
    ReleaseGateCheck("editable_grid_navigation_engine", "ui", "Editable table Enter traversal is centralized, preserves values and creates at most one trailing row", "tools/phase412_editable_grid_navigation_engine_guard.py", "tools/audit_outputs/editable_grid_navigation_engine_matrix.csv", phase=412),
    ReleaseGateCheck("user_preferences_persistence", "settings", "Dashboard privacy and runtime UI preferences persist per user across application restarts", "tools/phase413_user_preferences_persistence_guard.py", "tools/audit_outputs/user_preferences_persistence_matrix.csv", phase=413),
    ReleaseGateCheck("legacy_elimination_foundation", "architecture", "Legacy shell and transaction fallback routes are removed from production navigation", "tools/phase414_legacy_elimination_foundation_guard.py", "tools/audit_outputs/legacy_elimination_foundation_matrix.csv", phase=414),
    ReleaseGateCheck("unified_sales_invoice_grid_runtime", "ui", "Sales invoice grid uses a clean editor-entry hook and idempotent row lifecycle", "tools/phase415_unified_sales_invoice_grid_runtime_guard.py", "tools/audit_outputs/unified_sales_invoice_grid_runtime_matrix.csv", phase=415),
    ReleaseGateCheck("runtime_acceptance_harness", "acceptance", "Qt runtime acceptance harness captures shell geometry and editable-grid key navigation evidence", "tools/phase416_runtime_acceptance_harness_guard.py", "tools/audit_outputs/runtime_acceptance_harness_matrix.csv", phase=416),
    ReleaseGateCheck("legacy_transaction_quarantine", "architecture", "Legacy invoice and return adapters fail before loading old dialog code and cannot be used as production fallback", "tools/phase417_legacy_transaction_quarantine_guard.py", "tools/audit_outputs/legacy_transaction_quarantine_matrix.csv", phase=417),
    ReleaseGateCheck("editable_grid_lifecycle_unification", "ui", "Editable grid row lifecycle is unified across transactions, inventory transfers and BOM components", "tools/phase418_editable_grid_lifecycle_unification_guard.py", "tools/audit_outputs/editable_grid_lifecycle_unification_matrix.csv", phase=418),
    ReleaseGateCheck("preferences_registry_consolidation", "settings", "UI preferences resolve through a central scoped registry with QSettings usage audited", "tools/phase419_preferences_registry_consolidation_guard.py", "tools/audit_outputs/preferences_registry_consolidation_matrix.csv", phase=419),
    ReleaseGateCheck("api_multiuser_parity", "api", "API local/remote parity, branch scope, offline replay and idempotency metadata are audited", "tools/phase420_api_multiuser_parity_guard.py", "tools/audit_outputs/api_multiuser_parity_matrix.csv", phase=420),
    ReleaseGateCheck("activation_security", "security", "Activation records, signed license policy and production diagnostics exposure are hardened", "tools/phase421_activation_security_guard.py", "tools/audit_outputs/activation_security_matrix.csv", phase=421),
    ReleaseGateCheck("i18n_rtl_quality", "i18n", "Language catalog coverage and RTL/LTR runtime direction wiring are audited", "tools/phase422_i18n_rtl_quality_guard.py", "tools/audit_outputs/i18n_rtl_quality_matrix.csv", phase=422),
    ReleaseGateCheck("golden_dataset_scenarios", "accounting", "Golden accounting and inventory dataset reconciles invoices, returns, transfers, manufacturing, POS, restaurant and vouchers", "tools/phase423_golden_dataset_scenarios_guard.py", "tools/audit_outputs/golden_dataset_scenarios_matrix.csv", phase=423),
    ReleaseGateCheck("golden_dataset_runtime_replay", "accounting", "Golden dataset operation stream replays through a runtime adapter protocol and compares actual balances with Phase423 expectations", "tools/phase424_golden_dataset_runtime_replay_guard.py", "tools/audit_outputs/golden_dataset_runtime_replay_matrix.csv", phase=424),
    ReleaseGateCheck("editable_grid_enter_preserve", "ui", "Enter inside editable grid cells preserves untouched values and commits only real user edits", "tools/phase425_editable_grid_enter_preserve_guard.py", "tools/audit_outputs/editable_grid_enter_preserve_matrix.csv", phase=425),
    ReleaseGateCheck("editable_grid_enter_destination_focus", "ui", "Enter navigation selects destination cells without auto-opening editors that can clear them", "tools/phase426_editable_grid_enter_destination_focus_guard.py", "tools/audit_outputs/editable_grid_enter_destination_focus_matrix.csv", phase=426),
    ReleaseGateCheck("direct_qtablewidget_editable_sweep", "ui", "Editable direct QTableWidget surfaces are migrated to EditableSmartGrid or classified read-only", "tools/phase427_direct_qtablewidget_editable_sweep_guard.py", "tools/audit_outputs/direct_qtablewidget_editable_sweep_matrix.csv", phase=427),
    ReleaseGateCheck("operational_item_card_grid", "ui", "Restaurant and cafe material surfaces share a three-column operational item-card grid; POS is barcode/table-first", "tools/phase428_operational_item_card_grid_guard.py", "tools/audit_outputs/operational_item_card_grid_matrix.csv", phase=428),
    ReleaseGateCheck("operational_fullscreen", "ui", "POS, restaurant and cafe share a central operational fullscreen controller", "tools/phase429_operational_fullscreen_guard.py", "tools/audit_outputs/operational_fullscreen_matrix.csv", phase=429),
    ReleaseGateCheck("pos_barcode_table_first", "ui", "POS keeps barcode/search and cart table only while Restaurant/Cafe keep material cards", "tools/phase430_pos_barcode_table_first_guard.py", "tools/audit_outputs/pos_barcode_table_first_matrix.csv", phase=430),
    ReleaseGateCheck("horizontal_branded_login", "dialogs", "Login screen uses a horizontal branded identity/form layout", "tools/phase431_horizontal_branded_login_guard.py", phase=431),
    ReleaseGateCheck("horizontal_login_runtime_stabilization", "dialogs", "Horizontal login runtime dimensions, titlebar and non-overlap are stabilized", "tools/phase432_horizontal_login_runtime_stabilization_guard.py", phase=432),
    ReleaseGateCheck("login_password_row_visibility", "dialogs", "Login password input row remains visible before language options", "tools/phase433_login_password_row_visibility_guard.py", phase=433),
    ReleaseGateCheck("branded_prelogin_startup_splash", "dialogs", "Pre-login startup splash uses branded staged loading without legacy yellow header", "tools/phase434_branded_prelogin_startup_splash_guard.py", "tools/audit_outputs/branded_prelogin_startup_splash_matrix.json", phase=434),
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
