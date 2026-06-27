# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_table_direction_policy_declares_arabic_rtl_and_non_arabic_ltr():
    src = read("alrajhi_client/ui/table_direction_policy.py")
    translator = read("alrajhi_client/i18n/translator.py")
    contract = read("alrajhi_client/workspace/quality/table_language_direction_contract.py")

    assert "def apply_table_direction" in src
    assert "def apply_table_direction_tree" in src
    assert "qt_layout_direction" in src
    assert 'RTL_LANGUAGES = {"ar"}' in translator
    for lang in ['"ar": "rtl"', '"de": "ltr"', '"en": "ltr"', '"fr": "ltr"']:
        assert lang in contract


def test_custom_and_editable_tables_use_policy_instead_of_hardcoded_rtl():
    custom = read("alrajhi_client/views/custom_table_view.py")
    editable = read("alrajhi_client/ui/editable_smart_grid.py")
    transaction = read("alrajhi_client/features/transactions/grids/transaction_line_grid.py")

    assert "from ui.table_direction_policy import apply_table_direction" in custom
    assert "apply_table_direction(self)" in custom
    assert "self.setLayoutDirection(Qt.RightToLeft)" not in custom
    assert "from ui.table_direction_policy import apply_table_direction" in editable
    assert "apply_table_direction(self)" in editable
    assert "SmartTableView" in transaction  # inherits the patched Smart/Custom table path


def test_runtime_language_switch_reapplies_table_direction_to_existing_pages():
    settings = read("alrajhi_client/views/widgets/settings_widget.py")
    main_window = read("alrajhi_client/views/main_window.py")
    runtime = read("alrajhi_client/ui/runtime_visual_polish.py")

    assert "from ui.table_direction_policy import apply_table_direction_tree" in settings
    assert "apply_table_direction_tree(self, lang)" in settings
    assert "apply_table_direction_tree(main_window, lang)" in settings
    assert "apply_table_direction_tree(page, lang)" in settings
    assert "from ui.table_direction_policy import apply_table_direction_tree" in main_window
    assert "apply_table_direction_tree(self, self._current_language)" in main_window
    assert "apply_table_direction_tree(root)" in runtime
    assert "apply_table_direction(table)" in runtime


def test_generic_qtablewidget_surfaces_and_modern_helpers_are_bound_to_policy():
    modern = read("alrajhi_client/views/widgets/modern_ui.py")
    restaurant = read("alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    guard = read("tools/phase395_table_language_direction_guard.py")

    assert "widget.setLayoutDirection(qt_layout_direction())" in modern
    assert "dialog.setLayoutDirection(qt_layout_direction())" in modern
    assert "apply_table_direction(child)" in modern
    assert "apply_table_direction(table)" in modern
    invoice_dialog = read("alrajhi_client/views/dialogs/invoice_dialog.py")
    assert "apply_table_direction(self.invoice_table)" in restaurant
    assert "self.setLayoutDirection(qt_layout_direction())" in invoice_dialog
    assert "custom_table_no_hardcoded_rtl" in guard
    assert "modern_walk_no_tuple_findchildren" in guard
