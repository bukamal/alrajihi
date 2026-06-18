from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_notification_center_component_is_parseable_and_ui_only():
    path = ROOT / "alrajhi_client" / "shell" / "notification_center.py"
    source = path.read_text(encoding="utf-8")
    ast.parse(source)
    assert "class NotificationCenter" in source
    assert "class NotificationCard" in source
    assert "show_temporary" in source
    for forbidden in ("DatabaseConnection", "sqlite3", ".execute(", ".query(", "printing_service"):
        assert forbidden not in source


def test_main_window_uses_notification_center_not_legacy_alert_menu():
    source = (ROOT / "alrajhi_client" / "views" / "main_window.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "NotificationCenter" in source
    assert "refresh_notification_center" in source
    assert "notify_user" in source
    assert "menu.exec_(self.top_bar.alert_btn" not in source


def test_notification_center_translations_exist():
    source = (ROOT / "alrajhi_client" / "i18n" / "translator.py").read_text(encoding="utf-8")
    for key in ("notification.center", "notification.empty", "notification.clear"):
        assert key in source
