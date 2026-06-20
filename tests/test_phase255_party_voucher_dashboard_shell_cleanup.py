from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def test_party_lists_keep_document_shell_primary_and_dialog_fallback():
    for rel, route in (
        ('alrajhi_client/views/widgets/customers_widget.py', "main.open_party_document('customer'"),
        ('alrajhi_client/views/widgets/suppliers_widget.py', "main.open_party_document('supplier'"),
    ):
        source = read(rel)
        ast.parse(source)
        assert route in source
        assert 'AddEntityDialog' in source
        assert 'emergency fallback' in source


def test_party_editor_uses_canonical_document_descriptor():
    source = read('alrajhi_client/features/parties/party_editor_tab.py')
    ast.parse(source)
    assert "super().__init__(party_type" in source
    assert 'DOCUMENT_DESCRIPTOR_BY_PARTY_TYPE' in source
    assert 'DocumentPermissionBinder' in source


def test_voucher_editor_uses_actions_panel_and_browser_backed_export_paths():
    source = read('alrajhi_client/features/vouchers/voucher_editor_tab.py')
    ast.parse(source)
    assert 'VoucherActionsPanel' in source
    assert 'self.actions_panel = VoucherActionsPanel' in source
    assert 'printing_service.voucher_preview' in source
    assert 'printing_service.voucher_pdf' in source


def test_dashboard_modern_visual_components_are_service_fed():
    source = read('alrajhi_client/views/widgets/dashboard_widget.py')
    ast.parse(source)
    assert 'ModernKpiCard' in source
    assert 'DashboardChartPanel' in source
    assert '_build_kpi_grid()' in source
    assert 'dashboard_service.snapshot' in source
    assert 'printing_service' not in source


def test_shell_contract_files_exist():
    assert (ROOT / 'alrajhi_client/features/parties/party_shell_contract.py').exists()
    assert (ROOT / 'alrajhi_client/features/vouchers/voucher_shell_contract.py').exists()
