import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_tabbed_workspace_shell_files_exist_and_are_ui_only():
    for relative in [
        "alrajhi_client/shell/tab_workspace.py",
        "alrajhi_client/shell/tab_registry.py",
        "alrajhi_client/shell/tab_state.py",
        "alrajhi_client/shell/shortcuts.py",
    ]:
        source = _read(relative)
        ast.parse(source, filename=relative)
        upper = source.upper()
        assert "SELECT " not in upper
        assert "INSERT " not in upper
        assert "UPDATE " not in upper
        assert "DELETE " not in upper
        assert "DATABASE" not in upper


def test_main_window_uses_tabbed_workspace_not_stacked_window_navigation():
    source = _read("alrajhi_client/views/main_window.py")
    assert "TabbedWorkspace" in source
    assert "self.workspace.open_singleton" in source
    assert "bind_workspace_shortcuts" in source
    assert "QStackedWidget" not in source


def test_workspace_translation_keys_exist_for_all_languages():
    from alrajhi_client.i18n import translator

    for lang in ("ar", "de", "en"):
        translator.set_language(lang)
        assert translator.translate("workspace.unsaved_title") != "workspace.unsaved_title"
        assert translator.translate("workspace.close_tab") != "workspace.close_tab"
