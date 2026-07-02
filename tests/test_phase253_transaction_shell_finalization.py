# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
import types

ROOT = Path(__file__).resolve().parents[1]


def _load_document_contract():
    workspace_mod = sys.modules.setdefault("workspace", types.ModuleType("workspace"))
    documents_mod = sys.modules.setdefault("workspace.documents", types.ModuleType("workspace.documents"))
    setattr(workspace_mod, "documents", documents_mod)
    name = "workspace.documents.document_contract"
    if name in sys.modules:
        return sys.modules[name]
    path = ROOT / "alrajhi_client" / "workspace" / "documents" / "document_contract.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    setattr(documents_mod, "document_contract", module)
    spec.loader.exec_module(module)
    return module


def _load_transaction_shell_contract():
    _load_document_contract()
    path = ROOT / "alrajhi_client" / "features" / "transactions" / "transaction_shell_contract.py"
    spec = importlib.util.spec_from_file_location("phase253_transaction_shell_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_transaction_shell_contract_routes_are_complete():
    contract = _load_document_contract()
    shell = _load_transaction_shell_contract()
    assert shell.TRANSACTION_DOCUMENT_TYPES == (
        "sales_invoice",
        "purchase_invoice",
        "sales_return",
        "purchase_return",
    )
    assert not shell.validate_transaction_shell_routes()
    for route in shell.TRANSACTION_SHELL_ROUTES:
        descriptor = contract.descriptor_for(route.document_type)
        assert descriptor is not None
        assert descriptor.shell_family == contract.SHELL_TRANSACTION
        assert descriptor.document_class == route.class_path
        assert descriptor.api_resource == route.api_resource
        assert descriptor.currency_policy == contract.CURRENCY_DOCUMENT
        assert descriptor.capabilities.print is True
        assert descriptor.capabilities.export is True
        assert descriptor.capabilities.grid_layout is True
        assert descriptor.permissions.print
        assert descriptor.remote_gateway


def test_transaction_shell_normalizers_and_descriptor_lookup():
    shell = _load_transaction_shell_contract()
    assert shell.normalize_invoice_type("supplier") == "purchase"
    assert shell.normalize_invoice_type("anything") == "sale"
    assert shell.normalize_return_type("buy") == "purchase"
    assert shell.normalize_return_type(None) == "sale"
    assert shell.document_type_for_invoice("sale") == "sales_invoice"
    assert shell.document_type_for_invoice("purchase") == "purchase_invoice"
    assert shell.document_type_for_return("sale") == "sales_return"
    assert shell.document_type_for_return("purchase") == "purchase_return"
    assert shell.route_for_invoice_type("sale").document_type == "sales_invoice"
    assert shell.route_for_return_type("purchase").document_type == "purchase_return"
    assert shell.route_for_document_type("sales_return").is_return is True
    assert shell.descriptor_for_invoice("purchase").document_type == "purchase_invoice"
    assert shell.descriptor_for_return("sale").document_type == "sales_return"


def test_main_window_uses_unified_transaction_shell_before_legacy_fallback():
    source = (ROOT / "alrajhi_client/views/main_window.py").read_text(encoding="utf-8")
    assert "normalize_invoice_type" in source
    assert "normalize_return_type" in source
    assert "SalesInvoiceTab" in source
    assert "PurchaseInvoiceTab" in source
    assert "SalesReturnTab" in source
    assert "PurchaseReturnTab" in source
    assert "Unified transaction document shell unavailable" in source
    assert "Legacy invoice dialog is disabled by Phase414 and quarantined by Phase417" in source
    assert "from features.invoices import InvoiceEditorTab" not in source
    assert "from features.invoices.invoice_editor_tab import" not in source


def test_legacy_transaction_adapters_are_marked_and_not_official_shells():
    invoice_adapter = (ROOT / "alrajhi_client/features/invoices/invoice_editor_tab.py").read_text(encoding="utf-8")
    return_adapter = (ROOT / "alrajhi_client/features/returns/return_editor_tabs.py").read_text(encoding="utf-8")
    assert "LEGACY_TRANSACTION_ADAPTER = True" in invoice_adapter
    assert "LEGACY_TRANSACTION_ADAPTER = True" in return_adapter
    assert "TransactionDocumentTab is the official shell" in invoice_adapter
    assert "TransactionDocumentTab is the official return shell" in return_adapter


def test_legacy_transaction_fallback_is_explicitly_off_by_default():
    source = (ROOT / "alrajhi_client/features/transactions/feature_flags.py").read_text(encoding="utf-8")
    assert "LEGACY_TRANSACTION_DOCUMENTS_DISABLED = True" in source
    assert "def allow_legacy_transaction_documents" in source
    assert "return False" in source
    assert "features/allow_legacy_transaction_documents" not in source
    assert "ALRAJHI_ALLOW_LEGACY_TRANSACTION_DOCUMENTS" not in source
