import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_phase42_rolls_smart_table_into_core_management_widgets():
    widgets = [
        "audit_log_widget.py",
        "base_widget.py",
        "branches_widget.py",
        "cashboxes_widget.py",
        "categories_widget.py",
        "dashboard_widget.py",
        "invoices_widget.py",
        "manufacturing_widget.py",
        "reports_widget.py",
        "returns_widget.py",
        "users_widget.py",
        "vouchers_widget.py",
        "warehouses_widget.py",
    ]
    for filename in widgets:
        source = _read(f"alrajhi_client/views/widgets/{filename}")
        ast.parse(source)
        assert "from ui.smart_table_view import SmartTableView" in source
        assert "from views.custom_table_view import CustomTableView" not in source
        assert "CustomTableView(" not in source


def test_phase42_smart_table_has_shared_erp_actions():
    source = _read("alrajhi_client/ui/smart_table_view.py")
    ast.parse(source)
    for token in [
        "copy_selection",
        "export_to_excel",
        "print_table",
        "set_local_filter",
        "selected_source_rows",
        "reset_layout",
    ]:
        assert token in source


def test_phase42_rollout_guard_exists():
    source = _read("tools/smart_table_rollout_guard.py")
    ast.parse(source)
    assert "SmartTable rollout guard" in source
    assert "CustomTableView" in source
