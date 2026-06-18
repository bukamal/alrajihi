import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_phase43_unified_action_bar_exists_and_is_shell_only():
    source = read("alrajhi_client/shell/unified_action_bar.py")
    ast.parse(source)
    assert "class UnifiedActionBar" in source
    assert "QPrintDialog" not in source
    assert "QPrinter" not in source
    assert "printing_service" in source  # documented routing; actual call remains in existing tab/table methods


def test_phase43_main_window_binds_print_to_existing_unified_command():
    source = read("alrajhi_client/views/main_window.py")
    ast.parse(source)
    assert "UnifiedActionBar" in source
    assert "def setup_action_bar" in source
    assert "self.action_bar.bind('print', self.print_current_tab)" in source
    assert "self.action_bar.bind('export', self.export_current_tab)" in source


def test_phase43_table_printing_still_uses_central_service():
    source = read("alrajhi_client/views/custom_table_view.py")
    ast.parse(source)
    assert "from printing.printing_service import printing_service" in source
    assert "printing_service.report_preview" in source
    assert "printing_service.report_print" in source
    assert "printing_service.report_pdf" in source
