from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase318_shell_menu_compact_and_dashboard_hides_action_bar():
    src = read("alrajhi_client/views/main_window.py")
    assert "btn.setMaximumWidth(88 if not is_home else 68)" in src
    assert "self.menu_bar.setFixedHeight(66)" in src
    assert "self.action_bar.setVisible(pid != 'dashboard')" in src
    assert "QSizePolicy.Fixed" in src


def test_phase318_action_bar_is_compact_shared_chrome():
    src = read("alrajhi_client/shell/unified_action_bar.py")
    assert "self.setFixedHeight(44)" in src
    assert "layout.setSpacing(6)" in src
    assert "padding: 5px 8px" in src


def test_phase318_material_dialog_has_no_visible_top_identity_card():
    src = read("alrajhi_client/views/dialogs/item_dialog.py")
    assert "Do not render a separate top identity card" in src
    assert "main_layout.addWidget(header_card)" not in src
    assert "content_frame = QFrame()" in src


def test_phase318_transaction_grid_is_full_width_with_compact_footer():
    src = read("alrajhi_client/features/transactions/transaction_document_tab.py")
    assert "self.title_label.setVisible(False)" in src
    assert "root.addWidget(self.grid, 1)" in src
    assert "self.notes.setMaximumHeight(78)" in src
    assert "TransactionFooterPanel" in src
    assert "self.totals_panel.set_transaction_type(self.inv_type)" in src


def test_phase318_sales_and_purchase_payment_wording_is_contextual():
    totals = read("alrajhi_client/features/transactions/components/transaction_totals_panel.py")
    assert "def set_transaction_type" in totals
    assert '"transaction_received"' in totals
    tr = read("alrajhi_client/i18n/translator.py")
    assert "'transaction_received': 'المقبوض'" in tr
    assert "'transaction_received': 'Received'" in tr
    assert "'transaction_received': 'Eingegangen'" in tr
    assert "'apparel_col_sku': 'SKU'" not in tr
    assert "'apparel_col_sku': 'رمز المتغير'" in tr
    assert "'apparel_col_sku': 'Variant code'" in tr
