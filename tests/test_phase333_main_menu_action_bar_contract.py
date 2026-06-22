# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase333_registry_owns_shell_action_specs_and_effective_actions():
    from workspace.registry import ACTION_SPECS, effective_action_keys_for_page, action_specs_for_page, should_show_action_bar

    required = {"new", "save", "refresh", "print", "export", "quick_open", "alert", "theme", "screenshot", "user"}
    assert required.issubset(ACTION_SPECS)
    assert effective_action_keys_for_page("dashboard") == ("refresh", "theme", "screenshot", "user")
    assert "alert" not in effective_action_keys_for_page("dashboard")
    assert should_show_action_bar("dashboard") is True
    sales_keys = effective_action_keys_for_page("sales_invoices")
    assert {"new", "save", "refresh", "print", "export", "quick_open", "alert", "theme", "screenshot", "user"}.issubset(set(sales_keys))
    assert [spec.key for spec in action_specs_for_page("purchase_invoices")][:3] == ["new", "save", "refresh"]


def test_phase333_registry_owns_main_navigation_menus_without_pyqt():
    from workspace.registry import navigation_menus, PAGE_MANIFESTS

    menus = {menu.key: menu for menu in navigation_menus()}
    assert {"home", "sales", "purchases", "inventory", "restaurant", "cafe", "quick"}.issubset(menus)
    page_ids = {entry.page_id for menu in menus.values() for entry in menu.entries if entry.page_id}
    assert {"dashboard", "sales_invoices", "purchase_invoices", "restaurant", "cafe", "apparel", "items"}.issubset(page_ids)
    assert page_ids.issubset(PAGE_MANIFESTS.keys())
    callback_keys = {entry.callback_key for menu in menus.values() for entry in menu.entries if entry.callback_key}
    assert {"open_quick_item", "open_new_sales_invoice", "open_new_purchase_invoice", "open_quick_open"}.issubset(callback_keys)


def test_phase333_main_window_consumes_menu_and_action_contracts():
    main_window = read("alrajhi_client/views/main_window.py")
    assert "navigation_menus" in main_window
    assert "for menu_spec in navigation_menus()" in main_window
    assert "def _menu_callback_map(self):" in main_window
    assert "def _apply_action_bar_contract_for_tab" in main_window
    assert "effective_action_keys_for_page(manifest_id)" in main_window
    assert "self.action_bar.apply_action_contract(keys" in main_window
    assert "self.action_bar.setVisible(should_show_action_bar(pid))" not in main_window


def test_phase333_action_bar_can_show_only_contract_actions():
    action_bar = read("alrajhi_client/shell/unified_action_bar.py")
    assert "from workspace.registry import ACTION_SPECS" in action_bar
    assert "def apply_action_contract" in action_bar
    assert "def visible_action_keys" in action_bar
    assert "self._utility_widgets" in action_bar
    assert "button.setVisible(key in keys)" in action_bar
    assert "self.context_label.setVisible(bool(show_context))" in action_bar


def test_phase333_release_gate_registered_and_documented():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(333, "MAIN_MENU_ACTION_BAR_CONTRACT")' in gate
    assert "tests/test_phase333_main_menu_action_bar_contract.py" in gate
    assert 'ReleaseGateCheck("main_menu_action_bar_contract"' in gate
    assert (ROOT / "PHASE333_MAIN_MENU_ACTION_BAR_CONTRACT.md").exists()
