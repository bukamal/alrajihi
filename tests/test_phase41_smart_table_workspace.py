import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_smart_table_view_foundation_is_parseable_and_ui_only():
    source = _read("alrajhi_client/ui/smart_table_view.py")
    ast.parse(source)
    upper = source.upper()
    for token in ["SELECT ", "INSERT ", "UPDATE ", "DELETE "]:
        assert token not in upper
    assert "class SmartTableView" in source
    assert "set_table_identity" in source
    assert "set_local_filter" in source
    assert "selected_source_rows" in source


def test_first_management_tabs_use_smart_table_view():
    for relative in [
        "alrajhi_client/views/widgets/items_widget.py",
        "alrajhi_client/views/widgets/customers_widget.py",
        "alrajhi_client/views/widgets/suppliers_widget.py",
    ]:
        source = _read(relative)
        ast.parse(source)
        assert "from ui.smart_table_view import SmartTableView" in source
        assert "SmartTableView" in source
        assert "CustomTableView" not in source


def test_tabbed_workspace_supports_management_singletons_and_document_tabs():
    source = _read("alrajhi_client/shell/tab_workspace.py")
    ast.parse(source)
    assert "open_singleton" in source
    assert "singleton=False" not in source  # document control is at MainWindow call site
    main = _read("alrajhi_client/views/main_window.py")
    assert "self.workspace.open_tab(tab_id" in main
    assert "singleton=False" in main
    assert "self.workspace.open_singleton" in main
