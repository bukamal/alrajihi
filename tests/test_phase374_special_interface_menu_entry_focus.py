# -*- coding: utf-8 -*-
"""Phase 374 tests for specialized interface menu and editable-grid entry focus."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))


def test_specialized_interfaces_are_grouped_under_single_menu():
    from workspace.registry.ui_manifest import navigation_menus

    menus = {menu.key: menu for menu in navigation_menus()}
    assert "quick" in menus
    assert menus["quick"].label_key == "nav_special_interfaces"
    assert menus["quick"].icon == "layer-group"
    assert [entry.key for entry in menus["quick"].entries] == ["restaurant", "cafe", "apparel"]
    assert [entry.label_key for entry in menus["quick"].entries] == [
        "restaurant.interface_title",
        "cafe.interface_title",
        "apparel.interface_title",
    ]
    assert "restaurant" not in menus
    assert "cafe" not in menus


def test_specialized_interface_labels_are_translated():
    from i18n.translator import _translations

    expected = {
        "ar": ["واجهات النشاط", "واجهة المطعم", "واجهة المقهى", "واجهة الألبسة"],
        "en": ["Industry interfaces", "Restaurant interface", "Cafe interface", "Apparel interface"],
        "de": ["Branchenoberflächen", "Restaurant-Oberfläche", "Café-Oberfläche", "Bekleidungsoberfläche"],
    }
    for lang, values in expected.items():
        data = str(_translations[lang])
        for value in values:
            assert value in data


def test_transaction_entry_grid_starts_from_item_not_row_or_barcode():
    schema_source = (ROOT / "alrajhi_client/features/transactions/grids/transaction_column_schema.py").read_text(encoding="utf-8")
    assert schema_source.count('TransactionColumn("row", "#", True, True, True, 44, editable=False)') >= 2
    sales_block = schema_source.split("def sales_invoice_schema", 1)[1].split("def purchase_invoice_schema", 1)[0]
    purchase_block = schema_source.split("def purchase_invoice_schema", 1)[1].split("def sales_return_schema", 1)[0]
    for block in (sales_block, purchase_block):
        assert 'TransactionColumn("barcode"' in block
        assert 'TransactionColumn("item"' in block
        # Barcode may remain physically before item in the table, but the keyboard
        # policy must route initial editing to item/material semantically.
        assert block.index('TransactionColumn("barcode"') < block.index('TransactionColumn("item"')


def test_keyboard_policy_prioritizes_item_before_barcode_textually():
    source = (ROOT / "alrajhi_client/ui/table_keyboard_policy.py").read_text(encoding="utf-8")
    assert '_standard_preferred_entry_keys = ("item", "material", "product", "barcode")' in source
    assert "def _standard_entry_priority" in source
    assert "material/item beats barcode" in source
    assert "return sorted(preferred, key=lambda c: (self._standard_entry_priority(c), c))" in source


def test_phase374_guard_summary_is_clean():
    from workspace.quality.special_interface_menu_entry_focus_contract import special_interface_menu_entry_focus_summary

    summary = special_interface_menu_entry_focus_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 18
