import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_phase40_workspace_ux_files_are_parseable_and_ui_only():
    for relative in [
        "alrajhi_client/shell/quick_open_dialog.py",
        "alrajhi_client/shell/workspace_state.py",
    ]:
        source = _read(relative)
        ast.parse(source, filename=relative)
        upper = source.upper()
        assert "SELECT " not in upper
        assert "INSERT " not in upper
        assert "UPDATE " not in upper
        assert "DELETE " not in upper


def test_main_window_has_quick_open_recent_and_session_hooks():
    source = _read("alrajhi_client/views/main_window.py")
    ast.parse(source)
    assert "QuickOpenDialog" in source
    assert "WorkspaceStateStore" in source
    assert "Ctrl+K" in source
    assert "open_quick_open" in source
    assert "restore_workspace_session" in source
    assert "save_workspace_session" in source
    assert "workspace_state_store.add_recent" in source


def test_phase40_workspace_translations_exist():
    from alrajhi_client.i18n import translator

    for lang in ("ar", "de", "en"):
        translator.set_language(lang)
        assert translator.translate("workspace.quick_open") != "workspace.quick_open"
        assert translator.translate("workspace.recent_tabs") != "workspace.recent_tabs"
        assert translator.translate("workspace.favorites") != "workspace.favorites"
