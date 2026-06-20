from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / 'alrajhi_client/workspace/documents/document_contract.py'


def _load_contract():
    spec = importlib.util.spec_from_file_location('phase249_document_contract', CONTRACT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_phase249_document_contract_exists_and_is_data_only():
    assert CONTRACT_PATH.exists()
    text = CONTRACT_PATH.read_text(encoding='utf-8')
    assert 'class DocumentDescriptor' in text
    assert 'class DocumentPermissions' in text
    assert 'class DocumentCapabilities' in text
    assert 'from PyQt5' not in text


def test_phase249_all_descriptors_validate():
    contract = _load_contract()
    warnings = contract.validate_all_descriptors()
    assert warnings == {}
    descriptors = contract.all_descriptors()
    assert len(descriptors) >= 20
    by_type = {d.document_type: d for d in descriptors}
    for key in [
        'sales_invoice', 'purchase_invoice', 'sales_return', 'purchase_return',
        'material', 'customer', 'supplier', 'voucher', 'warehouse_transfer',
        'reports', 'pos', 'restaurant', 'settings_section',
    ]:
        assert key in by_type


def test_phase249_transaction_documents_are_network_currency_permission_aware():
    contract = _load_contract()
    by_type = {d.document_type: d for d in contract.all_descriptors()}
    for key in ['sales_invoice', 'purchase_invoice', 'sales_return', 'purchase_return']:
        d = by_type[key]
        assert d.shell_family == contract.SHELL_TRANSACTION
        assert d.api_resource.startswith('/api/')
        assert d.remote_gateway
        assert d.local_gateway
        assert d.currency_policy == contract.CURRENCY_DOCUMENT
        assert d.branch_policy == contract.BRANCH_REQUIRED
        assert d.permissions.view
        assert d.permissions.create
        assert d.permissions.update
        assert d.permissions.print
        assert d.capabilities.print is True
        assert d.capabilities.grid_layout is True


def test_phase249_document_classes_declare_contract_hooks():
    expected = {
        'alrajhi_client/features/transactions/transaction_document_tab.py': 'self.document_descriptor = descriptor_for(context.document_type)',
        'alrajhi_client/features/transactions/documents/sales_invoice_tab.py': 'DOCUMENT_DESCRIPTOR = descriptor_for("sales_invoice")',
        'alrajhi_client/features/transactions/documents/purchase_invoice_tab.py': 'DOCUMENT_DESCRIPTOR = descriptor_for("purchase_invoice")',
        'alrajhi_client/features/transactions/documents/sales_return_tab.py': 'DOCUMENT_DESCRIPTOR = descriptor_for("sales_return")',
        'alrajhi_client/features/transactions/documents/purchase_return_tab.py': 'DOCUMENT_DESCRIPTOR = descriptor_for("purchase_return")',
        'alrajhi_client/features/items/item_editor_tab.py': 'DOCUMENT_DESCRIPTOR = descriptor_for("material")',
        'alrajhi_client/features/parties/party_editor_tab.py': 'DOCUMENT_DESCRIPTOR_BY_PARTY_TYPE',
        'alrajhi_client/features/vouchers/voucher_editor_tab.py': 'DOCUMENT_DESCRIPTOR = descriptor_for("voucher")',
        'alrajhi_client/features/finance/documents/expense_document_tab.py': 'DOCUMENT_DESCRIPTOR = descriptor_for("expense")',
        'alrajhi_client/features/inventory/documents/inventory_transfer_document_tab.py': 'DOCUMENT_DESCRIPTOR = descriptor_for("warehouse_transfer")',
        'alrajhi_client/features/settings/settings_document_tabs.py': 'DOCUMENT_DESCRIPTOR = descriptor_for("settings_section")',
    }
    for rel, needle in expected.items():
        text = (ROOT / rel).read_text(encoding='utf-8')
        assert needle in text, rel


def test_phase249_contract_audit_tool_registered():
    tool = ROOT / 'tools/document_shell_contract_audit.py'
    assert tool.exists()
    text = tool.read_text(encoding='utf-8')
    assert 'Document Shell descriptors' in text
    assert 'validate_all_descriptors' in text
    assert 'from PyQt5' not in text
