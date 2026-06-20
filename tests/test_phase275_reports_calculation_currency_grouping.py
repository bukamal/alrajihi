from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_WIDGET = ROOT / "alrajhi_client" / "views" / "widgets" / "reports_widget.py"
TRANSLATOR = ROOT / "alrajhi_client" / "i18n" / "translator.py"


def _src(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_reports_widget_uses_grouped_report_navigation():
    src = _src(REPORTS_WIDGET)
    assert "def _build_grouped_report_tabs" in src
    assert "reports_group_financial" in src
    assert "reports_group_inventory" in src
    assert "reports_group_cash_pos" in src
    assert "self._report_tab_to_group" in src
    # Concrete report tabs should no longer be added directly to the top-level report tab widget.
    assert "self.tabs.addTab(self.income_tab" not in src
    assert "self.tabs.addTab(self.report_audit_tab" not in src


def test_reports_refresh_and_print_resolve_active_inner_report_tab():
    src = _src(REPORTS_WIDGET)
    mixin = _src(ROOT / "alrajhi_client" / "views" / "widgets" / "reports_phase36_mixin.py")
    assert "def _active_report_tab" in src
    assert "def _active_report_title" in src
    assert "def _report_table_for_tab" in src
    assert "self._active_report_tab()" in src
    assert "self._active_report_title()" in mixin
    assert "self._report_table_for_tab(tab)" in mixin


def test_reports_use_unified_money_helpers_for_known_bad_tables():
    src = _src(REPORTS_WIDGET)
    assert "def _money(" in src
    assert "def _qty(" in src
    assert "'avg': self._money(avg, display_curr)" in src
    assert "'value': self._money(value, display_curr)" in src
    assert "'cost': self._money(m.get('unit_cost') or 0, display_curr)" in src
    assert "'opening': self._money(s.get('opening_amount') or 0, display_curr)" in src
    assert "currency.format_amount(avg)" not in src
    assert "currency.format_amount(value)" not in src
    assert "currency.format_amount(s.get('opening_amount')" not in src


def test_reports_have_calculated_summary_for_income_and_balance():
    src = _src(REPORTS_WIDGET)
    assert "{tr('total_income')}: {self._money(total_income, display_curr)}" in src
    assert "{tr('total_expenses')}: {self._money(total_expenses, display_curr)}" in src
    assert "{tr('total_assets')}: {self._money(total_assets, display_curr)}" in src


def test_report_group_titles_are_translated_in_three_languages():
    src = _src(TRANSLATOR)
    for key in [
        "reports_group_financial",
        "reports_group_parties",
        "reports_group_inventory",
        "reports_group_cash_pos",
        "reports_group_profit_manufacturing",
        "reports_group_diagnostics",
        "total_income",
        "total_expenses",
    ]:
        assert src.count(f"'{key}'") >= 3
