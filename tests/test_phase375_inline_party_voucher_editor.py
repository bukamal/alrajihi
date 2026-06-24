from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
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


def test_customer_supplier_add_edit_are_inline_not_workspace_tabs():
    customers = read('alrajhi_client/views/widgets/customers_widget.py')
    suppliers = read('alrajhi_client/views/widgets/suppliers_widget.py')
    for source, add_fn, edit_fn in ((customers, 'add_customer', 'edit_customer'), (suppliers, 'add_supplier', 'edit_supplier')):
        ast.parse(source)
        assert 'PartyInlineEditorHostMixin' in source
        assert '_install_party_inline_host' in source
        assert '_show_inline_party_editor' in source
        assert 'open_party_document' not in calls_in_function(source, add_fn)
        assert 'open_party_document' not in calls_in_function(source, edit_fn)


def test_vouchers_have_inline_receipt_payment_expense_editors():
    source = read('alrajhi_client/views/widgets/vouchers_widget.py')
    ast.parse(source)
    assert 'UnifiedInlineWorkspaceMixin' in source
    assert '_install_unified_inline_workspace' in source
    assert '_show_inline_voucher_editor' in source
    assert 'VoucherEditorTab' in source
    assert 'ExpenseDocumentTab' in source
    assert 'add_receipt_action' in source
    assert 'add_payment_action' in source
    assert 'add_expense_action' in source
    assert "add_voucher('receipt')" in source
    assert "add_voucher('payment')" in source
    assert "add_voucher('expense')" in source
    assert 'open_quick_voucher' not in calls_in_function(source, 'add_voucher')
    assert 'open_quick_voucher' not in calls_in_function(source, 'edit_voucher')


def test_inline_contract_and_guard_exist():
    assert (ROOT / 'alrajhi_client/workspace/quality/inline_party_voucher_editor_contract.py').exists()
    assert (ROOT / 'tools/phase375_inline_party_voucher_editor_guard.py').exists()
