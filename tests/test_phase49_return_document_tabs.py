from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_returns_no_longer_use_dialog_document_bridge():
    text = (ROOT / 'alrajhi_client/features/returns/return_editor_tabs.py').read_text(encoding='utf-8')
    assert 'DialogDocumentTab' not in text
    assert 'class _ReturnDocumentMixin' in text
    assert 'workspace_save' in text
    assert 'workspace_print' in text
    assert 'document_payload' in text


def test_return_components_exist_and_are_unit_aware():
    component_dir = ROOT / 'alrajhi_client/features/returns/components'
    for name in ['return_header.py', 'return_lines.py', 'return_settlement.py', 'return_actions.py']:
        assert (component_dir / name).exists()
    lines = (component_dir / 'return_lines.py').read_text(encoding='utf-8')
    assert 'quantity_in_base' in lines
    assert 'conversion_factor' in lines
    assert 'unit_id' in lines
    assert '_ret_unit_price_usd_for_factor' in lines


def test_phase49_guard_is_registered_as_project_guard():
    guard = ROOT / 'tools/document_tabs_phase49_guard.py'
    text = guard.read_text(encoding='utf-8')
    assert 'Phase 49 return document-tabs guard' in text
    assert 'DialogDocumentTab' in text
