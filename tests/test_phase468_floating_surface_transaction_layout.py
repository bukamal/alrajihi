from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_phase468_floating_quick_create_has_solid_surface_contract():
    helper = read('alrajhi_client/ui/floating_quick_create.py')
    panel = read('alrajhi_client/ui/inline_quick_create.py')
    qss = read('alrajhi_client/theme/qss.py')
    assert 'def _apply_solid_surface(panel: QWidget) -> None:' in helper
    assert 'setAutoFillBackground(True)' in helper
    assert 'Qt.WA_TranslucentBackground, False' in helper
    assert 'QGraphicsDropShadowEffect' in helper
    assert 'floatingSurfaceSolid' in helper
    assert 'floatingSurfacePhase", "468"' in helper
    assert 'background-color:' in helper
    assert 'QPushButton#InlineQuickCreateCloseButton' in helper
    assert 'InlineQuickCreateCloseButton' in panel
    assert 'floatingSurfacePhase", "468"' in panel
    assert 'QFrame[floatingQuickCreate="true"]' in qss
    assert 'solid floating quick-create surfaces' in qss


def test_phase468_transaction_header_is_split_not_one_line_crowded_toolbar():
    src = read('alrajhi_client/features/transactions/transaction_document_tab.py')
    assert 'TransactionDocumentHeaderShell' in src
    assert 'transactionHeaderPhase", "468"' in src
    assert 'meta_row = QHBoxLayout()' in src
    assert 'search_row = QHBoxLayout()' in src
    assert 'header.addLayout(meta_row)' in src
    assert 'header.addLayout(search_row)' in src
    # The old one-line header pushed party/date/search/preset/save into one HBox.
    assert 'root.addWidget(inline_header)' in src
    assert 'Phase468: split the transaction header into two stable rows' in src


def test_phase468_transaction_bottom_actions_wrap_in_grid():
    src = read('alrajhi_client/features/transactions/components/transaction_bottom_actions.py')
    assert 'QGridLayout' in src
    assert 'transactionActionLayoutPhase", "468"' in src
    assert 'max_per_row = 5' in src
    assert 'row = index // max_per_row' in src
    assert 'layout.addWidget(button, row, col)' in src
    assert 'layout.addStretch' not in src


def test_phase468_i18n_key_leaks_are_hardened():
    src = read('alrajhi_client/i18n/translator.py')
    assert "if key == 'page_of':" in src
    assert "kwargs['total'] = kwargs.get('pages')" in src
    assert "kwargs['pages'] = kwargs.get('total')" in src
    assert "'row_density': 'كثافة الصفوف'" in src
    assert "'density_comfortable': 'مريح'" in src
