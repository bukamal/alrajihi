from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_invoice_uses_extended_bottom_action_layout():
    text = (ROOT / 'alrajhi_client' / 'views' / 'dialogs' / 'invoice_dialog.py').read_text(encoding='utf-8')
    assert 'SmartTableView' in text
    assert 'BottomActionBar' in text
    assert 'content_splitter = QSplitter(Qt.Horizontal)' in text
    assert 'title_layout.addWidget(btn)' not in text
    assert text.count('left_layout.addWidget(self.lines_table') == 1


def test_smart_table_has_enterprise_column_features():
    text = (ROOT / 'alrajhi_client' / 'ui' / 'smart_table_view.py').read_text(encoding='utf-8')
    for token in ['fit_columns_to_view', 'resizeEvent', 'setSectionsMovable(True)', 'set_column_visible', 'save_layout']:
        assert token in text
