from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def calls_in_function(source: str, function_name: str):
    tree = ast.parse(source)
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    func = sub.func
                    if isinstance(func, ast.Attribute):
                        calls.append(func.attr)
                    elif isinstance(func, ast.Name):
                        calls.append(func.id)
    return calls


def test_vouchers_use_same_master_detail_shell_as_customer_supplier_lists():
    source = read('alrajhi_client/views/widgets/vouchers_widget.py')
    customers = read('alrajhi_client/views/widgets/customers_widget.py')
    suppliers = read('alrajhi_client/views/widgets/suppliers_widget.py')
    ast.parse(source)
    for marker in ('ResponsiveMasterDetail', 'DetailPlaceholder', 'detail_stack', 'inline_editor_page', 'inline_editor_host'):
        assert marker in source
        assert marker in customers
        assert marker in suppliers
    assert 'self.master_detail = ResponsiveMasterDetail(self.table, self.detail_stack, self)' in source
    assert 'self.stack = QStackedWidget' not in source
    assert 'self.list_page = QWidget' not in source


def test_voucher_add_edit_stay_inline_for_receipt_payment_expense():
    source = read('alrajhi_client/views/widgets/vouchers_widget.py')
    assert '_show_inline_voucher_editor' in source
    assert 'VoucherEditorTab' in source
    assert 'ExpenseDocumentTab' in source
    for voucher_type in ('receipt', 'payment', 'expense'):
        assert f"add_voucher('{voucher_type}')" in source
    for fn in ('add_voucher', 'edit_voucher'):
        calls = calls_in_function(source, fn)
        assert 'open_quick_voucher' not in calls
        assert 'open_document_tab' not in calls
        assert 'open_tab' not in calls


def test_voucher_detail_preview_exists_like_party_preview():
    source = read('alrajhi_client/views/widgets/vouchers_widget.py')
    assert '_connect_selection_preview' in source
    assert '_update_detail_preview' in source
    assert 'self.detail_panel.set_summary' in source
    assert 'self.detail_stack.setCurrentWidget(self.detail_panel)' in source
    assert 'self.detail_stack.setCurrentWidget(self.inline_editor_page)' in source
