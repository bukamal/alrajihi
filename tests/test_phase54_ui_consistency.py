from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase54_guard_exists_and_documents_policy():
    guard = ROOT / 'tools' / 'ui_consistency_guard.py'
    assert guard.exists()
    text = guard.read_text(encoding='utf-8')
    assert 'ALLOWED_HEAVY_UI' in text
    assert 'ALLOWED_DIALOG_FILES' in text
    assert 'open_quick_invoice' in text
    assert 'open_item_document' in text
    assert 'UnifiedActionBar must stay UI-command only' in text


def test_phase54_report_exists():
    report = ROOT / 'docs' / 'UI_CONSISTENCY_PHASE54_REPORT.md'
    assert report.exists()
    text = report.read_text(encoding='utf-8')
    assert 'document-based workspace' in text
    assert 'migration debt' in text
