from pathlib import Path
root = Path(__file__).resolve().parents[1]
s = (root/'alrajhi_client/views/widgets/returns_widget.py').read_text(encoding='utf-8')
fail=[]
if 'setCellWidget(row, 4' in s or 'unit_combo = QComboBox()' in s:
    fail.append('Unit column still uses always-visible QComboBox cell widgets')
if 'class ReturnUnitDelegate(QStyledItemDelegate)' not in s:
    fail.append('ReturnUnitDelegate is missing')
if s.count('setItemDelegateForColumn(RET_COL_UNIT, ReturnUnitDelegate(self))') < 2:
    fail.append('Delegate not installed for both sales and purchase return dialogs')
if s.count('self.table.clicked.connect(lambda *_: self.toolbar.set_delete_enabled(True))') < 2:
    fail.append('Delete button is not enabled on selection for both return lists')
if s.count('delete_return(rid)') < 2:
    fail.append('Delete/cancel action is not wired to both return services')
if fail:
    print('PHASE125_RETURNS_UNIT_DELEGATE_DELETE_GUARD: FAIL')
    for f in fail:
        print('-', f)
    raise SystemExit(1)
print('PHASE125_RETURNS_UNIT_DELEGATE_DELETE_GUARD: PASS')
