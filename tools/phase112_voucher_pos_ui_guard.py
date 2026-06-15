from pathlib import Path
root = Path(__file__).resolve().parents[1]
vouchers = (root/'alrajhi_client/views/widgets/vouchers_widget.py').read_text(encoding='utf-8')
pos = (root/'alrajhi_client/views/widgets/pos_widget.py').read_text(encoding='utf-8')
translator = (root/'alrajhi_client/i18n/translator.py').read_text(encoding='utf-8')
assert 'self.delete_btn = QPushButton(tr("delete_voucher"))' in vouchers
assert 'delete_selected_voucher' in vouchers
assert 'voucher_service.delete(vid)' in vouchers
assert 'delete_voucher_confirm' in vouchers
assert 'pos/visible_columns' in pos
assert '_build_columns_menu' in pos
assert '_apply_pos_column_visibility' in pos
assert 'setColumnHidden' in pos
assert 'values_by_key' in pos
for key in ['delete_voucher', 'delete_voucher_confirm', 'voucher_deleted', 'pos_columns_btn']:
    assert key in translator, key
print('phase112_voucher_pos_ui_guard: PASS')
