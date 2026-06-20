# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def test_reports_phase36_populates_all_requested_runtime_tables():
    src = read('alrajhi_client/views/widgets/reports_phase36_mixin.py')
    assert 'reporting_service.net_profit_report' in src
    assert 'reporting_service.manufacturing_orders_report' in src
    assert 'reporting_service.product_cost_report' in src
    assert 'self.net_profit_table' in src
    assert 'self.manufacturing_orders_table' in src
    assert 'self.product_cost_table' in src
    assert 'reporting_service.customer_balances()' in src
    assert 'reporting_service.supplier_balances()' in src
    assert 'difference_quantity' in src
    assert 'operational_quantity' in src
    assert 'ledger_quantity' in src


def test_local_reporting_gateway_supports_real_ledger_inventory_and_manufacturing_schemas():
    src = read('alrajhi_client/gateways/local/reporting_gateway.py')
    assert 'journal_lines' in src
    assert 'journal_entry_id' in src
    assert '_entry_expr' in src
    assert 'item_warehouse_balances' in src
    assert 'production_orders' in src
    assert 'product_cost_report' in src
    assert 'expense_date_sql' in src


def test_customer_supplier_balances_are_calculated_from_documents_not_static_balance_only():
    src = read('alrajhi_client/database/dao/reporting_dao.py')
    assert 'def _customer_balance' in src
    assert 'sales_returns' in src
    assert 'purchase_returns' in src
    assert "type IN ('receipt'" in src
    assert "type IN ('payment'" in src
    assert 'calc = self._customer_balance' in src
    assert 'calc = self._supplier_balance' in src


def test_disabled_modules_are_hidden_from_main_navigation_and_quick_open():
    src = read('alrajhi_client/views/main_window.py')
    policy = read('alrajhi_client/workspace/navigation/module_visibility_policy.py')
    assert 'page_enabled' in src
    assert 'settings_section_enabled' in src
    assert 'if page and not page_enabled(page)' in src
    assert "if page_enabled('restaurant')" in src
    assert 'enabled_favorite_pages(favorites)' in src
    assert 'not page_enabled(pid)' in src
    assert "'restaurant': (('restaurant/enabled', True),)" in policy
    assert "'manufacturing': (('manufacturing/enabled', True),)" in policy
    assert "'reports': (('reports/enabled', True),)" in policy
    assert "'pos': (('pos/enabled', True),)" in policy


def test_contract_settings_refresh_menus_after_module_toggle():
    src = read('alrajhi_client/views/widgets/settings_widget.py')
    settings = read('alrajhi_client/core/services/settings_service.py')
    assert "'pos/enabled': self.contract_pos_enabled.isChecked()" in src
    assert "'enabled': self.get_bool('pos/enabled', True)" in settings
    assert 'main_window.setup_menus()' in src
    assert "main_window.switch_page('dashboard')" in src


def test_dashboard_top_cards_and_chart_are_not_built():
    src = read('alrajhi_client/views/widgets/dashboard_widget.py')
    build_ui = src.split('def _build_ui', 1)[1].split('def _build_hero', 1)[0]
    assert 'self._build_kpi_grid()' not in build_ui
    assert 'Phase 282: do not build the top KPI/card strip or chart panel' in src
    assert "if not self.cards and not hasattr(self, 'trend_panel')" in src
