from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
SETTINGS_WIDGET = ROOT / "alrajhi_client" / "views" / "widgets" / "settings_widget.py"
TRANSLATOR = ROOT / "alrajhi_client" / "i18n" / "translator.py"


def _source() -> str:
    return SETTINGS_WIDGET.read_text(encoding="utf-8")


def _method(name: str):
    tree = ast.parse(_source())
    return next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def test_settings_widget_uses_grouped_top_level_navigation():
    src = _source()
    assert "def _settings_group_specs" in src
    assert "def _build_grouped_settings_tabs" in src
    assert "self._settings_group_registry = tuple(self._settings_group_specs())" in src
    assert "self._build_grouped_settings_tabs()" in src
    assert "self._settings_group_tabs" in src
    assert "settingsGroupTabs_" in src


def test_settings_groups_cover_every_leaf_once():
    specs_method = _method("_settings_tab_specs")
    return_stmt = next(node for node in ast.walk(specs_method) if isinstance(node, ast.Return))
    leaf_keys = [elt.elts[0].value for elt in return_stmt.value.elts]

    group_method = _method("_settings_group_specs")
    group_return = next(node for node in ast.walk(group_method) if isinstance(node, ast.Return))
    grouped_keys = []
    group_names = []
    for group in group_return.value.elts:
        group_names.append(group.elts[0].value)
        grouped_keys.extend([elt.value for elt in group.elts[2].elts])

    assert group_names == [
        "general", "finance", "inventory", "operations", "security", "diagnostics",
    ]
    assert sorted(grouped_keys) == sorted(leaf_keys)
    assert len(grouped_keys) == len(set(grouped_keys)) == len(leaf_keys)


def test_language_refresh_updates_outer_and_inner_tab_titles():
    src = _source().split("def _refresh_language_texts", 1)[1].split("def save_appearance_settings", 1)[0]
    assert "group_label_factory()" in src
    assert "nested.setTabText" in src
    assert "label_factory()" in src
    assert "labels = [" not in src


def test_group_translations_exist_for_three_languages():
    src = TRANSLATOR.read_text(encoding="utf-8")
    assert "_PHASE274_SETTINGS_GROUP_TRANSLATIONS" in src
    for lang in ["'ar'", "'en'", "'de'"]:
        assert lang in src
    for key in [
        "settings_group_general",
        "settings_group_finance",
        "settings_group_inventory",
        "settings_group_operations",
        "settings_group_security",
        "settings_group_diagnostics",
    ]:
        assert key in src
