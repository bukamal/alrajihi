# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def test_column_preference_runtime_states_cover_contracts():
    from workspace.settings.column_preferences import contract_column_states, validate_column_preference_runtime
    from workspace.tables.table_column_registry import TABLE_COLUMN_CONTRACTS

    assert not validate_column_preference_runtime()
    for contract_id, contract in TABLE_COLUMN_CONTRACTS.items():
        states = contract_column_states(contract_id)
        assert len(states) == len(contract.columns)
        assert all(state.settings["display"].endswith("/visible") for state in states)
        assert all(state.settings["print"].endswith("/printable") for state in states)
        assert all(state.settings["export"].endswith("/exportable") for state in states)


def test_settings_surface_has_runtime_column_editor():
    text = (ROOT / "alrajhi_client/views/widgets/settings_widget.py").read_text(encoding="utf-8")
    assert "settings_surface_columns_table" in text
    assert "save_settings_surface_column_contract" in text
    assert "reset_settings_surface_selected_columns" in text
    assert "QTableWidget" in text


def test_contract_backed_tables_use_runtime_column_customizer():
    custom = (ROOT / "alrajhi_client/views/custom_table_view.py").read_text(encoding="utf-8")
    smart = (ROOT / "alrajhi_client/ui/smart_table_view.py").read_text(encoding="utf-8")
    dialog = (ROOT / "alrajhi_client/views/dialogs/column_contract_customizer.py").read_text(encoding="utf-8")
    assert "show_contract_column_customizer" in custom
    assert "_apply_contract_display_visibility" in custom
    assert "show_contract_column_customizer" in smart
    assert "ColumnContractCustomizerDialog" in dialog


def test_phase342_guard_runs_cleanly():
    from tools.phase342_settings_runtime_wiring_guard import main
    assert main() == 0
