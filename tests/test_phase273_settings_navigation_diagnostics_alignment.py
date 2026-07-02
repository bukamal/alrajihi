from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
SETTINGS_WIDGET = ROOT / "alrajhi_client" / "views" / "widgets" / "settings_widget.py"
TRANSLATOR = ROOT / "alrajhi_client" / "i18n" / "translator.py"


def _source() -> str:
    return SETTINGS_WIDGET.read_text(encoding="utf-8")


def test_settings_tabs_are_built_from_single_registry():
    src = _source()
    assert "def _settings_tab_specs" in src
    assert "self._settings_tab_registry = tuple(self._settings_tab_specs())" in src
    assert "for _tab_key, factory, label_factory in self._settings_tab_registry" in src
    assert "self.tabs.addTab(factory(), label_factory())" in src


def test_language_refresh_uses_same_registry_not_a_stale_label_list():
    src = _source()
    refresh = src.split("def _refresh_language_texts", 1)[1].split("def save_appearance_settings", 1)[0]
    assert "_settings_tab_registry" in refresh
    assert "label_factory()" in refresh
    assert "labels = [" not in refresh
    assert "phase233_ui_039" not in refresh  # no hard-coded positional title list


def test_settings_registry_contains_expected_tabs_in_order():
    tree = ast.parse(_source())
    method = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_settings_tab_specs"
    )
    return_stmt = next(node for node in ast.walk(method) if isinstance(node, ast.Return))
    keys = []
    for elt in return_stmt.value.elts:
        keys.append(elt.elts[0].value)
    assert keys == [
        "appearance", "languages", "profiles", "contracts", "company",
        "invoices", "units", "returns", "inventory", "manufacturing",
        "reports", "printing", "settings_surface", "pos", "currency", "rates", "network",
        "security", "workflow", "settings_audit", "security_events",
        "backup", "diagnostics",
    ]


def test_diagnostics_tab_is_existing_settings_page_and_has_contract_health():
    src = _source()
    assert "def create_diagnostics_tab" in src
    assert "def _append_unification_diagnostics" in src
    assert "settings_diagnostics_unification_title" in src
    for name in [
        "Document Shell", "List Workspace", "Report Shell", "Operational Shell",
        "Settings Contract", "RBAC Contract", "Branch Scope", "Offline Sync",
        "E2E Scenarios", "Runtime Smoke",
    ]:
        assert name in src


def test_diagnostics_translations_exist_for_three_languages():
    src = TRANSLATOR.read_text(encoding="utf-8")
    assert "_PHASE273_SETTINGS_NAV_TRANSLATIONS" in src
    for lang in ["'ar'", "'en'", "'de'"]:
        assert lang in src
    for key in [
        "settings_diagnostics_title",
        "settings_diagnostics_help",
        "settings_diagnostics_unification_title",
    ]:
        assert key in src
