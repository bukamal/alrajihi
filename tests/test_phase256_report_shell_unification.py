# -*- coding: utf-8 -*-
from pathlib import Path
import importlib.util
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "alrajhi_client/workspace/documents/document_contract.py"
REPORT_CONTRACT_PATH = ROOT / "alrajhi_client/features/reports/report_shell_contract.py"
REPORTS_WIDGET_PATH = ROOT / "alrajhi_client/views/widgets/reports_widget.py"
REPORTS_MIXIN_PATH = ROOT / "alrajhi_client/views/widgets/reports_phase36_mixin.py"
REPORT_POLICY_PATH = ROOT / "alrajhi_client/core/services/report_operation_policy.py"
SETTINGS_PATH = ROOT / "alrajhi_client/core/services/settings_service.py"


def _load_report_contract():
    sys.modules.setdefault("workspace", types.ModuleType("workspace"))
    pkg = types.ModuleType("workspace.documents")
    pkg.__path__ = [str(CONTRACT_PATH.parent)]
    sys.modules["workspace.documents"] = pkg

    spec = importlib.util.spec_from_file_location("workspace.documents.document_contract", CONTRACT_PATH)
    contract = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = contract
    spec.loader.exec_module(contract)

    sys.modules.setdefault("features", types.ModuleType("features"))
    pkg2 = types.ModuleType("features.reports")
    pkg2.__path__ = [str(REPORT_CONTRACT_PATH.parent)]
    sys.modules["features.reports"] = pkg2
    spec2 = importlib.util.spec_from_file_location("features.reports.report_shell_contract", REPORT_CONTRACT_PATH)
    module = importlib.util.module_from_spec(spec2)
    assert spec2.loader is not None
    sys.modules[spec2.name] = module
    spec2.loader.exec_module(module)
    return contract, module


def test_phase256_report_shell_contract_is_data_only_and_valid():
    text = REPORT_CONTRACT_PATH.read_text(encoding="utf-8")
    assert "class ReportShellDescriptor" in text
    assert "REPORT_SHELL_DESCRIPTORS" in text
    assert "from PyQt5" not in text
    contract, module = _load_report_contract()
    assert module.validate_all_report_descriptors() == {}
    descriptors = module.all_report_descriptors()
    assert len(descriptors) >= 30
    assert module.REPORTS_DOCUMENT_DESCRIPTOR.document_type == "reports"
    assert module.REPORTS_DOCUMENT_DESCRIPTOR.shell_family == contract.SHELL_REPORT


def test_phase256_core_reports_declare_language_currency_permissions_api_network():
    _contract, module = _load_report_contract()
    by_key = {d.report_key: d for d in module.all_report_descriptors()}
    for key in ["income_statement", "balance_sheet", "trial_balance", "customer_statement", "supplier_statement"]:
        d = by_key[key]
        assert d.i18n_scope == "reports.shell"
        assert d.settings_scope == "reports"
        assert d.permission_view == "reports.view"
        assert d.permission_print == "reports.print"
        assert d.permission_export == "reports.export"
        assert d.currency_policy
        assert d.api_resource.startswith("/api/")
        assert d.network_mode == module.NETWORK_REMOTE_AVAILABLE


def test_phase256_reports_widget_uses_report_shell_contract_and_permission_binder():
    text = REPORTS_WIDGET_PATH.read_text(encoding="utf-8")
    assert "REPORT_SHELL_DESCRIPTORS = all_report_descriptors()" in text
    assert "self.document_descriptor = self.DOCUMENT_DESCRIPTOR" in text
    assert "DocumentPermissionBinder(self.document_descriptor)" in text
    assert "bind_report_widgets(self)" in text
    assert "def _current_report_descriptor" in text
    assert "def can_report_action" in text
    assert "report_api_resource" in text
    assert "report_network_mode" in text


def test_phase256_report_print_uses_print_permission_not_export_permission():
    policy = REPORT_POLICY_PATH.read_text(encoding="utf-8")
    mixin = REPORTS_MIXIN_PATH.read_text(encoding="utf-8")
    settings = SETTINGS_PATH.read_text(encoding="utf-8")
    assert "OP_PRINT = 'print'" in policy
    assert "'allow_print'" in policy
    assert "reports.operation.print" in policy
    assert "reports/operations/allow_print" in settings
    assert "_require_report_print_permission" in mixin
    assert "OP_EXPORT, context=f'report_print" not in mixin


def test_phase256_report_shell_audit_tool_registered():
    tool = ROOT / "tools/report_shell_contract_audit.py"
    assert tool.exists()
    text = tool.read_text(encoding="utf-8")
    assert "Report Shell descriptors" in text
    assert "validate_all_report_descriptors" in text
    assert "from PyQt5" not in text
